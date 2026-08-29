import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const API_DIR = join(ROOT, "rust/src/api");
const TYPES_DIR = join(ROOT, "rust/src/types");
const OPENAPI_PATH = join(ROOT, "fixtures/api/openapi.json");
const schemas = {};
const defaults = new Map();
const schemaDefaults = new Map();
// `statuses` is a Rust Vec for application use but its query adapter emits one
// comma-separated string, matching the OpenAPI parameter's wire scalar.
const queryWireTypeOverrides = new Map([["PublicMarketsRawQuery.statuses", "string"]]);

for (const file of readdirSync(API_DIR).filter((name) => name.endsWith(".rs") && name !== "wire_int.rs")) {
  parseDeclarations(readFileSync(join(API_DIR, file), "utf8"));
}
const apiSchemaNames = new Set(Object.keys(schemas));
for (const file of readdirSync(TYPES_DIR).filter((name) => name.endsWith(".rs") && name !== "mod.rs")) {
  parseDeclarations(readFileSync(join(TYPES_DIR, file), "utf8"));
}
parseDeclarations(readFileSync(join(ROOT, "rust/src/ws.rs"), "utf8"));
materializeSerdeDefaults();
validateApiDeclarations(readFileSync(join(ROOT, "typescript/src/api.ts"), "utf8"), apiSchemaNames);
if (schemas.UnsignedRfqOrderRequest[1].order_type[2] !== "d2")
  throw new Error("default_order_type must decode to 2");
validateCurrentOpenApi(
  JSON.parse(readFileSync(OPENAPI_PATH, "utf8")),
  new Set(Object.keys(schemas)),
);
for (const [name, schema] of Object.entries(schemas)) {
  if (schema[0] === "o" && schema[2] && Object.values(schema[1]).some((field) => field[2] === "f"))
    throw new Error(`${name} combines flatten with deny_unknown_fields`);
}

const reachable = assertResolved(Object.keys(schemas));
const runtimeSchemas = Object.fromEntries([...reachable].map((name) => [name, schemas[name]]));
writeFileSync(join(ROOT, "typescript/src/serde.generated.ts"), [
  "// Generated from Rust serde declarations. Do not edit.",
  `export const API_SCHEMAS: Record<string, unknown> = JSON.parse(${JSON.stringify(JSON.stringify(runtimeSchemas))});`,
  "",
].join("\n"));

function parseDeclarations(source) {
  for (const match of source.matchAll(/fn\s+([A-Za-z0-9_]+)\(\)\s*->[^{]+\{\s*(-?\d+|true|false|"[^"]*")\s*\}/gu))
    defaults.set(match[1], JSON.parse(match[2]));
  const lines = source.split(/\r?\n/);
  let attrs = [];
  for (let index = 0; index < lines.length;) {
    const line = lines[index].trim();
    if (line.startsWith("#[")) {
      const [attr, next] = readAttr(lines, index);
      attrs.push(attr);
      index = next;
      continue;
    }
    const match = line.match(/^pub (struct|enum) ([A-Za-z0-9_]+)(.*)$/);
    if (match) {
      const parsed = match[1] === "struct"
        ? parseStruct(lines, index, match[3], attrs)
        : parseEnum(lines, index, attrs, match[2]);
      if (attrs.some((attr) => /\b(?:Serialize|Deserialize)\b/u.test(attr)) && !docHidden(attrs))
        schemas[match[2]] = parsed[0];
      [attrs, index] = [[], parsed[1]];
      continue;
    }
    if (line && !line.startsWith("//")) attrs = [];
    index += 1;
  }
}

function parseStruct(lines, index, suffix, attrs) {
  if (suffix.trimStart().startsWith("{}"))
    return [["o", {}, hasAttr(attrs, "deny_unknown_fields")], index + 1];
  const tuple = suffix.match(/^\s*\(\s*(?:pub\s+)?(.+)\);$/);
  if (tuple) return [typeDescriptor(tuple[1], []), index + 1];
  const [fields, next] = parseFields(lines, index + 1);
  return [["o", fields, hasAttr(attrs, "deny_unknown_fields")], next];
}

function parseEnum(lines, index, attrs, name) {
  const variants = [];
  let variantAttrs = [];
  let variantDefault = false;
  for (index += 1; index < lines.length;) {
    const line = lines[index].trim();
    if (line === "}") break;
    if (line.startsWith("#[")) {
      const [attr, next] = readAttr(lines, index);
      variantAttrs.push(attr);
      if (hasAttr([attr], "default")) variantDefault = true;
      index = next;
      continue;
    }
    if (!line || line.startsWith("//")) { index += 1; continue; }

    // A repr discriminant controls Rust/binary conversion; Serde still emits the
    // unit variant name, so retain the variant while ignoring its expression.
    const unit = line.match(/^([A-Za-z0-9_]+)(?:\s*=\s*[^,]+)?,$/);
    const payload = line.match(/^([A-Za-z0-9_]+)\((.+)\),$/);
    const inline = line.match(/^([A-Za-z0-9_]+)\s*\{\s*(.+)\s*\},$/);
    const structured = line.match(/^([A-Za-z0-9_]+)\s*\{$/);
    let variant;
    if (unit) variant = { name: unit[1], kind: "unit" };
    else if (payload)
      variant = { name: payload[1], kind: "payload", payload: typeDescriptor(payload[2], variantAttrs) };
    else if (inline)
      variant = { name: inline[1], kind: "fields", fields: parseInlineFields(inline[2]) };
    else if (structured) {
      const [fields, next] = parseFields(lines, index + 1);
      variant = { name: structured[1], kind: "fields", fields };
      index = next - 1;
    } else throw new Error(`unsupported Rust enum variant: ${line}`);
    if (variant) {
      if (!docHidden(variantAttrs))
        variants.push({ ...variant, attrs: variantAttrs, default: variantDefault });
      variantAttrs = [];
      variantDefault = false;
    }
    index += 1;
  }

  const renameAll = attrValue(attrs, "rename_all");
  const tagged = attrValue(attrs, "tag");
  const content = attrValue(attrs, "content");
  const denyUnknown = hasAttr(attrs, "deny_unknown_fields");
  const defaultVariants = variants.filter((variant) => variant.default);
  if (defaultVariants.length > 1)
    throw new Error(`${name} has multiple Rust default variants`);
  if (defaultVariants.length === 1) {
    if (defaultVariants[0].kind !== "unit")
      throw new Error(`${name} has a non-unit Rust default variant`);
    schemaDefaults.set(name, variantWireName(defaultVariants[0], renameAll));
  }
  if (hasAttr(attrs, "untagged")) return [["u", variants.map(variantDescriptor)], index + 1];
  if (tagged) {
    return [["u", variants.map((variant) => {
      const wire = variantWireName(variant, renameAll);
      if (content) {
        const fields = { [tagged]: [literal(wire), true] };
        if (variant.kind !== "unit") fields[content] = [variantDescriptor(variant), true];
        return ["o", fields, denyUnknown];
      }
      if (variant.kind === "unit")
        return ["o", { [tagged]: [literal(wire), true] }, denyUnknown];
      if (variant.kind === "fields")
        return ["o", { [tagged]: [literal(wire), true], ...variant.fields }, denyUnknown];
      return ["m", tagged, wire, variant.payload];
    })], index + 1];
  }
  if (variants.every((variant) => variant.kind === "unit"))
    return [["v", variants.map((variant) => variantWireName(variant, renameAll))], index + 1];
  return [["u", variants.map((variant) => {
    const wire = variantWireName(variant, renameAll);
    return variant.kind === "unit" ? literal(wire)
      : ["o", { [wire]: [variantDescriptor(variant), true] }, false];
  })], index + 1];
}

function parseInlineFields(source) {
  return Object.fromEntries(splitTopLevel(source).map((field) => {
    const match = field.match(/^((?:r#)?[A-Za-z0-9_]+)\s*:\s*(.+)$/);
    if (!match) throw new Error(`unsupported inline enum field: ${field}`);
    return [match[1].replace(/^r#/u, ""), [typeDescriptor(match[2], []), true, ""]];
  }));
}

function splitTopLevel(source) {
  const values = [];
  let depth = 0;
  let start = 0;
  for (let index = 0; index < source.length; index += 1) {
    if ("<([".includes(source[index])) depth++;
    else if (">)]".includes(source[index])) depth--;
    else if (source[index] === "," && depth === 0) {
      values.push(source.slice(start, index).trim());
      start = index + 1;
    }
  }
  values.push(source.slice(start).trim());
  return values;
}

function variantDescriptor(variant) {
  if (variant.kind === "unit") return "z";
  return variant.kind === "fields" ? ["o", variant.fields, false] : variant.payload;
}

function variantWireName(variant, rule) {
  return attrValue(variant.attrs, "rename") ?? rename(variant.name, rule);
}

function parseFields(lines, index) {
  const fields = {};
  let attrs = [];
  for (; index < lines.length; index += 1) {
    const line = lines[index].trim();
    if (line === "}" || line === "},") return [fields, index + 1];
    if (line.startsWith("#[")) {
      const [attr, next] = readAttr(lines, index);
      if (attr.startsWith("#[serde(")) attrs.push(attr);
      index = next - 1;
      continue;
    }
    const field = line.match(/^(?:pub\s+)?((?:r#)?[A-Za-z0-9_]+)\s*:\s*(.+),$/);
    if (!field) { if (line && !line.startsWith("//")) attrs = []; continue; }
    const rustName = field[1].replace(/^r#/u, "");
    const flatten = hasAttr(attrs, "flatten");
    const name = flatten ? rustName
      : attrValue(attrs, "rename") ?? (rustName === "from" ? "from_" : rustName);
    const optional = /^Option\s*</u.test(field[2].trim());
    const defaulted = hasAttr(attrs, "default");
    const required = !defaulted && (!optional || hasDeserializer(attrs));
    const defaultFn = attrValue(attrs, "default");
    if (defaultFn !== undefined && !defaults.has(defaultFn))
      throw new Error(`unsupported serde default function ${defaultFn}`);
    fields[name] = [
      typeDescriptor(field[2], attrs),
      required,
      flatten ? "f" : defaultFn !== undefined ? `d${JSON.stringify(defaults.get(defaultFn))}`
        : defaulted ? "d" : "",
    ];
    attrs = [];
  }
  throw new Error("unterminated Rust field block");
}

function materializeSerdeDefaults() {
  for (const [name, schema] of Object.entries(schemas)) materializeDefaults(schema, name);
}

function materializeDefaults(descriptor, path) {
  if (!Array.isArray(descriptor)) return;
  const kind = descriptor[0];
  if (kind === "o") {
    for (const [name, field] of Object.entries(descriptor[1])) {
      if (field[2] === "d") {
        // Embed the concrete Rust default so unsupported Default implementations fail
        // generation instead of silently leaving decoded runtime values absent.
        field[2] = `d${JSON.stringify(rustDefaultValue(field[0], `${path}.${name}`))}`;
      }
      materializeDefaults(field[0], `${path}.${name}`);
    }
  } else if (kind === "u") {
    descriptor[1].forEach((candidate, index) =>
      materializeDefaults(candidate, `${path}[${index}]`));
  } else if (kind === "m") materializeDefaults(descriptor[3], path);
  else if (["a", "d", "n", "w"].includes(kind)) materializeDefaults(descriptor[1], path);
}

function rustDefaultValue(descriptor, path) {
  if (typeof descriptor === "string") {
    if (descriptor === "s") return "";
    if (descriptor === "b") return false;
    if (descriptor === "f" || /^[ui](?:8|16|32|64|128)$|^[ui]size$/u.test(descriptor)) return 0;
    if (descriptor === "j" || descriptor === "z") return null;
    throw new Error(`${path} uses unsupported Rust default type ${descriptor}`);
  }
  if (descriptor[0] === "a") return [];
  if (descriptor[0] === "d") return {};
  if (descriptor[0] === "n") return null;
  if (descriptor[0] === "w") return rustDefaultValue(descriptor[1], path);
  if (descriptor[0] === "r") {
    const name = descriptor[1];
    if (schemaDefaults.has(name)) return schemaDefaults.get(name);
    throw new Error(`${path} uses unsupported Rust default schema ${name}`);
  }
  throw new Error(`${path} uses unsupported Rust default descriptor ${JSON.stringify(descriptor)}`);
}

function typeDescriptor(raw, attrs) {
  const type = raw.trim();
  const generic = type.match(/^([^<]+)<(.+)>$/u);
  const args = generic ? splitTopLevel(generic[2]) : [];
  let descriptor;
  if (generic?.[1].trim() === "Option") descriptor = ["n", typeDescriptor(args[0], [])];
  else if (["Vec", "List"].includes(generic?.[1].trim())) descriptor = ["a", typeDescriptor(args[0], [])];
  else if (["BTreeMap", "HashMap"].includes(generic?.[1].trim())) {
    if (args[0]?.trim() !== "String") throw new Error(`unsupported Rust map key type: ${args[0]}`);
    descriptor = ["d", typeDescriptor(args[1], [])];
  }
  else if (["Arc", "Box"].includes(generic?.[1].trim())) descriptor = typeDescriptor(args[0], []);
  else if (type === "String" || type === "str") descriptor = "s";
  else if (type === "bool") descriptor = "b";
  else if (type === "f32" || type === "f64") descriptor = "f";
  else if (type === "()") descriptor = "z";
  else if (type === "Value" || type === "serde_json::Value") descriptor = "j";
  else if (/^[ui](?:8|16|32|64|128)$|^[ui]size$/u.test(type)) descriptor = type;
  else if (type === "Uuid" || type === "RequestId") descriptor = "uuid";
  else if (type === "MarketId") descriptor = "mid";
  else if (type === "PositionId") descriptor = "pid";
  else if (type === "Address") descriptor = "addr";
  else descriptor = ["r", type.replace(/^crate::[^:]+::/u, "")];
  const adapters = attrs.flatMap((attr) => [...attr.matchAll(
    /\b(?:with|deserialize_with|serialize_with)\s*=\s*"([^"]+)"/gu
  )].map((match) => match[1]));
  let wireInteger = false;
  for (const adapter of adapters) {
    if (/^crate::api::wire_int::(?:option_)?[ui]64_string(?:::(?:deserialize|serialize))?$/u.test(adapter))
      wireInteger = true;
    else if (adapter !== "status_list_query")
      throw new Error(`unsupported serde adapter ${adapter}`);
  }
  return wireInteger ? ["w", descriptor] : descriptor;
}

function readAttr(lines, index) {
  let attr = lines[index++].trim();
  let depth = (attr.match(/\[/g) ?? []).length - (attr.match(/\]/g) ?? []).length;
  while (index < lines.length && depth > 0) {
    const line = lines[index++].trim();
    attr += ` ${line}`;
    depth += (line.match(/\[/g) ?? []).length - (line.match(/\]/g) ?? []).length;
  }
  return [attr, index];
}

function hasAttr(attrs, name) {
  return attrs.some((attr) => new RegExp(`\\b${name}\\b`, "u").test(attr));
}

function docHidden(attrs) {
  return attrs.some((attr) => /\bdoc\s*\(\s*hidden\s*\)/u.test(attr));
}

function hasDeserializer(attrs) {
  return attrs.some((attr) => /\b(?:with|deserialize_with)\s*=/u.test(attr));
}

function attrValue(attrs, name) {
  for (const attr of attrs) {
    const value = attr.match(new RegExp(`\\b${name}\\s*=\\s*"([^"]+)"`, "u"))?.[1];
    if (value !== undefined) return value;
  }
  return undefined;
}

function rename(name, rule) {
  const snake = name.replace(/([A-Z]+)([A-Z][a-z])/g, "$1_$2").replace(/([a-z0-9])([A-Z])/g, "$1_$2");
  if (rule === "snake_case") return snake.toLowerCase();
  if (rule === "lowercase") return name.toLowerCase();
  if (rule === "UPPERCASE") return name.toUpperCase();
  return rule === "SCREAMING_SNAKE_CASE" ? snake.toUpperCase() : name;
}

function validateCurrentOpenApi(document, protocolNames) {
  const components = document.components?.schemas ?? {};
  const roots = new Set(["CreateSessionRequest", "SessionResponse"]);
  const excludedPaths = new Set([
    "/health",
    "/readyz",
    "/v1/auth/invite_code/verify",
    "/v1/mm/max_payouts",
    "/v1/mm/profit_caps",
    "/v1/mm/taker_pnl",
    "/v1/user/app_token_grants",
    "/v1/user/available_app_token_balance",
    "/v1/user/deposit_app_token",
    "/v1/user/deposit_match_opportunities",
    "/v1/user/grant_app_token",
    "/v1/user/reserved_app_token_balance",
    // First-party presentation and private service routes are not part of the
    // external protocol package.
    "/v1/community-picks",
    "/v1/community-picks/{position_id}/reactions/{emoji}",
    "/v1/market-data/candles",
    "/v1/market-data/reference-price",
    "/v1/market-data/stream",
    "/v1/market-data/top-of-book",
    "/v1/market-data/top-of-book/history",
    "/v1/market-data/top-of-book/stream",
    "/v1/market-data/window-results",
    "/v1/nfl_hub_config",
    "/v1/recent-winners",
    "/v1/u/{handle}/followers",
    "/v1/u/{handle}/following",
    "/v1/user/deposit_vault",
    "/v1/user/following/{handle}",
    "/v1/user/request_withdrawal_vault",
    "/v1/user/vault/performance",
    "/v1/vault/claim_fees",
    "/v1/vault/contributors",
    "/v1/vault/events",
    "/v1/vault/get_vault",
    "/v1/vault/pnl_history",
    "/v1/vault/position_vault/{id}",
    "/v1/vault/positions",
    "/v1/vault/positions/{id}",
    "/v1/vault/stats",
    "/v1/vault/withdrawal_queue",
  ]);
  const excludedFields = new Map([
    ["CreateSessionRequest", new Set(["invite_code"])],
    ["EventMarket", new Set(["featured_slot"])],
    ["PublicMarketsRawQuery", new Set(["include_featured", "featured_only"])],
    ["SessionResponse", new Set(["signup_access_code", "signup_access_code_type"])],
    ["WalletAuthRequest", new Set(["invite_code"])],
  ]);
  // These Rust DTOs deliberately retain the protocol's `Response` suffix;
  // the server publishes the same wire shapes under shorter `schema(as = ...)` names.
  const schemaAliases = {
    AppTokenGrantCategory: "AppTokenGrantCategoryResponse",
    PortfolioIntegrityError: "PortfolioIntegrityErrorResponse",
  };

  // Every supported external route remains checked against the full server fixture.
  // Explicit exclusions keep first-party presentation and server-only contracts out
  // of the registry packages without weakening drift checks for supported routes.
  for (const [path, pathItem] of Object.entries(document.paths ?? {})) {
    if (path.split("/").includes("admin") || excludedPaths.has(path)) continue;
    for (const [method, operation] of Object.entries(pathItem)) {
      if (!/^(?:delete|get|patch|post|put)$/u.test(method)) continue;
      collectJsonSchemaRoots(operation.requestBody, roots);
      for (const [status, response] of Object.entries(operation.responses ?? {})) {
        if (/^2\d\d$/u.test(status)) collectJsonSchemaRoots(response, roots);
      }
    }
  }

  const missing = [...roots].filter((name) => !protocolNames.has(name)).sort();
  if (missing.length)
    throw new Error(`Rust protocol is missing current supported OpenAPI schemas: ${missing.join(", ")}`);

  const reachable = new Set();
  const visit = (name) => {
    if (reachable.has(name)) return;
    reachable.add(name);
    walkOpenApiSchema(components[name], visit);
  };
  roots.forEach(visit);

  const missingReachable = [...reachable]
    .filter((name) => !protocolNames.has(schemaAliases[name] ?? name))
    .sort();
  if (missingReachable.length) {
    throw new Error(
      `Rust protocol is missing schemas reachable from current supported OpenAPI contracts: `
      + missingReachable.join(", "),
    );
  }

  const schemaDrifts = [];
  for (const name of [...reachable].sort()) {
    const protocolName = schemaAliases[name] ?? name;
    const rustFields = rustObjectFieldNames(protocolName);
    const openApiFields = openApiObjectFieldNames(components[name], components);
    for (const field of excludedFields.get(name) ?? []) openApiFields?.delete(field);
    if (rustFields && openApiFields && !sameSet(rustFields, openApiFields)) {
      schemaDrifts.push(
        `${name} field drift between Rust protocol and current OpenAPI: `
        + `Rust=[${[...rustFields].sort().join(", ")}], `
        + `OpenAPI=[${[...openApiFields].sort().join(", ")}]`,
      );
    }

    const rustEnum = schemas[protocolName]?.[0] === "v" ? schemas[protocolName][1] : undefined;
    const openApiEnum = openApiEnumValues(components[name], components);
    if (rustEnum && openApiEnum && JSON.stringify(rustEnum) !== JSON.stringify(openApiEnum))
      schemaDrifts.push(`${name} enum variants drifted between Rust protocol and current OpenAPI`);
  }
  if (schemaDrifts.length) throw new Error(schemaDrifts.join("\n"));

  // OpenAPI preserves route-local query fields but not their Rust DTO names.
  // Keep every supported query operation bound explicitly so a new route cannot
  // silently evade requiredness and scalar-type validation.
  const queryOperations = [
    ["ChatMentionCandidatesQuery", "/v1/chat/mention_candidates", "get"],
    ["ChatRecentMessagesQuery", "/v1/chat/recent_messages", "get"],
    ["ChatStreamQuery", "/v1/chat/stream", "get"],
    ["ListContestsQuery", "/v1/contests", "get"],
    ["ContestDetailQuery", "/v1/contests/{id}", "get"],
    ["ContestLeaderboardQuery", "/v1/contests/{id}/leaderboard", "get"],
    ["FeedRawQuery", "/v1/feed", "get"],
    ["LeaderboardRawQuery", "/v1/leaderboard", "get"],
    ["PublicMarketsRawQuery", "/v1/markets", "get"],
    ["RecentResolutionsQuery", "/v1/mm/recent_resolutions", "get"],
    ["FantasyEntriesQuery", "/v1/portfolio/fantasy", "get"],
    ["PnlHistoryScopedQuery", "/v1/portfolio/pnl", "get"],
    ["PositionsByMarketsQuery", "/v1/portfolio/positions", "get"],
    ["PortfolioSummaryRawQuery", "/v1/portfolio/summary", "get"],
    ["PositionsQuery", "/v1/positions", "get"],
    ["MarketCurrentQuery", "/v1/price-markets/current", "get"],
    ["MarketLookupQuery", "/v1/price-markets/lookup", "get"],
    ["StreakHistoryRawQuery", "/v1/streak/history", "get"],
    ["StreakLeaderboardRawQuery", "/v1/streak/leaderboard", "get"],
    ["StreakPicksRawQuery", "/v1/streak/picks", "get"],
    ["ContestDetailQuery", "/v1/u/{handle}/contests/{id}", "get"],
    ["FantasyEntriesQuery", "/v1/u/{handle}/fantasy", "get"],
    ["PnlHistoryScopedQuery", "/v1/u/{handle}/pnl", "get"],
    ["PositionsQuery", "/v1/u/{handle}/positions", "get"],
    ["StreakHistoryRawQuery", "/v1/u/{handle}/streak/history", "get"],
    ["StreakPicksRawQuery", "/v1/u/{handle}/streak/picks", "get"],
    ["PortfolioSummaryRawQuery", "/v1/u/{handle}/summary", "get"],
    ["UserTransactionsRawQuery", "/v1/user/transactions", "get"],
    ["ConfirmPositionQuery", "/v1/user/confirm_position", "post"],
    ["NotificationsRawQuery", "/v1/user/notifications", "get"],
    ["NotificationStreamRawQuery", "/v1/user/notifications/stream", "get"],
    ["ProfileUpdateQuery", "/v1/user/profile", "put"],
    ["HandleAvailabilityQuery", "/v1/user/profile/check-handle", "get"],
    ["UserReferralStatsRawQuery", "/v1/user/referral_stats", "get"],
    ["ReferralsListRawQuery", "/v1/user/referrals", "get"],
  ];
  const mappedOperations = new Set();
  for (const [name, path, method] of queryOperations) {
    const operationKey = `${method.toUpperCase()} ${path}`;
    if (mappedOperations.has(operationKey))
      throw new Error(`duplicate supported query operation mapping: ${operationKey}`);
    mappedOperations.add(operationKey);
    if (!protocolNames.has(name)) throw new Error(`Rust protocol is missing current query DTO ${name}`);
    const operation = document.paths?.[path]?.[method];
    if (!operation) throw new Error(`OpenAPI operation missing for ${name}: ${operationKey}`);
    const parameters = queryParameters(document.paths[path], operation, document);
    const rustFields = rustObjectFields(name);
    if (!rustFields) throw new Error(`${name} is not a Rust object query DTO`);
    const openApiFields = new Map(parameters.map((parameter) => [parameter.name, parameter]));
    for (const field of excludedFields.get(name) ?? []) openApiFields.delete(field);
    if (!sameSet(new Set(rustFields.keys()), new Set(openApiFields.keys()))) {
      throw new Error(
        `${name} query drift between Rust protocol and ${operationKey}: `
        + `Rust=[${[...rustFields.keys()].sort().join(", ")}], `
        + `OpenAPI=[${[...openApiFields.keys()].sort().join(", ")}]`,
      );
    }
    for (const [field, rust] of rustFields) {
      const parameter = openApiFields.get(field);
      const openApiRequired = parameter.required === true;
      if (rust.required !== openApiRequired) {
        throw new Error(
          `${name}.${field} requiredness drift for ${operationKey}: `
          + `Rust=${rust.required}, OpenAPI=${openApiRequired}`,
        );
      }
      const rustType = queryWireTypeOverrides.get(`${name}.${field}`)
        ?? rustScalarType(rust.type, `${name}.${field}`);
      const openApiType = openApiScalarType(parameter.schema, document, `${operationKey}.${field}`);
      if (rustType !== openApiType) {
        throw new Error(
          `${name}.${field} scalar type drift for ${operationKey}: `
          + `Rust=${rustType}, OpenAPI=${openApiType}`,
        );
      }
    }
  }

  const supportedQueryOperations = new Set();
  for (const [path, pathItem] of Object.entries(document.paths ?? {})) {
    if (path.split("/").includes("admin") || excludedPaths.has(path)) continue;
    for (const [method, operation] of Object.entries(pathItem)) {
      if (!/^(?:delete|get|patch|post|put)$/u.test(method)) continue;
      if (queryParameters(pathItem, operation, document).length)
        supportedQueryOperations.add(`${method.toUpperCase()} ${path}`);
    }
  }
  if (!sameSet(mappedOperations, supportedQueryOperations)) {
    const missing = [...supportedQueryOperations].filter((key) => !mappedOperations.has(key)).sort();
    const stale = [...mappedOperations].filter((key) => !supportedQueryOperations.has(key)).sort();
    throw new Error(
      `supported query operation coverage drift: missing=[${missing.join(", ")}], stale=[${stale.join(", ")}]`,
    );
  }

  function collectJsonSchemaRoots(container, output) {
    const resolved = resolveOpenApiDocumentRef(container, document);
    for (const [mediaType, media] of Object.entries(resolved?.content ?? {})) {
      if (mediaType === "application/json" || mediaType.endsWith("+json"))
        collectOpenApiRootRefs(media.schema, output);
    }
  }
}

function collectOpenApiRootRefs(schema, output) {
  if (!schema || typeof schema !== "object") return;
  const ref = openApiRefName(schema.$ref);
  if (ref) output.add(ref);
  for (const branch of [...(schema.oneOf ?? []), ...(schema.anyOf ?? []), ...(schema.allOf ?? [])]) {
    const branchRef = openApiRefName(branch?.$ref);
    if (branchRef) output.add(branchRef);
  }
  const itemRef = openApiRefName(schema.items?.$ref);
  if (itemRef) output.add(itemRef);
}

function walkOpenApiSchema(schema, visit) {
  if (!schema || typeof schema !== "object") return;
  const ref = openApiRefName(schema.$ref);
  if (ref) visit(ref);
  for (const value of Object.values(schema)) walkOpenApiSchema(value, visit);
}

function openApiRefName(ref) {
  const prefix = "#/components/schemas/";
  return typeof ref === "string" && ref.startsWith(prefix) ? ref.slice(prefix.length) : undefined;
}

function resolveOpenApiDocumentRef(value, document) {
  if (!value?.$ref) return value;
  const match = value.$ref.match(/^#\/components\/([^/]+)\/([^/]+)$/u);
  return match ? document.components?.[match[1]]?.[match[2]] : undefined;
}

function resolveOpenApiRef(value, components) {
  if (!value?.$ref) return value;
  return components[value.$ref.split("/").at(-1)];
}

function queryParameters(pathItem, operation, document) {
  return [...(pathItem.parameters ?? []), ...(operation.parameters ?? [])]
    .map((parameter) => resolveOpenApiDocumentRef(parameter, document))
    .filter((parameter) => parameter?.in === "query");
}

function rustObjectFields(name, stack = new Set()) {
  const descriptor = schemas[name];
  if (!descriptor || descriptor[0] !== "o") return undefined;
  if (stack.has(name)) return new Map();
  stack.add(name);
  const fields = new Map();
  for (const [field, [type, required, flag]] of Object.entries(descriptor[1])) {
    if (flag === "f") {
      const ref = descriptorRefName(type);
      const flattened = ref && rustObjectFields(ref, stack);
      if (flattened) flattened.forEach((value, key) => fields.set(key, value));
    } else {
      fields.set(field === "from_" ? "from" : field, { type, required });
    }
  }
  stack.delete(name);
  return fields;
}

function rustScalarType(descriptor, path, stack = new Set()) {
  if (typeof descriptor === "string") {
    if (["s", "uuid", "addr", "pid"].includes(descriptor)) return "string";
    if (descriptor === "b") return "boolean";
    if (descriptor === "f") return "number";
    if (descriptor === "mid" || /^[ui](?:8|16|32|64|128)$|^[ui]size$/u.test(descriptor))
      return "integer";
    if (descriptor === "j") return "object";
    throw new Error(`${path} uses unsupported query scalar ${descriptor}`);
  }
  if (["n", "w"].includes(descriptor[0])) return rustScalarType(descriptor[1], path, stack);
  if (descriptor[0] === "a") return "array";
  if (descriptor[0] === "d" || descriptor[0] === "o") return "object";
  if (descriptor[0] === "l") return typeof descriptor[1];
  if (descriptor[0] === "v") return "string";
  if (descriptor[0] === "u") {
    const types = new Set(descriptor[1].map((candidate) => rustScalarType(candidate, path, stack)));
    if (types.size === 1) return [...types][0];
    throw new Error(`${path} uses mixed query scalar union ${[...types].join("|")}`);
  }
  if (descriptor[0] === "r") {
    const name = descriptor[1];
    if (stack.has(name)) throw new Error(`${path} has recursive query scalar ${name}`);
    if (!(name in schemas)) throw new Error(`${path} references unknown query scalar ${name}`);
    stack.add(name);
    const type = rustScalarType(schemas[name], path, stack);
    stack.delete(name);
    return type;
  }
  throw new Error(`${path} uses unsupported query descriptor ${JSON.stringify(descriptor)}`);
}

function openApiScalarType(schema, document, path, stack = new Set()) {
  if (!schema || typeof schema !== "object") throw new Error(`${path} has no OpenAPI schema`);
  if (schema.$ref) {
    if (stack.has(schema.$ref)) throw new Error(`${path} has recursive OpenAPI scalar ${schema.$ref}`);
    const resolved = resolveOpenApiDocumentRef(schema, document);
    if (!resolved) throw new Error(`${path} has unresolved OpenAPI scalar ${schema.$ref}`);
    stack.add(schema.$ref);
    const type = openApiScalarType(resolved, document, path, stack);
    stack.delete(schema.$ref);
    return type;
  }
  if (schema.type && schema.type !== "null") return schema.type;
  if (Array.isArray(schema.enum) && schema.enum.length) return typeof schema.enum[0];
  const branches = [...(schema.allOf ?? []), ...(schema.oneOf ?? []), ...(schema.anyOf ?? [])];
  const types = new Set(branches
    .filter((branch) => branch?.type !== "null")
    .map((branch) => openApiScalarType(branch, document, path, stack)));
  if (types.size === 1) return [...types][0];
  throw new Error(`${path} has unsupported OpenAPI scalar ${JSON.stringify(schema)}`);
}

function rustObjectFieldNames(name, stack = new Set()) {
  const descriptor = schemas[name];
  if (!descriptor || descriptor[0] !== "o") return undefined;
  if (stack.has(name)) return new Set();
  stack.add(name);
  const fields = new Set();
  for (const [field, [type, , flag]] of Object.entries(descriptor[1])) {
    if (flag === "f") {
      const ref = descriptorRefName(type);
      const flattened = ref && rustObjectFieldNames(ref, stack);
      if (flattened) flattened.forEach((item) => fields.add(item));
    } else fields.add(field);
  }
  stack.delete(name);
  return fields;
}

function descriptorRefName(descriptor) {
  if (!Array.isArray(descriptor)) return undefined;
  if (descriptor[0] === "r") return descriptor[1];
  if (descriptor[0] === "n") return descriptorRefName(descriptor[1]);
  return undefined;
}

function openApiObjectFieldNames(schema, components, stack = new Set()) {
  if (!schema || typeof schema !== "object") return undefined;
  const ref = openApiRefName(schema.$ref);
  if (ref) {
    if (stack.has(ref)) return new Set();
    stack.add(ref);
    const fields = openApiObjectFieldNames(components[ref], components, stack);
    stack.delete(ref);
    return fields;
  }
  const fields = new Set(Object.keys(schema.properties ?? {}));
  let hasObjectShape = Boolean(schema.properties || schema.type === "object");
  for (const part of schema.allOf ?? []) {
    const nested = openApiObjectFieldNames(part, components, stack);
    if (nested) {
      hasObjectShape = true;
      nested.forEach((field) => fields.add(field));
    }
  }
  return hasObjectShape ? fields : undefined;
}

function openApiEnumValues(schema, components) {
  if (!schema || typeof schema !== "object") return undefined;
  const ref = openApiRefName(schema.$ref);
  if (ref) return openApiEnumValues(components[ref], components);
  if (Array.isArray(schema.enum)) return schema.enum;
  for (const part of schema.allOf ?? []) {
    const values = openApiEnumValues(part, components);
    if (values) return values;
  }
  return undefined;
}

function sameSet(left, right) {
  return left.size === right.size && [...left].every((value) => right.has(value));
}

function literal(value) { return ["l", value]; }

function validateApiDeclarations(source, names) {
  const file = ts.createSourceFile("api.ts", source, ts.ScriptTarget.Latest, true);
  const interfaces = new Map(file.statements.filter(ts.isInterfaceDeclaration)
    .map((node) => [node.name.text, node]));
  const aliases = new Map(file.statements.filter(ts.isTypeAliasDeclaration)
    .map((node) => [node.name.text, node]));
  for (const name of names) {
    const descriptor = schemas[name];
    if (descriptor[0] === "o") {
      const node = interfaces.get(`${name}SerdeShape`) ?? interfaces.get(name);
      if (!node) throw new Error(`TypeScript interface missing for Rust serde struct ${name}`);
      const members = new Map(node.members.filter(ts.isPropertySignature)
        .map((member) => [member.name.getText(file), member]));
      const extras = [...members.keys()].filter((fieldName) => !(fieldName in descriptor[1]));
      if (extras.length) throw new Error(`${name} has extra TypeScript fields: ${extras.join(", ")}`);
      for (const [fieldName, [type, required]] of Object.entries(descriptor[1])) {
        const member = members.get(fieldName);
        const actual = member?.type && normalizeType(member.type.getText(file), aliases);
        const expected = normalizeType(typescriptType(type));
        if (!member || Boolean(member.questionToken) === required || actual !== expected)
          throw new Error(`${name}.${fieldName} TypeScript drift: expected ${required ? "" : "optional "}${expected}`);
      }
    } else if (descriptor[0] === "v") {
      const body = source.match(new RegExp(`export const ${name} = \\\\{([\\\\s\\\\S]*?)\\\\n\\\\} as const;`, "m"))?.[1];
      if (!body) continue;
      const actual = [...body.matchAll(/:\\s*'([^']+)'/g)].map((match) => match[1]);
      if (JSON.stringify(actual) !== JSON.stringify(descriptor[1]))
        throw new Error(`${name} TypeScript enum variants drifted from Rust serde`);
    }
    const expectedWide = descriptor[0] === "o" ? [] : collectWideFields(descriptor).sort();
    if (expectedWide.length) {
      const alias = aliases.get(name);
      if (!alias) throw new Error(`TypeScript type alias missing for wide Rust enum ${name}`);
      const actualWide = [];
      walk(alias.type, (node) => {
        if (ts.isPropertySignature(node) && node.type && plainWideTypeText(node.type.getText(file)))
          actualWide.push(`${node.name.getText(file)}:${normalizeType(node.type.getText(file))}`);
      });
      if (JSON.stringify(actualWide.sort()) !== JSON.stringify(expectedWide))
        throw new Error(`${name} TypeScript wide-integer variants drifted from Rust serde`);
    }
  }
}

function collectWideFields(descriptor, fields = []) {
  if (!Array.isArray(descriptor)) return fields;
  if (descriptor[0] === "o") {
    for (const [name, [type]] of Object.entries(descriptor[1])) {
      const expected = plainWideType(type);
      if (expected) fields.push(`${name}:${normalizeType(expected)}`);
    }
  } else if (descriptor[0] === "u") descriptor[1].forEach((item) => collectWideFields(item, fields));
  else if (descriptor[0] === "m") collectWideFields(descriptor[3], fields);
  return fields;
}

function plainWideType(descriptor) {
  if (typeof descriptor === "string")
    return /^(?:[ui](?:64|128)|[ui]size)$/u.test(descriptor) ? "WideInteger" : undefined;
  if (descriptor[0] === "n" && plainWideType(descriptor[1]))
    return `${plainWideType(descriptor[1])} | null`;
  if (descriptor[0] === "a" && plainWideType(descriptor[1]))
    return `${plainWideType(descriptor[1])}[]`;
  return undefined;
}

function plainWideTypeText(type) {
  return /(?:^|[|(])\s*WideInteger(?:\s*[|)\[]|$)/u.test(type);
}

function typescriptType(descriptor, exact = true) {
  if (typeof descriptor === "string") {
    if (descriptor === "s" || descriptor === "uuid") return "string";
    if (descriptor === "b") return "boolean";
    if (descriptor === "f") return "number";
    if (descriptor === "j") return "unknown";
    if (descriptor === "mid") return "MarketId";
    if (descriptor === "pid") return "PositionId";
    if (descriptor === "addr") return "Address";
    if (/^(?:[ui](?:64|128)|[ui]size)$/u.test(descriptor)) return exact ? "WideInteger" : "number";
    return /^(?:[fiu]\d+)$/u.test(descriptor) ? "number" : descriptor;
  }
  if (descriptor[0] === "r") return descriptor[1];
  if (descriptor[0] === "a") return `${typescriptType(descriptor[1], exact)}[]`;
  if (descriptor[0] === "d") return `Record<string, ${typescriptType(descriptor[1], exact)}>`;
  if (descriptor[0] === "n") return `${typescriptType(descriptor[1], exact)} | null`;
  if (descriptor[0] === "w") return `${typescriptType(descriptor[1], false)} | string`;
  return "unknown";
}

function normalizeType(type, aliases) {
  if (aliases) {
    for (const [name, alias] of aliases) {
      const members = ts.isUnionTypeNode(alias.type) ? alias.type.types : [alias.type];
      if (
        members.length
        && members.every((member) => ts.isLiteralTypeNode(member) && ts.isNumericLiteral(member.literal))
      )
        type = type.replace(new RegExp(`\\b${name}\\b`, "gu"), "number");
    }
  }
  return type.split("|").map((part) => part.trim()).sort().join("|");
}

function assertResolved(roots) {
  const seen = new Set(roots);
  const visit = (descriptor) => {
    if (Array.isArray(descriptor)) {
      if (descriptor[0] === "r") {
        const name = descriptor[1];
        if (!(name in schemas)) throw new Error(`unresolved reachable serde schema ${name}`);
        if (!seen.has(name)) { seen.add(name); visit(schemas[name]); }
      } else descriptor.forEach(visit);
    } else if (descriptor && typeof descriptor === "object") Object.values(descriptor).forEach(visit);
  };
  roots.forEach((name) => {
    if (!(name in schemas)) throw new Error(`missing response serde schema ${name}`);
    visit(schemas[name]);
  });
  return seen;
}

function walk(node, visit) { visit(node); node.forEachChild((child) => walk(child, visit)); }
