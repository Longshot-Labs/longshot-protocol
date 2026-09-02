"""Shared model helpers for Rust serde-compatible Python DTOs."""

from __future__ import annotations

import sys
from copy import deepcopy
from dataclasses import fields, is_dataclass
from enum import Enum
from functools import lru_cache
from math import isfinite
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)
from uuid import UUID

T = TypeVar("T", bound="LongshotModel")
RustStringEnumT = TypeVar("RustStringEnumT", bound="RustStringEnum")
RustTaggedUnionT = TypeVar("RustTaggedUnionT", bound="RustTaggedUnion")
_MISSING = object()
_INTEGER_BOUNDS = {
    **{f"u{bits}": (0, (1 << bits) - 1) for bits in (8, 16, 32, 64, 128)},
    **{
        f"i{bits}": (-(1 << (bits - 1)), (1 << (bits - 1)) - 1)
        for bits in (8, 16, 32, 64, 128)
    },
    "usize": (0, (sys.maxsize << 1) + 1),
    "isize": (-sys.maxsize - 1, sys.maxsize),
}


@lru_cache(maxsize=None)
def _type_hints_for(cls: Type[Any]) -> Dict[str, Any]:
    try:
        return get_type_hints(cls)
    except (NameError, TypeError):
        return {}


def to_serde_value(value: Any) -> Any:
    if isinstance(value, LongshotModel):
        return value.to_dict()
    if isinstance(value, RustStringEnum):
        return value.value
    if isinstance(value, RustTaggedUnion):
        return value.to_dict()
    if hasattr(value, "serde_value") and callable(value.serde_value):
        return value.serde_value()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, list):
        return [to_serde_value(item) for item in value]
    if isinstance(value, tuple):
        return [to_serde_value(item) for item in value]
    if isinstance(value, dict):
        return {key: to_serde_value(item) for key, item in value.items()}
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    if (
        value.__class__.__name__ == "Address"
        and hasattr(value, "hex")
        and callable(value.hex)
    ):
        return value.hex()
    return value


def _sized_integer_to_serde(value: Any, integer_type: str) -> Any:
    if value is None:
        return None
    if integer_type.startswith("[]"):
        if not isinstance(value, list):
            raise _serde_type_error(value, integer_type)
        return [_sized_integer_to_serde(item, integer_type[2:]) for item in value]
    return _coerce_sized_integer(to_serde_value(value), integer_type)


class LongshotModel:
    """Base class for Python DTOs that mirror Rust serde structs."""

    __serde_renames__: ClassVar[Dict[str, str]] = {}
    __serde_skip_none__: ClassVar[Set[str]] = set()
    __serde_skip_empty__: ClassVar[Set[str]] = set()
    __serde_flatten__: ClassVar[Set[str]] = set()
    __serde_integer_types__: ClassVar[Dict[str, str]] = {}
    __serde_deserialize_string_ints__: ClassVar[Set[str]] = set()
    __serde_string_ints__: ClassVar[Set[str]] = set()
    __serde_required__: ClassVar[Set[str]] = set()
    __serde_required_nullable__: ClassVar[Set[str]] = set()
    __serde_deny_unknown__: ClassVar[bool] = False
    __serde_defaults__: ClassVar[Dict[str, Any]] = {}
    __serde_skip_non_finite__: ClassVar[Set[str]] = set()
    __serde_query_csv__: ClassVar[Set[str]] = set()
    __repr_redacted_fields__: ClassVar[Set[str]] = set()

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        if not isinstance(data, dict):
            raise ValueError(f"{cls.__name__} expects an object")
        type_hints = _type_hints_for(cls)
        integer_types = cls.__serde_integer_types__
        known_wire_names = {
            cls.__serde_renames__.get(field.name, field.name)
            for field in fields(cls)
            if field.name not in cls.__serde_flatten__
        }
        if cls.__serde_deny_unknown__:
            unknown = set(data) - known_wire_names
            if unknown:
                raise ValueError(f"unknown fields: {', '.join(sorted(unknown))}")
        non_flatten_wire_names = {
            cls.__serde_renames__.get(field.name, field.name)
            for field in fields(cls)
            if field.name not in cls.__serde_flatten__
        }
        kwargs = {}
        for field in fields(cls):
            if field.name in cls.__serde_flatten__:
                value = {
                    key: value
                    for key, value in data.items()
                    if key not in non_flatten_wire_names
                }
                kwargs[field.name] = _coerce_from_serde(value, type_hints.get(field.name))
                continue
            wire_name = cls.__serde_renames__.get(field.name, field.name)
            if wire_name in data:
                value = data[wire_name]
            elif not cls.__serde_deny_unknown__ and field.name in data:
                value = data[field.name]
            else:
                continue
            if field.name in cls.__serde_query_csv__ and value is not None:
                if type(value) is not str:
                    raise _serde_type_error(value, "comma-separated query string")
                # Match the Rust form adapter: whitespace and empty tokens are
                # ignored, and an empty CSV value deserializes as no filter.
                tokens = [token.strip() for token in value.split(",")]
                value = [token for token in tokens if token] or None
            if value is None and field.name in cls.__serde_defaults__:
                raise ValueError(f"{wire_name} cannot be null")
            integer_type = integer_types.get(field.name)
            if field.name in cls.__serde_deserialize_string_ints__ and value is not None:
                value = _coerce_wire_int(value, integer_type)
            value = _coerce_from_serde(value, type_hints.get(field.name))
            if integer_type:
                value = _coerce_sized_integer(value, integer_type)
            kwargs[field.name] = value
        for field_name, default in cls.__serde_defaults__.items():
            if field_name not in kwargs:
                kwargs[field_name] = deepcopy(default)
        missing_required = {
            cls.__serde_renames__.get(field_name, field_name)
            for field_name in cls.__serde_required__
            if kwargs.get(field_name) is None
        }
        # Serde's Option controls value nullability, while a custom deserializer
        # still requires the key unless the Rust field also declares a default.
        missing_required.update(
            cls.__serde_renames__.get(field_name, field_name)
            for field_name in cls.__serde_required_nullable__
            if field_name not in kwargs
        )
        if missing_required:
            raise ValueError(
                f"missing required fields: {', '.join(sorted(missing_required))}"
            )
        return cls(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        type_hints = _type_hints_for(type(self))
        integer_types = self.__serde_integer_types__
        for field in fields(self):
            value = getattr(self, field.name)
            if value is None and field.name in self.__serde_defaults__:
                value = deepcopy(self.__serde_defaults__[field.name])
            if value is None and field.name in self.__serde_required__:
                wire_name = self.__serde_renames__.get(field.name, field.name)
                raise ValueError(f"missing required field: {wire_name}")
            if value is None and field.name in self.__serde_skip_none__:
                continue
            if value == [] and field.name in self.__serde_skip_empty__:
                continue
            if field.name in self.__serde_skip_non_finite__:
                try:
                    if not isfinite(float(value)):
                        continue
                except (TypeError, ValueError):
                    continue
            integer_type = integer_types.get(field.name)
            if value is not None and not integer_type:
                value = _coerce_from_serde(value, type_hints.get(field.name))
            value = (
                _sized_integer_to_serde(value, integer_type)
                if integer_type
                else to_serde_value(value)
            )
            if field.name in self.__serde_query_csv__ and value is not None:
                if not isinstance(value, list) or any(
                    type(item) is not str for item in value
                ):
                    raise _serde_type_error(value, "list of query strings")
                value = ",".join(value)
            if field.name in self.__serde_flatten__:
                if not isinstance(value, dict):
                    raise ValueError(f"flattened field {field.name} must serialize to an object")
                result.update(value)
                continue
            if field.name in self.__serde_string_ints__ and value is not None:
                result[self.__serde_renames__.get(field.name, field.name)] = str(value)
                continue
            result[self.__serde_renames__.get(field.name, field.name)] = value
        return result

    def __repr__(self) -> str:
        rendered_fields = []
        for model_field in fields(self):
            value = getattr(self, model_field.name)
            if model_field.name in self.__repr_redacted_fields__ and value is not None:
                value = "<redacted>"
            rendered_fields.append(f"{model_field.name}={value!r}")
        return f"{type(self).__name__}({', '.join(rendered_fields)})"


class RustStringEnum(str, Enum):
    """String-valued enum matching Rust serde unit enum output."""

    @classmethod
    def from_json(cls: Type[RustStringEnumT], value: str) -> RustStringEnumT:
        return cls(value)

    def to_json(self) -> str:
        return self.value


class RustTaggedUnion:
    """Runtime representation for Rust serde tagged and untagged enums."""

    __serde_tag__: ClassVar[Optional[str]] = "type"
    __serde_content__: ClassVar[Optional[str]] = None
    __serde_untagged__: ClassVar[bool] = False
    __serde_variants__: ClassVar[Dict[str, str]] = {}
    __serde_untagged_payloads__: ClassVar[Dict[str, Type[Any]]] = {}
    __serde_untagged_required_fields__: ClassVar[Dict[str, Set[str]]] = {}
    __serde_variant_payloads__: ClassVar[Dict[str, Type[Any]]] = {}
    __serde_variant_integer_types__: ClassVar[Dict[str, Dict[str, str]]] = {}
    __serde_variant_string_ints__: ClassVar[Dict[str, Set[str]]] = {}
    __serde_variant_fields__: ClassVar[Dict[str, Dict[str, str]]] = {}
    __serde_variant_deny_unknown__: ClassVar[bool] = False
    __repr_redacted_fields__: ClassVar[Set[str]] = set()

    def __init__(self, variant: str, payload: Any = None, **fields: Any) -> None:
        if payload is not None and fields:
            raise ValueError("pass either payload or fields, not both")
        if variant not in self.__serde_variants__:
            raise ValueError(f"unknown {type(self).__name__} variant: {variant}")
        self.variant = variant
        if payload is not None:
            self.payload = payload
        elif fields:
            payload_type = self.__serde_variant_payloads__.get(variant)
            self.payload = payload_type(**fields) if payload_type is not None else fields
        else:
            self.payload = None

    @property
    def tag_value(self) -> str:
        return self.__serde_variants__[self.variant]

    @classmethod
    def from_dict(cls: Type[RustTaggedUnionT], data: Any) -> RustTaggedUnionT:
        if cls.__serde_untagged__:
            if not cls.__serde_untagged_required_fields__:
                return cls(next(iter(cls.__serde_variants__)), data)
            if not isinstance(data, dict):
                raise ValueError(f"{cls.__name__} expects an object")
            keys = set(data)
            for variant in cls.__serde_variants__:
                required = cls.__serde_untagged_required_fields__.get(variant, set())
                if required <= keys:
                    payload_type = cls.__serde_untagged_payloads__.get(variant)
                    payload = (
                        payload_type.from_dict(data)
                        if payload_type is not None
                        and hasattr(payload_type, "from_dict")
                        else data
                    )
                    return cls(variant, payload)
            raise ValueError(f"{cls.__name__} did not match any untagged variant")
        if not isinstance(data, dict):
            raise ValueError(f"{cls.__name__} expects an object")
        tag = cls.__serde_tag__
        if tag is None or tag not in data:
            raise ValueError(f"{cls.__name__} missing tag field")
        reverse = {wire: name for name, wire in cls.__serde_variants__.items()}
        try:
            variant = reverse[data[tag]]
        except (KeyError, TypeError) as error:
            raise ValueError(f"unknown {cls.__name__} variant: {data[tag]!r}") from error
        if cls.__serde_content__ is not None:
            payload = data.get(cls.__serde_content__, _MISSING)
        else:
            payload = {key: value for key, value in data.items() if key != tag}
        schema = cls.__serde_variant_fields__.get(variant)
        if schema is not None:
            if cls.__serde_content__ and cls.__serde_variant_deny_unknown__:
                unknown = set(data) - {tag, cls.__serde_content__}
                if unknown:
                    raise ValueError(f"unknown fields: {', '.join(sorted(unknown))}")
            payload = _coerce_tagged_payload(cls, variant, payload, from_wire=True)
            return cls(variant, payload)
        integer_types = cls.__serde_variant_integer_types__.get(variant, {})
        if isinstance(payload, dict):
            for field_name in cls.__serde_variant_string_ints__.get(variant, set()):
                if field_name in payload and payload[field_name] is not None:
                    payload[field_name] = _coerce_wire_int(
                        payload[field_name], integer_types.get(field_name)
                    )
        if "" in integer_types:
            payload = _coerce_sized_integer(payload, integer_types[""])
        elif isinstance(payload, dict):
            for field_name, integer_type in integer_types.items():
                if field_name in payload:
                    payload[field_name] = _coerce_sized_integer(
                        payload[field_name], integer_type
                    )
        payload_type = cls.__serde_variant_payloads__.get(variant)
        if payload_type is not None:
            payload = _coerce_from_serde(payload, payload_type)
        return cls(variant, payload)

    def to_dict(self) -> Any:
        payload = self.payload
        if self.variant in self.__serde_variant_fields__:
            payload = _coerce_tagged_payload(
                type(self), self.variant, payload, from_wire=False
            )
        payload = to_serde_value(payload)
        if self.__serde_untagged__:
            return payload
        if self.__serde_content__ is not None:
            result = {self.__serde_tag__: self.tag_value}
            if payload is not None:
                result[self.__serde_content__] = payload
            return result
        if payload is None:
            payload_dict: Dict[str, Any] = {}
        elif isinstance(payload, dict):
            payload_dict = payload
        else:
            payload_dict = to_serde_value(payload)
            if not isinstance(payload_dict, dict):
                payload_dict = {"value": payload_dict}
        for field_name in self.__serde_variant_string_ints__.get(self.variant, set()):
            if field_name in payload_dict and payload_dict[field_name] is not None:
                payload_dict[field_name] = str(payload_dict[field_name])
        return {self.__serde_tag__: self.tag_value, **payload_dict}

    def __repr__(self) -> str:
        payload = self.payload
        if isinstance(payload, dict):
            payload = {
                key: "<redacted>"
                if key in self.__repr_redacted_fields__ and value is not None
                else value
                for key, value in payload.items()
            }
        return f"{type(self).__name__}({self.variant!r}, {payload!r})"


def is_model_instance(value: Any) -> bool:
    return is_dataclass(value) and isinstance(value, LongshotModel)


def _serde_type_error(value: Any, target_type: Any) -> ValueError:
    return ValueError(f"expected {target_type!r}, got {type(value).__name__}")


def _coerce_wire_int(value: Any, integer_type: Optional[str] = None) -> int:
    if type(value) is int:
        return value
    if isinstance(value, str) and value:
        digits = value[1:] if value[0] in "+-" else value
        unsigned_negative = integer_type and integer_type.startswith("u") and value[0] == "-"
        if not unsigned_negative and digits.isascii() and digits.isdigit():
            return int(value)
    raise _serde_type_error(value, int)


def _coerce_wire_bytes(value: Any, target_type: Any) -> bytes:
    if not isinstance(value, list) or any(
        type(item) is not int or not 0 <= item <= 0xFF for item in value
    ):
        raise _serde_type_error(value, target_type)
    return bytes(value)


def _coerce_sized_integer(value: Any, integer_type: str) -> Any:
    if value is None:
        return None
    if integer_type.startswith("[]"):
        if not isinstance(value, list):
            raise _serde_type_error(value, integer_type)
        return [_coerce_sized_integer(item, integer_type[2:]) for item in value]
    if type(value) is not int:
        raise _serde_type_error(value, integer_type)
    minimum, maximum = _INTEGER_BOUNDS[integer_type]
    if not minimum <= value <= maximum:
        raise ValueError(f"{value} must fit in {integer_type}")
    return value


def _install_serde_metadata(
    namespace: Dict[str, Any],
    struct_fields: Dict[str, str],
    required_fields: Dict[str, str],
    tagged_union_fields: Dict[str, str],
    deny_unknown_tagged_unions: Set[str],
    required_nullable_fields: Optional[Dict[str, str]] = None,
) -> None:
    for class_name, encoded in struct_fields.items():
        if class_name not in namespace:
            continue
        fields = {}
        deserialize_string_ints = set()
        string_ints = set()
        for group in encoded.split(";"):
            integer_type, names = group.split(":", 1)
            # `#` mirrors serde(with) in both directions; `~` is deserialize-only.
            if integer_type.startswith("#"):
                integer_type = integer_type[1:]
                deserialize_string_ints.update(names.split(","))
                string_ints.update(names.split(","))
            elif integer_type.startswith("~"):
                integer_type = integer_type[1:]
                deserialize_string_ints.update(names.split(","))
            fields.update((name, integer_type) for name in names.split(","))
        namespace[class_name].__serde_integer_types__ = fields
        namespace[class_name].__serde_deserialize_string_ints__ = (
            deserialize_string_ints
        )
        namespace[class_name].__serde_string_ints__ = string_ints
    for class_name, encoded in required_fields.items():
        if class_name in namespace:
            namespace[class_name].__serde_required__ = set(encoded.split(","))
    for class_name, encoded in (required_nullable_fields or {}).items():
        if class_name in namespace:
            namespace[class_name].__serde_required_nullable__ = set(encoded.split(","))
    for class_name, encoded in tagged_union_fields.items():
        if class_name not in namespace:
            continue
        schemas: Dict[str, Dict[str, str]] = {}
        variants: Dict[str, Dict[str, str]] = {}
        string_ints: Dict[str, Set[str]] = {}
        for group in encoded.split(";"):
            variant, body = group.split("=", 1)
            if body.startswith("$"):
                fields = {"": body[1:]}
            elif body:
                fields = dict(field.split(":", 1) for field in body.split(","))
            else:
                fields = {}
            schemas[variant] = fields
            for field_name, spec in fields.items():
                integer_type = _integer_type_from_spec(spec)
                if integer_type:
                    variants.setdefault(variant, {})[field_name] = integer_type
                if spec.lstrip("?=").startswith("#"):
                    string_ints.setdefault(variant, set()).add(
                        field_name.partition(">")[2] or field_name
                    )
        namespace[class_name].__serde_variant_fields__ = schemas
        namespace[class_name].__serde_variant_integer_types__ = variants
        namespace[class_name].__serde_variant_string_ints__ = string_ints
        namespace[class_name].__serde_variant_deny_unknown__ = (
            class_name in deny_unknown_tagged_unions
        )


def _integer_type_from_spec(spec: str) -> Optional[str]:
    core = spec.lstrip("?=")
    if core.startswith(("#", "~")):
        core = core[1:]
    prefix = ""
    while core.startswith("[]"):
        prefix += "[]"
        core = core[2:]
    return prefix + core if core in _INTEGER_BOUNDS else None


def _coerce_serde_spec(
    owner: Type[RustTaggedUnion], value: Any, spec: str, from_wire: bool
) -> Any:
    core = spec.lstrip("?=")
    optional = "?" in spec[: len(spec) - len(core)]
    if value is None and optional:
        return None
    wire_int = core.startswith(("#", "~"))
    if wire_int:
        core = core[1:]
    if core.startswith("[]"):
        if not isinstance(value, list):
            raise _serde_type_error(value, list)
        return [
            _coerce_serde_spec(owner, item, core[2:], from_wire)
            for item in value
        ]
    if core.startswith("{}"):
        if not isinstance(value, dict) or any(type(key) is not str for key in value):
            raise _serde_type_error(value, dict)
        return {
            key: _coerce_serde_spec(owner, item, core[2:], from_wire)
            for key, item in value.items()
        }
    if core in _INTEGER_BOUNDS:
        value = _coerce_wire_int(value, core) if wire_int and from_wire else value
        return _coerce_sized_integer(value, core)
    if core == "unit":
        if value is not None:
            raise _serde_type_error(value, type(None))
        return None
    target_type = {
        "str": str,
        "bool": bool,
        "float": float,
        "uuid": UUID,
    }.get(core)
    if core.startswith("@"):
        target_type = vars(sys.modules[owner.__module__]).get(core[1:])
        if target_type is None:
            raise ValueError(f"unknown serde payload type: {core[1:]}")
        if value is None and is_dataclass(target_type) and not fields(target_type):
            value = {}
    if target_type is None:
        raise ValueError(f"unknown serde field spec: {spec}")
    return _coerce_from_serde(value, target_type)


def _default_serde_spec(owner: Type[RustTaggedUnion], spec: str) -> Any:
    core = spec.lstrip("?=")
    if "?" in spec[: len(spec) - len(core)]:
        return None
    if core.startswith(("#", "~")):
        core = core[1:]
    if core.startswith("[]"):
        return []
    if core.startswith("{}"):
        return {}
    defaults = {"str": "", "bool": False, "float": 0.0}
    if core in defaults:
        return defaults[core]
    if core in _INTEGER_BOUNDS:
        return 0
    if core.startswith("@"):
        target_type = vars(sys.modules[owner.__module__]).get(core[1:])
        if target_type is not None:
            return target_type()
    raise ValueError(f"unsupported serde default: {spec}")


def _coerce_tagged_payload(
    owner: Type[RustTaggedUnion], variant: str, payload: Any, from_wire: bool
) -> Any:
    schema = owner.__serde_variant_fields__[variant]
    if not schema:
        return None
    if "" in schema:
        if payload is _MISSING:
            raise ValueError(f"missing required field: {owner.__serde_content__ or 'payload'}")
        return _coerce_serde_spec(owner, payload, schema[""], from_wire)
    if not isinstance(payload, dict):
        raise ValueError(f"{owner.__name__}.{variant} expects an object")

    field_names = {
        name.partition(">")[2] or name
        for name in schema
    }
    accepted_names = field_names | (
        {name.partition(">")[0] for name in schema} if not from_wire else set()
    )
    unknown = set(payload) - accepted_names
    if unknown and owner.__serde_variant_deny_unknown__:
        raise ValueError(f"unknown fields: {', '.join(sorted(unknown))}")

    result = {}
    missing = []
    for name, spec in schema.items():
        local, separator, wire = name.partition(">")
        wire = wire if separator else local
        source = wire if wire in payload else local if not from_wire and local in payload else None
        if source is None:
            flags = spec[: len(spec) - len(spec.lstrip("?="))]
            if "?" not in flags and "=" not in flags:
                missing.append(wire)
                continue
            value = _default_serde_spec(owner, spec)
        else:
            value = payload[source]
        result[wire] = _coerce_serde_spec(owner, value, spec, from_wire)
    if missing:
        raise ValueError(f"missing required fields: {', '.join(sorted(missing))}")
    return result


def _coerce_from_serde(value: Any, target_type: Any) -> Any:
    if target_type is Any:
        return _coerce_json_value(value)
    if target_type is None:
        return value
    origin = get_origin(target_type)
    args = get_args(target_type)
    if origin is Union:
        if value is None and type(None) in args:
            return None
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return _coerce_from_serde(value, non_none_args[0])
        for candidate in non_none_args:
            try:
                return _coerce_from_serde(value, candidate)
            except (TypeError, ValueError, OverflowError):
                continue
        raise _serde_type_error(value, target_type)
    if value is None:
        raise _serde_type_error(value, target_type)
    if origin in (list, List):
        if not isinstance(value, list):
            raise _serde_type_error(value, target_type)
        return (
            [_coerce_from_serde(item, args[0]) for item in value]
            if args
            else value
        )
    if origin in (dict, Dict):
        if not isinstance(value, dict):
            raise _serde_type_error(value, target_type)
        if len(args) != 2:
            return value
        return {
            _coerce_from_serde(key, args[0]): _coerce_from_serde(item, args[1])
            for key, item in value.items()
        }
    if origin is tuple:
        if not isinstance(value, list):
            raise _serde_type_error(value, target_type)
        if not args:
            return tuple(value)
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_coerce_from_serde(item, args[0]) for item in value)
        if len(value) != len(args):
            raise _serde_type_error(value, target_type)
        return tuple(
            _coerce_from_serde(item, item_type)
            for item, item_type in zip(value, args)
        )
    if target_type in (bool, int, str):
        if type(value) is not target_type:
            raise _serde_type_error(value, target_type)
        return value
    if target_type is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise _serde_type_error(value, target_type)
        try:
            coerced = float(value)
        except OverflowError as error:
            raise _serde_type_error(value, target_type) from error
        if not isfinite(coerced):
            raise _serde_type_error(value, target_type)
        return coerced
    if target_type in (bytes, bytearray):
        return target_type(_coerce_wire_bytes(value, target_type))
    if isinstance(target_type, type):
        if isinstance(value, target_type):
            return value
        if issubclass(target_type, LongshotModel):
            if isinstance(value, dict):
                return target_type.from_dict(value)
            raise _serde_type_error(value, target_type)
        if issubclass(target_type, RustTaggedUnion):
            return target_type.from_dict(value)
        if issubclass(target_type, RustStringEnum):
            return target_type.from_json(value)
        if issubclass(target_type, str):
            if type(value) is not str:
                raise _serde_type_error(value, target_type)
            return target_type(value)
        if issubclass(target_type, Enum):
            try:
                return target_type(value)
            except ValueError:
                for member in target_type:
                    if to_serde_value(member) == value:
                        return member
                raise
        if target_type is UUID:
            if not isinstance(value, str):
                raise _serde_type_error(value, target_type)
            return UUID(value)
        if hasattr(target_type, "from_evm"):
            return target_type.from_evm(
                value
                if isinstance(value, str)
                else _coerce_wire_bytes(value, target_type)
            )
        if hasattr(target_type, "from_uuid") and isinstance(value, UUID):
            return target_type.from_uuid(value)
        if hasattr(target_type, "from_string"):
            if not isinstance(value, str):
                raise _serde_type_error(value, target_type)
            return target_type.from_string(value)
        if hasattr(target_type, "from_bytes"):
            if not isinstance(value, (bytes, bytearray)):
                raise _serde_type_error(value, target_type)
            return target_type.from_bytes(bytes(value))
        if is_dataclass(target_type) and len(fields(target_type)) == 1:
            field = fields(target_type)[0]
            field_type = _type_hints_for(target_type).get(field.name, field.type)
            return target_type(_coerce_from_serde(value, field_type))
    return value


def _coerce_json_value(value: Any) -> Any:
    if value is None or type(value) in (bool, str):
        return value
    if type(value) is int:
        if -(1 << 63) <= value < 1 << 64:
            return value
        try:
            value = float(value)
        except OverflowError as error:
            raise _serde_type_error(value, "finite JSON number") from error
    if type(value) is float:
        if not isfinite(value):
            raise _serde_type_error(value, "finite JSON number")
        return value
    if isinstance(value, list):
        return [_coerce_json_value(item) for item in value]
    if isinstance(value, dict) and all(type(key) is str for key in value):
        return {key: _coerce_json_value(item) for key, item in value.items()}
    raise _serde_type_error(value, "JSON value")
