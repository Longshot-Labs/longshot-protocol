import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const REPO_ROOT = join(process.cwd(), "..");
const RUST_API_DIR = join(REPO_ROOT, "rust/src/api");
const TS_API = readFileSync(join(process.cwd(), "src/api.ts"), "utf8");
const RUST_TOP_LEVEL_FILES = [
  "rust/src/taker.rs",
  "rust/src/ws.rs",
  ...["ids.rs", "market.rs", "primitives.rs", "rfq.rs"].map((file) => `rust/src/types/${file}`),
];
const TS_TOP_LEVEL = ["taker.ts", "types.ts", "rfq.ts", "ws.ts"]
  .map((file) => readFileSync(join(process.cwd(), "src", file), "utf8"))
  .join("\n");

function rustApiFiles(): string[] {
  return readdirSync(RUST_API_DIR)
    .filter((file) => file.endsWith(".rs") && file !== "mod.rs" && file !== "wire_int.rs")
    .map((file) => join(RUST_API_DIR, file));
}

function exportedTsNames(source: string): Set<string> {
  const names = new Set<string>();
  for (const match of source.matchAll(/^export\s+(?:interface|type|const|class|enum|function)\s+([A-Za-z0-9_]+)/gm)) {
    names.add(match[1]);
  }
  for (const match of source.matchAll(/^export\s+\{\s*([A-Za-z0-9_]+)\s+as\s+([A-Za-z0-9_]+)\s*\}/gm)) {
    names.add(match[2]);
  }
  return names;
}

function rustPublicTypeNames(source: string): string[] {
  const hidden = new Set(
    [...source.matchAll(/#\[doc\(hidden\)\](?:\s*#\[[^\]]*\])*\s*pub\s+(?:struct|enum)\s+(\w+)/gu)]
      .map((match) => match[1]),
  );
  return [...source.matchAll(/^pub\s+(?:struct|enum)\s+(\w+)/gmu)]
    .map((match) => match[1])
    .filter((name) => !hidden.has(name));
}

function rustApiPublicDeclarations(): Set<string> {
  const names = new Set<string>();
  for (const file of rustApiFiles()) {
    const text = readFileSync(file, "utf8");
    for (const match of text.matchAll(/^pub\s+(?:struct|enum|type|const)\s+([A-Za-z0-9_]+)/gm)) {
      names.add(match[1]);
    }
  }
  return names;
}

function rustApiPublicConstants(): Map<string, number> {
  const constants = new Map<string, number>();
  for (const file of rustApiFiles()) {
    const text = readFileSync(file, "utf8");
    for (const match of text.matchAll(/^pub\s+const\s+([A-Za-z0-9_]+)\s*:\s*[^=]+=\s*([0-9_]+);/gm)) {
      constants.set(match[1], Number(match[2].replaceAll("_", "")));
    }
  }
  return constants;
}

test("api exports every public Rust API declaration", () => {
  const missing = [...rustApiPublicDeclarations()]
    .filter((name) => !exportedTsNames(TS_API).has(name))
    .sort();
  assert.deepEqual(missing, []);
});

test("top-level protocol exports every public Rust type", () => {
  const rustNames = new Set(
    RUST_TOP_LEVEL_FILES.flatMap((file) =>
      rustPublicTypeNames(readFileSync(join(REPO_ROOT, file), "utf8")),
    ),
  );
  const missing = [...rustNames].filter((name) => !exportedTsNames(TS_TOP_LEVEL).has(name)).sort();
  assert.deepEqual(missing, []);
});

test("api constants match Rust values", () => {
  const mismatches: Record<string, { rust: number; typescript?: number }> = {};
  for (const [name, rustValue] of rustApiPublicConstants()) {
    const tsValue = TS_API.match(new RegExp(`export const ${name} = ([0-9_]+) as const;`))?.[1];
    const parsed = tsValue === undefined ? undefined : Number(tsValue.replaceAll("_", ""));
    if (parsed !== rustValue) mismatches[name] = { rust: rustValue, typescript: parsed };
  }
  assert.deepEqual(mismatches, {});
});

test("aggregate fantasy notification replaces legacy variants", () => {
  const union = TS_API.match(/export type NotificationPayload =([\s\S]*?);/)?.[1] ?? "";
  assert.match(union, /type: 'fantasy_result'/);
  assert.doesNotMatch(union, /type: 'fantasy_(?:win|settled)'/);
  for (const name of ["FantasyWinNotificationPayload", "FantasySettledNotificationPayload", "FantasySettledOutcome"])
    assert.equal(exportedTsNames(TS_API).has(name), false);
});
