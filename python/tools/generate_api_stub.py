"""Generate Python API typing contracts from the runtime mirror and Rust serde metadata."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import keyword
import re
import runpy
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


PUBLIC_SUPPLEMENTAL_CLASS_INVENTORY = {
    "__init__.py": set(),
    "_serde_metadata.py": set(),
    "mm.py": {"AuthChallengeIdError", "MmDecodeError"},
    "model.py": {"LongshotModel", "RustStringEnum", "RustTaggedUnion"},
    "rfq.py": {
        "_CallableOdds",
        "_CallableOrderType",
        "_CallablePriceWindowSecs",
        "BroadcastRfqRequest",
        "QuoteResponse",
        "RfqLeg",
        "RfqLegType",
        "RfqLegWire",
        "RfqLegWireDecodeError",
        "TakerMetadata",
    },
    "taker.py": {"OrderLeg", "SignedOrder", "SignedOrderError", "TakerSignError"},
    "types.py": {
        "Address",
        "Amount",
        "Asset",
        "ClientQuoteId",
        "ContestId",
        "Direction",
        "Duration",
        "MarketId",
        "MarketStatus",
        "MarketType",
        "MathError",
        "Odds",
        "OrderType",
        "Outcome",
        "PositionId",
        "QuoteId",
        "RequestId",
        "Timestamp",
        "TradingChannel",
        "UserId",
        "UserTier",
        "UuidId",
        "_AssetMeta",
    },
    "ws.py": {
        "ClientMessage",
        "QuoteResultStatus",
        "RfqSubscription",
        "ServerMessage",
    },
}

PUBLIC_SUPPLEMENTAL_DEFINITION_INVENTORY = {
    "mm.py": {
        "AUTH_DOMAIN",
        "AuthChallengeIdError",
        "MmDecodeError",
        "auth_response_message",
        "build_auth_message",
        "decode_broadcast_rfq",
        "decode_quote_response",
        "encode_quote_response",
        "parse_auth_challenge_id",
        "quote_response_message",
        "sign_auth_response",
        "sign_quote_response",
        "signed_quote_response",
        "signed_quote_response_with_client_quote_id",
    },
    "model.py": {
        "LongshotModel",
        "RustStringEnum",
        "RustStringEnumT",
        "RustTaggedUnion",
        "RustTaggedUnionT",
        "T",
        "is_model_instance",
        "to_serde_value",
    },
    "rfq.py": {
        "BROADCAST_RFQ_REQUEST_SIZE",
        "BroadcastRfqRequest",
        "MAX_RFQ_LEGS",
        "QUOTE_RESPONSE_SIGNED_DATA_SIZE",
        "QUOTE_RESPONSE_SIZE",
        "QuoteResponse",
        "RFQ_LEG_TYPE_BINARY_EVENT_TAG",
        "RFQ_LEG_TYPE_PRICE_STRIKE_TAG",
        "RFQ_LEG_WIRE_FORMAT",
        "RFQ_LEG_WIRE_SIZE",
        "RFQ_PROTOCOL_VERSION",
        "RfqLeg",
        "RfqLegType",
        "RfqLegWire",
        "RfqLegWireDecodeError",
        "TAKER_METADATA_WIRE_SIZE",
        "TakerMetadata",
    },
    "taker.py": {
        "OrderLeg",
        "SignedOrder",
        "SignedOrderError",
        "TakerSignError",
        "sign_order",
        "signed_order",
    },
    "types.py": {
        "Address",
        "Amount",
        "Asset",
        "ClientQuoteId",
        "ContestId",
        "Direction",
        "Duration",
        "MIN_BET_MICROS",
        "MarketId",
        "MarketStatus",
        "MarketType",
        "MathError",
        "Odds",
        "OrderType",
        "Outcome",
        "PositionId",
        "QuoteId",
        "RequestId",
        "Timestamp",
        "TradingChannel",
        "U64_MAX",
        "UserId",
        "UserTier",
        "UuidId",
    },
    "ws.py": {
        "ClientMessage",
        "QuoteResultStatus",
        "RfqSubscription",
        "ServerMessage",
    },
}

# Wheels and sdists publish the package source and documentation verbatim. Lock
# every approved package path and byte so comments, runtime effects, and package
# data cannot enter the external artifact without a boundary review.
PUBLIC_PYTHON_PACKAGE_SHA256 = "0a0ebd090d1cd021f2cf9371607ecac9d36272673038dc4535776a40314da4d1"
PUBLIC_PYTHON_RELEASE_FILES_SHA256 = "75495bda0e504f4abb7bde8fad6d92f8f9e67030dd6587bbeb936a9c530fa064"

PUBLIC_ROOT_SUPPLEMENTAL_EXPORTS = {
    "AUTH_DOMAIN",
    "Address",
    "Amount",
    "Asset",
    "AuthChallengeIdError",
    "BroadcastRfqRequest",
    "ClientMessage",
    "ClientQuoteId",
    "ContestId",
    "Direction",
    "Duration",
    "MAX_RFQ_LEGS",
    "MIN_BET_MICROS",
    "MarketId",
    "MarketStatus",
    "MarketType",
    "MathError",
    "MmDecodeError",
    "Odds",
    "OrderLeg",
    "OrderType",
    "Outcome",
    "PositionId",
    "QuoteId",
    "QuoteResponse",
    "QuoteResultStatus",
    "RFQ_LEG_TYPE_BINARY_EVENT_TAG",
    "RFQ_LEG_TYPE_PRICE_STRIKE_TAG",
    "RFQ_PROTOCOL_VERSION",
    "RequestId",
    "RfqLeg",
    "RfqLegType",
    "RfqLegWire",
    "RfqLegWireDecodeError",
    "RfqSubscription",
    "ServerMessage",
    "SignedOrder",
    "SignedOrderError",
    "TakerMetadata",
    "TakerSignError",
    "Timestamp",
    "TradingChannel",
    "UserId",
    "UserTier",
    "auth_response_message",
    "build_auth_message",
    "decode_broadcast_rfq",
    "decode_quote_response",
    "encode_quote_response",
    "parse_auth_challenge_id",
    "quote_response_message",
    "sign_auth_response",
    "sign_order",
    "sign_quote_response",
    "signed_order",
    "signed_quote_response",
    "signed_quote_response_with_client_quote_id",
}

PUBLIC_API_HELPER_EXPORTS = {
    "build_wallet_authentication_message",
    "build_wallet_withdrawal_authorization_message",
    "encode_wallet_signature",
}


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


def _top_level_binding_names(tree: ast.Module) -> List[str]:
    names = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            names.extend(
                target.id for target in node.targets if isinstance(target, ast.Name)
            )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.append(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names.extend(
                alias.asname or alias.name.split(".")[0]
                for alias in node.names
                if alias.name != "*"
            )
    return names


def _top_level_local_definition_names(tree: ast.Module) -> List[str]:
    names = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            names.extend(
                target.id for target in node.targets if isinstance(target, ast.Name)
            )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.append(node.target.id)
    return names


def _read_rust_attr(lines: List[str], index: int) -> Tuple[str, int]:
    attr = lines[index].strip()
    depth = attr.count("[") - attr.count("]")
    index += 1
    while index < len(lines) and depth > 0:
        line = lines[index].strip()
        attr += " " + line
        depth += line.count("[") - line.count("]")
        index += 1
    return attr, index


def _python_field_name(rust_name: str) -> str:
    name = rust_name.removeprefix("r#")
    return f"{name}_" if keyword.iskeyword(name) else name


def _snake_case(name: str) -> str:
    value = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value).lower()


def _rust_renamed_variant(name: str, rename_all: Optional[str]) -> str:
    if rename_all == "snake_case":
        return _snake_case(name)
    if rename_all == "lowercase":
        return name.lower()
    return name


def _rust_api_enum_inventory(
    repo_root: Path,
) -> Dict[str, Tuple[str, List[str], Optional[str], Optional[str], bool, bool]]:
    inventory = {}
    api_dir = repo_root / "rust" / "src" / "api"
    for path in sorted(api_dir.glob("*.rs")):
        if path.name in {"mod.rs", "wire_int.rs"}:
            continue
        lines = path.read_text().splitlines()
        attrs: List[str] = []
        index = 0
        while index < len(lines):
            line = lines[index].strip()
            if line.startswith("#["):
                attr, index = _read_rust_attr(lines, index)
                attrs.append(attr)
                continue
            match = re.match(r"pub\s+enum\s+([A-Za-z0-9_]+)", line)
            if match is None:
                if line and not line.startswith(("//", "///", "//!")):
                    attrs = []
                index += 1
                continue

            name = match.group(1)
            enum_attrs, attrs = attrs, []
            is_serde = any(
                re.search(r"\b(?:Serialize|Deserialize)\b", attr)
                for attr in enum_attrs
            )
            rename_all_match = next(
                (
                    re.search(r'rename_all\s*=\s*"([^"]+)"', attr)
                    for attr in enum_attrs
                    if "rename_all" in attr
                ),
                None,
            )
            rename_all = rename_all_match.group(1) if rename_all_match else None
            tag_match = next(
                (re.search(r'tag\s*=\s*"([^"]+)"', attr) for attr in enum_attrs if "tag" in attr),
                None,
            )
            content_match = next(
                (
                    re.search(r'content\s*=\s*"([^"]+)"', attr)
                    for attr in enum_attrs
                    if "content" in attr
                ),
                None,
            )
            tag = tag_match.group(1) if tag_match else None
            content = content_match.group(1) if content_match else None
            untagged = any(re.search(r"\buntagged\b", attr) for attr in enum_attrs)

            depth = line.count("{") - line.count("}")
            index += 1
            variants: List[str] = []
            variant_attrs: List[str] = []
            has_payload = False
            while index < len(lines) and depth > 0:
                raw = lines[index]
                stripped = raw.strip()
                if stripped.startswith("#["):
                    attr, index = _read_rust_attr(lines, index)
                    variant_attrs.append(attr)
                    continue
                if depth == 1 and stripped and not stripped.startswith(("//", "///")):
                    variant_match = re.match(r"([A-Za-z0-9_]+)\s*(.*)$", stripped)
                    if variant_match and variant_match.group(1) != "where":
                        variant_name, suffix = variant_match.groups()
                        if not any("doc(hidden)" in attr.replace(" ", "") for attr in variant_attrs):
                            rename = next(
                                (
                                    match.group(1)
                                    for attr in variant_attrs
                                    if (match := re.search(r'rename\s*=\s*"([^"]+)"', attr))
                                ),
                                None,
                            )
                            variants.append(rename or _rust_renamed_variant(variant_name, rename_all))
                            has_payload |= suffix.lstrip().startswith(("(", "{"))
                        variant_attrs = []
                depth += raw.count("{") - raw.count("}")
                index += 1

            base = "RustTaggedUnion" if has_payload or tag or content or untagged else "RustStringEnum"
            inventory[name] = (base, variants, tag, content, untagged, is_serde)
    return inventory


def _class_bases(node: ast.ClassDef) -> Set[str]:
    return {
        base.id
        for base in node.bases
        if isinstance(base, ast.Name)
    }


def _class_assignment(node: ast.ClassDef, name: str, default: object) -> object:
    for item in node.body:
        if not isinstance(item, (ast.Assign, ast.AnnAssign)):
            continue
        targets = [item.target] if isinstance(item, ast.AnnAssign) else item.targets
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            if item.value is None:
                return default
            return ast.literal_eval(item.value)
    return default


def _python_string_enum_variants(node: ast.ClassDef) -> List[str]:
    variants = []
    for item in node.body:
        if not isinstance(item, (ast.Assign, ast.AnnAssign)):
            continue
        targets = [item.target] if isinstance(item, ast.AnnAssign) else item.targets
        if len(targets) != 1 or not isinstance(targets[0], ast.Name):
            continue
        if targets[0].id.startswith("_") or item.value is None:
            continue
        value = ast.literal_eval(item.value)
        if isinstance(value, str):
            variants.append(value)
    return variants


def _rust_api_inventory(repo_root: Path) -> Tuple[Set[str], Dict[str, List[str]]]:
    declarations: Set[str] = set()
    struct_fields: Dict[str, List[str]] = {}
    api_dir = repo_root / "rust" / "src" / "api"
    for path in sorted(api_dir.glob("*.rs")):
        if path.name in {"mod.rs", "wire_int.rs"}:
            continue
        lines = path.read_text().splitlines()
        pending_attrs: List[str] = []
        index = 0
        while index < len(lines):
            line = lines[index].strip()
            if line.startswith("#["):
                attr, index = _read_rust_attr(lines, index)
                pending_attrs.append(attr)
                continue
            if not line or line.startswith(("///", "//!")):
                index += 1
                continue

            declaration = re.match(r"pub\s+(struct|enum)\s+([A-Za-z0-9_]+)", line)
            attrs, pending_attrs = pending_attrs, []
            if declaration is None:
                index += 1
                continue

            kind, name = declaration.groups()
            hidden = any("doc(hidden)" in attr.replace(" ", "") for attr in attrs)
            if not hidden:
                declarations.add(name)

            if kind == "enum":
                depth = line.count("{") - line.count("}")
                index += 1
                while index < len(lines) and depth > 0:
                    depth += lines[index].count("{") - lines[index].count("}")
                    index += 1
                continue

            if re.match(r"pub\s+struct\s+[A-Za-z0-9_]+\s*\(", line):
                if not hidden:
                    struct_fields[name] = ["value"]
                index += 1
                continue
            if "{}" in line:
                if not hidden:
                    struct_fields[name] = []
                index += 1
                continue

            fields: List[str] = []
            depth = line.count("{") - line.count("}")
            index += 1
            while index < len(lines) and depth > 0:
                raw = lines[index]
                field = re.match(r"pub\s+((?:r#)?[A-Za-z0-9_]+)\s*:", raw.strip())
                if field is not None:
                    fields.append(_python_field_name(field.group(1)))
                depth += raw.count("{") - raw.count("}")
                index += 1
            if not hidden:
                struct_fields[name] = fields
    return declarations, struct_fields


def _validate_api_inventory(repo_root: Path, tree: ast.Module) -> None:
    exports = set(_export_names(tree))
    class_nodes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    duplicate_classes = sorted(
        {
            node.name
            for node in class_nodes
            if sum(candidate.name == node.name for candidate in class_nodes) > 1
        }
    )
    if duplicate_classes:
        raise SystemExit(
            "Python api.py has duplicate classes: " + ", ".join(duplicate_classes)
        )
    classes = {node.name: node for node in class_nodes}
    expected, struct_fields = _rust_api_inventory(repo_root)
    actual = set(classes)
    extra = sorted(actual - expected)
    missing = sorted(expected - actual)
    if extra or missing:
        raise SystemExit(
            f"closed Python protocol inventory drift: extra=[{', '.join(extra)}], "
            f"missing=[{', '.join(missing)}]"
        )

    expected_exports = expected | PUBLIC_API_HELPER_EXPORTS
    extra_exports = sorted(exports - expected_exports)
    missing_exports = sorted(expected_exports - exports)
    if extra_exports or missing_exports:
        raise SystemExit(
            "closed Python api.py export inventory drift: "
            f"extra=[{', '.join(extra_exports)}], missing=[{', '.join(missing_exports)}]"
        )
    bindings = _top_level_binding_names(tree)
    duplicate_export_bindings = sorted(
        name for name in expected_exports if bindings.count(name) != 1
    )
    if duplicate_export_bindings:
        raise SystemExit(
            "Python api.py exported bindings must be declared once: "
            + ", ".join(duplicate_export_bindings)
        )
    local_definitions = [
        name for name in _top_level_local_definition_names(tree) if not name.startswith("_")
    ]
    extra_definitions = sorted(set(local_definitions) - expected_exports)
    if len(set(local_definitions)) != len(local_definitions) or extra_definitions:
        raise SystemExit(
            "closed Python api.py definition inventory drift: "
            f"extra=[{', '.join(extra_definitions)}]"
        )

    for name, expected_fields in struct_fields.items():
        expected_bases = {"LongshotModel"}
        actual_bases = _class_bases(classes[name])
        if actual_bases != expected_bases:
            raise SystemExit(
                f"Python protocol class kind drift for {name}: "
                f"expected=[{', '.join(sorted(expected_bases))}], "
                f"actual=[{', '.join(sorted(actual_bases))}]"
            )
        actual_fields = [_field_name(field) for field in _field_nodes(classes[name])]
        if actual_fields != expected_fields:
            raise SystemExit(
                f"Python protocol field inventory drift for {name}: "
                f"expected=[{', '.join(expected_fields)}], "
                f"actual=[{', '.join(actual_fields)}]"
            )

    for name, (base, variants, tag, content, untagged, is_serde) in _rust_api_enum_inventory(
        repo_root
    ).items():
        node = classes[name]
        actual_bases = _class_bases(node)
        if actual_bases != {base}:
            raise SystemExit(
                f"Python protocol enum kind drift for {name}: "
                f"expected={base}, actual=[{', '.join(sorted(actual_bases))}]"
            )
        if base == "RustStringEnum":
            actual_variants = _python_string_enum_variants(node)
        else:
            mapping = _class_assignment(node, "__serde_variants__", {})
            if not isinstance(mapping, dict) or not all(
                isinstance(value, str) for value in mapping.values()
            ):
                raise SystemExit(f"Python protocol enum variants are invalid for {name}")
            actual_variants = list(mapping.values())
            actual_shape = (
                _class_assignment(node, "__serde_tag__", None),
                _class_assignment(node, "__serde_content__", None),
                _class_assignment(node, "__serde_untagged__", False),
            )
            if is_serde and actual_shape != (tag, content, untagged):
                raise SystemExit(
                    f"Python protocol enum shape drift for {name}: "
                    f"expected={tag, content, untagged}, actual={actual_shape}"
                )
        if actual_variants != variants:
            raise SystemExit(
                f"Python protocol enum variant drift for {name}: "
                f"expected=[{', '.join(variants)}], "
                f"actual=[{', '.join(actual_variants)}]"
            )


def _validate_supplemental_class_inventory(repo_root: Path) -> None:
    source_dir = repo_root / "python" / "src"
    package_dir = source_dir / "longshot_protocol"
    expected_modules = set(PUBLIC_SUPPLEMENTAL_CLASS_INVENTORY) | {"api.py"}
    expected_package_files = expected_modules | {
        "CUSTOM_CLIENTS.md",
        "README.md",
        "api.pyi",
        "py.typed",
    }
    expected_source_files = {
        f"longshot_protocol/{path}" for path in expected_package_files
    }
    source_entries = [
        path
        for path in source_dir.rglob("*")
        if "__pycache__" not in path.relative_to(source_dir).parts
        and path.suffix not in {".pyc", ".pyo"}
    ]
    symbolic_links = sorted(
        path.relative_to(source_dir).as_posix()
        for path in source_entries
        if path.is_symlink()
    )
    if symbolic_links:
        raise SystemExit(
            "Python package source may not contain symbolic links: "
            + ", ".join(symbolic_links)
        )
    actual_source_files = {
        path.relative_to(source_dir).as_posix()
        for path in source_entries
        if path.is_file()
    }
    extra_source_files = sorted(actual_source_files - expected_source_files)
    missing_source_files = sorted(expected_source_files - actual_source_files)
    if extra_source_files or missing_source_files:
        raise SystemExit(
            "closed Python source file inventory drift: "
            f"extra=[{', '.join(extra_source_files)}], "
            f"missing=[{', '.join(missing_source_files)}]"
        )
    for file_name, expected in PUBLIC_SUPPLEMENTAL_CLASS_INVENTORY.items():
        tree = ast.parse((package_dir / file_name).read_text())
        names = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
        duplicates = sorted(
            {name for name in names if names.count(name) > 1}
        )
        if duplicates:
            raise SystemExit(
                f"Python {file_name} has duplicate classes: {', '.join(duplicates)}"
            )
        actual = set(names)
        extra = sorted(actual - expected)
        missing = sorted(expected - actual)
        if extra or missing:
            raise SystemExit(
                f"closed Python {file_name} class inventory drift: "
                f"extra=[{', '.join(extra)}], missing=[{', '.join(missing)}]"
            )
        bindings = _top_level_binding_names(tree)
        rebound = sorted(name for name in expected if bindings.count(name) != 1)
        if rebound:
            raise SystemExit(
                f"Python {file_name} class bindings must be declared once: "
                + ", ".join(rebound)
            )
        expected_definitions = PUBLIC_SUPPLEMENTAL_DEFINITION_INVENTORY.get(file_name)
        if expected_definitions is not None:
            definitions = [
                name
                for name in _top_level_local_definition_names(tree)
                if not name.startswith("_")
            ]
            actual_definitions = set(definitions)
            extra_definitions = sorted(actual_definitions - expected_definitions)
            missing_definitions = sorted(expected_definitions - actual_definitions)
            if (
                len(actual_definitions) != len(definitions)
                or extra_definitions
                or missing_definitions
            ):
                raise SystemExit(
                    f"closed Python {file_name} definition inventory drift: "
                    f"extra=[{', '.join(extra_definitions)}], "
                    f"missing=[{', '.join(missing_definitions)}]"
                )


def _validate_root_export_inventory(repo_root: Path) -> None:
    init_path = repo_root / "python" / "src" / "longshot_protocol" / "__init__.py"
    tree = ast.parse(init_path.read_text())
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        )
    ]
    all_references = [
        node for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id == "__all__"
    ]
    if len(assignments) != 1 or len(all_references) != 1:
        raise SystemExit("Python package __all__ must have one static assignment")

    value = assignments[0].value
    if not isinstance(value, ast.List):
        raise SystemExit("Python package __all__ must be a static list")
    starred = [
        item.value.id
        for item in value.elts
        if isinstance(item, ast.Starred) and isinstance(item.value, ast.Name)
    ]
    exports = [
        item.value
        for item in value.elts
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    ]
    if len(value.elts) != len(exports) + 1 or starred != ["_api_all"]:
        raise SystemExit("Python package __all__ must expand only the checked API inventory")

    actual = set(exports)
    extra = sorted(actual - PUBLIC_ROOT_SUPPLEMENTAL_EXPORTS)
    missing = sorted(PUBLIC_ROOT_SUPPLEMENTAL_EXPORTS - actual)
    if len(actual) != len(exports) or extra or missing:
        raise SystemExit(
            "closed Python package export inventory drift: "
            f"extra=[{', '.join(extra)}], missing=[{', '.join(missing)}]"
        )

    imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
    imported_names = []
    api_imports = []
    for node in imports:
        if node.level != 1 or node.module is None:
            raise SystemExit("Python package root may import only checked local modules")
        if node.module == "api":
            api_imports.extend(
                (alias.name, alias.asname) for alias in node.names
            )
            continue
        for alias in node.names:
            if alias.name == "*":
                raise SystemExit("Python supplemental modules may not use star imports")
            imported_names.append(alias.asname or alias.name)

    if sorted(api_imports) != [("*", None), ("__all__", "_api_all")]:
        raise SystemExit("Python package root API imports drifted")
    actual_imports = set(imported_names)
    extra_imports = sorted(actual_imports - PUBLIC_ROOT_SUPPLEMENTAL_EXPORTS)
    missing_imports = sorted(PUBLIC_ROOT_SUPPLEMENTAL_EXPORTS - actual_imports)
    if len(actual_imports) != len(imported_names) or extra_imports or missing_imports:
        raise SystemExit(
            "closed Python package import inventory drift: "
            f"extra=[{', '.join(extra_imports)}], missing=[{', '.join(missing_imports)}]"
        )


def _validate_python_release_files(repo_root: Path) -> None:
    release_files = [
        "python/LICENSE.txt",
        "python/MANIFEST.in",
        "python/README.md",
        "python/pyproject.toml",
    ]
    release_hash = hashlib.sha256()
    for relative in release_files:
        release_hash.update(relative.encode())
        release_hash.update(b"\0")
        release_hash.update((repo_root / relative).read_bytes())
        release_hash.update(b"\0")
    actual = release_hash.hexdigest()
    if actual != PUBLIC_PYTHON_RELEASE_FILES_SHA256:
        raise SystemExit(f"closed Python release file hash drift: actual={actual}")


def _validate_python_package_hash(repo_root: Path) -> None:
    source_dir = repo_root / "python" / "src"
    source_files = sorted(
        path
        for path in source_dir.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.relative_to(source_dir).parts
        and path.suffix not in {".pyc", ".pyo"}
    )
    package_hash = hashlib.sha256()
    for path in source_files:
        relative = path.relative_to(source_dir).as_posix()
        package_hash.update(relative.encode())
        package_hash.update(b"\0")
        package_hash.update(path.read_bytes())
        package_hash.update(b"\0")
    actual = package_hash.hexdigest()
    if actual != PUBLIC_PYTHON_PACKAGE_SHA256:
        raise SystemExit(f"closed Python package hash drift: actual={actual}")


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
    _validate_supplemental_class_inventory(repo_root)
    _validate_root_export_inventory(repo_root)
    _validate_python_release_files(repo_root)
    _validate_api_inventory(repo_root, ast.parse(api_path.read_text()))
    _validate_python_package_hash(repo_root)
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
