from __future__ import annotations

import ast
import json
import keyword
import re
import runpy
import sys
import unittest
from base64 import b64encode
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID

from longshot_protocol import (
    Address,
    Amount,
    Asset,
    ClientMessage,
    Direction,
    Duration,
    ErrorResponse,
    MarketId,
    MarketStatus,
    MarketType,
    NotificationPayload,
    NotificationResponse,
    OrderLeg,
    OrderLegJson,
    OrderType,
    Odds,
    PriceShareCard,
    QuoteDeclineReason,
    QuoteResultStatus,
    RequestId,
    RfqSubscription,
    ServerMessage,
    ShareCardFooter,
    ShareCardSnapshot,
    ShareStat,
    SignedOrder,
    SignedOrderJson,
    Timestamp,
    UserTier,
)
import longshot_protocol
from longshot_protocol import api, model, ws
from longshot_protocol.model import LongshotModel, RustStringEnum, RustTaggedUnion, to_serde_value
from longshot_protocol.types import _check_u8, _check_u32, _check_u64

REPO_ROOT = Path(__file__).resolve().parents[2]
SERDE_METADATA_GENERATOR = runpy.run_path(
    str(REPO_ROOT / "python" / "tools" / "generate_serde_metadata.py")
)
API_STUB_GENERATOR = runpy.run_path(
    str(REPO_ROOT / "python" / "tools" / "generate_api_stub.py")
)


def rust_api_files() -> list[Path]:
    return sorted(
        path
        for path in (REPO_ROOT / "rust" / "src" / "api").glob("*.rs")
        if path.name not in {"mod.rs", "wire_int.rs"}
    )


def rust_api_public_declarations() -> set[str]:
    declarations: set[str] = set()
    for path in rust_api_files():
        text = path.read_text()
        declarations.update(re.findall(r"^pub\s+(?:struct|enum|const)\s+([A-Za-z0-9_]+)", text, re.M))
    return declarations


def rust_api_public_constants() -> dict[str, int]:
    constants: dict[str, int] = {}
    for path in rust_api_files():
        text = path.read_text()
        for name, value in re.findall(
            r"^pub\s+const\s+([A-Za-z0-9_]+)\s*:\s*[^=]+=\s*([0-9_]+);",
            text,
            re.M,
        ):
            constants[name] = int(value.replace("_", ""))
    return constants


RUST_PRIMITIVE_PYTHON_TYPES = {
    "String": "str",
    "&'static str": "str",
    "bool": "bool",
    "f32": "float",
    "f64": "float",
    "u8": "int",
    "u16": "int",
    "u32": "int",
    "u64": "int",
    "usize": "int",
    "i8": "int",
    "i16": "int",
    "i32": "int",
    "i64": "int",
    "isize": "int",
    "Uuid": "UUID",
}

RUST_SHARED_PROTOCOL_TYPES = {
    "Address",
    "Direction",
    "MarketId",
    "MarketStatus",
    "MarketType",
    "Outcome",
    "PositionId",
    "TradingChannel",
}


def _snake_case(name: str) -> str:
    value = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value).lower()


def _python_field_name(rust_name: str) -> str:
    if rust_name.startswith("r#"):
        rust_name = rust_name[2:]
    return f"{rust_name}_" if keyword.iskeyword(rust_name) else rust_name


def _rust_renamed_variant(name: str, rename_all: str | None) -> str:
    if rename_all == "snake_case":
        return _snake_case(name)
    if rename_all == "lowercase":
        return name.lower()
    return name


def _read_rust_attr(lines: list[str], index: int) -> tuple[str, int]:
    attr = lines[index].strip()
    depth = attr.count("[") - attr.count("]")
    index += 1
    while index < len(lines) and depth > 0:
        line = lines[index].strip()
        attr += " " + line
        depth += line.count("[") - line.count("]")
        index += 1
    return attr, index


def _unwrap_rust_generic(value: str, name: str) -> str | None:
    prefix = f"{name}<"
    if value.startswith(prefix) and value.endswith(">"):
        return value[len(prefix) : -1].strip()
    return None


def _rust_type_to_python_core(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip().rstrip(","))
    option_inner = _unwrap_rust_generic(value, "Option")
    if option_inner is not None:
        return f"Optional[{_rust_type_to_python_core(option_inner)}]"
    vec_inner = _unwrap_rust_generic(value, "Vec")
    if vec_inner is not None:
        return f"List[{_rust_type_to_python_core(vec_inner)}]"
    for map_name in ("BTreeMap", "HashMap"):
        map_inner = _unwrap_rust_generic(value, map_name)
        if map_inner is not None:
            key, item = (part.strip() for part in map_inner.split(",", 1))
            return f"Dict[{_rust_type_to_python_core(key)}, {_rust_type_to_python_core(item)}]"
    box_inner = _unwrap_rust_generic(value, "Box")
    if box_inner is not None:
        return _rust_type_to_python_core(box_inner)
    if value in RUST_PRIMITIVE_PYTHON_TYPES:
        return RUST_PRIMITIVE_PYTHON_TYPES[value]
    if value in rust_api_public_declarations() or value in RUST_SHARED_PROTOCOL_TYPES:
        return value
    return "Any"


def _rust_type_to_python_annotation(value: str) -> str:
    # Generated API dataclasses currently preserve historical `= None`
    # construction, so fields are Optional even when Rust requires them.
    value = re.sub(r"\s+", " ", value.strip().rstrip(","))
    option_inner = _unwrap_rust_generic(value, "Option")
    return f"Optional[{_rust_type_to_python_core(option_inner or value)}]"


def rust_api_struct_field_annotations() -> dict[str, dict[str, str]]:
    struct_fields: dict[str, dict[str, str]] = {}
    for path in rust_api_files():
        lines = path.read_text().splitlines()
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            tuple_match = re.match(r"pub struct ([A-Za-z0-9_]+)\(pub\s+(.+)\);", stripped)
            if tuple_match:
                if (
                    tuple_match.group(1) == "PoolImageRawBytes"
                    and tuple_match.group(2) == "Vec<u8>"
                ):
                    struct_fields[tuple_match.group(1)] = {"value": "bytes"}
                    index += 1
                    continue
                struct_fields[tuple_match.group(1)] = {
                    "value": _rust_type_to_python_annotation(tuple_match.group(2))
                }
                index += 1
                continue

            struct_match = re.match(r"pub struct ([A-Za-z0-9_]+)", stripped)
            if not struct_match:
                index += 1
                continue

            name = struct_match.group(1)
            if "{}" in stripped or "(" in stripped:
                index += 1
                continue

            depth = stripped.count("{") - stripped.count("}")
            index += 1
            fields_out: dict[str, str] = {}
            while index < len(lines) and depth > 0:
                raw = lines[index]
                line = raw.strip()
                if line.startswith("#["):
                    _, index = _read_rust_attr(lines, index)
                    continue
                field_match = re.match(r"pub\s+((?:r#)?[A-Za-z0-9_]+)\s*:\s*(.+?)(?:,)?$", line)
                if field_match:
                    fields_out[_python_field_name(field_match.group(1))] = (
                        _rust_type_to_python_annotation(field_match.group(2))
                    )
                depth += raw.count("{") - raw.count("}")
                index += 1

            struct_fields[name] = fields_out
    return struct_fields


def rust_api_struct_fields_and_flatten() -> tuple[dict[str, list[str]], dict[str, set[str]]]:
    struct_fields: dict[str, list[str]] = {}
    flatten_fields: dict[str, set[str]] = {}
    for path in rust_api_files():
        lines = path.read_text().splitlines()
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            tuple_match = re.match(r"pub struct ([A-Za-z0-9_]+)\(pub ", stripped)
            if tuple_match:
                struct_fields[tuple_match.group(1)] = ["value"]
                index += 1
                continue

            struct_match = re.match(r"pub struct ([A-Za-z0-9_]+)", stripped)
            if not struct_match:
                index += 1
                continue

            name = struct_match.group(1)
            if "{}" in stripped:
                struct_fields[name] = []
                index += 1
                continue

            depth = stripped.count("{") - stripped.count("}")
            index += 1
            fields_out: list[str] = []
            flattened: set[str] = set()
            field_attrs: list[str] = []
            while index < len(lines) and depth > 0:
                raw = lines[index]
                line = raw.strip()
                if line.startswith("#["):
                    attr, index = _read_rust_attr(lines, index)
                    field_attrs.append(attr)
                    continue
                else:
                    field_match = re.match(r"pub\s+([A-Za-z0-9_]+)\s*:", line)
                    if field_match:
                        field_name = field_match.group(1)
                        rename = None
                        for attr in field_attrs:
                            rename_match = re.search(r'rename = "([^"]+)"', attr)
                            if rename_match:
                                rename = rename_match.group(1)
                            if "flatten" in attr:
                                flattened.add(field_name)
                        fields_out.append(rename or field_name)
                        field_attrs = []
                depth += raw.count("{") - raw.count("}")
                index += 1

            struct_fields[name] = fields_out
            if flattened:
                flatten_fields[name] = flattened
    return struct_fields, flatten_fields


def rust_api_struct_skip_fields() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    skip_none: dict[str, set[str]] = {}
    skip_empty: dict[str, set[str]] = {}
    for path in rust_api_files():
        lines = path.read_text().splitlines()
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            struct_match = re.match(r"pub struct ([A-Za-z0-9_]+)", stripped)
            if not struct_match or "{}" in stripped or "(" in stripped:
                index += 1
                continue

            name = struct_match.group(1)
            depth = stripped.count("{") - stripped.count("}")
            index += 1
            none_fields: set[str] = set()
            empty_fields: set[str] = set()
            field_attrs: list[str] = []
            while index < len(lines) and depth > 0:
                raw = lines[index]
                line = raw.strip()
                if line.startswith("#["):
                    attr, index = _read_rust_attr(lines, index)
                    field_attrs.append(attr)
                    continue
                else:
                    field_match = re.match(r"pub\s+([A-Za-z0-9_]+)\s*:", line)
                    if field_match:
                        field_name = field_match.group(1)
                        rename = None
                        for attr in field_attrs:
                            rename_match = re.search(r'rename = "([^"]+)"', attr)
                            if rename_match:
                                rename = rename_match.group(1)
                        wire_name = rename or field_name
                        if any('skip_serializing_if = "Option::is_none"' in attr for attr in field_attrs):
                            none_fields.add(wire_name)
                        if any('skip_serializing_if = "Vec::is_empty"' in attr for attr in field_attrs):
                            empty_fields.add(wire_name)
                        field_attrs = []
                depth += raw.count("{") - raw.count("}")
                index += 1
            if none_fields:
                skip_none[name] = none_fields
            if empty_fields:
                skip_empty[name] = empty_fields
    return skip_none, skip_empty


def rust_api_wire_int_fields() -> dict[str, set[str]]:
    wire_fields: dict[str, set[str]] = {}
    for path in rust_api_files():
        lines = path.read_text().splitlines()
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            struct_match = re.match(r"pub struct ([A-Za-z0-9_]+)", stripped)
            if not struct_match or "{}" in stripped or "(" in stripped:
                index += 1
                continue

            name = struct_match.group(1)
            depth = stripped.count("{") - stripped.count("}")
            index += 1
            fields_out: set[str] = set()
            field_attrs: list[str] = []
            while index < len(lines) and depth > 0:
                raw = lines[index]
                line = raw.strip()
                if line.startswith("#["):
                    attr, index = _read_rust_attr(lines, index)
                    field_attrs.append(attr)
                    continue
                else:
                    field_match = re.match(r"pub\s+([A-Za-z0-9_]+)\s*:", line)
                    if field_match:
                        if any(
                            re.search(
                                r'\bwith\s*=\s*"crate::api::wire_int::', attr
                            )
                            for attr in field_attrs
                        ):
                            fields_out.add(field_match.group(1))
                        field_attrs = []
                depth += raw.count("{") - raw.count("}")
                index += 1
            if fields_out:
                wire_fields[name] = fields_out
    return wire_fields


def rust_api_custom_defaults() -> dict[str, int]:
    defaults: dict[str, int] = {}
    pattern = re.compile(
        r"fn\s+(default_[A-Za-z0-9_]+)\(\)\s*->\s*[^\{]+\{\s*([0-9_]+)\s*\}"
    )
    for path in rust_api_files():
        for name, value in pattern.findall(path.read_text()):
            defaults[name] = int(value.replace("_", ""))
    return defaults


def rust_api_defaults() -> dict[str, dict[str, object]]:
    defaults: dict[str, dict[str, object]] = {}
    custom_defaults = rust_api_custom_defaults()
    enum_defaults = rust_api_default_enum_variants()
    for path in rust_api_files():
        lines = path.read_text().splitlines()
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            struct_match = re.match(r"pub struct ([A-Za-z0-9_]+)", stripped)
            if not struct_match or "{}" in stripped or "(" in stripped:
                index += 1
                continue

            name = struct_match.group(1)
            depth = stripped.count("{") - stripped.count("}")
            index += 1
            fields_out: dict[str, object] = {}
            field_attrs: list[str] = []
            while index < len(lines) and depth > 0:
                raw = lines[index]
                line = raw.strip()
                if line.startswith("#["):
                    attr, index = _read_rust_attr(lines, index)
                    field_attrs.append(attr)
                    continue
                field_match = re.match(
                    r"pub\s+([A-Za-z0-9_]+)\s*:\s*(.+?)(?:,)?$", line
                )
                if field_match:
                    field_name = field_match.group(1)
                    field_type = field_match.group(2).strip()
                    serde_attrs = " ".join(
                        attr for attr in field_attrs if attr.startswith("#[serde")
                    )
                    custom_match = re.search(r'default\s*=\s*"([^"]+)"', serde_attrs)
                    if custom_match:
                        default_function = custom_match.group(1)
                        if default_function not in custom_defaults:
                            raise AssertionError(
                                f"unsupported custom default {default_function}"
                            )
                        fields_out[field_name] = custom_defaults[default_function]
                    elif "default" not in serde_attrs:
                        pass
                    elif _unwrap_rust_generic(field_type, "Option") is not None:
                        pass
                    elif field_type.startswith("Vec<"):
                        fields_out[field_name] = []
                    elif field_type == "bool":
                        fields_out[field_name] = False
                    elif re.fullmatch(r"[ui](8|16|32|64|128|size)", field_type):
                        fields_out[field_name] = 0
                    elif field_type in {"f32", "f64"}:
                        fields_out[field_name] = 0.0
                    elif field_type == "String":
                        fields_out[field_name] = ""
                    elif any(
                        field_type.startswith(f"{map_type}<")
                        for map_type in ("BTreeMap", "HashMap")
                    ):
                        fields_out[field_name] = {}
                    elif field_type in enum_defaults:
                        fields_out[field_name] = enum_defaults[field_type]
                    else:
                        raise AssertionError(
                            f"unsupported serde default type {field_type} for "
                            f"{name}.{field_name}"
                        )
                    field_attrs = []
                depth += raw.count("{") - raw.count("}")
                index += 1
            if fields_out:
                defaults[name] = fields_out
    return defaults


def rust_api_field_presence() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    required: dict[str, set[str]] = {}
    required_nullable: dict[str, set[str]] = {}
    for path in rust_api_files():
        lines = path.read_text().splitlines()
        serde_contract = False
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped.startswith("#["):
                attr, index = _read_rust_attr(lines, index)
                serde_contract |= bool(re.search(r"\b(?:Serialize|Deserialize)\b", attr))
                continue
            if not stripped or stripped.startswith(("///", "//!")):
                index += 1
                continue
            struct_match = re.match(r"pub struct ([A-Za-z0-9_]+)", stripped)
            is_serde, serde_contract = serde_contract, False
            if not struct_match or not is_serde or "{}" in stripped or "(" in stripped:
                index += 1
                continue

            name = struct_match.group(1)
            depth = stripped.count("{") - stripped.count("}")
            index += 1
            fields_out: set[str] = set()
            nullable_fields_out: set[str] = set()
            field_attrs: list[str] = []
            while index < len(lines) and depth > 0:
                raw = lines[index]
                line = raw.strip()
                if line.startswith("#["):
                    attr, index = _read_rust_attr(lines, index)
                    field_attrs.append(attr)
                    continue
                field_match = re.match(
                    r"pub\s+((?:r#)?[A-Za-z0-9_]+)\s*:\s*(.+?)(?:,)?$",
                    line,
                )
                if field_match:
                    field_name = _python_field_name(field_match.group(1))
                    field_type = field_match.group(2).strip()
                    serde_attrs = " ".join(
                        attr for attr in field_attrs if attr.startswith("#[serde(")
                    )
                    defaulted = bool(re.search(r"\bdefault\b", serde_attrs))
                    optional = _unwrap_rust_generic(field_type, "Option") is not None
                    custom_deserializer = bool(
                        re.search(r"\b(?:with|deserialize_with)\s*=", serde_attrs)
                    )
                    if not defaulted:
                        if not optional:
                            fields_out.add(field_name)
                        elif custom_deserializer:
                            nullable_fields_out.add(field_name)
                    field_attrs = []
                depth += raw.count("{") - raw.count("}")
                index += 1
            if fields_out:
                required[name] = fields_out
            if nullable_fields_out:
                required_nullable[name] = nullable_fields_out
    return required, required_nullable


def rust_api_required_fields() -> dict[str, set[str]]:
    return rust_api_field_presence()[0]


def rust_api_required_nullable_fields() -> dict[str, set[str]]:
    return rust_api_field_presence()[1]


def rust_api_skip_non_finite_fields() -> dict[str, set[str]]:
    skipped: dict[str, set[str]] = {}
    for path in rust_api_files():
        lines = path.read_text().splitlines()
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            struct_match = re.match(r"pub struct ([A-Za-z0-9_]+)", stripped)
            if not struct_match or "{}" in stripped or "(" in stripped:
                index += 1
                continue

            name = struct_match.group(1)
            depth = stripped.count("{") - stripped.count("}")
            index += 1
            fields_out: set[str] = set()
            field_attrs: list[str] = []
            while index < len(lines) and depth > 0:
                raw = lines[index]
                line = raw.strip()
                if line.startswith("#["):
                    attr, index = _read_rust_attr(lines, index)
                    field_attrs.append(attr)
                    continue
                field_match = re.match(r"pub\s+([A-Za-z0-9_]+)\s*:", line)
                if field_match:
                    if any('skip_serializing_if = "odds_is_none_or_non_finite"' in attr for attr in field_attrs):
                        fields_out.add(field_match.group(1))
                    field_attrs = []
                depth += raw.count("{") - raw.count("}")
                index += 1
            if fields_out:
                skipped[name] = fields_out
    return skipped


def rust_api_deny_unknown_structs() -> set[str]:
    structs: set[str] = set()
    for path in rust_api_files():
        attrs: list[str] = []
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if line.startswith("#["):
                attrs.append(line)
                continue
            struct_match = re.match(r"pub struct ([A-Za-z0-9_]+)", line)
            if struct_match:
                if any("deny_unknown_fields" in attr for attr in attrs):
                    structs.add(struct_match.group(1))
                attrs = []
                continue
            if line and not line.startswith("//"):
                attrs = []
    return structs


def _rust_api_enum_contracts() -> tuple[dict[str, list[str]], dict[str, str]]:
    enums: dict[str, list[str]] = {}
    defaults: dict[str, str] = {}
    for path in rust_api_files():
        lines = path.read_text().splitlines()
        index = 0
        attrs: list[str] = []
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped.startswith("#["):
                attr, index = _read_rust_attr(lines, index)
                attrs.append(attr)
                continue

            enum_match = re.match(r"pub enum ([A-Za-z0-9_]+)", stripped)
            if not enum_match:
                if stripped and not stripped.startswith("//"):
                    attrs = []
                index += 1
                continue

            name = enum_match.group(1)
            rename_all_match = next(
                (re.search(r'rename_all = "([^"]+)"', attr) for attr in attrs if "rename_all" in attr),
                None,
            )
            rename_all = rename_all_match.group(1) if rename_all_match else None
            attrs = []
            depth = stripped.count("{") - stripped.count("}")
            index += 1
            variant_attrs: list[str] = []
            variants: list[str] = []
            while index < len(lines) and depth > 0:
                raw = lines[index]
                line = raw.strip()
                if line.startswith("#["):
                    attr, index = _read_rust_attr(lines, index)
                    variant_attrs.append(attr)
                    continue
                elif depth == 1:
                    variant_match = re.match(r"([A-Za-z0-9_]+)\s*(?:[({,]|$)", line)
                    if variant_match and not line.startswith("//"):
                        variant = variant_match.group(1)
                        rename = None
                        for attr in variant_attrs:
                            rename_match = re.search(r'rename = "([^"]+)"', attr)
                            if rename_match:
                                rename = rename_match.group(1)
                        wire_variant = rename or _rust_renamed_variant(variant, rename_all)
                        variants.append(wire_variant)
                        if any(attr == "#[default]" for attr in variant_attrs):
                            defaults[name] = wire_variant
                        variant_attrs = []
                depth += raw.count("{") - raw.count("}")
                index += 1
            enums[name] = variants
    return enums, defaults


def rust_api_enum_wire_variants() -> dict[str, list[str]]:
    return _rust_api_enum_contracts()[0]


def rust_api_default_enum_variants() -> dict[str, str]:
    return _rust_api_enum_contracts()[1]


def rust_api_enum_shapes() -> dict[str, tuple[object, object, bool]]:
    shapes: dict[str, tuple[object, object, bool]] = {}
    for path in rust_api_files():
        attrs: list[str] = []
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if line.startswith("#["):
                attrs.append(line)
                continue
            enum_match = re.match(r"pub enum ([A-Za-z0-9_]+)", line)
            if enum_match:
                tag = None
                content = None
                untagged = False
                for attr in attrs:
                    tag_match = re.search(r'tag = "([^"]+)"', attr)
                    content_match = re.search(r'content = "([^"]+)"', attr)
                    if tag_match:
                        tag = tag_match.group(1)
                    if content_match:
                        content = content_match.group(1)
                    if "untagged" in attr:
                        untagged = True
                if tag is not None or content is not None or untagged:
                    shapes[enum_match.group(1)] = (tag, content, untagged)
                attrs = []
                continue
            if line and not line.startswith("//"):
                attrs = []
    return shapes


def python_api_struct_wire_fields() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for name in api.__all__:
        value = getattr(api, name)
        if not is_dataclass(value):
            continue
        renames = getattr(value, "__serde_renames__", {})
        result[name] = [renames.get(field.name, field.name) for field in fields(value)]
    return result


def python_api_enum_wire_variants() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for name in api.__all__:
        value = getattr(api, name)
        if isinstance(value, type) and issubclass(value, RustStringEnum):
            result[name] = [member.value for member in value]
        elif isinstance(value, type) and issubclass(value, RustTaggedUnion):
            result[name] = list(value.__serde_variants__.values())
    return result


def python_api_enum_shapes() -> dict[str, tuple[object, object, bool]]:
    result: dict[str, tuple[object, object, bool]] = {}
    for name in api.__all__:
        value = getattr(api, name)
        if isinstance(value, type) and issubclass(value, RustTaggedUnion):
            result[name] = (
                value.__serde_tag__,
                value.__serde_content__,
                value.__serde_untagged__,
            )
    return result


def python_api_skip_fields(attr_name: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for name in api.__all__:
        value = getattr(api, name)
        if not is_dataclass(value):
            continue
        renames = getattr(value, "__serde_renames__", {})
        skipped = {renames.get(field, field) for field in getattr(value, attr_name, set())}
        if skipped:
            result[name] = skipped
    return result


def python_api_wire_int_fields() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for name in api.__all__:
        value = getattr(api, name)
        fields_out = set(getattr(value, "__serde_string_ints__", set()))
        if fields_out:
            result[name] = fields_out
    return result


def python_api_defaults() -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for name in api.__all__:
        value = getattr(api, name)
        defaults = dict(getattr(value, "__serde_defaults__", {}))
        if defaults:
            result[name] = defaults
    return result


def python_api_required_fields() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for name in api.__all__:
        value = getattr(api, name)
        fields_out = set(getattr(value, "__serde_required__", set()))
        if fields_out:
            result[name] = fields_out
    return result


def python_api_required_nullable_fields() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for name in api.__all__:
        value = getattr(api, name)
        fields_out = set(getattr(value, "__serde_required_nullable__", set()))
        if fields_out:
            result[name] = fields_out
    return result


def python_api_skip_non_finite_fields() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for name in api.__all__:
        value = getattr(api, name)
        fields_out = set(getattr(value, "__serde_skip_non_finite__", set()))
        if fields_out:
            result[name] = fields_out
    return result


def python_api_deny_unknown_structs() -> set[str]:
    return {
        name
        for name in api.__all__
        if getattr(getattr(api, name), "__serde_deny_unknown__", False)
    }


def rust_mm_public_declarations() -> set[str]:
    text = (REPO_ROOT / "rust" / "src" / "mm.rs").read_text()
    declarations = set(re.findall(r"^pub\s+(?:enum|fn|const)\s+([A-Za-z0-9_]+)", text, re.M))
    return declarations


def rust_public_type_declarations(text: str) -> set[str]:
    hidden = set(
        re.findall(
            r"#\[doc\(hidden\)\](?:\s*#\[[^]]*\])*\s*pub\s+(?:struct|enum)\s+(\w+)",
            text,
        )
    )
    return set(re.findall(r"^pub\s+(?:struct|enum)\s+(\w+)", text, re.M)) - hidden


def rust_top_level_public_type_declarations() -> set[str]:
    declarations: set[str] = set()
    for path in [
        REPO_ROOT / "rust" / "src" / "ws.rs",
        REPO_ROOT / "rust" / "src" / "taker.rs",
        REPO_ROOT / "rust" / "src" / "types" / "ids.rs",
        REPO_ROOT / "rust" / "src" / "types" / "market.rs",
        REPO_ROOT / "rust" / "src" / "types" / "primitives.rs",
        REPO_ROOT / "rust" / "src" / "types" / "rfq.rs",
    ]:
        declarations.update(rust_public_type_declarations(path.read_text()))
    declarations.update(
        {"RequestId", "UserId", "QuoteId", "PositionId", "ContestId", "ChatId", "MessageId"}
    )
    return declarations


class ApiParityTests(unittest.TestCase):
    def test_market_type_preserves_unknown_category_slugs(self) -> None:
        self.assertEqual(
            [
                MarketType.Sports,
                MarketType.Culture,
                MarketType.Crypto,
                MarketType.Politics,
                MarketType.Earnings,
                MarketType.Entertainment,
                MarketType.Esports,
                MarketType.Weather,
                MarketType.Other,
            ],
            [
                "sports",
                "culture",
                "crypto",
                "politics",
                "earnings",
                "entertainment",
                "esports",
                "weather",
                "other",
            ],
        )
        self.assertEqual(MarketType("new-category"), "new-category")

        query = api.PublicMarketsRawQuery.from_dict({"market_type": "new-category"})
        self.assertIsInstance(query.market_type, MarketType)
        self.assertEqual(query.to_dict()["market_type"], "new-category")
        for invalid in (7, False, {"slug": "culture"}, ["culture"]):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    api.PublicMarketsRawQuery.from_dict({"market_type": invalid})

    def test_public_market_statuses_round_trip_as_one_csv_query_value(self) -> None:
        query = api.PublicMarketsRawQuery(
            market_type=MarketType.Sports,
            statuses=[MarketStatus.Pending, MarketStatus.Open],
        )

        encoded = query.to_dict()

        self.assertEqual(encoded["statuses"], "PENDING,OPEN")
        decoded = api.PublicMarketsRawQuery.from_dict(encoded)
        self.assertEqual(decoded.statuses, [MarketStatus.Pending, MarketStatus.Open])
        self.assertEqual(
            api.PublicMarketsRawQuery.from_dict(
                {"statuses": " PENDING, , OPEN "}
            ).statuses,
            [MarketStatus.Pending, MarketStatus.Open],
        )
        self.assertIsNone(
            api.PublicMarketsRawQuery.from_dict({"statuses": " , "}).statuses
        )
        self.assertEqual(
            api.PublicMarketsRawQuery(statuses=[]).to_dict()["statuses"], ""
        )
        with self.assertRaises(ValueError):
            api.PublicMarketsRawQuery.from_dict({"statuses": ["PENDING", "OPEN"]})
        with self.assertRaises(ValueError):
            api.PublicMarketsRawQuery.from_dict({"statuses": "PENDING,UNKNOWN"})

    def test_contest_entry_index_remains_optional_and_stable(self) -> None:
        self.assertIsNone(api.PlaceContestBetRequest().entry_index)
        self.assertEqual(api.PlaceContestBetRequest(entry_index=1).entry_index, 1)

    def test_top_level_exports_every_public_rust_protocol_type(self) -> None:
        expected = (
            rust_top_level_public_type_declarations()
            | rust_api_public_declarations()
            | rust_mm_public_declarations()
        )
        missing = sorted(name for name in expected if not hasattr(longshot_protocol, name))
        self.assertEqual(missing, [])

    def test_api_exports_every_public_rust_api_declaration(self) -> None:
        missing = sorted(rust_api_public_declarations() - set(api.__all__))
        self.assertEqual(missing, [])

    def test_api_constants_match_rust_values(self) -> None:
        mismatched = {
            name: (expected, getattr(api, name, None))
            for name, expected in rust_api_public_constants().items()
            if getattr(api, name, None) != expected
        }
        self.assertEqual(mismatched, {})

    def test_api_model_fields_and_enum_wire_variants_match_rust(self) -> None:
        rust_structs, _ = rust_api_struct_fields_and_flatten()
        python_structs = python_api_struct_wire_fields()
        struct_mismatches = {
            name: (expected, python_structs.get(name))
            for name, expected in rust_structs.items()
            if python_structs.get(name) != expected
        }
        self.assertEqual(struct_mismatches, {})

        rust_enums = rust_api_enum_wire_variants()
        python_enums = python_api_enum_wire_variants()
        enum_mismatches = {
            name: (expected, python_enums.get(name))
            for name, expected in rust_enums.items()
            if python_enums.get(name) != expected
        }
        self.assertEqual(enum_mismatches, {})

    def test_api_model_field_annotations_match_rust_types(self) -> None:
        expected_annotations = rust_api_struct_field_annotations()
        mismatches = {}
        any_fields = {}
        for name in api.__all__:
            value = getattr(api, name)
            if not is_dataclass(value):
                continue
            expected = expected_annotations.get(name, {})
            actual = getattr(value, "__annotations__", {})
            for field in fields(value):
                actual_annotation = actual.get(field.name)
                expected_annotation = expected.get(field.name)
                if actual_annotation == "Any":
                    any_fields.setdefault(name, []).append(field.name)
                if expected_annotation is not None and actual_annotation != expected_annotation:
                    mismatches.setdefault(name, {})[field.name] = (
                        expected_annotation,
                        actual_annotation,
                    )

        self.assertEqual(any_fields, {})
        self.assertEqual(mismatches, {})

    def test_api_enum_shapes_match_rust(self) -> None:
        rust_shapes = rust_api_enum_shapes()
        python_shapes = python_api_enum_shapes()
        mismatches = {
            name: (expected, python_shapes.get(name))
            for name, expected in rust_shapes.items()
            if python_shapes.get(name) != expected
        }
        self.assertEqual(mismatches, {})

    def test_api_flatten_metadata_matches_rust(self) -> None:
        _, rust_flatten = rust_api_struct_fields_and_flatten()
        python_flatten = {
            name: getattr(getattr(api, name), "__serde_flatten__", set())
            for name in rust_flatten
        }
        self.assertEqual(python_flatten, rust_flatten)

    def test_api_skip_serializing_metadata_matches_rust(self) -> None:
        rust_skip_none, rust_skip_empty = rust_api_struct_skip_fields()

        self.assertEqual(python_api_skip_fields("__serde_skip_none__"), rust_skip_none)
        self.assertEqual(python_api_skip_fields("__serde_skip_empty__"), rust_skip_empty)

    def test_api_wire_int_metadata_matches_rust(self) -> None:
        self.assertEqual(python_api_wire_int_fields(), rust_api_wire_int_fields())

    def test_generated_serde_metadata_matches_every_rust_field(self) -> None:
        collect = SERDE_METADATA_GENERATOR["collect_serde_metadata"]
        render = SERDE_METADATA_GENERATOR["render_metadata"]
        (
            expected_structs,
            expected_required,
            expected_required_nullable,
            expected_tagged,
            expected_deny,
        ) = collect(REPO_ROOT / "rust" / "src")
        expected_integer_types = {
            name: {
                field: model._integer_type_from_spec(spec)
                for field, spec in fields.items()
            }
            for name, fields in expected_structs.items()
        }
        protocol_classes = {**vars(api), **vars(ws)}
        actual_structs = {
            name: value.__dict__["__serde_integer_types__"]
            for name, value in protocol_classes.items()
            if isinstance(value, type) and value.__dict__.get("__serde_integer_types__")
        }
        tagged_classes = {
            name: getattr(api, name, None) or getattr(ws, name)
            for name in expected_tagged
        }
        actual_variants = {
            name: value.__dict__["__serde_variant_fields__"]
            for name, value in tagged_classes.items()
        }
        expected_field_names = {
            (name, field) for name, fields in expected_structs.items() for field in fields
        }
        annotated_field_names = {
            (name, field)
            for name, fields in rust_api_struct_field_annotations().items()
            for field, annotation in fields.items()
            if annotation in {"Optional[int]", "Optional[List[int]]"}
        }
        annotated_field_names.update(
            (name, field)
            for name, value in vars(ws).items()
            if is_dataclass(value)
            if value.__module__ == ws.__name__
            for field, annotation in getattr(value, "__annotations__", {}).items()
            if annotation in {"int", "List[int]"}
        )

        actual_required = python_api_required_fields()
        actual_required.update(
            (name, fields_out)
            for name, value in vars(ws).items()
            if isinstance(value, type)
            if (fields_out := set(getattr(value, "__serde_required__", set())))
        )

        self.assertEqual(actual_structs, expected_integer_types)
        self.assertEqual(actual_required, expected_required)
        self.assertEqual(
            python_api_required_nullable_fields(), expected_required_nullable
        )
        self.assertEqual(actual_variants, expected_tagged)
        self.assertEqual(
            {
                name
                for name, value in tagged_classes.items()
                if value.__serde_variant_deny_unknown__
            },
            expected_deny,
        )
        self.assertEqual(expected_field_names, annotated_field_names)
        self.assertEqual(
            (REPO_ROOT / "python/src/longshot_protocol/_serde_metadata.py").read_text(),
            render(
                expected_structs,
                expected_required,
                expected_required_nullable,
                expected_tagged,
                expected_deny,
            ),
        )

    def test_api_defaults_metadata_matches_rust(self) -> None:
        self.assertEqual(python_api_defaults(), rust_api_defaults())

    def test_api_required_fields_metadata_matches_rust(self) -> None:
        self.assertEqual(python_api_required_fields(), rust_api_required_fields())
        self.assertEqual(
            python_api_required_nullable_fields(),
            rust_api_required_nullable_fields(),
        )
        self.assertEqual(
            sum(map(len, rust_api_required_nullable_fields().values())), 20
        )

    def test_required_nullable_wire_field_distinguishes_missing_from_null(self) -> None:
        payload = {
            "scope": "all",
            "active_count": 0,
            "potential_payout_micros": "0",
            "realized_pnl_micros": "0",
        }

        with self.assertRaisesRegex(ValueError, "biggest_win_micros"):
            api.PortfolioSummaryResponse.from_dict(payload)

        decoded_null = api.PortfolioSummaryResponse.from_dict(
            {**payload, "biggest_win_micros": None}
        )
        self.assertIsNone(decoded_null.biggest_win_micros)
        self.assertEqual(decoded_null.to_dict()["biggest_win_micros"], None)

        decoded_value = api.PortfolioSummaryResponse.from_dict(
            {**payload, "biggest_win_micros": "1250000"}
        )
        self.assertEqual(decoded_value.biggest_win_micros, 1_250_000)
        self.assertEqual(decoded_value.to_dict()["biggest_win_micros"], "1250000")

    def test_user_transactions_preserve_wire_amounts_and_query_strictness(self) -> None:
        payload = {
            "items": [
                {
                    "id": "ledger-event",
                    "category": "withdrawal",
                    "title": "Withdrawal",
                    "status": "completed",
                    "occurred_at_ms": 1_700_000_000_000,
                    "amount_micros": "-9007199254740993",
                    "unit": "usdc",
                    "tx_hash": "0xabc",
                }
            ],
            "next_cursor": None,
        }
        response = api.UserTransactionsResponse.from_dict(payload)
        self.assertEqual(response.items[0].amount_micros, -9_007_199_254_740_993)
        self.assertEqual(response.items[0].category, api.UserTransactionCategory.Withdrawal)
        self.assertEqual(response.to_dict(), payload)

        query = api.UserTransactionsRawQuery.from_dict(
            {"category": "withdrawal", "from_ms": "1", "limit": 25}
        )
        self.assertEqual(
            query.to_dict(),
            {
                "category": "withdrawal",
                "from_ms": "1",
                "to_ms": None,
                "limit": 25,
                "cursor": None,
            },
        )
        with self.assertRaises(ValueError):
            api.UserTransactionsRawQuery.from_dict({"unexpected": True})

    def test_generated_api_stub_matches_rust_required_fields(self) -> None:
        render = API_STUB_GENERATOR["render_api_stub"]
        api_path = REPO_ROOT / "python/src/longshot_protocol/api.py"
        stub_path = api_path.with_suffix(".pyi")
        self.assertEqual(
            stub_path.read_text(),
            render(
                api_path,
                rust_api_required_fields(),
                rust_api_required_nullable_fields(),
            ),
        )

        stub_classes = {
            node.name: node
            for node in ast.parse(stub_path.read_text()).body
            if isinstance(node, ast.ClassDef)
        }
        mismatches = []
        for class_name, required_fields in rust_api_required_fields().items():
            class_node = stub_classes[class_name]
            annotations = {
                node.target.id: ast.unparse(node.annotation)
                for node in class_node.body
                if isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
            }
            constructor = next(
                node
                for node in class_node.body
                if isinstance(node, ast.FunctionDef) and node.name == "__init__"
            )
            defaults = {
                argument.arg: default
                for argument, default in zip(
                    constructor.args.kwonlyargs, constructor.args.kw_defaults
                )
            }
            for field in required_fields:
                if field not in defaults or defaults[field] is not None:
                    mismatches.append((class_name, field, "constructor default"))
                if annotations.get(field, "").startswith("Optional["):
                    mismatches.append((class_name, field, "optional annotation"))
        for class_name, required_fields in rust_api_required_nullable_fields().items():
            class_node = stub_classes[class_name]
            annotations = {
                node.target.id: ast.unparse(node.annotation)
                for node in class_node.body
                if isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
            }
            constructor = next(
                node
                for node in class_node.body
                if isinstance(node, ast.FunctionDef) and node.name == "__init__"
            )
            defaults = {
                argument.arg: default
                for argument, default in zip(
                    constructor.args.kwonlyargs, constructor.args.kw_defaults
                )
            }
            for field in required_fields:
                if field not in defaults or defaults[field] is not None:
                    mismatches.append((class_name, field, "constructor default"))
                if not annotations.get(field, "").startswith("Optional["):
                    mismatches.append((class_name, field, "nullable annotation"))
        self.assertEqual(mismatches, [])

    def test_recent_resolution_round_trips_window_start(self) -> None:
        payload = {
            "market_id": 42,
            "outcome": "YES",
            "window_start_ms": 1_735_689_600_000,
            "resolved_at_ms": 1_735_689_901_000,
        }
        self.assertEqual(api.RecentResolutionEntry.from_dict(payload).to_dict(), payload)

    def test_api_skip_non_finite_metadata_matches_rust(self) -> None:
        self.assertEqual(python_api_skip_non_finite_fields(), rust_api_skip_non_finite_fields())

    def test_api_deny_unknown_metadata_matches_rust(self) -> None:
        self.assertEqual(python_api_deny_unknown_structs(), rust_api_deny_unknown_structs())

    def test_top_level_exports_every_public_rust_mm_declaration(self) -> None:
        missing = sorted(name for name in rust_mm_public_declarations() if not hasattr(longshot_protocol, name))
        self.assertEqual(missing, [])

    def test_signed_order_json_round_trips_protocol_order(self) -> None:
        order = SignedOrder(
            user=Address.from_hex("0x52908400098527886e0f7030069857d2e4169ee7"),
            wager_micros=100_000_000,
            min_odds_bps=25_000,
            legs=[OrderLeg(MarketId(42), 0)],
            nonce=123,
            expires_at_ms=456,
            order_type=OrderType.FOK,
            shield_on=False,
            signature=bytes([0xAB]) * 65,
        )

        wire = SignedOrderJson.from_signed_order(order)
        wire_dict = wire.to_dict()

        self.assertEqual(wire_dict["user"], "0x52908400098527886E0F7030069857D2E4169EE7")
        self.assertEqual(
            {
                field: wire_dict[field]
                for field in ("wager_micros", "nonce", "expires_at_ms")
            },
            {
                "wager_micros": 100_000_000,
                "nonce": 123,
                "expires_at_ms": 456,
            },
        )
        self.assertEqual(wire_dict["min_odds"], 2.5)
        self.assertEqual(wire_dict["signature"], b64encode(bytes([0xAB]) * 65).decode("ascii"))
        string_input = {
            **wire_dict,
            "wager_micros": "100000000",
            "nonce": "123",
            "expires_at_ms": "456",
        }
        self.assertEqual(SignedOrderJson.from_dict(string_input).to_dict(), wire_dict)
        parsed = wire.to_signed_order()
        self.assertEqual(parsed.signing_bytes(True), order.signing_bytes(True))
        self.assertEqual(parsed.signature, order.signature)

        canonical_zero_signature = b64encode(bytes(65)).decode("ascii")
        noncanonical_wire = {
            **wire_dict,
            "signature": canonical_zero_signature[:-2] + "B=",
        }
        with self.assertRaisesRegex(ValueError, "invalid signature format"):
            SignedOrderJson.from_dict(noncanonical_wire).to_signed_order()

    def test_rfq_order_conversion_rejects_non_boolean_shield(self) -> None:
        for invalid_shield in (None, 0, 1, "false"):
            with self.subTest(shield_on=invalid_shield):
                signed = SignedOrderJson(
                    user=Address.ZERO.to_checksum(),
                    wager_micros=1_000_000,
                    min_odds=2.5,
                    legs=[OrderLegJson(market_id=42, direction="up")],
                    nonce=123,
                    expires_at_ms=456,
                    order_type=2,
                    shield_on=invalid_shield,
                    signature=b64encode(bytes(65)).decode("ascii"),
                )
                unsigned = api.UnsignedRfqOrderRequest(
                    wager_micros=1_000_000,
                    min_odds=2.5,
                    legs=[OrderLegJson(market_id=42, direction="up")],
                    order_type=2,
                    shield_on=invalid_shield,
                    idempotency_key="00112233-4455-6677-8899-aabbccddeeff",
                )

                with self.assertRaisesRegex(ValueError, "shield_on must be bool"):
                    signed.to_signed_order()
                with self.assertRaisesRegex(ValueError, "shield_on must be bool"):
                    unsigned.into_signed_order_for_session(Address.ZERO, nonce=123, expires_at_ms=456)

    def test_rfq_order_conversion_rejects_non_integer_scalars(self) -> None:
        invalid_values = (True, 1.5, "1")
        for field in ("wager_micros", "nonce", "expires_at_ms"):
            for invalid_value in invalid_values:
                with self.subTest(payload="signed", field=field, value=invalid_value):
                    signed = SignedOrderJson(
                        user=Address.ZERO.to_checksum(),
                        wager_micros=1_000_000,
                        min_odds=2.5,
                        legs=[OrderLegJson(market_id=42, direction="up")],
                        nonce=123,
                        expires_at_ms=456,
                        order_type=2,
                        shield_on=False,
                        signature=b64encode(bytes(65)).decode("ascii"),
                    )
                    setattr(signed, field, invalid_value)

                    with self.assertRaisesRegex(ValueError, f"{field} must fit in u64"):
                        signed.to_signed_order()

        for invalid_value in invalid_values:
            with self.subTest(payload="leg", field="market_id", value=invalid_value):
                with self.assertRaisesRegex(ValueError, "market_id must fit in u64"):
                    OrderLegJson(market_id=invalid_value, direction="up").parse()

            for payload in ("signed", "unsigned"):
                with self.subTest(payload=payload, field="order_type", value=invalid_value):
                    if payload == "signed":
                        order = SignedOrderJson(
                            user=Address.ZERO.to_checksum(),
                            wager_micros=1_000_000,
                            min_odds=2.5,
                            legs=[OrderLegJson(market_id=42, direction="up")],
                            nonce=123,
                            expires_at_ms=456,
                            order_type=invalid_value,
                            shield_on=False,
                            signature=b64encode(bytes(65)).decode("ascii"),
                        )
                        convert = order.to_signed_order
                    else:
                        order = api.UnsignedRfqOrderRequest(
                            wager_micros=1_000_000,
                            min_odds=2.5,
                            legs=[OrderLegJson(market_id=42, direction="up")],
                            order_type=invalid_value,
                            shield_on=False,
                            idempotency_key="00112233-4455-6677-8899-aabbccddeeff",
                        )
                        convert = lambda: order.into_signed_order_for_session(
                            Address.ZERO, nonce=123, expires_at_ms=456
                        )

                    with self.assertRaisesRegex(ValueError, "order_type must be int"):
                        convert()

        for invalid_value in invalid_values:
            with self.subTest(payload="unsigned", field="wager_micros", value=invalid_value):
                unsigned = api.UnsignedRfqOrderRequest(
                    wager_micros=invalid_value,
                    min_odds=2.5,
                    legs=[OrderLegJson(market_id=42, direction="up")],
                    order_type=2,
                    shield_on=False,
                    idempotency_key="00112233-4455-6677-8899-aabbccddeeff",
                )

                with self.assertRaisesRegex(ValueError, "wager_micros must fit in u64"):
                    unsigned.into_signed_order_for_session(
                        Address.ZERO, nonce=123, expires_at_ms=456
                    )

            for field in ("nonce", "expires_at_ms"):
                with self.subTest(payload="unsigned", field=field, value=invalid_value):
                    nonce = invalid_value if field == "nonce" else 123
                    expires_at_ms = invalid_value if field == "expires_at_ms" else 456
                    with self.assertRaisesRegex(ValueError, f"{field} must fit in u64"):
                        api.UnsignedRfqOrderRequest(
                            wager_micros=1_000_000,
                            min_odds=2.5,
                            legs=[OrderLegJson(market_id=42, direction="up")],
                            order_type=2,
                            shield_on=False,
                            idempotency_key="00112233-4455-6677-8899-aabbccddeeff",
                        ).into_signed_order_for_session(
                            Address.ZERO,
                            nonce=nonce,
                            expires_at_ms=expires_at_ms,
                        )

    def test_order_leg_json_validation_matches_rust_helper(self) -> None:
        parsed = OrderLegJson(market_id=42, direction="Down").parse()

        self.assertEqual(parsed.market_id, MarketId(42))
        self.assertEqual(parsed.direction, Direction.Down)
        with self.assertRaises(ValueError):
            OrderLegJson.from_dict({"market_id": "0", "direction": "up"}).parse()

    def test_rfq_order_deserialization_rejects_string_market_id(self) -> None:
        for payload_type, payload in [
            (
                api.SignedOrderJson,
                {
                    "user": "0x1111111111111111111111111111111111111111",
                    "wager_micros": 100_000_000,
                    "min_odds": 2.5,
                    "legs": [{"market_id": "0", "direction": "up"}],
                    "nonce": 123,
                    "expires_at_ms": 456,
                    "shield_on": False,
                    "signature": b64encode(bytes(65)).decode("ascii"),
                },
            ),
            (
                api.UnsignedRfqOrderRequest,
                {
                    "wager_micros": 100_000_000,
                    "min_odds": 2.5,
                    "legs": [{"market_id": "0", "direction": "up"}],
                    "shield_on": False,
                    "idempotency_key": "00112233-4455-6677-8899-aabbccddeeff",
                },
            ),
        ]:
            with self.subTest(payload_type=payload_type):
                with self.assertRaisesRegex(ValueError, "expected <class 'int'>"):
                    payload_type.from_dict(payload)

    def test_api_tagged_unions_emit_serde_tags(self) -> None:
        notification = NotificationPayload.binary_event_start_soon(
            market_title="BTC higher", source="kalshi", event_id="evt", starts_at_ms=1
        )
        self.assertEqual(
            notification.to_dict(),
            {
                "type": "binary_event_start_soon",
                "market_title": "BTC higher",
                "source": "kalshi",
                "event_id": "evt",
                "starts_at_ms": 1,
            },
        )

        snapshot = ShareCardSnapshot.price(
            PriceShareCard(
                contest_id="contest",
                entry_index=0,
                state="live",
                question="BTC?",
                prediction=100.0,
                current_price=101.0,
                chart_prices=[100.0, 101.0],
                footer=ShareCardFooter(handle="alice"),
            )
        )
        self.assertEqual(snapshot.to_dict()["type"], "price")
        self.assertEqual(snapshot.to_dict()["footer"], {"handle": "alice"})

    def test_survivor_hidden_picks_require_null_and_portfolio_state_survives_decode(self) -> None:
        hidden = api.SurvivorRoundPicksResponse.from_dict(
            {"visibility": "hidden", "picks": None}
        )
        self.assertEqual(hidden.to_dict(), {"visibility": "hidden", "picks": None})
        with self.assertRaisesRegex(ValueError, "NoneType"):
            api.SurvivorRoundPicksResponse.from_dict(
                {"visibility": "hidden", "picks": []}
            )

        entry = api.PortfolioFantasyEntryResponse.from_dict(
            {
                "contest_id": "11111111-1111-1111-1111-111111111111",
                "title": "Survivor",
                "category": "crypto",
                "status": "open",
                "game_type": "survivor",
                "current_game_index": 0,
                "bet_amount_micros": "1000000",
                "protocol_prize_pool_micros": "0",
                "total_pot_micros": "1000000",
                "entries_filled": 1,
                "entry_cap": 5,
                "betting_closes_ms": 2,
                "joined_at_ms": 1,
                "entry_index": 0,
                "open_leg_count": 1,
                "resolved_win_count": 0,
                "payout_micros": None,
                "net_payout_micros": None,
                "pnl_micros": None,
                "selection_count": 1,
                "survivor": {
                    "status": "alive",
                    "eligible_for_current_game": True,
                    "rounds": [],
                },
            }
        )
        self.assertEqual(entry.game_type, api.ContestGameTypeResponse.Survivor)
        self.assertEqual(entry.current_game_index, 0)
        self.assertEqual(entry.survivor.variant, "Alive")

    def test_fantasy_result_notification_uses_aggregate_wire_contract(self) -> None:
        notification = NotificationPayload.fantasy_result(
            contest_id="contest-outcast",
            game_index=2,
            game_type=api.FantasyResultGameType.Outcast,
            contest_title="Stay With The Pack",
            contest_terminal=True,
            contest_refunded=True,
            entry_count=3,
            successful_entry_count=2,
            held_entry_count=1,
            credited_payout_micros=7_500_000,
            held_payout_micros=2_500_000,
            best_entry=api.FantasyResultBestEntry(
                entry_index=1,
                rank=3,
                correct_count=5,
                selection_count=6,
            ),
            tiebreaker_result=42,
        )
        encoded = {
            "type": "fantasy_result",
            "contest_id": "contest-outcast",
            "game_index": 2,
            "game_type": "outcast",
            "contest_title": "Stay With The Pack",
            "contest_terminal": True,
            "contest_refunded": True,
            "entry_count": 3,
            "successful_entry_count": 2,
            "held_entry_count": 1,
            "credited_payout_micros": 7_500_000,
            "held_payout_micros": 2_500_000,
            "best_entry": {
                "entry_index": 1,
                "rank": 3,
                "correct_count": 5,
                "selection_count": 6,
            },
            "tiebreaker_result": 42,
        }

        self.assertEqual(notification.to_dict(), encoded)
        decoded = NotificationPayload.from_dict(encoded)
        self.assertIsInstance(decoded.payload, api.FantasyResultNotificationPayload)
        self.assertEqual(decoded.to_dict(), encoded)

    def test_chat_mention_notification_round_trips_room_destination(self) -> None:
        encoded = {
            "type": "chat_mention",
            "chat_id": "55555555-5555-4555-8555-555555555555",
            "message_id": "66666666-6666-4666-8666-666666666666",
        }

        notification = NotificationPayload.chat_mention(
            chat_id=encoded["chat_id"],
            message_id=encoded["message_id"],
        )
        self.assertEqual(notification.to_dict(), encoded)
        decoded = NotificationPayload.from_dict(encoded)
        self.assertIsInstance(decoded.payload, api.ChatMentionNotificationPayload)
        self.assertEqual(decoded.to_dict(), encoded)

        legacy = NotificationPayload.chat_mention(
            chat_id="9187ca06-569d-5bc7-8aa1-cb4dd2da71ac",
            chat_context=api.ChatMentionContext.CryptoMarket,
            message_id="77777777-7777-4777-8777-777777777777",
        )
        self.assertEqual(legacy.to_dict()["chat_context"], "crypto_market")
        self.assertNotIn("contest_id", legacy.to_dict())

    def test_fantasy_refund_defaults_and_legacy_variants(self) -> None:
        encoded = {
            "entry_index": 0,
            "created_at_ms": 1,
            "picks": [],
            "open_leg_count": 0,
            "resolved_win_count": 0,
        }

        self.assertFalse(api.ContestUserEntryResponse.from_dict(encoded).refunded)
        self.assertTrue(
            api.ContestUserEntryResponse.from_dict({**encoded, "refunded": True}).refunded
        )

        for removed_tag in ("fantasy_win", "fantasy_settled"):
            with self.assertRaisesRegex(ValueError, "unknown NotificationPayload variant"):
                NotificationPayload.from_dict({"type": removed_tag})

        for removed_name in (
            "FantasyWinNotificationPayload",
            "FantasySettledNotificationPayload",
            "FantasySettledOutcome",
        ):
            self.assertNotIn(removed_name, api.__all__)
            self.assertFalse(hasattr(api, removed_name))
            self.assertFalse(hasattr(longshot_protocol, removed_name))

    def test_active_position_hydrates_typed_fields(self) -> None:
        raw = {
            "position_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "open",
            "role": "maker",
            "taker_address": "0x1111111111111111111111111111111111111111",
            "wager_micros": "1000000",
            "app_token_wager_micros": "0",
            "payout_micros": "1500000",
            "legs": [],
        }
        position = api.ActivePosition.from_dict(raw)
        self.assertEqual(
            position.taker_address,
            Address.from_hex("0x1111111111111111111111111111111111111111"),
        )
        self.assertEqual(position.to_dict(), raw)

        self.assertFalse(hasattr(NotificationPayload, "fantasy_win"))
        self.assertFalse(hasattr(NotificationPayload, "fantasy_settled"))

    def test_api_inline_tagged_fields_match_serde(self) -> None:
        avatar = api.ChatUserAvatarResponse.from_dict(
            {"type": "x_avatar_url", "url": "https://example.test/a", "ignored": True}
        )
        self.assertEqual(
            avatar.to_dict(),
            {"type": "x_avatar_url", "url": "https://example.test/a"},
        )
        for payload in (
            {"type": "x_avatar_url"},
            {"type": "x_avatar_url", "url": 1},
            {"type": "seed", "seed": 1 << 31},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                api.ChatUserAvatarResponse.from_dict(payload)

    def test_api_struct_serde_renames_and_enum_values(self) -> None:
        response = NotificationResponse(
            seq=1,
            id="n1",
            notification_type="binary_event",
            category="positions",
            title="title",
            body="body",
            icon="bell",
            payload=NotificationPayload.unknown(),
            created_at_ms=2,
            read_at_ms=None,
        )

        encoded = response.to_dict()
        self.assertEqual(encoded["type"], "binary_event")
        self.assertNotIn("read_at_ms", encoded)

    def test_api_from_dict_hydrates_nested_notification_payload(self) -> None:
        response = api.NotificationResponse.from_dict(
            {
                "seq": 1,
                "id": "n1",
                "type": "binary_event",
                "category": "positions",
                "title": "title",
                "body": "body",
                "icon": "bell",
                "payload": {
                    "type": "binary_event_start_soon",
                    "source": "kalshi",
                    "event_id": "evt",
                    "market_title": "BTC higher",
                    "starts_at_ms": 123,
                },
                "created_at_ms": 2,
            }
        )

        self.assertIsInstance(response.payload, api.NotificationPayload)
        self.assertEqual(response.payload.variant, "BinaryEventStartSoon")
        self.assertIsInstance(
            response.payload.payload,
            api.BinaryEventStartSoonNotificationPayload,
        )
        self.assertEqual(response.payload.payload.market_title, "BTC higher")

    def test_api_from_dict_hydrates_nested_rfq_request_and_rejects_unknowns(self) -> None:
        payload = {
            "privy_token": "token",
            "use_app_tokens": True,
            "rfq_params": {
                "wager_micros": 100_000_000,
                "min_odds": 2.5,
                "legs": [{"market_id": 42, "direction": "up"}],
                "shield_on": False,
                "idempotency_key": "00112233-4455-6677-8899-aabbccddeeff",
            },
        }
        request = api.CreateUnsignedRfqRequest.from_dict(payload)

        self.assertIsInstance(request.rfq_params, api.UnsignedRfqOrderRequest)
        self.assertIsInstance(request.rfq_params.legs[0], api.OrderLegJson)
        for invalid_market_id in (True, -1, 1 << 64):
            payload["rfq_params"]["legs"][0]["market_id"] = invalid_market_id
            with self.subTest(market_id=invalid_market_id):
                with self.assertRaises(ValueError):
                    api.CreateUnsignedRfqRequest.from_dict(payload)
        payload["rfq_params"]["legs"][0]["market_id"] = 42
        with self.assertRaisesRegex(ValueError, "unexpected"):
            api.CreateUnsignedRfqRequest.from_dict(
                {
                    "privy_token": "token",
                    "use_app_tokens": True,
                    "rfq_params": {
                        "wager_micros": 100_000_000,
                        "min_odds": 2.5,
                        "legs": [{"market_id": 42, "direction": "up"}],
                        "shield_on": False,
                        "idempotency_key": "00112233-4455-6677-8899-aabbccddeeff",
                        "unexpected": True,
                    },
                }
            )

    def test_serde_coercion_enforces_primitive_and_container_shapes(self) -> None:
        valid_cases = [
            (True, bool, True),
            (7, int, 7),
            (7, float, 7.0),
            ("value", str, "value"),
            ([0, 255], bytes, b"\x00\xff"),
            ([0] * 20, Address, Address.ZERO),
            ([1, 2], List[int], [1, 2]),
            ({"key": 3}, Dict[str, int], {"key": 3}),
            (["key", 4], Tuple[str, int], ("key", 4)),
            ("value", Union[int, str], "value"),
            (None, Optional[int], None),
        ]
        invalid_cases = [
            (1, bool),
            (True, int),
            (1.0, int),
            (True, float),
            ("1.0", float),
            (float("nan"), float),
            (1, str),
            (bytes(20), Address),
            ([256], bytes),
            ((1,), List[int]),
            ([], Dict[str, int]),
            ({"key": True}, Dict[str, int]),
            (["key"], Tuple[str, int]),
            (1.5, Union[int, str]),
        ]

        for value, target_type, expected in valid_cases:
            with self.subTest(value=value, target_type=target_type):
                self.assertEqual(model._coerce_from_serde(value, target_type), expected)
        for value, target_type in invalid_cases:
            with self.subTest(value=value, target_type=target_type):
                with self.assertRaises(ValueError):
                    model._coerce_from_serde(value, target_type)
        with self.assertRaisesRegex(ValueError, "expected <class 'int'>"):
            api.RfqResponse.from_dict(
                {
                    "request_id": "00112233-4455-6677-8899-aabbccddeeff",
                    "status": "completed",
                    "odds": 2.5,
                    "payout_micros": True,
                    "quotes_received": 1,
                }
            )
        for check in (_check_u8, _check_u32, _check_u64):
            for invalid in (True, 1.5):
                with self.subTest(check=check.__name__, invalid=invalid), self.assertRaises(ValueError):
                    check(invalid, "value")
        self.assertEqual(_check_u8(OrderType.FOK, "value"), OrderType.FOK)

    def test_integer_width_boundaries_match_rust_serde(self) -> None:
        cases = [
            (
                api.UserDepositWalletResponse,
                "token_decimals",
                0,
                (1 << 8) - 1,
                {"address": "0x0", "token_symbol": "USDC"},
            ),
            (api.ListContestsQuery, "limit", 0, (1 << 32) - 1, {}),
            (
                api.StreakTierResponse,
                "payout_micros",
                0,
                (1 << 64) - 1,
                {"streak": 0, "has_app_token": False},
            ),
        ]
        for payload_type, field, minimum, maximum, required in cases:
            for value in (minimum, maximum):
                with self.subTest(payload_type=payload_type, field=field, value=value):
                    decoded = payload_type.from_dict({**required, field: value})
                    self.assertEqual(getattr(decoded, field), value)
            for value in (minimum - 1, maximum + 1):
                with self.subTest(payload_type=payload_type, field=field, value=value):
                    with self.assertRaises(ValueError):
                        payload_type.from_dict({**required, field: value})

        max_u64 = (1 << 64) - 1
        balance = api.AvailableBalanceResponse.from_dict(
            {"available_micros": str(max_u64)}
        )
        self.assertEqual(balance.available_micros, max_u64)
        for invalid_balance in ("-0", "-1", str(1 << 64)):
            with self.assertRaises(ValueError):
                api.AvailableBalanceResponse.from_dict(
                    {"available_micros": invalid_balance}
                )
        notification = {
            "position_id": "position",
            "net_payout_micros": 0,
            "multiplier_bps": 0,
            "leg_summary": "legs",
            "is_multi_asset": False,
            "duration_secs": [(1 << 31) - 1],
        }
        api.PriceStrikeParlayWinNotificationPayload.from_dict(notification)
        notification["duration_secs"] = [1 << 31]
        with self.assertRaises(ValueError):
            api.PriceStrikeParlayWinNotificationPayload.from_dict(notification)

        emoji = api.ChatEmojiResponse(
            code="party",
            display=api.ChatEmojiDisplayResponse.unicode(value="🎉"),
        )
        outbound_cases = [
            (api.ListContestsQuery(limit=(1 << 32) - 1), False),
            (api.ListContestsQuery(limit=True), True),
            (api.ListContestsQuery(limit="1"), True),
            (api.ListContestsQuery(limit=1 << 32), True),
            (
                api.PriceStrikeParlayWinNotificationPayload(
                    **{**notification, "duration_secs": [(1 << 31) - 1]}
                ),
                False,
            ),
            (api.PriceStrikeParlayWinNotificationPayload(**notification), True),
            (api.ChatEmojisResponse(emojis=[emoji]), False),
            (api.ChatEmojisResponse(emojis=["party"]), True),
        ]
        for payload, invalid in outbound_cases:
            with self.subTest(payload=payload, invalid=invalid):
                if invalid:
                    with self.assertRaises(ValueError):
                        payload.to_dict()
                else:
                    self.assertIsInstance(payload.to_dict(), dict)

        bet_type = api.ContestBetTypeResponse.from_dict(
            {"type": "num_bets", "value": (sys.maxsize << 1) + 1}
        )
        self.assertEqual(bet_type.payload, (sys.maxsize << 1) + 1)
        with self.assertRaises(ValueError):
            api.ContestBetTypeResponse.from_dict(
                {"type": "num_bets", "value": (sys.maxsize + 1) << 1}
            )
        for spec, minimum, maximum in (
            ("u128", 0, (1 << 128) - 1),
            ("i128", -(1 << 127), (1 << 127) - 1),
        ):
            self.assertEqual(model._coerce_sized_integer(maximum, spec), maximum)
            for invalid in (minimum - 1, maximum + 1):
                with self.assertRaises(ValueError):
                    model._coerce_sized_integer(invalid, spec)

    def test_api_serde_unwraps_rust_transparent_primitives(self) -> None:
        price_market = api.PriceStrikeMarket(
            id=MarketId(42),
            market_type=MarketType.Crypto,
            trading_channels=[api.TradingChannel.Rfq],
            name="BTC up",
            description="desc",
            status=MarketStatus.Open,
            tradeable=True,
            category_tags=[],
            betting_closes_at_ms=Timestamp.from_millis(1_000),
            resolution_time_ms=Timestamp.from_millis(2_000),
            open_strike_micros=None,
            resolved_outcome=None,
            created_at_ms=Timestamp.from_millis(500),
            opened_at_ms=None,
            resolved_at_ms=None,
        )
        market = api.PublicMarketResponse(
            market=api.PublicMarket.price_strike(price_market)
        )

        encoded = market.to_dict()

        self.assertEqual(encoded["market"]["market_type"], "crypto")
        self.assertEqual(encoded["market"]["id"], 42)
        self.assertEqual(encoded["market"]["betting_closes_at_ms"], 1_000)
        self.assertEqual(encoded["market"]["resolution_time_ms"], 2_000)
        self.assertEqual(encoded["market"]["created_at_ms"], 500)
        json.dumps(encoded)
        self.assertEqual(
            to_serde_value(
                {
                    "request_id": RequestId.nil(),
                    "amount": Amount.from_micro(1_000_000),
                    "odds": Odds(25_000),
                    "duration": Duration.FIVE_MINUTES,
                    "tier": UserTier.Gold,
                }
            ),
            {
                "request_id": "00000000-0000-0000-0000-000000000000",
                "amount": 1_000_000,
                "odds": 25_000,
                "duration": 300,
                "tier": "Gold",
            },
        )

    def test_api_from_dict_hydrates_annotated_rust_mirror_types(self) -> None:
        market = api.PublicMarketResponse.from_dict(
            {
                "market": {
                    "id": 42,
                    "market_type": "new-category",
                    "trading_channels": ["rfq"],
                    "name": "BTC up",
                    "description": "desc",
                    "status": "OPEN",
                    "tradeable": True,
                    "category_tags": [],
                    "betting_closes_at_ms": 1_000,
                    "resolution_time_ms": 2_000,
                    "open_strike_micros": None,
                    "resolved_outcome": "YES",
                    "created_at_ms": 500,
                    "resolved_at_ms": None,
                },
            }
        )
        response = api.RfqResponse.from_dict(
            {
                "request_id": "00112233-4455-6677-8899-aabbccddeeff",
                "status": "completed",
                "odds": 2.5,
                "payout_micros": "250000000",
                "quotes_received": 3,
            }
        )

        self.assertIsNotNone(market.market)
        self.assertEqual(market.market.variant, "PriceStrike")
        self.assertIsInstance(market.market.payload, api.PriceStrikeMarket)
        self.assertEqual(market.market.payload.id, MarketId(42))
        self.assertEqual(market.market.payload.market_type, "new-category")
        self.assertIs(market.market.payload.status, MarketStatus.Open)
        self.assertIs(market.market.payload.resolved_outcome, api.Outcome.Yes)
        self.assertIsInstance(response.request_id, UUID)
        self.assertIs(response.status, api.RfqStatus.Completed)
        self.assertEqual(
            response.to_dict()["request_id"],
            "00112233-4455-6677-8899-aabbccddeeff",
        )

    def test_renamed_optional_fields_can_be_absent(self) -> None:
        typed_query = api.PnlHistoryQuery.from_dict({})
        scoped_query = api.PnlHistoryScopedQuery.from_dict({})

        self.assertIsNone(typed_query.from_)
        self.assertIsNone(typed_query.to)
        self.assertIsNone(scoped_query.from_)
        self.assertIsNone(scoped_query.to)

    def test_deny_unknown_renamed_fields_only_accept_wire_names(self) -> None:
        typed_query = api.PnlHistoryQuery.from_dict({"from": 1, "to": 2})
        scoped_query = api.PnlHistoryScopedQuery.from_dict({"from": 1, "to": 2})

        self.assertEqual(typed_query.from_, 1)
        self.assertEqual(typed_query.to, 2)
        self.assertEqual(scoped_query.from_, 1)
        self.assertEqual(scoped_query.to, 2)
        with self.assertRaisesRegex(ValueError, "from_"):
            api.PnlHistoryQuery.from_dict({"from_": 1})
        with self.assertRaisesRegex(ValueError, "from_"):
            api.PnlHistoryScopedQuery.from_dict({"from_": 1})

    def test_client_query_contracts_require_semantic_route_values(self) -> None:
        cases = [
            (api.ChatMentionCandidatesQuery, {"chat_id": "room-id"}),
            (
                api.MarketLookupQuery,
                {"asset": "BTC", "duration_secs": 300, "window_start_ms": 1},
            ),
            (api.MarketCurrentQuery, {"asset": "BTC", "duration_secs": 300}),
            (api.PositionsByMarketsQuery, {"market_ids": "1,2"}),
            (
                api.ConfirmPositionQuery,
                {"position_id": "position", "accept": True},
            ),
        ]
        for model, payload in cases:
            with self.subTest(model=model.__name__):
                with self.assertRaises(ValueError):
                    model.from_dict({})
                decoded = model.from_dict(payload)
                for field, value in payload.items():
                    self.assertEqual(getattr(decoded, field), value)

        invalid_scalars = [
            (
                api.MarketLookupQuery,
                {"asset": "BTC", "duration_secs": "300", "window_start_ms": 1},
            ),
            (api.MarketCurrentQuery, {"asset": "BTC", "duration_secs": "300"}),
            (
                api.ConfirmPositionQuery,
                {"position_id": "position", "accept": "true"},
            ),
            (api.PnlHistoryScopedQuery, {"from": "1"}),
        ]
        for model, payload in invalid_scalars:
            with self.subTest(model=model.__name__):
                with self.assertRaises(ValueError):
                    model.from_dict(payload)

    def test_error_response_helpers_match_rust_builders(self) -> None:
        response = ErrorResponse.new("Invalid session token", "INVALID_SESSION")

        self.assertEqual(
            response.to_dict(),
            {"error": "Invalid session token", "code": "INVALID_SESSION"},
        )
        self.assertEqual(
            response.with_details("expired").to_dict(),
            {"error": "Invalid session token", "code": "INVALID_SESSION", "details": "expired"},
        )

    def test_wire_int_fields_serialize_as_strings(self) -> None:
        response = api.UserWithdrawResponse(
            amount_micros=1_000_000,
            operation_id="00112233-4455-6677-8899-aabbccddeeff",
            destination_address=None,
            tx_hash="0xabc",
        )

        encoded = response.to_dict()

        self.assertEqual(encoded["amount_micros"], "1000000")
        self.assertNotIn("destination_address", encoded)
        self.assertEqual(api.UserWithdrawResponse.from_dict(encoded).amount_micros, 1_000_000)

    def test_rfq_response_omits_non_finite_odds_and_stringifies_payout(self) -> None:
        encoded = api.RfqResponse(
            request_id="00112233-4455-6677-8899-aabbccddeeff",
            status=api.RfqStatus.Completed,
            odds=float("nan"),
            payout_micros=250_000_000,
            error=None,
            quotes_received=3,
        ).to_dict()

        self.assertNotIn("odds", encoded)
        self.assertNotIn("error", encoded)
        self.assertEqual(encoded["payout_micros"], "250000000")
        self.assertEqual(api.RfqResponse.from_dict(encoded).payout_micros, 250_000_000)

    def test_defaulted_api_fields_match_rust_deserialization(self) -> None:
        signed = api.SignedOrderJson.from_dict(
            {
                "user": "0x1111111111111111111111111111111111111111",
                "wager_micros": 100_000_000,
                "min_odds": 2.5,
                "legs": [{"market_id": 42, "direction": "up"}],
                "nonce": 123,
                "expires_at_ms": 456,
                "shield_on": False,
                "signature": b64encode(bytes(65)).decode("ascii"),
            }
        )
        unsigned = api.UnsignedRfqOrderRequest.from_dict(
            {
                "wager_micros": 100_000_000,
                "min_odds": 2.5,
                "legs": [{"market_id": 42, "direction": "up"}],
                "shield_on": False,
                "idempotency_key": "00112233-4455-6677-8899-aabbccddeeff",
            }
        )

        self.assertEqual(signed.order_type, 2)
        self.assertEqual(unsigned.order_type, 2)
        market_source_a = api.EventMarketSource.from_dict(
            {"source": "kalshi", "source_market_ids": ["KX-1"]}
        )
        market_source_b = api.EventMarketSource.from_dict(
            {"source": "kalshi", "source_market_ids": ["KX-2"]}
        )
        self.assertEqual(market_source_a.attributes, {})
        self.assertEqual(market_source_b.to_dict()["attributes"], {})
        market_source_a.attributes["series"] = "KX"
        self.assertEqual(market_source_b.attributes, {})
        with self.assertRaisesRegex(ValueError, "attributes"):
            api.EventMarketSource.from_dict(
                {
                    "source": "kalshi",
                    "source_market_ids": ["KX-3"],
                    "attributes": None,
                }
            )

        event_market_wire = {
            "id": 42,
            "market_type": "culture",
            "trading_channels": ["rfq"],
            "chat_id": "culture-event",
            "name": "Culture event",
            "status": "OPEN",
            "tradeable": True,
            "category_tags": ["culture"],
            "betting_closes_at_ms": 1_000,
            "resolution_time_ms": 2_000,
            "created_at_ms": 500,
            "source": {"source": "kalshi", "source_market_ids": ["KX-1"]},
        }
        event_market = api.EventMarket.from_dict(event_market_wire)
        self.assertEqual(event_market.resolution_rules, "")
        self.assertEqual(event_market.to_dict()["resolution_rules"], "")
        with self.assertRaisesRegex(ValueError, "resolution_rules"):
            api.EventMarket.from_dict(
                {**event_market_wire, "resolution_rules": None}
            )

        share_card_cases = [
            (
                {
                    "type": "markets",
                    "position_id": "00000000-0000-0000-0000-000000000001",
                    "footer": {"handle": "alice"},
                },
                {
                    "type": "markets",
                    "position_id": "00000000-0000-0000-0000-000000000001",
                    "state": "pre",
                    "multi_asset": False,
                    "assets": [],
                    "windows": [],
                    "date_label": "",
                    "wager_label": "",
                    "multiplier_label": "",
                    "payout_label": "",
                    "footer": {"handle": "alice"},
                },
            ),
            (
                {
                    "type": "survivor",
                    "contest_id": "00000000-0000-0000-0000-000000000002",
                    "entry_index": 0,
                    "footer": {"handle": "alice"},
                },
                {
                    "type": "survivor",
                    "contest_id": "00000000-0000-0000-0000-000000000002",
                    "entry_index": 0,
                    "state": "pre",
                    "contest_type": "free",
                    "presentation": "daily",
                    "title": "",
                    "rounds": [],
                    "footer": {"handle": "alice"},
                },
            ),
            (
                {
                    "type": "event_position",
                    "position_id": "00000000-0000-0000-0000-000000000003",
                    "footer": {"handle": "alice"},
                },
                {
                    "type": "event_position",
                    "position_id": "00000000-0000-0000-0000-000000000003",
                    "state": "active",
                    "title": "",
                    "picks": [],
                    "wager_label": "",
                    "multiplier_label": "",
                    "footer": {"handle": "alice"},
                },
            ),
        ]
        for skeleton, expected_wire in share_card_cases:
            with self.subTest(card_type=skeleton["type"]):
                snapshot = ShareCardSnapshot.from_dict(skeleton)
                self.assertEqual(snapshot.to_dict(), expected_wire)
                with self.assertRaisesRegex(ValueError, "state"):
                    ShareCardSnapshot.from_dict({**skeleton, "state": None})
        self.assertEqual(
            api.PriceShareCard.from_dict(
                {
                    "contest_id": "contest",
                    "entry_index": 0,
                    "state": "live",
                    "question": "BTC?",
                    "prediction": 100.0,
                    "current_price": 101.0,
                    "chart_prices": [100.0, 101.0],
                    "footer": {"handle": "alice"},
                }
            ).summary,
            [],
        )
        self.assertEqual(
            api.QuestionsShareCard.from_dict(
                {
                    "contest_id": "contest",
                    "entry_index": 0,
                    "state": "live",
                    "contest_type": "free",
                    "question": "Who wins?",
                    "legs": [],
                    "footer": {"handle": "alice"},
                }
            ).summary,
            [],
        )

    def test_feed_event_defaults_omitted_legs_to_empty_list(self) -> None:
        payload = {
            "event_type": "place_bet",
            "position_id": "00000000-0000-0000-0000-000000000001",
            "market": "test",
            "legs_count": 1,
            "user_display_name": "Anonymous",
            "user_avatar_seed": 0,
            "wager_micros": "500000",
            "multiplier_bps": 20_000,
            "payout_micros": "1000000",
            "event_at_ms": 1,
            "primary_asset": None,
            "has_binary_event_leg": False,
        }

        decoded = api.FeedEventWithLegsResponse.from_dict(payload)

        self.assertEqual(decoded.legs, [])
        self.assertIsNone(decoded.primary_asset)
        self.assertFalse(decoded.has_binary_event_leg)
        self.assertNotIn("legs", decoded.to_dict())

    def test_required_api_fields_reject_missing_and_null_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "order"):
            api.CreateRfqRequest().to_dict()
        with self.assertRaisesRegex(ValueError, "order"):
            api.CreateRfqRequest.from_dict({})
        with self.assertRaisesRegex(ValueError, "use_app_tokens"):
            api.CreateRfqRequest(
                order=api.SignedOrderJson(
                    user="0x1111111111111111111111111111111111111111",
                    wager_micros=100_000_000,
                    min_odds=2.5,
                    legs=[api.OrderLegJson(market_id=42, direction="up")],
                    nonce=123,
                    expires_at_ms=1_735_430_300_000,
                    shield_on=False,
                    signature="signature",
                )
            ).to_dict()
        with self.assertRaisesRegex(ValueError, "user"):
            api.SignedOrderJson().to_dict()
        with self.assertRaisesRegex(ValueError, "user"):
            api.SignedOrderJson.from_dict({"user": None})

    def test_rfq_min_odds_rounds_half_bps_like_rust(self) -> None:
        signed = api.SignedOrderJson.from_dict(
            {
                "user": "0x1111111111111111111111111111111111111111",
                "wager_micros": 100_000_000,
                "min_odds": 2.00005,
                "legs": [{"market_id": 42, "direction": "up"}],
                "nonce": 123,
                "expires_at_ms": 456,
                "shield_on": False,
                "signature": b64encode(bytes(65)).decode("ascii"),
            }
        ).to_signed_order()
        unsigned = api.UnsignedRfqOrderRequest.from_dict(
            {
                "wager_micros": 100_000_000,
                "min_odds": 2.00005,
                "legs": [{"market_id": 42, "direction": "up"}],
                "shield_on": False,
                "idempotency_key": "00112233-4455-6677-8899-aabbccddeeff",
            }
        ).into_signed_order_for_session(Address.ZERO, nonce=123, expires_at_ms=456)

        self.assertEqual(signed.min_odds_bps, 20_001)
        self.assertEqual(unsigned.min_odds_bps, 20_001)

    def test_withdrawal_authorization_is_tagged_and_operation_responses_are_untagged(self) -> None:
        withdraw_params = {
            "amount_micros": 1_000_000,
            "destination_address": None,
            "idempotency_key": "00112233-4455-6677-8899-aabbccddeeff",
        }

        privy = api.UserWithdrawRequest.from_dict(
            {
                "withdraw_params": withdraw_params,
                "authorization": {"type": "privy_token", "token": "token"},
            }
        )
        self.assertEqual(privy.authorization.variant, "PrivyToken")
        self.assertEqual(privy.authorization.payload, {"token": "token"})
        self.assertIsInstance(privy.withdraw_params, api.UserWithdrawParams)
        self.assertEqual(privy.withdraw_params.to_dict(), withdraw_params)
        self.assertEqual(
            privy.to_dict(),
            {
                "withdraw_params": withdraw_params,
                "authorization": {"type": "privy_token", "token": "token"},
            },
        )

        wallet_authorized = api.UserWithdrawRequest.from_dict(
            {
                "withdraw_params": withdraw_params,
                "authorization": {
                    "type": "wallet_signature",
                    "signature": "base64-signature",
                    "signed_at_ms": 1_785_529_737_000,
                },
            }
        )
        self.assertEqual(wallet_authorized.authorization.variant, "WalletSignature")
        self.assertEqual(
            wallet_authorized.authorization.payload,
            {
                "signature": "base64-signature",
                "signed_at_ms": 1_785_529_737_000,
            },
        )
        self.assertIsInstance(wallet_authorized.withdraw_params, api.UserWithdrawParams)
        self.assertEqual(wallet_authorized.withdraw_params.to_dict(), withdraw_params)
        self.assertEqual(
            wallet_authorized.to_dict(),
            {
                "withdraw_params": withdraw_params,
                "authorization": {
                    "type": "wallet_signature",
                    "signature": "base64-signature",
                    "signed_at_ms": 1_785_529_737_000,
                },
            },
        )

        completed = api.DepositOperationResponse.from_dict(
            {
                "amount_micros": "1000000",
                "operation_id": "00112233-4455-6677-8899-aabbccddeeff",
                "tx_hash": "0xabc",
            }
        )
        status = api.DepositOperationResponse.from_dict(
            {
                "amount_micros": "1000000",
                "operation_id": "00112233-4455-6677-8899-aabbccddeeff",
                "status": "pending",
            }
        )

        self.assertEqual(completed.variant, "Completed")
        self.assertIsInstance(completed.payload, api.UserDepositResponse)
        self.assertEqual(status.variant, "OperationStatus")
        self.assertIsInstance(status.payload, api.BalanceOperationStatusResponse)

    def test_wallet_withdrawal_authorization_helpers_are_canonical(self) -> None:
        authentication_message = api.build_wallet_authentication_message(
            "longshot.xyz",
            "0x52908400098527886e0f7030069857d2e4169ee7",
            1_735_430_000_000,
        )
        self.assertEqual(
            authentication_message,
            "Longshot Wallet Authentication\n\nVersion: 1\nDomain: longshot.xyz\nAuth Address: 0x52908400098527886E0F7030069857D2E4169EE7\nTimestamp: 1735430000000",
        )

        message = api.build_wallet_withdrawal_authorization_message(
            "longshot.xyz",
            8453,
            "0x52908400098527886e0f7030069857d2e4169ee7",
            "0xde709f2102306220921060314715629080e2fb77",
            1_000_000,
            "550E8400-E29B-41D4-A716-446655440000",
            1_785_529_737_000,
        )
        self.assertEqual(
            message,
            "Longshot Withdrawal Authorization\n\nVersion: 1\nDomain: longshot.xyz\nChain ID: 8453\nAuth Address: 0x52908400098527886E0F7030069857D2E4169EE7\nDestination Address: 0xde709f2102306220921060314715629080e2fb77\nAmount Micros: 1000000\nIdempotency Key: 550e8400-e29b-41d4-a716-446655440000\nTimestamp: 1785529737000",
        )
        self.assertEqual(
            api.encode_wallet_signature(bytes([7]) * 65),
            "BwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwc=",
        )
        with self.assertRaisesRegex(ValueError, "65 bytes"):
            api.encode_wallet_signature(bytes(64))

    def test_deny_unknown_models_reject_extra_wire_fields(self) -> None:
        with self.assertRaises(ValueError):
            api.FeedRawQuery.from_dict({"limit": 10, "unexpected": True})

    def test_share_card_snapshot_helpers_match_rust_validation(self) -> None:
        snapshot = ShareCardSnapshot.price(
            PriceShareCard(
                contest_id="00112233-4455-6677-8899-aabbccddeeff",
                entry_index=0,
                state="live",
                question="BTC?",
                prediction=100.0,
                current_price=101.0,
                chart_prices=[100.0, 101.0],
                footer=ShareCardFooter(handle="alice"),
                summary=[ShareStat(value="2.5x", label="Odds")],
            )
        )

        self.assertEqual(snapshot.type_str(), "price")
        self.assertIsNone(snapshot.validate())

        invalid = ShareCardSnapshot.price(
            PriceShareCard(
                contest_id="not-a-uuid",
                entry_index=0,
                state="live",
                question="BTC?",
                prediction=100.0,
                current_price=101.0,
                chart_prices=[100.0],
                footer=ShareCardFooter(handle="alice"),
            )
        )
        with self.assertRaises(ValueError) as error:
            invalid.validate()
        self.assertEqual(error.exception.args[0], "contest_id")

        survivor = ShareCardSnapshot.from_dict(
            {
                "type": "survivor",
                "contest_id": "00112233-4455-6677-8899-aabbccddeeff",
                "entry_index": 0,
                "footer": {"handle": "alice"},
            }
        )
        self.assertEqual(survivor.type_str(), "survivor")
        self.assertEqual(survivor.payload.rounds, [])
        self.assertIsNone(survivor.validate())

        survivor.payload.rounds = [
            api.SurvivorShareRound(
                result=api.SurvivorEntryRoundResultResponse.Pending,
                pick_count=api.MAX_SURVIVOR_SHARE_PICKS + 1,
            )
        ]
        with self.assertRaisesRegex(ValueError, "rounds.pick_count"):
            survivor.validate()

    def test_flattened_models_emit_rust_wire_shape(self) -> None:
        summary = api.PublicContestSummaryResponse(
            contest_id="contest-1",
            category="mentions",
            status="open",
            game_type="lineups",
            survivor_current_game_index=0,
            title="Contest",
            bet_amount_micros=1,
            protocol_prize_pool_micros=3,
            total_pot_micros=4,
            entries_filled=5,
            entry_cap=6,
            entry_opens_at_ms=7,
            betting_closes_ms=8,
            live_ends_at_ms=None,
            resolved_at_ms=None,
            created_at_ms=9,
            image_url=None,
        )
        wrapped = api.CallerContestSummaryResponse(summary, caller=None)

        encoded = wrapped.to_dict()

        self.assertIn("contest_id", encoded)
        self.assertEqual(encoded["survivor_current_game_index"], 0)
        self.assertNotIn("contest", encoded)
        self.assertEqual(api.CallerContestSummaryResponse.from_dict(encoded).to_dict(), encoded)

        legacy_lobby = api.ContestLobbySummaryResponse.from_dict(
            {
                **encoded,
                "caller": {"joined": True},
                "protocol_prize_pool_pays_app_tokens": False,
            }
        )
        self.assertIsNone(legacy_lobby.description)
        self.assertEqual(legacy_lobby.max_entries_per_player, 1)
        self.assertEqual(legacy_lobby.summary.caller.entry_count, 0)

    def test_pool_image_raw_bytes_matches_rust_binary_wrapper(self) -> None:
        raw = api.PoolImageRawBytes(bytearray(b"image-bytes"))

        self.assertEqual(raw.as_bytes(), b"image-bytes")
        self.assertEqual(bytes(raw), b"image-bytes")
        self.assertFalse(isinstance(raw, LongshotModel))


class WsParityTests(unittest.TestCase):
    def test_client_message_shapes_match_rust_tags(self) -> None:
        self.assertEqual(ClientMessage.auth().to_dict(), {"type": "auth"})
        self.assertEqual(
            ClientMessage.auth_response("0xabc", "sig").to_dict(),
            {"type": "auth_response", "wallet_address": "0xabc", "signature": "sig"},
        )
        self.assertEqual(
            ClientMessage.quote_decline(
                RequestId(UUID("00112233-4455-6677-8899-aabbccddeeff")),
                QuoteDeclineReason.SportsCombinationUnsupported,
            ).to_dict(),
            {
                "type": "quote_decline",
                "request_id": "00112233-4455-6677-8899-aabbccddeeff",
                "reason": "sports_combination_unsupported",
            },
        )
        self.assertEqual(ClientMessage.pong().to_dict(), {"type": "pong"})

    def test_subscription_content_field_matches_rust_shape(self) -> None:
        self.assertEqual(RfqSubscription.all().to_dict(), {"type": "all"})
        self.assertEqual(
            RfqSubscription.binary_event().to_dict(), {"type": "binary_event"}
        )
        self.assertEqual(
            RfqSubscription.price_strike(Asset.BTC).to_dict(),
            {"type": "price_strike", "asset": "BTC"},
        )
        self.assertEqual(
            ClientMessage.subscribe(
                2,
                [
                    RfqSubscription.all(),
                    RfqSubscription.binary_event(),
                    RfqSubscription.price_strike(Asset.BTC),
                ]
            ).to_dict(),
            {
                "type": "subscribe",
                "protocol_version": 2,
                "subscriptions": [
                    {"type": "all"},
                    {"type": "binary_event"},
                    {"type": "price_strike", "asset": "BTC"},
                ],
            },
        )

    def test_server_message_shapes_match_rust_tags(self) -> None:
        self.assertEqual(ServerMessage.ping(123).to_dict(), {"type": "ping", "timestamp": 123})
        self.assertEqual(
            ServerMessage.quote_result(
                request_id="r",
                quote_id="q",
                client_quote_id=None,
                status=QuoteResultStatus.Filled,
                position_id="p",
                fill_amount="100",
                fill_odds=25000,
                filled_at_ms=123,
            ).to_dict(),
            {
                "type": "quote_result",
                "request_id": "r",
                "quote_id": "q",
                "client_quote_id": None,
                "status": "filled",
                "position_id": "p",
                "fill_amount": "100",
                "fill_odds": 25000,
                "filled_at_ms": 123,
                "reason": None,
            },
        )

    def test_ws_tagged_fields_validate_required_types_and_bounds(self) -> None:
        auth = ServerMessage.from_dict({"type": "auth_result", "success": False})
        self.assertIs(auth.payload["success"], False)
        self.assertEqual(auth.payload["error"], None)
        for payload in (
            {"type": "auth_result"},
            {"type": "auth_result", "success": "false"},
            {"type": "ping", "timestamp": -1},
            {"type": "ping", "timestamp": 1 << 64},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                ServerMessage.from_dict(payload)

        maximum = ServerMessage.from_dict(
            {"type": "ping", "timestamp": (1 << 64) - 1, "ignored": True}
        )
        self.assertEqual(
            maximum.to_dict(), {"type": "ping", "timestamp": (1 << 64) - 1}
        )
        quote = ServerMessage.from_dict(
            {"type": "quote_result", "request_id": "r", "quote_id": "q", "status": "filled"}
        )
        self.assertIs(quote.payload["status"], QuoteResultStatus.Filled)
        subscription = ClientMessage.from_dict(
            {
                "type": "subscribe",
                "protocol_version": 2,
                "subscriptions": [{"type": "price_strike", "asset": "BTC"}],
            }
        )
        self.assertIs(subscription.payload["subscriptions"][0].payload, Asset.BTC)
        decline = ClientMessage.from_dict(
            {
                "type": "quote_decline",
                "request_id": "00112233-4455-6677-8899-aabbccddeeff",
                "reason": "sports_combination_unsupported",
            }
        )
        self.assertEqual(
            decline.payload["request_id"],
            RequestId(UUID("00112233-4455-6677-8899-aabbccddeeff")),
        )
        self.assertIs(
            decline.payload["reason"],
            QuoteDeclineReason.SportsCombinationUnsupported,
        )


if __name__ == "__main__":
    unittest.main()
