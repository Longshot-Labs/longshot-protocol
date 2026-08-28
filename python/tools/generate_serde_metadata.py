"""Generate compact Python runtime metadata from Rust serde DTOs."""

from __future__ import annotations

import argparse
import keyword
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

INTEGER_TYPES = set("u8 u16 u32 u64 u128 usize i8 i16 i32 i64 i128 isize".split())
INTEGER_TOKEN = re.compile(r"\b(?:u8|u16|u32|u64|u128|usize|i8|i16|i32|i64|i128|isize)\b")
PRIMITIVES = {
    "()": "unit",
    "String": "str",
    "str": "str",
    "&'staticstr": "str",
    "bool": "bool",
    "f32": "float",
    "f64": "float",
    "Uuid": "uuid",
}


def _read_attr(lines: List[str], index: int) -> Tuple[str, int]:
    attr = lines[index].strip()
    depth = attr.count("[") - attr.count("]")
    index += 1
    while index < len(lines) and depth > 0:
        line = lines[index].strip()
        attr += " " + line
        depth += line.count("[") - line.count("]")
        index += 1
    return attr, index


def _unwrap(value: str, wrapper: str) -> Optional[str]:
    prefix = f"{wrapper}<"
    return value[len(prefix) : -1] if value.startswith(prefix) and value.endswith(">") else None


def _split_top_level(value: str) -> List[str]:
    parts: List[str] = []
    start = depth = 0
    for index, char in enumerate(value):
        if char in "<([{":
            depth += 1
        elif char in ">)]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
    if tail := value[start:].strip():
        parts.append(tail)
    return parts


def _python_field_name(name: str) -> str:
    name = name.removeprefix("r#")
    return f"{name}_" if keyword.iskeyword(name) else name


def _wire_int_adapter(attrs: List[str]) -> Optional[Tuple[str, str]]:
    serde_attrs = " ".join(attr for attr in attrs if "serde" in attr)
    wire_int = re.search(r'wire_int::(?:option_)?([ui]\d+)_string', serde_attrs)
    if wire_int is None:
        return None
    if re.search(r"\bwith\s*=", serde_attrs):
        return wire_int.group(1), "#"
    if re.search(r"\bdeserialize_with\s*=", serde_attrs):
        return wire_int.group(1), "~"
    raise ValueError(f"unsupported wire-int serde direction: {serde_attrs}")


def _field_spec(rust_type: str, attrs: List[str]) -> str:
    value = re.sub(r"\s+", "", rust_type.strip().rstrip(","))
    flags = "=" if any(re.search(r"\bdefault(?:\s*[,)]|\s*$)", attr) for attr in attrs) else ""
    if any(re.search(r"\bdefault\s*=", attr) for attr in attrs):
        raise ValueError(f"custom serde default is unsupported: {' '.join(attrs)}")
    if inner := _unwrap(value, "Option"):
        spec = "?" + _field_spec(inner, [])
    elif inner := _unwrap(value, "Vec"):
        spec = "[]" + _field_spec(inner, [])
    elif any(
        (inner := _unwrap(value, wrapper)) is not None
        for wrapper in ("BTreeMap", "HashMap")
    ):
        parts = _split_top_level(inner)
        if len(parts) != 2 or parts[0].replace(" ", "") != "String":
            raise ValueError(f"unsupported Rust serde map type: {rust_type}")
        spec = "{}" + _field_spec(parts[1], [])
    elif any((inner := _unwrap(value, wrapper)) is not None for wrapper in ("Box", "Arc")):
        spec = _field_spec(inner, [])
    elif value in INTEGER_TYPES:
        spec = value
    elif value in PRIMITIVES:
        spec = PRIMITIVES[value]
    elif re.fullmatch(r"(?:[A-Za-z_]\w*::)*[A-Za-z_]\w*", value):
        spec = "@" + value.rsplit("::", 1)[-1]
    else:
        raise ValueError(f"unsupported Rust serde field type: {rust_type}")

    serde_attrs = " ".join(attr for attr in attrs if "serde" in attr)
    wire_int = _wire_int_adapter(attrs)
    if wire_int:
        bare = spec.lstrip("?=")
        integer_type, marker = wire_int
        if bare != integer_type:
            raise ValueError(f"wire-int adapter/type mismatch: {rust_type} {serde_attrs}")
        spec = spec[: len(spec) - len(bare)] + marker + bare
    if re.search(r"\bwith\s*=", serde_attrs) and not wire_int:
        raise ValueError(f"unsupported inline serde adapter: {serde_attrs}")
    unsupported = re.search(
        r"\b(?:flatten|alias|deserialize_with|skip_deserializing|"
        r"skip_serializing_if|skip)\b",
        serde_attrs,
    )
    if unsupported and not (wire_int and unsupported.group(0) == "deserialize_with"):
        raise ValueError(f"unsupported inline serde attribute: {unsupported.group(0)}")
    return flags + spec


def _integer_spec(rust_type: str, attrs: List[str]) -> Optional[str]:
    value = re.sub(r"\s+", "", rust_type.strip().rstrip(","))
    for wrapper in ("Option", "Box", "Arc"):
        if inner := _unwrap(value, wrapper):
            return _integer_spec(inner, attrs)
    if inner := _unwrap(value, "Vec"):
        return f"[]{spec}" if (spec := _integer_spec(inner, attrs)) else None
    if value in INTEGER_TYPES:
        wire_int = _wire_int_adapter(attrs)
        if wire_int and wire_int[0] != value:
            raise ValueError(f"wire-int adapter/type mismatch: {rust_type} {' '.join(attrs)}")
        return (wire_int[1] if wire_int else "") + value
    if INTEGER_TOKEN.search(value):
        raise ValueError(f"unsupported integer-bearing Rust type: {rust_type}")
    return None


def _field_key(name: str, attrs: List[str]) -> str:
    local = _python_field_name(name)
    joined = " ".join(attrs)
    rename = re.search(r'\brename\s*=\s*"([^"]+)"', joined)
    wire = rename.group(1) if rename else name.removeprefix("r#")
    return f"{local}>{wire}" if local != wire else wire


def _parse_struct(
    lines: List[str], index: int, declaration: str
) -> Tuple[int, Dict[str, str], Set[str], Set[str]]:
    tuple_match = re.match(r"pub struct \w+\(pub\s+(.+)\);", declaration)
    if tuple_match:
        spec = _integer_spec(tuple_match.group(1), [])
        return index + 1, {"value": spec} if spec else {}, set(), set()
    if "{" not in declaration or "{}" in declaration:
        return index + 1, {}, set(), set()

    fields: Dict[str, str] = {}
    required: Set[str] = set()
    required_nullable: Set[str] = set()
    attrs: List[str] = []
    depth = declaration.count("{") - declaration.count("}")
    index += 1
    while index < len(lines) and depth > 0:
        raw, line = lines[index], lines[index].strip()
        if line.startswith("#["):
            attr, index = _read_attr(lines, index)
            attrs.append(attr)
            continue
        match = re.match(r"pub\s+((?:r#)?\w+)\s*:\s*(.+?)(?:,)?$", line)
        if match:
            field_name = _python_field_name(match.group(1))
            if spec := _integer_spec(match.group(2), attrs):
                fields[field_name] = spec
            rust_type = re.sub(r"\s+", "", match.group(2))
            serde_attrs = " ".join(
                attr for attr in attrs if attr.startswith("#[serde(")
            )
            defaulted = bool(re.search(r"\bdefault\b", serde_attrs))
            optional = _unwrap(rust_type, "Option") is not None
            custom_deserializer = bool(
                re.search(r"\b(?:with|deserialize_with)\s*=", serde_attrs)
            )
            if not defaulted:
                if not optional:
                    required.add(field_name)
                elif custom_deserializer:
                    required_nullable.add(field_name)
            attrs = []
        elif line and not line.startswith("///"):
            attrs = []
        depth += raw.count("{") - raw.count("}")
        index += 1
    return index, fields, required, required_nullable


def _inline_fields(value: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for field in _split_top_level(value):
        match = re.match(r"((?:r#)?\w+)\s*:\s*(.+)$", field)
        if not match:
            raise ValueError(f"unsupported inline enum field: {field}")
        fields[_field_key(match.group(1), [])] = _field_spec(match.group(2), [])
    return fields


def _parse_enum(
    lines: List[str], index: int, declaration: str
) -> Tuple[int, Dict[str, Dict[str, str]]]:
    variants: Dict[str, Dict[str, str]] = {}
    attrs: List[str] = []
    depth = declaration.count("{") - declaration.count("}")
    index += 1
    current: Optional[str] = None
    variant_depth = 0

    while index < len(lines) and depth > 0:
        raw, line = lines[index], lines[index].strip()
        if line.startswith("#["):
            attr, index = _read_attr(lines, index)
            attrs.append(attr)
            continue
        if current:
            match = re.match(r"((?:r#)?\w+)\s*:\s*(.+?)(?:,)?$", line)
            if match:
                variants[current][_field_key(match.group(1), attrs)] = _field_spec(
                    match.group(2), attrs
                )
                attrs = []
            elif line and not line.startswith("///") and not line.startswith("}"):
                attrs = []
        elif depth == 1:
            named = re.match(r"(\w+)\s*\{(.*)\}\s*,?$", line)
            opened = re.match(r"(\w+)\s*\{\s*$", line)
            tuple_variant = re.match(r"(\w+)\((.*)\)\s*,?$", line)
            unit = re.match(r"(\w+)\s*,?$", line)
            hidden = any("doc(hidden)" in attr.replace(" ", "") for attr in attrs)
            if named and not hidden:
                variants[named.group(1)] = _inline_fields(named.group(2))
            elif opened and not hidden:
                current = opened.group(1)
                variants[current] = {}
                variant_depth = depth + 1
            elif tuple_variant and not hidden:
                payloads = _split_top_level(tuple_variant.group(2))
                if len(payloads) != 1:
                    raise ValueError(f"unsupported tuple variant: {line}")
                variants[tuple_variant.group(1)] = {"": _field_spec(payloads[0], [])}
            elif unit and not hidden:
                variants[unit.group(1)] = {}
            attrs = []

        depth += raw.count("{") - raw.count("}")
        if current and depth < variant_depth:
            current = None
            attrs = []
        index += 1
    return index, variants


def collect_serde_metadata(
    rust_src: Path,
) -> Tuple[
    Dict[str, Dict[str, str]],
    Dict[str, Set[str]],
    Dict[str, Set[str]],
    Dict[str, Dict[str, Dict[str, str]]],
    Set[str],
]:
    structs: Dict[str, Dict[str, str]] = {}
    required: Dict[str, Set[str]] = {}
    required_nullable: Dict[str, Set[str]] = {}
    tagged: Dict[str, Dict[str, Dict[str, str]]] = {}
    deny_unknown: Set[str] = set()
    paths = sorted((rust_src / "api").glob("*.rs")) + [rust_src / "ws.rs"]
    for path in paths:
        if path.name in {"mod.rs", "wire_int.rs"}:
            continue
        lines = path.read_text().splitlines()
        pending: List[str] = []
        index = 0
        while index < len(lines):
            line = lines[index].strip()
            if line.startswith("#["):
                attr, index = _read_attr(lines, index)
                pending.append(attr)
                continue
            if not line or line.startswith(("///", "//!")):
                index += 1
                continue
            declaration = re.match(r"pub\s+(struct|enum)\s+(\w+)", line)
            if not declaration:
                pending = []
                index += 1
                continue

            attrs = " ".join(pending)
            pending = []
            hidden = "doc(hidden)" in attrs.replace(" ", "")
            serde_contract = bool(re.search(r"\b(?:Serialize|Deserialize)\b", attrs)) and not hidden
            kind, name = declaration.groups()
            if kind == "struct":
                index, fields, required_fields, required_nullable_fields = _parse_struct(
                    lines, index, line
                )
                if serde_contract and fields:
                    structs[name] = fields
                if serde_contract and required_fields:
                    required[name] = required_fields
                if serde_contract and required_nullable_fields:
                    required_nullable[name] = required_nullable_fields
            else:
                index, variants = _parse_enum(lines, index, line)
                if serde_contract and re.search(r"\btag\s*=", attrs):
                    tagged[name] = variants
                    if "deny_unknown_fields" in attrs:
                        deny_unknown.add(name)
    return structs, required, required_nullable, tagged, deny_unknown


def _encoded_struct(fields: Dict[str, str]) -> str:
    grouped: Dict[str, List[str]] = {}
    for field, spec in sorted(fields.items()):
        grouped.setdefault(spec, []).append(field)
    return ";".join(f"{spec}:{','.join(names)}" for spec, names in sorted(grouped.items()))


def _encoded_variants(variants: Dict[str, Dict[str, str]]) -> str:
    values = []
    for variant, fields in sorted(variants.items()):
        if "" in fields:
            body = "$" + fields[""]
        else:
            body = ",".join(f"{field}:{spec}" for field, spec in sorted(fields.items()))
        values.append(f"{variant}={body}")
    return ";".join(values)


def render_metadata(
    structs: Dict[str, Dict[str, str]],
    required: Dict[str, Set[str]],
    required_nullable: Dict[str, Set[str]],
    tagged: Dict[str, Dict[str, Dict[str, str]]],
    deny_unknown: Set[str],
) -> str:
    struct_count = sum(map(len, structs.values()))
    variant_count = sum(len(fields) for variants in tagged.values() for fields in variants.values())
    lines = [
        '"""Generated Rust serde runtime metadata. Do not edit by hand."""',
        "",
        f"# {struct_count} integer fields; {variant_count} tagged-union payload fields.",
        "STRUCT_INTEGER_FIELDS = {",
        *(f'    "{name}": "{_encoded_struct(fields)}",' for name, fields in sorted(structs.items())),
        "}",
        "",
        "STRUCT_REQUIRED_FIELDS = {",
        *(f'    "{name}": "{",".join(sorted(fields))}",' for name, fields in sorted(required.items())),
        "}",
        "",
        "STRUCT_REQUIRED_NULLABLE_FIELDS = {",
        *(
            f'    "{name}": "{",".join(sorted(fields))}",'
            for name, fields in sorted(required_nullable.items())
        ),
        "}",
        "",
        "TAGGED_UNION_FIELDS = {",
        *(f'    "{name}": "{_encoded_variants(variants)}",' for name, variants in sorted(tagged.items())),
        "}",
        "",
        "DENY_UNKNOWN_TAGGED_UNIONS = {",
        *(f'    "{name}",' for name in sorted(deny_unknown)),
        "}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    output = repo_root / "python/src/longshot_protocol/_serde_metadata.py"
    rendered = render_metadata(*collect_serde_metadata(repo_root / "rust/src"))
    if args.stdout:
        print(rendered, end="")
    elif args.check:
        if not output.exists() or output.read_text() != rendered:
            raise SystemExit(f"{output} is stale; regenerate serde metadata")
    else:
        output.write_text(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
