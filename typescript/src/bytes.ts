export type BytesLike = Uint8Array | ArrayBuffer | string | number[];

export const U64_MAX = (1n << 64n) - 1n;
export const U32_MAX = (1n << 32n) - 1n;
export const U8_MAX = 0xffn;

export function checkU8(value: number | bigint, name: string): number {
  // Untyped JavaScript callers can bypass this signature. Keep byte-sized wire
  // fields strict so strings and booleans cannot become different enum values.
  if (typeof value !== "number" && typeof value !== "bigint") {
    throw new RangeError(`${name} must be an unsigned integer`);
  }
  const checked = checkUnsigned(value, U8_MAX, name);
  return Number(checked);
}

export function checkU32(value: number | bigint, name: string): number {
  const checked = checkUnsigned(value, U32_MAX, name);
  return Number(checked);
}

export function checkU64(value: number | bigint | string, name: string): bigint {
  return checkUnsigned(value, U64_MAX, name);
}

function checkUnsigned(value: number | bigint | string, max: bigint, name: string): bigint {
  const bigintValue = toBigInt(value, name);
  if (bigintValue < 0n || bigintValue > max) {
    throw new RangeError(`${name} must fit in u${max === U8_MAX ? 8 : max === U32_MAX ? 32 : 64}`);
  }
  return bigintValue;
}

export function toBigInt(value: number | bigint | string, name = "value"): bigint {
  if (typeof value === "bigint") {
    return value;
  }
  if (typeof value === "string") {
    if (!/^[0-9]+$/.test(value)) {
      throw new RangeError(`${name} must be an unsigned integer`);
    }
    return BigInt(value);
  }
  if (!Number.isInteger(value) || value < 0) {
    throw new RangeError(`${name} must be an unsigned integer`);
  }
  if (!Number.isSafeInteger(value)) {
    throw new RangeError(`${name} must be a safe integer or bigint`);
  }
  return BigInt(value);
}

export function toSafeNumber(value: bigint, name = "value"): number {
  if (value > BigInt(Number.MAX_SAFE_INTEGER)) {
    throw new RangeError(`${name} exceeds Number.MAX_SAFE_INTEGER`);
  }
  return Number(value);
}

export function bytesFrom(value: BytesLike, expectedLength?: number, name = "bytes"): Uint8Array {
  let bytes: Uint8Array;
  if (typeof value === "string") {
    bytes = hexToBytes(value);
  } else if (value instanceof ArrayBuffer) {
    bytes = new Uint8Array(value.slice(0));
  } else if (Array.isArray(value)) {
    for (const byte of value) {
      if (!Number.isInteger(byte) || byte < 0 || byte > 0xff) {
        throw new RangeError(`${name} must contain integers from 0 to 255`);
      }
    }
    bytes = Uint8Array.from(value);
  } else {
    bytes = new Uint8Array(value);
  }
  if (expectedLength !== undefined && bytes.length !== expectedLength) {
    throw new RangeError(`${name} must be ${expectedLength} bytes`);
  }
  return bytes;
}

export function hexToBytes(value: string): Uint8Array {
  const raw = value.startsWith("0x") ? value.slice(2) : value;
  if (raw.length % 2 !== 0 || !/^[0-9a-fA-F]*$/.test(raw)) {
    throw new Error("invalid hex string");
  }
  const bytes = new Uint8Array(raw.length / 2);
  for (let i = 0; i < bytes.length; i += 1) {
    bytes[i] = Number.parseInt(raw.slice(i * 2, i * 2 + 2), 16);
  }
  return bytes;
}

export function bytesToHex(bytes: Uint8Array, prefixed = false): string {
  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
  return prefixed ? `0x${hex}` : hex;
}

export function concatBytes(...chunks: Uint8Array[]): Uint8Array {
  const length = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const result = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.length;
  }
  return result;
}

export function writeU64Le(view: DataView, offset: number, value: number | bigint | string): void {
  view.setBigUint64(offset, checkU64(value, "u64"), true);
}

export function writeU32Le(view: DataView, offset: number, value: number | bigint): void {
  view.setUint32(offset, checkU32(value, "u32"), true);
}

export function readU64Le(view: DataView, offset: number): bigint {
  return view.getBigUint64(offset, true);
}

export function readU32Le(view: DataView, offset: number): number {
  return view.getUint32(offset, true);
}

export function u64LeBytes(value: number | bigint | string): Uint8Array {
  const bytes = new Uint8Array(8);
  writeU64Le(new DataView(bytes.buffer), 0, value);
  return bytes;
}

export function u32LeBytes(value: number | bigint): Uint8Array {
  const bytes = new Uint8Array(4);
  writeU32Le(new DataView(bytes.buffer), 0, value);
  return bytes;
}

const BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

export function encodeBase64NoPad(bytes: Uint8Array): string {
  return encodeBase64(bytes).replace(/=+$/u, "");
}

export function encodeBase64(bytes: Uint8Array): string {
  let encoded = "";
  for (let i = 0; i < bytes.length; i += 3) {
    const b0 = bytes[i] ?? 0;
    const b1 = bytes[i + 1] ?? 0;
    const b2 = bytes[i + 2] ?? 0;

    encoded += BASE64_ALPHABET[b0 >> 2];
    encoded += BASE64_ALPHABET[((b0 & 0x03) << 4) | (b1 >> 4)];
    encoded += i + 1 < bytes.length ? BASE64_ALPHABET[((b1 & 0x0f) << 2) | (b2 >> 6)] : "=";
    encoded += i + 2 < bytes.length ? BASE64_ALPHABET[b2 & 0x3f] : "=";
  }
  return encoded;
}

export function decodeBase64(data: string): Uint8Array {
  if (!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/u.test(data)) {
    throw new Error("invalid base64 payload");
  }
  const decoded = decodeBase64Padded(data);
  if (encodeBase64(decoded) !== data) throw new Error("invalid base64 payload");
  return decoded;
}

export function decodeBase64NoPad(data: string): Uint8Array {
  if (data.includes("=")) {
    throw new Error("invalid base64 payload: padding is not allowed");
  }
  if (!/^[A-Za-z0-9+/]*$/u.test(data)) {
    throw new Error("invalid base64 payload");
  }
  if (data.length % 4 === 1) {
    throw new Error("invalid base64 payload");
  }
  const paddingLength = (4 - (data.length % 4)) % 4;
  const decoded = decodeBase64Padded(`${data}${"=".repeat(paddingLength)}`);
  if (encodeBase64NoPad(decoded) !== data) throw new Error("invalid base64 payload");
  return decoded;
}

function decodeBase64Padded(data: string): Uint8Array {
  if (data.length % 4 !== 0) {
    throw new Error("invalid base64 payload");
  }

  let padding = 0;
  if (data.endsWith("==")) {
    padding = 2;
  } else if (data.endsWith("=")) {
    padding = 1;
  }
  const decoded = new Uint8Array((data.length / 4) * 3 - padding);
  let offset = 0;

  for (let i = 0; i < data.length; i += 4) {
    const c0 = decodeBase64Char(data[i]);
    const c1 = decodeBase64Char(data[i + 1]);
    const c2 = data[i + 2] === "=" ? 0 : decodeBase64Char(data[i + 2]);
    const c3 = data[i + 3] === "=" ? 0 : decodeBase64Char(data[i + 3]);
    const chunk = (c0 << 18) | (c1 << 12) | (c2 << 6) | c3;

    if (offset < decoded.length) decoded[offset++] = (chunk >> 16) & 0xff;
    if (offset < decoded.length) decoded[offset++] = (chunk >> 8) & 0xff;
    if (offset < decoded.length) decoded[offset++] = chunk & 0xff;
  }

  return decoded;
}

function decodeBase64Char(char: string): number {
  const value = BASE64_ALPHABET.indexOf(char);
  if (value === -1) {
    throw new Error("invalid base64 payload");
  }
  return value;
}
