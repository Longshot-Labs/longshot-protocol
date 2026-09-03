import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";
import {
  PUBLIC_OPENAPI_COMPONENT_NAMES,
  PUBLIC_OPENAPI_OPERATIONS,
  PUBLIC_PROTOCOL_NON_SERDE_TYPES,
  PUBLIC_PROTOCOL_SUPPLEMENTAL_SCHEMAS,
} from "./public-openapi-contract.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const API_DIR = join(ROOT, "rust/src/api");
const TYPES_DIR = join(ROOT, "rust/src/types");
const OPENAPI_PATH = join(ROOT, "fixtures/api/openapi.json");
const args = process.argv.slice(2);
let surfaceKind;
if (args.length === 0) surfaceKind = "generate";
else if (args.length === 1 && args[0] === "--check-public-surface") surfaceKind = "source";
else if (args.length === 1 && args[0] === "--check-packed-surface") surfaceKind = "packed";
else {
  throw new Error(
    "usage: node scripts/generate-serde.mjs "
    + "[--check-public-surface|--check-packed-surface]",
  );
}
const schemas = {};
const defaults = new Map();
const schemaDefaults = new Map();
// `statuses` is a Rust Vec for application use but its query adapter emits one
// comma-separated string, matching the OpenAPI parameter's wire scalar.
const queryWireTypeOverrides = new Map([["PublicMarketsRawQuery.statuses", "string"]]);
// Existing decoders accept these omissions even though the current response
// contract requires the keys. Pin that compatibility surface exactly so this
// gate catches every new drift and every stale exception.
const openApiOnlyRequiredFieldExceptions = new Map([
  ["ActivePosition", new Set(["taker_address"])],
  ["EventMarket", new Set([
    "description", "live_ends_at_ms", "opened_at_ms", "resolved_at_ms",
    "resolved_outcome", "source_starts_at_ms",
  ])],
  ["PriceStrikeMarket", new Set([
    "description", "open_strike_micros", "opened_at_ms", "resolved_at_ms", "resolved_outcome",
  ])],
  ["PublicMarketsResponse", new Set(["next_cursor"])],
  ["SessionResponse", new Set(["account_created"])],
]);
const PUBLIC_TYPESCRIPT_API_HELPERS = new Set([
  "createRfqRequestFromSignedOrder",
  "orderLegJsonFromOrderLeg",
  "parseOrderLegJson",
  "parseUnsignedRfqIdempotencyKey",
  "pnlHistoryScopedQueryToWire",
  "publicMarketsRawQueryToWire",
  "signedOrderJsonFromSignedOrder",
  "signedOrderJsonToSignedOrder",
]);
const PUBLIC_TYPESCRIPT_TYPE_ONLY_STRING_ENUMS = new Set(["CommunityPickMode"]);
const PUBLIC_TYPESCRIPT_TYPE_DECLARATIONS = Object.freeze({
  "bytes.ts": Object.freeze(["BytesLike"]),
  "index.ts": Object.freeze([]),
  "mm.ts": Object.freeze(["MmDecodeError", "PrivateKey"]),
  "model.ts": Object.freeze(["JsonValue", "SerdeSerializable"]),
  "rfq.ts": Object.freeze([
    "BroadcastRfqRequest", "BroadcastRfqRequestInput", "QuoteResponse",
    "QuoteResponseInput", "RfqLeg", "RfqLegInput", "RfqLegType", "RfqLegWire",
    "RfqLegWireDecodeError", "TakerMetadata",
  ]),
  "serde.generated.ts": Object.freeze([]),
  "serde.ts": Object.freeze([
    "Descriptor", "Field", "JsonMetadata", "ObjectDescriptor", "SerdeDecodeError",
  ]),
  "taker.ts": Object.freeze([
    "OrderLeg", "OrderLegInput", "SignedOrder", "SignedOrderError", "SignedOrderInput",
    "TakerSignError",
  ]),
  "types.ts": Object.freeze([
    "Address", "Amount", "ArithmeticError", "Asset", "ClientQuoteId",
    "ContestId", "Direction", "Duration", "MarketId", "MarketStatus", "MarketType",
    "MathError", "Odds", "OrderType", "Outcome", "PositionId",
    "QuoteId", "RequestId", "Timestamp", "TradingChannel", "UserId", "UserTier",
    "UuidId", "WideInteger",
  ]),
  "uuid.ts": Object.freeze([]),
  "ws.ts": Object.freeze([
    "ClientMessage", "QuoteResultStatus", "RfqSubscription", "ServerMessage",
  ]),
});
const PUBLIC_TYPESCRIPT_OPTIONAL_DECLARATION_TYPES = Object.freeze({
  // Implementation-only descriptors are not emitted in the packed .d.ts file.
  "serde.ts": new Set(["Descriptor", "Field", "JsonMetadata", "ObjectDescriptor"]),
});
const PUBLIC_TYPESCRIPT_MODULE_EXPORTS = Object.freeze({
  "bytes.ts": Object.freeze([
    "BytesLike", "U32_MAX", "U64_MAX", "U8_MAX", "bytesFrom", "bytesToHex",
    "checkU32", "checkU64", "checkU8", "concatBytes", "decodeBase64",
    "decodeBase64NoPad", "encodeBase64", "encodeBase64NoPad", "hexToBytes",
    "readU32Le", "readU64Le", "toBigInt", "toSafeNumber", "u32LeBytes",
    "u64LeBytes", "writeU32Le", "writeU64Le",
  ]),
  "mm.ts": Object.freeze([
    "AUTH_DOMAIN", "MmDecodeError", "PrivateKey", "authResponseMessage",
    "buildAuthMessage", "decodeBroadcastRfq", "decodeQuoteResponse",
    "encodeQuoteResponse", "parseAuthChallengeId", "quoteResponseMessage",
    "signAuthResponse", "signQuoteResponse", "signedQuoteResponse",
  ]),
  "model.ts": Object.freeze([
    "JsonValue", "SerdeSerializable", "isSerdeSerializable", "stringifySerde",
    "tagged", "toQueryParams", "toSerdeValue",
  ]),
  "rfq.ts": Object.freeze([
    "BROADCAST_RFQ_REQUEST_SIZE", "BroadcastRfqRequest", "BroadcastRfqRequestInput",
    "MAX_RFQ_LEGS", "QUOTE_RESPONSE_SIGNED_DATA_SIZE", "QUOTE_RESPONSE_SIZE",
    "QuoteResponse", "QuoteResponseInput", "RFQ_LEG_TYPE_BINARY_EVENT_TAG",
    "RFQ_LEG_TYPE_PRICE_STRIKE_TAG", "RFQ_LEG_WIRE_SIZE", "RFQ_PROTOCOL_VERSION",
    "RfqLeg", "RfqLegInput", "RfqLegType", "RfqLegWire", "RfqLegWireDecodeError",
    "TAKER_METADATA_WIRE_SIZE", "TakerMetadata",
  ]),
  "serde.generated.ts": Object.freeze(["API_SCHEMAS"]),
  "serde.ts": Object.freeze(["SerdeDecodeError", "decodeApiJson"]),
  "taker.ts": Object.freeze([
    "OrderLeg", "OrderLegInput", "SignedOrder", "SignedOrderError", "SignedOrderInput",
    "TakerSignError", "signOrder", "signedOrder",
  ]),
  "types.ts": Object.freeze([
    "Address", "Amount", "ArithmeticError", "Asset", "ClientQuoteId",
    "ContestId", "Direction", "Duration", "MIN_BET_MICROS", "MarketId",
    "MarketStatus", "MarketType", "MathError", "Odds", "OrderType",
    "Outcome", "PositionId", "QuoteId", "RequestId", "Timestamp", "TradingChannel",
    "U64_MAX", "UserId", "UserTier", "UuidId", "WideInteger",
    "marketStatusCanTransitionTo", "marketStatusIsTerminal", "marketStatusIsTradeable",
    "marketStatusIsVisible",
    "outcomeOpposite", "u64SerdeValue",
  ]),
  "uuid.ts": Object.freeze(["normalizeUuid"]),
  "ws.ts": Object.freeze([
    "ClientMessage", "QuoteResultStatus", "RfqSubscription", "ServerMessage",
  ]),
});
const PUBLIC_TYPESCRIPT_RUNTIME_TYPE_EXPORTS = Object.freeze({
  "bytes.ts": new Set(),
  "mm.ts": new Set(["MmDecodeError"]),
  "model.ts": new Set(),
  "rfq.ts": new Set([
    "BroadcastRfqRequest", "QuoteResponse", "RfqLeg", "RfqLegType", "RfqLegWire",
    "RfqLegWireDecodeError", "TakerMetadata",
  ]),
  "serde.generated.ts": new Set(),
  "serde.ts": new Set(["SerdeDecodeError"]),
  "taker.ts": new Set([
    "OrderLeg", "SignedOrder", "SignedOrderError", "TakerSignError",
  ]),
  "types.ts": new Set([
    "Address", "Amount", "ArithmeticError", "Asset", "ClientQuoteId",
    "ContestId", "Direction", "Duration", "MarketId", "MarketStatus", "MarketType",
    "MathError", "Odds", "OrderType", "Outcome", "PositionId",
    "QuoteId", "RequestId", "Timestamp", "TradingChannel", "UserId", "UserTier", "UuidId",
  ]),
  "uuid.ts": new Set(),
  "ws.ts": new Set([
    "ClientMessage", "QuoteResultStatus", "RfqSubscription", "ServerMessage",
  ]),
});
const PUBLIC_TYPESCRIPT_INDEX_MODULES = new Set([
  "./api.js", "./bytes.js", "./mm.js", "./model.js", "./rfq.js", "./serde.js",
  "./taker.js", "./types.js", "./ws.js",
]);
const PUBLIC_TYPESCRIPT_PACKAGE_EXPORTS = Object.freeze({
  ".": Object.freeze({ types: "./dist/src/index.d.ts", import: "./dist/src/index.js" }),
  "./api": Object.freeze({ types: "./dist/src/api.d.ts", import: "./dist/src/api.js" }),
  "./mm": Object.freeze({ types: "./dist/src/mm.d.ts", import: "./dist/src/mm.js" }),
  "./rfq": Object.freeze({ types: "./dist/src/rfq.d.ts", import: "./dist/src/rfq.js" }),
  "./taker": Object.freeze({ types: "./dist/src/taker.d.ts", import: "./dist/src/taker.js" }),
  "./types": Object.freeze({ types: "./dist/src/types.d.ts", import: "./dist/src/types.js" }),
  "./ws": Object.freeze({ types: "./dist/src/ws.d.ts", import: "./dist/src/ws.js" }),
});
const PUBLIC_TYPESCRIPT_PACKAGE_FILES = new Set(["CUSTOM_CLIENTS.md", "dist/src"]);
// Crates publish their complete Rust source. Lock the exact source tree so a
// new method, free item, private field, comment, or file cannot enter the
// external package without an explicit boundary review.
const PUBLIC_RUST_SOURCE_SHA256 = "bc6ba8effbd99f961c506362b87bc543fb9ab59ada3a9881e1dfd67b8396d7c1";
const PUBLIC_RUST_RELEASE_FILES_SHA256 = "9a86a4777c9ff0b453d0d123b70f4720f9ce3673c283224571e986ce1175af08";
// These hashes cover normalized emitted declarations, not implementations or
// formatting. Any published signature change therefore needs an explicit
// boundary review, including a field added to an already approved DTO.
const PUBLIC_TYPESCRIPT_DECLARATION_SHA256 = Object.freeze({
  "api.ts": "96cad496ae0641e6b4d0add9ca2f5e5831c41376785a259c896ef5e36e9837a2",
  "bytes.ts": "5405fdfcd96c23dc7a3f6a15c508dfd0cdcaa51c94ea1dca2bf2df3b130902c9",
  "mm.ts": "7ba066db6c59fa31db33fa2f7a0b4f1681db38055289cb2a06e1a6170afd9f61",
  "model.ts": "1340a51bb7996864d0d51eb68ca9c3c4e9665cc81b9f6d6c83df372e83d04226",
  "rfq.ts": "ef31805a7527f17fcad61bdc226b81c6039241b9956b2bc492a4d0df03b05d9f",
  "serde.ts": "3bca99d83f0c767755c9c2bfe2e71cdce4d9e71e82c15d4a410b872957f8bb6a",
  "taker.ts": "b63f2e777459d9b9dd6d7fefa90afb1d0fe8e764cdeec8e86aa65cf503757724",
  "types.ts": "143173d079ebb9019ef3cacbf0d2bd0e7e344ac15c773aeb98312284e0b5a023",
  "uuid.ts": "2449a993c5d1f8d900ca56505f336cfde2f0375e35ea2e9a9c201eff030a8789",
  "ws.ts": "80285ca74375b17acefac833e5727b3888e455c6bea3c59edad772802d6331e8",
});
const PUBLIC_TYPESCRIPT_RUNTIME_SHA256 = "59e66aabbcdd4571d86c2fd1d7c2c460efc41e230a1f77af5429a9124af762a8";
const PUBLIC_TYPESCRIPT_BUILD_CONFIG_SHA256 = "c0e38372142046682e2d1840ec563efbd5d9bbaf5db8a4278eafdda6d3352117";
let emittedTypeScriptPackageOutputs;

const publicRustTypeNames = new Set();
const publicRustApiTypeNames = new Set();
const publicRustApiValueExports = new Set();

for (const file of readdirSync(API_DIR).filter((name) => name.endsWith(".rs") && name !== "wire_int.rs")) {
  const source = readFileSync(join(API_DIR, file), "utf8");
  collectRustPublicTypeNames(source, publicRustTypeNames);
  collectRustPublicTypeNames(source, publicRustApiTypeNames);
  collectRustPublicApiValueExports(source, publicRustApiValueExports);
  parseDeclarations(source);
}
const apiSchemaNames = new Set(Object.keys(schemas));
for (const file of readdirSync(TYPES_DIR).filter((name) => name.endsWith(".rs") && name !== "mod.rs")) {
  const source = readFileSync(join(TYPES_DIR, file), "utf8");
  collectRustPublicTypeNames(source, publicRustTypeNames);
  parseDeclarations(source);
}
const wsSource = readFileSync(join(ROOT, "rust/src/ws.rs"), "utf8");
collectRustPublicTypeNames(wsSource, publicRustTypeNames);
parseDeclarations(wsSource);
for (const path of ["rust/src/mm.rs", "rust/src/taker.rs"])
  collectRustPublicTypeNames(readFileSync(join(ROOT, path), "utf8"), publicRustTypeNames);
materializeSerdeDefaults();
const protocolNames = new Set(Object.keys(schemas));
validateClosedNonSerdeInventory(protocolNames);
validateApiDeclarations(
  readFileSync(join(ROOT, "typescript/src/api.ts"), "utf8"),
  apiSchemaNames,
);
validateSupplementalTypeScriptInventory();
validateTypeScriptBuildConfig();
if (schemas.UnsignedRfqOrderRequest[1].order_type[2] !== "d2")
  throw new Error("default_order_type must decode to 2");
const openApiDocument = JSON.parse(readFileSync(OPENAPI_PATH, "utf8"));
validateCurrentOpenApi(openApiDocument, protocolNames);
validateClosedProtocolInventory(openApiDocument, protocolNames);
validateSupplementalTypeScriptDeclarationShapes();
validateSupplementalTypeScriptRuntime();
validateRustPackageSourceIntegrity();
validateRustReleaseFiles();
for (const [name, schema] of Object.entries(schemas)) {
  if (schema[0] === "o" && schema[2] && Object.values(schema[1]).some((field) => field[2] === "f"))
    throw new Error(`${name} combines flatten with deny_unknown_fields`);
}

const reachable = assertResolved(Object.keys(schemas));
const runtimeSchemas = Object.fromEntries([...reachable].map((name) => [name, schemas[name]]));
if (surfaceKind === "generate") {
  writeFileSync(join(ROOT, "typescript/src/serde.generated.ts"), [
    "// Generated from Rust serde declarations. Do not edit.",
    `export const API_SCHEMAS: Record<string, unknown> = JSON.parse(${JSON.stringify(JSON.stringify(runtimeSchemas))});`,
    "",
  ].join("\n"));
}

function collectRustPublicTypeNames(source, names) {
  for (const match of source.matchAll(/^pub\s+(?:struct|enum|type)\s+([A-Za-z0-9_]+)/gmu))
    names.add(match[1]);
}

function collectRustPublicApiValueExports(source, values) {
  for (const match of source.matchAll(/^pub\s+const\s+([A-Za-z0-9_]+)/gmu))
    values.add(match[1]);
  for (const match of source.matchAll(/^pub\s+(?:async\s+)?fn\s+([A-Za-z0-9_]+)/gmu)) {
    const name = match[1].replace(/_([a-z0-9])/gu, (_, character) => character.toUpperCase());
    values.add(name);
  }
}

function validateClosedNonSerdeInventory(protocolNames) {
  const actual = new Set([...publicRustTypeNames].filter((name) => !protocolNames.has(name)));
  validateNameInventory(
    "closed non-Serde Rust protocol inventory",
    actual,
    new Set(PUBLIC_PROTOCOL_NON_SERDE_TYPES),
  );
}

function typeDeclarationNames(source, fileName) {
  const file = ts.createSourceFile(fileName, source, ts.ScriptTarget.Latest, true);
  const declarations = file.statements.filter((statement) =>
    ts.isInterfaceDeclaration(statement)
    || ts.isTypeAliasDeclaration(statement)
    || ts.isClassDeclaration(statement)
    || ts.isEnumDeclaration(statement));
  const names = declarations.map((statement) => statement.name.text);
  const duplicates = [...new Set(names.filter((name, index) => names.indexOf(name) !== index))].sort();
  if (duplicates.length)
    throw new Error(`${fileName} has duplicate type declarations: ${duplicates.join(", ")}`);
  return new Set(names);
}

function exportedDeclarationNamespaces(source, fileName) {
  const file = ts.createSourceFile(fileName, source, ts.ScriptTarget.Latest, true);
  const types = new Set();
  const values = new Set();
  for (const statement of file.statements) {
    if (ts.isExportDeclaration(statement)) {
      if (statement.exportClause && ts.isNamedExports(statement.exportClause))
        statement.exportClause.elements.forEach((element) => values.add(element.name.text));
      continue;
    }
    if (!statement.modifiers?.some((modifier) => modifier.kind === ts.SyntaxKind.ExportKeyword))
      continue;
    if (ts.isInterfaceDeclaration(statement) || ts.isTypeAliasDeclaration(statement)) {
      types.add(statement.name.text);
    } else if (ts.isClassDeclaration(statement) || ts.isEnumDeclaration(statement)) {
      types.add(statement.name.text);
      values.add(statement.name.text);
    } else if (ts.isModuleDeclaration(statement)) {
      types.add(statement.name.text);
      values.add(statement.name.text);
    } else if (ts.isVariableStatement(statement)) {
      for (const declaration of statement.declarationList.declarations) {
        if (!ts.isIdentifier(declaration.name))
          throw new Error(`${fileName} has an unsupported exported binding`);
        values.add(declaration.name.text);
      }
    } else if (ts.isFunctionDeclaration(statement) && statement.name) {
      values.add(statement.name.text);
    } else {
      throw new Error(`${fileName} has an unsupported exported declaration`);
    }
  }
  return { types, values };
}

function validateNameInventory(label, actual, expected) {
  const extra = [...actual].filter((name) => !expected.has(name)).sort();
  const missing = [...expected].filter((name) => !actual.has(name)).sort();
  if (extra.length || missing.length) {
    throw new Error(
      `${label} drift: extra=[${extra.join(", ")}], missing=[${missing.join(", ")}]`,
    );
  }
}

function collectRelativeFiles(root, include) {
  const files = [];
  const collect = (directory, relativeDirectory) => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name);
      const relative = relativeDirectory
        ? `${relativeDirectory}/${entry.name}`
        : entry.name;
      if (entry.isDirectory()) collect(path, relative);
      else if (entry.isFile()) {
        if (include(entry.name)) files.push([relative, path]);
      } else {
        throw new Error(`unsupported package source entry: ${relative}`);
      }
    }
  };
  collect(root, "");
  return files.sort(([left], [right]) => left.localeCompare(right));
}

function validateSupplementalTypeScriptInventory() {
  const sourceDir = join(ROOT, "typescript/src");
  const expectedFiles = new Set(["api.ts", ...Object.keys(PUBLIC_TYPESCRIPT_TYPE_DECLARATIONS)]);
  const sourceFiles = collectRelativeFiles(sourceDir, () => true);
  const actualFiles = new Set(
    (surfaceKind === "packed"
      ? sourceFiles.filter(([relative]) => relative.endsWith(".ts"))
      : sourceFiles)
      .map(([relative]) => relative),
  );
  validateNameInventory("closed TypeScript source module inventory", actualFiles, expectedFiles);

  for (const [fileName, expectedNames] of Object.entries(PUBLIC_TYPESCRIPT_TYPE_DECLARATIONS)) {
    const source = readFileSync(join(sourceDir, fileName), "utf8");
    const actual = typeDeclarationNames(source, fileName);
    const expected = new Set(expectedNames);
    const optional = PUBLIC_TYPESCRIPT_OPTIONAL_DECLARATION_TYPES[fileName] ?? new Set();
    const extra = [...actual].filter((name) => !expected.has(name)).sort();
    const missing = [...expected]
      .filter((name) => !actual.has(name) && !optional.has(name))
      .sort();
    if (extra.length || missing.length) {
      throw new Error(
        `closed TypeScript ${fileName} type inventory drift: `
        + `extra=[${extra.join(", ")}], missing=[${missing.join(", ")}]`,
      );
    }
  }

  for (const [fileName, expectedNames] of Object.entries(PUBLIC_TYPESCRIPT_MODULE_EXPORTS)) {
    const source = readFileSync(join(sourceDir, fileName), "utf8");
    const actualNamespaces = exportedDeclarationNamespaces(source, fileName);
    const optionalTypes = PUBLIC_TYPESCRIPT_OPTIONAL_DECLARATION_TYPES[fileName] ?? new Set();
    const expectedTypes = new Set(
      (PUBLIC_TYPESCRIPT_TYPE_DECLARATIONS[fileName] ?? [])
        .filter((name) => !optionalTypes.has(name)),
    );
    const runtimeTypes = PUBLIC_TYPESCRIPT_RUNTIME_TYPE_EXPORTS[fileName] ?? new Set();
    const expectedValues = new Set(
      expectedNames.filter((name) => !expectedTypes.has(name) || runtimeTypes.has(name)),
    );
    validateNameInventory(
      `closed TypeScript ${fileName} type export inventory`,
      actualNamespaces.types,
      expectedTypes,
    );
    validateNameInventory(
      `closed TypeScript ${fileName} value export inventory`,
      actualNamespaces.values,
      expectedValues,
    );
  }

  const indexSource = readFileSync(join(ROOT, "typescript/src/index.ts"), "utf8");
  const indexFile = ts.createSourceFile("index.ts", indexSource, ts.ScriptTarget.Latest, true);
  const modules = new Set();
  for (const statement of indexFile.statements) {
    if (
      !ts.isExportDeclaration(statement)
      || statement.exportClause
      || !statement.moduleSpecifier
      || !ts.isStringLiteral(statement.moduleSpecifier)
    ) throw new Error("TypeScript index.ts must contain only approved export-star declarations");
    modules.add(statement.moduleSpecifier.text);
  }
  validateNameInventory(
    "closed TypeScript index module inventory",
    modules,
    PUBLIC_TYPESCRIPT_INDEX_MODULES,
  );

  const packageJson = JSON.parse(readFileSync(join(ROOT, "typescript/package.json"), "utf8"));
  if (
    packageJson.main !== "./dist/src/index.js"
    || packageJson.types !== "./dist/src/index.d.ts"
  ) throw new Error("closed TypeScript package root targets drifted");
  const packageFiles = Array.isArray(packageJson.files) ? packageJson.files : [];
  if (new Set(packageFiles).size !== packageFiles.length) {
    throw new Error("closed TypeScript package files contain duplicates");
  }
  validateNameInventory(
    "closed TypeScript package file inventory",
    new Set(packageFiles),
    PUBLIC_TYPESCRIPT_PACKAGE_FILES,
  );
  validateNameInventory(
    "closed TypeScript package subpath inventory",
    new Set(Object.keys(packageJson.exports ?? {})),
    new Set(Object.keys(PUBLIC_TYPESCRIPT_PACKAGE_EXPORTS)),
  );
  for (const [name, expected] of Object.entries(PUBLIC_TYPESCRIPT_PACKAGE_EXPORTS)) {
    const actual = packageJson.exports?.[name];
    if (
      !actual
      || Object.keys(actual).length !== Object.keys(expected).length
      || Object.entries(expected).some(([key, value]) => actual[key] !== value)
    ) throw new Error(`closed TypeScript package target inventory drift: ${name}`);
  }
}

function validateTypeScriptBuildConfig() {
  if (surfaceKind === "packed") return;
  const configFiles = [
    "typescript/CUSTOM_CLIENTS.md",
    "typescript/LICENSE.txt",
    "typescript/README.md",
    "typescript/package.json",
    "typescript/tsconfig.json",
  ];
  const hash = createHash("sha256");
  for (const relative of configFiles) {
    hash.update(relative);
    hash.update("\0");
    hash.update(readFileSync(join(ROOT, relative)));
    hash.update("\0");
  }
  const actual = hash.digest("hex");
  if (actual !== PUBLIC_TYPESCRIPT_BUILD_CONFIG_SHA256) {
    throw new Error(`closed TypeScript build config hash drift: actual=${actual}`);
  }
}

function validateSupplementalTypeScriptDeclarationShapes() {
  const sourceDir = join(ROOT, "typescript/src");
  const declarations = surfaceKind === "packed"
    ? new Map(Object.keys(PUBLIC_TYPESCRIPT_DECLARATION_SHA256).map((fileName) => [
      fileName,
      readFileSync(join(sourceDir, fileName), "utf8"),
    ]))
    : emitTypeScriptPackageOutputs(sourceDir);
  const drifts = [];
  for (const [fileName, expected] of Object.entries(PUBLIC_TYPESCRIPT_DECLARATION_SHA256)) {
    const declaration = declarations.get(fileName.replace(/\.ts$/u, ".d.ts"))
      ?? declarations.get(fileName);
    if (declaration === undefined)
      throw new Error(`TypeScript declaration emit is missing ${fileName}`);
    const normalized = normalizePublicTypeScriptDeclaration(declaration, fileName);
    const actual = createHash("sha256").update(normalized).digest("hex");
    if (actual !== expected) drifts.push(`${fileName}=${actual}`);
  }
  if (drifts.length) {
    throw new Error(
      "closed TypeScript public declaration shape drift: " + drifts.join(", "),
    );
  }
}

function validateSupplementalTypeScriptRuntime() {
  const sourceDir = join(ROOT, "typescript/src");
  const runtimeFiles = surfaceKind === "packed"
    ? new Map(collectRelativeFiles(sourceDir, (fileName) => fileName.endsWith(".js"))
      .map(([relative, path]) => [relative, readFileSync(path, "utf8")]))
    : new Map([...emitTypeScriptPackageOutputs(sourceDir)]
      .filter(([fileName]) => fileName.endsWith(".js")));
  const expectedFiles = new Set(
    ["api.ts", ...Object.keys(PUBLIC_TYPESCRIPT_TYPE_DECLARATIONS)]
      .map((fileName) => fileName.replace(/\.ts$/u, ".js")),
  );
  validateNameInventory(
    "closed TypeScript runtime module inventory",
    new Set(runtimeFiles.keys()),
    expectedFiles,
  );
  const hash = createHash("sha256");
  for (const [fileName, source] of [...runtimeFiles].sort(([left], [right]) => (
    left.localeCompare(right)
  ))) {
    hash.update(fileName);
    hash.update("\0");
    hash.update(source);
    hash.update("\0");
  }
  const actual = hash.digest("hex");
  if (actual !== PUBLIC_TYPESCRIPT_RUNTIME_SHA256) {
    throw new Error(`closed TypeScript runtime hash drift: actual=${actual}`);
  }
}

function validateRustPackageSourceIntegrity() {
  const sourceRoot = join(ROOT, "rust/src");
  const files = collectRelativeFiles(sourceRoot, () => true);
  const hash = createHash("sha256");
  for (const [relative, path] of files) {
    hash.update(`rust/src/${relative}`);
    hash.update("\0");
    hash.update(readFileSync(path));
    hash.update("\0");
  }
  const actual = hash.digest("hex");
  if (actual !== PUBLIC_RUST_SOURCE_SHA256) {
    throw new Error(`closed Rust package source hash drift: actual=${actual}`);
  }
}

function validateRustReleaseFiles() {
  if (surfaceKind === "packed") return;
  const releaseFiles = [
    "rust/CUSTOM_CLIENTS.md",
    "rust/Cargo.toml",
    "rust/LICENSE.txt",
    "rust/README.md",
  ];
  const hash = createHash("sha256");
  for (const relative of releaseFiles) {
    const path = join(ROOT, relative);
    if (!existsSync(path)) throw new Error(`missing Rust release file: ${relative}`);
    hash.update(relative);
    hash.update("\0");
    hash.update(readFileSync(path));
    hash.update("\0");
  }
  const actual = hash.digest("hex");
  if (actual !== PUBLIC_RUST_RELEASE_FILES_SHA256) {
    throw new Error(`closed Rust release file hash drift: actual=${actual}`);
  }
}

function emitTypeScriptPackageOutputs(sourceDir) {
  if (emittedTypeScriptPackageOutputs !== undefined)
    return emittedTypeScriptPackageOutputs;
  const options = {
    declaration: true,
    declarationMap: false,
    emitDeclarationOnly: false,
    esModuleInterop: true,
    module: ts.ModuleKind.NodeNext,
    moduleResolution: ts.ModuleResolutionKind.NodeNext,
    noEmit: false,
    outDir: join(ROOT, "typescript/.public-surface-declarations"),
    rootDir: sourceDir,
    skipLibCheck: true,
    strict: true,
    target: ts.ScriptTarget.ES2022,
    typeRoots: [join(ROOT, "typescript/node_modules/@types")],
    types: ["node"],
  };
  const rootNames = collectRelativeFiles(sourceDir, (fileName) => fileName.endsWith(".ts"))
    .map(([, path]) => path);
  const outputs = new Map();
  const host = ts.createCompilerHost(options);
  host.writeFile = (path, contents) => {
    outputs.set(basename(path), contents);
  };
  const program = ts.createProgram(rootNames, options, host);
  const diagnostics = ts.getPreEmitDiagnostics(program);
  if (diagnostics.length) {
    throw new Error(ts.formatDiagnostics(diagnostics, {
      getCanonicalFileName: (fileName) => fileName,
      getCurrentDirectory: () => sourceDir,
      getNewLine: () => "\n",
    }));
  }
  const result = program.emit();
  if (result.emitSkipped)
    throw new Error("TypeScript public package emit was skipped");
  emittedTypeScriptPackageOutputs = outputs;
  return outputs;
}

function normalizePublicTypeScriptDeclaration(source, fileName) {
  const file = ts.createSourceFile(fileName, source, ts.ScriptTarget.Latest, true);
  const transformed = ts.transform(file, [(context) => (root) => {
    const visit = (node) => {
      if (ts.isClassDeclaration(node)) {
        const members = node.members
          // ECMAScript private identifiers emit only as the opaque `#private`
          // marker. Named private/protected members still appear in the packed
          // declaration and remain part of the audited artifact.
          .filter((member) => !member.name || !ts.isPrivateIdentifier(member.name))
          .map((member) => ts.visitEachChild(member, visit, context));
        return ts.factory.updateClassDeclaration(
          node,
          node.modifiers,
          node.name,
          node.typeParameters,
          node.heritageClauses,
          members,
        );
      }
      return ts.visitEachChild(node, visit, context);
    };
    return ts.visitNode(root, visit);
  }]);
  const printer = ts.createPrinter({
    newLine: ts.NewLineKind.LineFeed,
    removeComments: false,
  });
  const normalized = printer.printFile(transformed.transformed[0]).trim();
  transformed.dispose();
  return `${normalized}\n`;
}

function validateClosedProtocolInventory(document, protocolNames) {
  const expected = new Set(PUBLIC_PROTOCOL_SUPPLEMENTAL_SCHEMAS);
  for (const name of Object.keys(document.components?.schemas ?? {})) expected.add(name);
  const extra = [...protocolNames].filter((name) => !expected.has(name)).sort();
  const missing = [...expected].filter((name) => !protocolNames.has(name)).sort();
  if (extra.length || missing.length) {
    throw new Error(
      `closed public protocol inventory drift: extra=[${extra.join(", ")}], `
      + `missing=[${missing.join(", ")}]`,
    );
  }
}

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
    else if (!["deserialize_required_nullable_u64", "status_list_query"].includes(adapter))
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
  const roots = new Set(["SessionResponse"]);

  validatePublicOpenApiBoundary();

  // Every operation in this fixture is explicitly public. New private server
  // routes cannot enter package generation through a default-allow rule.
  for (const [path, pathItem] of Object.entries(document.paths ?? {})) {
    for (const [method, operation] of Object.entries(pathItem)) {
      if (!/^(?:delete|get|head|options|patch|post|put|trace)$/u.test(method)) continue;
      collectJsonSchemaRoots(operation.requestBody, roots);
      for (const response of Object.values(operation.responses ?? {}))
        collectJsonSchemaRoots(response, roots);
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
    .filter((name) => !protocolNames.has(name))
    .sort();
  if (missingReachable.length) {
    throw new Error(
      `Rust protocol is missing schemas reachable from current supported OpenAPI contracts: `
      + missingReachable.join(", "),
    );
  }

  const schemaDrifts = [];
  for (const name of [...reachable].sort()) {
    const rustFields = rustObjectFields(name);
    const openApiFields = openApiObjectFields(components[name], components);
    if (rustFields && openApiFields) {
      const rustNames = new Set(rustFields.keys());
      const openApiNames = new Set(openApiFields.keys());
      if (!sameSet(rustNames, openApiNames)) {
        schemaDrifts.push(
          `${name} field drift between Rust protocol and current OpenAPI: `
          + `Rust=[${[...rustNames].sort().join(", ")}], `
          + `OpenAPI=[${[...openApiNames].sort().join(", ")}]`,
        );
      }

      const rustRequired = requiredFieldNames(rustFields);
      const openApiRequired = requiredFieldNames(openApiFields);
      const rustOnly = new Set([...rustRequired].filter((field) => !openApiRequired.has(field)));
      const openApiOnly = new Set([...openApiRequired].filter((field) => !rustRequired.has(field)));
      const expectedOpenApiOnly = openApiOnlyRequiredFieldExceptions.get(name) ?? new Set();
      if (rustOnly.size || !sameSet(openApiOnly, expectedOpenApiOnly)) {
        schemaDrifts.push(
          `${name} required-field drift between Rust protocol and current OpenAPI: `
          + `Rust=[${[...rustRequired].sort().join(", ")}], `
          + `OpenAPI=[${[...openApiRequired].sort().join(", ")}]`,
        );
      }
    }

    const rustEnum = schemas[name]?.[0] === "v" ? schemas[name][1] : undefined;
    const openApiEnum = openApiEnumValues(components[name], components);
    if (rustEnum && openApiEnum && JSON.stringify(rustEnum) !== JSON.stringify(openApiEnum))
      schemaDrifts.push(`${name} enum variants drifted between Rust protocol and current OpenAPI`);
  }
  const unreachableRequirednessExceptions = [...openApiOnlyRequiredFieldExceptions.keys()]
    .filter((name) => !reachable.has(name));
  if (unreachableRequirednessExceptions.length) {
    schemaDrifts.push(
      `required-field compatibility exceptions are unreachable: `
      + unreachableRequirednessExceptions.sort().join(", "),
    );
  }
  if (schemaDrifts.length) throw new Error(schemaDrifts.join("\n"));

  // OpenAPI preserves route-local query fields but not their Rust DTO names.
  // Keep every supported query operation bound explicitly so a new route cannot
  // silently evade requiredness and scalar-type validation.
  const queryOperations = [
    ["PublicMarketsRawQuery", "/v1/markets", "get"],
    ["RecentResolutionsQuery", "/v1/mm/recent_resolutions", "get"],
    ["PnlHistoryScopedQuery", "/v1/portfolio/pnl", "get"],
    ["PositionsByMarketsQuery", "/v1/portfolio/positions", "get"],
    ["PositionsQuery", "/v1/positions", "get"],
    ["MarketCurrentQuery", "/v1/price-markets/current", "get"],
    ["MarketLookupQuery", "/v1/price-markets/lookup", "get"],
    ["UserTransactionsRawQuery", "/v1/user/transactions", "get"],
    ["ConfirmPositionQuery", "/v1/user/confirm_position", "post"],
    ["HandleAvailabilityQuery", "/v1/user/profile/check-handle", "get"],
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

  function validatePublicOpenApiBoundary() {
    const expectedOperations = new Set(PUBLIC_OPENAPI_OPERATIONS);
    const expectedPaths = new Set(PUBLIC_OPENAPI_OPERATIONS.map((key) => key.slice(key.indexOf(" ") + 1)));
    const actualOperations = new Set();
    const actualPaths = new Set(Object.keys(document.paths ?? {}));
    const pathItemMembers = new Set([
      "$ref",
      "delete",
      "description",
      "get",
      "head",
      "options",
      "parameters",
      "patch",
      "post",
      "put",
      "servers",
      "summary",
      "trace",
    ]);
    for (const [path, pathItem] of Object.entries(document.paths ?? {})) {
      for (const method of Object.keys(pathItem)) {
        if (!pathItemMembers.has(method))
          throw new Error(`public OpenAPI path item contains unsupported member ${path}.${method}`);
        if (/^(?:delete|get|head|options|patch|post|put|trace)$/u.test(method))
          actualOperations.add(`${method.toUpperCase()} ${path}`);
      }
    }
    if (!sameSet(expectedPaths, actualPaths) || !sameSet(expectedOperations, actualOperations)) {
      const extra = [...actualOperations].filter((key) => !expectedOperations.has(key)).sort();
      const missing = [...expectedOperations].filter((key) => !actualOperations.has(key)).sort();
      throw new Error(
        `public OpenAPI allowlist drift: extra=[${extra.join(", ")}], missing=[${missing.join(", ")}]`,
      );
    }

    const expectedSections = new Set(Object.keys(PUBLIC_OPENAPI_COMPONENT_NAMES));
    const actualSections = new Set(Object.keys(document.components ?? {}));
    if (!sameSet(expectedSections, actualSections)) {
      throw new Error(
        `public OpenAPI component section drift: expected=[${[...expectedSections].sort().join(", ")}], `
        + `actual=[${[...actualSections].sort().join(", ")}]`,
      );
    }
    for (const [section, expectedNames] of Object.entries(PUBLIC_OPENAPI_COMPONENT_NAMES)) {
      const expected = new Set(expectedNames);
      const actual = new Set(Object.keys(document.components?.[section] ?? {}));
      if (!sameSet(expected, actual)) {
        const extra = [...actual].filter((name) => !expected.has(name)).sort();
        const missing = [...expected].filter((name) => !actual.has(name)).sort();
        throw new Error(
          `public OpenAPI ${section} allowlist drift: `
          + `extra=[${extra.join(", ")}], missing=[${missing.join(", ")}]`,
        );
      }
    }
    validateUnsupportedOpenApiSurfaces(document);
    const rendered = JSON.stringify(document);
    for (const reference of [
      "/private/",
      "/Users/",
      "file://",
      "fixtures/api/",
      "github.com/Longshot-Labs/longshot",
      "localhost",
      "127.0.0.1",
    ]) {
      if (rendered.includes(reference))
        throw new Error(`public OpenAPI contains private source reference: ${reference}`);
    }
  }

  function collectJsonSchemaRoots(container, output) {
    const resolved = resolveOpenApiDocumentRef(container, document);
    for (const [mediaType, media] of Object.entries(resolved?.content ?? {})) {
      if (mediaType === "application/json" || mediaType.endsWith("+json"))
        collectOpenApiRootRefs(media.schema, output);
    }
  }
}

function validateUnsupportedOpenApiSurfaces(document) {
  if (Object.hasOwn(document, "webhooks"))
    throw new Error("public OpenAPI webhooks are not classified");
  for (const [path, pathItem] of Object.entries(document.paths ?? {})) {
    for (const [method, operation] of Object.entries(pathItem)) {
      if (!/^(?:delete|get|head|options|patch|post|put|trace)$/u.test(method)) continue;
      if (Object.hasOwn(operation, "callbacks"))
        throw new Error(`public OpenAPI callbacks are not classified: ${method.toUpperCase()} ${path}`);
      for (const [status, response] of Object.entries(operation.responses ?? {})) {
        if (response && typeof response === "object" && Object.hasOwn(response, "links")) {
          throw new Error(
            `public OpenAPI response links are not classified: ${method.toUpperCase()} ${path} ${status}`,
          );
        }
      }
    }
  }

  walk(document);

  function walk(value) {
    if (Array.isArray(value)) {
      value.forEach(walk);
      return;
    }
    if (!value || typeof value !== "object") return;
    if (Object.hasOwn(value, "$ref")) {
      const match = typeof value.$ref === "string"
        ? value.$ref.match(/^#\/components\/([^/]+)\/([^/]+)$/u)
        : undefined;
      if (!match)
        throw new Error(`public OpenAPI contains unsupported external or nested reference: ${value.$ref}`);
      if (!document.components?.[match[1]]?.[match[2]])
        throw new Error(`public OpenAPI reference is unresolved: ${value.$ref}`);
    }
    Object.values(value).forEach(walk);
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

function descriptorRefName(descriptor) {
  if (!Array.isArray(descriptor)) return undefined;
  if (descriptor[0] === "r") return descriptor[1];
  if (descriptor[0] === "n") return descriptorRefName(descriptor[1]);
  return undefined;
}

function openApiObjectFields(schema, components, stack = new Set()) {
  if (!schema || typeof schema !== "object") return undefined;
  const ref = openApiRefName(schema.$ref);
  if (ref) {
    if (stack.has(ref)) return new Map();
    stack.add(ref);
    const fields = openApiObjectFields(components[ref], components, stack);
    stack.delete(ref);
    return fields;
  }
  const fields = new Map(
    Object.keys(schema.properties ?? {}).map((field) => [field, { required: false }]),
  );
  let hasObjectShape = Boolean(schema.properties || schema.required || schema.type === "object");
  for (const part of schema.allOf ?? []) {
    const nested = openApiObjectFields(part, components, stack);
    if (nested) {
      hasObjectShape = true;
      nested.forEach((value, field) => {
        fields.set(field, { required: value.required || fields.get(field)?.required === true });
      });
    }
  }
  for (const field of schema.required ?? []) fields.set(field, { required: true });
  return hasObjectShape ? fields : undefined;
}

function requiredFieldNames(fields) {
  return new Set(
    [...fields]
      .filter(([, field]) => field.required)
      .map(([name]) => name),
  );
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
  validateNameInventory(
    "closed TypeScript api.ts type inventory",
    typeDeclarationNames(source, "api.ts"),
    publicRustApiTypeNames,
  );
  const namespaces = exportedDeclarationNamespaces(source, "api.ts");
  validateNameInventory(
    "closed TypeScript api.ts type export inventory",
    namespaces.types,
    publicRustApiTypeNames,
  );
  const enumValues = [...names].filter((name) =>
    schemas[name]?.[0] === "v" && !PUBLIC_TYPESCRIPT_TYPE_ONLY_STRING_ENUMS.has(name));
  validateNameInventory(
    "closed TypeScript api.ts value export inventory",
    namespaces.values,
    new Set([
      ...publicRustApiValueExports,
      ...PUBLIC_TYPESCRIPT_API_HELPERS,
      ...enumValues,
    ]),
  );
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
