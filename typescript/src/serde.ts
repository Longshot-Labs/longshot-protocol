import { API_SCHEMAS } from "./serde.generated.js";
import { Address, MarketId, PositionId } from "./types.js";
import { normalizeUuid } from "./uuid.js";

type Descriptor = string | unknown[];
type Field = [Descriptor, boolean, string?];
type ObjectDescriptor = ["o", Record<string, Field>, boolean];
type JsonMetadata =
  | { kind: "array"; items: JsonMetadata[] }
  | { kind: "object"; duplicates: Set<string>; fields: Map<string, JsonMetadata> }
  | undefined;

export class SerdeDecodeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SerdeDecodeError";
  }
}

export function decodeApiJson<T>(json: string, schema: string): T {
  const descriptor = API_SCHEMAS[schema] as Descriptor | undefined;
  if (descriptor === undefined) throw new SerdeDecodeError(`unknown API response schema ${schema}`);
  const [value, marker, metadata] = parseLosslessJson(json);
  return decode(descriptor, value, "$", marker, metadata) as T;
}

function parseLosslessJson(json: string): [unknown, string, JsonMetadata] {
  let parsed: unknown;
  try {
    parsed = JSON.parse(json) as unknown;
  } catch (error) {
    throw new SerdeDecodeError(`invalid JSON: ${(error as Error).message}`);
  }
  const canonical = JSON.stringify(parsed);
  let marker = "__longshot_raw_integer__";
  while (canonical.includes(marker)) marker += "_";
  return [
    JSON.parse(protectIntegers(json, marker)) as unknown,
    marker,
    scanJsonMetadata(json),
  ];
}

function scanJsonMetadata(json: string): JsonMetadata {
  // Syntax was validated by JSON.parse above; this lightweight second pass only
  // retains container structure and keys that JSON.parse would collapse.
  let index = 0;

  const skipWhitespace = (): void => {
    while (/\s/u.test(json[index] ?? "")) index += 1;
  };
  const scanString = (): string => {
    const start = index++;
    while (index < json.length) {
      if (json[index] === "\\") index += 2;
      else if (json[index++] === '"') break;
    }
    return JSON.parse(json.slice(start, index)) as string;
  };
  const scanValue = (): JsonMetadata => {
    skipWhitespace();
    if (json[index] === '"') {
      scanString();
      return undefined;
    }
    if (json[index] === "[") return scanArray();
    if (json[index] === "{") return scanObject();
    while (index < json.length && !/[\s,\]}]/u.test(json[index])) index += 1;
    return undefined;
  };
  const scanArray = (): JsonMetadata => {
    index += 1;
    const items: JsonMetadata[] = [];
    skipWhitespace();
    if (json[index] === "]") {
      index += 1;
      return { kind: "array", items };
    }
    while (index < json.length) {
      items.push(scanValue());
      skipWhitespace();
      if (json[index++] === "]") break;
    }
    return { kind: "array", items };
  };
  const scanObject = (): JsonMetadata => {
    index += 1;
    const duplicates = new Set<string>();
    const fields = new Map<string, JsonMetadata>();
    skipWhitespace();
    if (json[index] === "}") {
      index += 1;
      return { kind: "object", duplicates, fields };
    }
    while (index < json.length) {
      skipWhitespace();
      const key = scanString();
      skipWhitespace();
      index += 1;
      const metadata = scanValue();
      if (fields.has(key)) duplicates.add(key);
      fields.set(key, metadata);
      skipWhitespace();
      if (json[index++] === "}") break;
    }
    return { kind: "object", duplicates, fields };
  };

  return scanValue();
}

function protectIntegers(json: string, marker: string): string {
  let output = "";
  const numberPattern = /-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/uy;
  for (let index = 0; index < json.length;) {
    if (json[index] === '"') {
      const start = index++;
      while (index < json.length)
        if (json[index] === "\\") index += 2;
        else if (json[index++] === '"') break;
      output += json.slice(start, index);
      continue;
    }
    if (json[index] !== "-" && (json[index] < "0" || json[index] > "9")) {
      output += json[index++];
      continue;
    }
    numberPattern.lastIndex = index;
    const number = numberPattern.exec(json)?.[0];
    if (number !== undefined) {
      output += /[.eE]/u.test(number) ? number : `{"${marker}":"${number}"}`;
      index += number.length;
    } else output += json[index++];
  }
  return output;
}

function decode(descriptor: Descriptor, value: unknown, path: string, marker: string,
  metadata: JsonMetadata): unknown {
  if (typeof descriptor === "string") {
    if (descriptor === "s" || descriptor === "b" || descriptor === "z") {
      const valid = descriptor === "s" ? typeof value === "string"
        : descriptor === "b" ? typeof value === "boolean" : value === null;
      if (!valid) fail(path, descriptor === "s" ? "string" : descriptor === "b" ? "boolean" : "null");
      return value;
    }
    if (descriptor === "f") return decodeFloat(value, path, marker);
    if (descriptor === "j") return decodeJsonValue(value, path, marker);
    if (descriptor === "uuid") return decodeUuid(value, path);
    if (descriptor === "mid") return new MarketId(decodeInteger(value, "u64", path, marker));
    if (descriptor === "pid") return new PositionId(decodeUuid(value, path));
    if (descriptor === "addr") return decodeAddress(value, path);
    if (/^[ui](?:8|16|32|64|128)$|^[ui]size$/u.test(descriptor))
      return decodeInteger(value, descriptor, path, marker);
    throw new SerdeDecodeError(`${path}: unknown primitive descriptor ${descriptor}`);
  }

  const kind = descriptor[0];
  if (kind === "a") {
    if (!Array.isArray(value)) fail(path, "array");
    const items = metadata?.kind === "array" ? metadata.items : [];
    return value.map((item, index) =>
      decode(descriptor[1] as Descriptor, item, `${path}[${index}]`, marker, items[index]));
  }
  if (kind === "d") {
    if (!isRecord(value)) fail(path, "object");
    const fields = metadata?.kind === "object" ? metadata.fields : new Map();
    return Object.fromEntries(Object.entries(value)
      .map(([key, item]) => [
        key,
        decode(descriptor[1] as Descriptor, item, `${path}.${key}`, marker, fields.get(key)),
      ]));
  }
  if (kind === "n")
    return value === null ? null : decode(descriptor[1] as Descriptor, value, path, marker, metadata);
  if (kind === "r") {
    const name = descriptor[1] as string;
    const schema = API_SCHEMAS[name] as Descriptor | undefined;
    if (schema === undefined) throw new SerdeDecodeError(`${path}: unknown schema ${name}`);
    return decode(schema, value, path, marker, metadata);
  }
  if (kind === "o")
    return decodeObject(descriptor as ObjectDescriptor, value, path, marker, metadata);
  if (kind === "u") {
    for (const candidate of descriptor[1] as Descriptor[]) {
      try { return decode(candidate, value, path, marker, metadata); }
      catch (error) { if (!(error instanceof SerdeDecodeError)) throw error; }
    }
    throw new SerdeDecodeError(`${path}: no enum variant matched`);
  }
  if (kind === "v") {
    if (typeof value !== "string" || !(descriptor[1] as string[]).includes(value))
      fail(path, `one of ${(descriptor[1] as string[]).join(", ")}`);
    return value;
  }
  if (kind === "l") {
    if (value !== descriptor[1]) fail(path, JSON.stringify(descriptor[1]));
    return value;
  }
  if (kind === "m") {
    const tag = descriptor[1] as string;
    if (!isRecord(value) || value[tag] !== descriptor[2])
      fail(path, `${tag}=${JSON.stringify(descriptor[2])}`);
    const payload = decode(descriptor[3] as Descriptor, value, path, marker, metadata);
    if (!isRecord(payload)) fail(path, "object enum payload");
    return { [tag]: descriptor[2], ...payload };
  }
  if (kind === "w") return decodeWireInteger(descriptor[1] as Descriptor, value, path, marker);
  throw new SerdeDecodeError(`${path}: unknown descriptor ${String(kind)}`);
}

function decodeJsonValue(value: unknown, path: string, marker: string): unknown {
  const raw = rawInteger(value, marker);
  if (raw !== undefined) {
    const integer = BigInt(raw);
    if (raw === "-0") return -0;
    if (integer >= -(1n << 63n) && integer < 1n << 64n)
      return Number.isSafeInteger(Number(integer)) ? Number(integer) : integer;
    const number = Number(raw);
    if (!Number.isFinite(number)) fail(path, "finite JSON number");
    return number;
  }
  if (typeof value === "number" && !Number.isFinite(value)) fail(path, "finite JSON number");
  if (Array.isArray(value))
    return value.map((item, index) => decodeJsonValue(item, `${path}[${index}]`, marker));
  if (isRecord(value))
    return Object.fromEntries(Object.entries(value)
      .map(([key, item]) => [key, decodeJsonValue(item, `${path}.${key}`, marker)]));
  return value;
}

function decodeObject([_, fields, denyUnknown]: ObjectDescriptor, value: unknown, path: string,
  marker: string, metadata: JsonMetadata): Record<string, unknown> {
  if (!isRecord(value) || rawInteger(value, marker) !== undefined) fail(path, "object");
  const objectMetadata = metadata?.kind === "object" ? metadata : undefined;
  // JSON.parse is last-value-wins, but Rust structs reject a repeated declared
  // field. Retain that distinction without changing serde map/JSON semantics.
  const duplicate = [...(objectMetadata?.duplicates ?? [])]
    .find((key) => Object.hasOwn(fields, key));
  if (duplicate !== undefined)
    throw new SerdeDecodeError(`${path}: duplicate field ${duplicate}`);
  if (denyUnknown) {
    // Prototype names are not schema fields; Rust's deny_unknown_fields rejects
    // them just like any other undeclared key.
    const unknown = Object.keys(value).filter((key) => !Object.hasOwn(fields, key));
    if (unknown.length) throw new SerdeDecodeError(`${path}: unknown fields ${unknown.join(", ")}`);
  }
  const result: Record<string, unknown> = {};
  for (const [name, [type, required, flag]] of Object.entries(fields)) {
    if (flag === "f") result[name] = decode(type, value, `${path}.${name}`, marker, metadata);
    else if (Object.hasOwn(value, name))
      result[name] = decode(
        type,
        value[name],
        `${path}.${name}`,
        marker,
        objectMetadata?.fields.get(name),
      );
    else if (required) throw new SerdeDecodeError(`${path}: missing required field ${name}`);
    else if (flag?.startsWith("d")) {
      if (flag.length === 1)
        throw new SerdeDecodeError(`${path}: unresolved generated default for ${name}`);
      result[name] = JSON.parse(flag.slice(1)) as unknown;
    }
  }
  return result;
}

function decodeFloat(value: unknown, path: string, marker: string): number {
  const raw = rawInteger(value, marker);
  const number = raw === undefined ? value : Number(raw);
  if (typeof number !== "number" || !Number.isFinite(number)) fail(path, "finite number");
  return number;
}

function decodeInteger(value: unknown, kind: string, path: string, marker: string): number | bigint {
  const raw = rawInteger(value, marker);
  if (raw === undefined) fail(path, `${kind} JSON integer`);
  const parsed = checkedInteger(raw, kind, path);
  return Number.isSafeInteger(Number(parsed)) ? Number(parsed) : parsed;
}

function decodeWireInteger(descriptor: Descriptor, value: unknown, path: string,
  marker: string): string | number | null {
  if (Array.isArray(descriptor) && descriptor[0] === "n") {
    if (value === null) return null;
    descriptor = descriptor[1] as Descriptor;
  }
  if (typeof descriptor !== "string") fail(path, "generated wire integer");
  const raw = rawInteger(value, marker);
  const source = raw ?? (typeof value === "string" ? value : undefined);
  if (source === undefined) fail(path, `${descriptor} decimal string or JSON integer`);
  const parsed = checkedInteger(source, descriptor, path);
  return raw !== undefined && Number.isSafeInteger(Number(parsed)) ? Number(parsed) : parsed.toString();
}

function checkedInteger(source: string, kind: string, path: string): bigint {
  const match = kind.match(/^([ui])(\d+|size)$/u);
  if (!match || !/^[+-]?\d+$/u.test(source)) fail(path, `${kind} decimal integer`);
  const bits = match[2] === "size" ? 64 : Number(match[2]);
  const signed = match[1] === "i";
  if (!signed && source.startsWith("-")) fail(path, kind);
  const limit = 1n << BigInt(signed ? bits - 1 : bits);
  const parsed = BigInt(source);
  if (parsed < (signed ? -limit : 0n) || parsed >= limit) fail(path, kind);
  return parsed;
}

function rawInteger(value: unknown, marker: string): string | undefined {
  return isRecord(value) && Object.keys(value).length === 1 && typeof value[marker] === "string"
    ? value[marker] : undefined;
}

function decodeUuid(value: unknown, path: string): string {
  if (typeof value !== "string") fail(path, "UUID string");
  try {
    return normalizeUuid(value);
  } catch {
    return fail(path, "UUID string");
  }
}

function decodeAddress(value: unknown, path: string): Address {
  if (typeof value !== "string") fail(path, "EVM address");
  try {
    return Address.fromHex(value);
  } catch {
    return fail(path, "EVM address");
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function fail(path: string, expected: string): never {
  throw new SerdeDecodeError(`${path}: expected ${expected}`);
}
