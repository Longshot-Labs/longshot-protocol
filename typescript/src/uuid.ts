const SIMPLE_UUID = /^[0-9a-fA-F]{32}$/u;
const HYPHENATED_UUID =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/u;

/** Normalize the text formats accepted by Rust `Uuid::parse_str`. */
export function normalizeUuid(value: string): string {
  let body: string;
  if (SIMPLE_UUID.test(value)) {
    body = value;
  } else if (HYPHENATED_UUID.test(value)) {
    body = value;
  } else if (
    value.length === 38
    && value.startsWith("{")
    && value.endsWith("}")
    && HYPHENATED_UUID.test(value.slice(1, -1))
  ) {
    body = value.slice(1, -1);
  } else if (
    value.length === 45
    && value.startsWith("urn:uuid:")
    && HYPHENATED_UUID.test(value.slice(9))
  ) {
    body = value.slice(9);
  } else {
    throw new Error("invalid UUID");
  }

  const compact = body.replaceAll("-", "").toLowerCase();
  return `${compact.slice(0, 8)}-${compact.slice(8, 12)}-${compact.slice(12, 16)}-${compact.slice(16, 20)}-${compact.slice(20)}`;
}
