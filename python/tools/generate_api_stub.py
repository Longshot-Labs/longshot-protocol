"""Generate Python API typing contracts from the runtime mirror and Rust serde metadata."""

from __future__ import annotations

import argparse
import ast
import copy
import runpy
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


def _is_dataclass(node: ast.ClassDef) -> bool:
    return any(
        (isinstance(decorator, ast.Name) and decorator.id == "dataclass")
        or (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "dataclass"
        )
        for decorator in node.decorator_list
    )


def _is_dto(node: ast.ClassDef) -> bool:
    return _is_dataclass(node) and any(
        isinstance(base, ast.Name) and base.id == "LongshotModel" for base in node.bases
    )


def _unwrap_optional(annotation: ast.expr) -> ast.expr:
    if (
        isinstance(annotation, ast.Subscript)
        and isinstance(annotation.value, ast.Name)
        and annotation.value.id == "Optional"
    ):
        return annotation.slice
    return annotation


def _stub_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    name: Optional[str] = None,
    classmethod: bool = False,
) -> List[str]:
    copied = copy.deepcopy(node)
    if name is not None:
        copied.name = name
    copied.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
    copied.decorator_list = [
        decorator
        for decorator in copied.decorator_list
        if isinstance(decorator, ast.Name)
        and decorator.id in {"classmethod", "staticmethod", "property"}
    ]
    if classmethod and not any(
        isinstance(decorator, ast.Name) and decorator.id == "classmethod"
        for decorator in copied.decorator_list
    ):
        copied.decorator_list.insert(0, ast.Name(id="classmethod"))
    return ast.unparse(ast.fix_missing_locations(copied)).splitlines()


def _field_nodes(node: ast.ClassDef) -> List[ast.AnnAssign]:
    return [
        item
        for item in node.body
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
    ]


def _field_name(field: ast.AnnAssign) -> str:
    if not isinstance(field.target, ast.Name):
        raise ValueError("DTO fields must use simple names")
    return field.target.id


def _render_dto_body(
    node: ast.ClassDef, required: Set[str], required_nullable: Set[str]
) -> List[str]:
    fields = _field_nodes(node)
    lines: List[str] = []
    for field in fields:
        name = _field_name(field)
        annotation = (
            _unwrap_optional(field.annotation)
            if name in required
            else field.annotation
        )
        lines.append(f"{name}: {ast.unparse(annotation)}")

    if fields:
        parameters = []
        for field in fields:
            name = _field_name(field)
            annotation = (
                _unwrap_optional(field.annotation)
                if name in required
                else field.annotation
            )
            default = "" if name in required or name in required_nullable else " = ..."
            parameters.append(f"{name}: {ast.unparse(annotation)}{default}")
        lines.append("def __init__(self, *, " + ", ".join(parameters) + ") -> None: ...")
    else:
        lines.append("def __init__(self) -> None: ...")
    return lines


def _render_class(
    node: ast.ClassDef,
    required: Set[str],
    required_nullable: Set[str],
    dynamic_methods: Dict[str, List[Tuple[str, ast.FunctionDef, bool]]],
) -> List[str]:
    bases = ", ".join(ast.unparse(base) for base in node.bases)
    header = f"class {node.name}({bases}):" if bases else f"class {node.name}:"
    body: List[str] = []

    if _is_dto(node):
        body.extend(_render_dto_body(node, required, required_nullable))
    elif _is_dataclass(node):
        for field in _field_nodes(node):
            body.append(f"{_field_name(field)}: {ast.unparse(field.annotation)}")
        parameters = [
            f"{_field_name(field)}: {ast.unparse(field.annotation)}"
            + (" = ..." if field.value is not None else "")
            for field in _field_nodes(node)
        ]
        body.append("def __init__(self, " + ", ".join(parameters) + ") -> None: ...")
    else:
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        body.append(f"{target.id} = {ast.unparse(item.value)}")
            elif (
                isinstance(item, ast.AnnAssign)
                and isinstance(item.target, ast.Name)
                and not item.target.id.startswith("_")
            ):
                body.append(f"{item.target.id}: {ast.unparse(item.annotation)}")

    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body.extend(_stub_function(item))
    for name, function, is_classmethod in dynamic_methods.get(node.name, []):
        body.extend(_stub_function(function, name=name, classmethod=is_classmethod))

    if not body:
        body.append("...")
    return [header, *(f"    {line}" if line else "" for line in body)]


def _export_names(tree: ast.Module) -> List[str]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, list) and all(isinstance(item, str) for item in value):
                return value
    raise ValueError("api.py must define __all__ as a list of strings")


def _dynamic_methods(
    tree: ast.Module,
    functions: Dict[str, ast.FunctionDef],
) -> Dict[str, List[Tuple[str, ast.FunctionDef, bool]]]:
    methods: Dict[str, List[Tuple[str, ast.FunctionDef, bool]]] = {}
    for node in tree.body:
        if not (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Attribute)
            and isinstance(node.targets[0].value, ast.Name)
        ):
            continue
        target = node.targets[0]
        if target.attr.startswith("__serde_"):
            continue
        value = node.value
        is_classmethod = False
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "classmethod"
            and len(value.args) == 1
        ):
            value = value.args[0]
            is_classmethod = True
        if isinstance(value, ast.Name) and value.id in functions:
            if not isinstance(target.value, ast.Name):
                continue
            methods.setdefault(target.value.id, []).append(
                (target.attr, functions[value.id], is_classmethod)
            )
    return methods


def _assignment(node: ast.Assign | ast.AnnAssign) -> Iterable[Tuple[str, str]]:
    if isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            yield node.target.id, ast.unparse(node.value) if node.value else "..."
        return
    for target in node.targets:
        if isinstance(target, ast.Name):
            yield target.id, ast.unparse(node.value)


def render_api_stub(
    api_path: Path,
    required_fields: Dict[str, Set[str]],
    required_nullable_fields: Dict[str, Set[str]],
) -> str:
    tree = ast.parse(api_path.read_text())
    exports = _export_names(tree)
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assignments = {
        name: value
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for name, value in _assignment(node)
    }
    dynamic_methods = _dynamic_methods(
        tree,
        {name: node for name, node in functions.items() if isinstance(node, ast.FunctionDef)},
    )

    lines = [
        '"""Generated public API typing contracts. Do not edit by hand."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, Dict, List, Optional",
        "from uuid import UUID",
        "",
        "from .model import LongshotModel, RustStringEnum, RustTaggedUnion",
        "from .taker import OrderLeg, SignedOrder",
        "from .types import (",
        "    Address,",
        "    Direction,",
        "    MarketId,",
        "    MarketStatus,",
        "    MarketType,",
        "    Odds,",
        "    OrderType,",
        "    Outcome,",
        "    PositionId,",
        "    TradingChannel,",
        ")",
        "",
        "# Runtime dataclasses remain permissive for decoding, but Rust-required fields",
        "# must be supplied by typed callers; nullable fields retain Optional annotations.",
    ]

    for name in exports:
        lines.append("")
        if name in classes:
            lines.extend(
                _render_class(
                    classes[name],
                    required_fields.get(name, set()),
                    required_nullable_fields.get(name, set()),
                    dynamic_methods,
                )
            )
        elif name in functions:
            lines.extend(_stub_function(functions[name]))
        elif name in assignments:
            lines.append(f"{name} = {assignments[name]}")
        else:
            raise ValueError(f"export {name} has no declaration")

    lines.extend(["", "__all__ = ["])
    lines.extend(f'    "{name}",' for name in exports)
    lines.extend(["]", ""])
    rendered = "\n".join(lines)
    ast.parse(rendered)
    return rendered


def _required_fields(
    repo_root: Path,
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    generator = runpy.run_path(
        str(repo_root / "python" / "tools" / "generate_serde_metadata.py")
    )
    _, required, required_nullable, _, _ = generator["collect_serde_metadata"](
        repo_root / "rust" / "src"
    )
    return required, required_nullable


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    api_path = repo_root / "python" / "src" / "longshot_protocol" / "api.py"
    output = api_path.with_suffix(".pyi")
    rendered = render_api_stub(api_path, *_required_fields(repo_root))
    if args.stdout:
        print(rendered, end="")
    elif args.check:
        if not output.exists() or output.read_text() != rendered:
            raise SystemExit(f"{output} is stale; regenerate the API stub")
    else:
        output.write_text(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
