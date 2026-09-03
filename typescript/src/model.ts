export type JsonValue =
  | null
  | boolean
  | number
  | string
  | JsonValue[]
  | { [key: string]: JsonValue };

export interface SerdeSerializable {
  serdeValue(): unknown;
}

export function isSerdeSerializable(value: unknown): value is SerdeSerializable {
  return (
    typeof value === "object" &&
    value !== null &&
    "serdeValue" in value &&
    typeof (value as { serdeValue?: unknown }).serdeValue === "function"
  );
}

export function toSerdeValue(value: unknown): unknown {
  return normalizeSerdeValue(value, false);
}

function normalizeSerdeValue(value: unknown, preserveBigInt: boolean): unknown {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  if (isSerdeSerializable(value)) {
    return normalizeSerdeValue(value.serdeValue(), preserveBigInt);
  }
  if (typeof value === "bigint") {
    return preserveBigInt ? value : value.toString();
  }
  if (value instanceof Uint8Array) {
    return Array.from(value);
  }
  if (Array.isArray(value)) {
    return value.map((item) => normalizeSerdeValue(item, preserveBigInt));
  }
  if (typeof value === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value)) {
      if (item !== undefined) {
        result[key] = normalizeSerdeValue(item, preserveBigInt);
      }
    }
    return result;
  }
  return value;
}

export function stringifySerde(value: unknown): string {
  const serde = normalizeSerdeValue(value, true);
  let marker = "__longshot_raw_bigint__";
  const probe = JSON.stringify(serde, (_key, item) =>
    typeof item === "bigint" ? item.toString() : item
  );
  if (probe === undefined) throw new TypeError("value cannot be serialized as JSON");
  while (probe.includes(marker)) marker += "_";
  return JSON.stringify(serde, (_key, item) =>
    typeof item === "bigint" ? `${marker}${item}` : item
  ).replace(new RegExp(`"${marker}(-?\\d+)"`, "gu"), "$1");
}

export function toQueryParams(query: unknown): URLSearchParams {
  const params = new URLSearchParams();
  const raw = toSerdeValue(query ?? {});
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) {
    throw new TypeError("query parameters must serialize to an object");
  }
  for (const [key, value] of Object.entries(raw)) {
    if (value === undefined || value === null) {
      continue;
    }
    if (Array.isArray(value)) {
      for (const item of value) {
        params.append(key, String(item));
      }
    } else {
      params.set(key, String(value));
    }
  }
  return params;
}

export function tagged<TType extends string>(
  type: TType,
  fields?: Record<string, unknown>,
): { type: TType } & Record<string, unknown> {
  return { type, ...(fields ?? {}) };
}
