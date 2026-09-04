import { getAddress, isAddress } from "viem";

import {
  type BytesLike,
  bytesFrom,
  bytesToHex,
  checkU32,
  checkU64,
  checkU8,
  toSafeNumber,
  U64_MAX,
} from "./bytes.js";
import { normalizeUuid } from "./uuid.js";

export { U64_MAX } from "./bytes.js";
export type WideInteger = number | bigint;

export const MIN_BET_MICROS = 500_000;

export class Address {
  static readonly ZERO = new Address(new Uint8Array(20));

  readonly #bytes: Uint8Array;

  constructor(value: BytesLike | Address) {
    if (value instanceof Address) {
      this.#bytes = new Uint8Array(value.#bytes);
      return;
    }
    if (typeof value === "string") {
      const prefixed = ensureEvmAddressPrefix(value);
      // Addresses are 20-byte protocol values; EIP-55 is canonical output
      // formatting, so input casing must not change whether the bytes are valid.
      if (!isAddress(prefixed, { strict: false })) {
        throw new Error("invalid EVM address");
      }
      this.#bytes = bytesFrom(prefixed, 20, "address");
      return;
    }
    this.#bytes = bytesFrom(value, 20, "address");
  }

  get bytes(): Uint8Array {
    return new Uint8Array(this.#bytes);
  }

  static zero(): Address {
    return Address.ZERO;
  }

  static fromEvm(value: string | BytesLike | Address): Address {
    return value instanceof Address ? value : new Address(value);
  }

  static fromHex(value: string): Address {
    return Address.fromEvm(value);
  }

  static fromSlice(value: BytesLike): Address {
    return new Address(value);
  }

  hex(prefixed = true): string {
    return bytesToHex(this.#bytes, prefixed);
  }

  serdeValue(): string {
    return this.hex(true);
  }

  toChecksum(): string {
    return getAddress(this.hex(true));
  }

  intoArray(): Uint8Array {
    return new Uint8Array(this.#bytes);
  }

  asSlice(): Uint8Array {
    return new Uint8Array(this.#bytes);
  }

  equals(other: Address | string | BytesLike): boolean {
    const rhs = Address.fromEvm(other);
    return this.hex(false) === rhs.hex(false);
  }

  toString(): string {
    return this.toChecksum();
  }
}

function ensureEvmAddressPrefix(value: string): `0x${string}` {
  if (value.startsWith("0x")) {
    return value as `0x${string}`;
  }
  return `0x${value}`;
}

export class MarketId {
  readonly value: bigint;

  constructor(value: number | bigint | string) {
    this.value = checkU64(value, "market_id");
  }

  static new(value: number | bigint | string): MarketId {
    return new MarketId(value);
  }

  asU64(): bigint {
    return this.value;
  }

  asNumber(): number {
    return toSafeNumber(this.value, "market_id");
  }

  serdeValue(): number | bigint {
    return this.value <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(this.value) : this.value;
  }

  toString(): string {
    return this.value.toString();
  }
}

export class UuidId {
  readonly value: string;

  constructor(value: string) {
    this.value = normalizeUuid(value);
  }

  static new(): UuidId {
    return new this(globalThis.crypto.randomUUID());
  }

  static fromUuid(value: string): UuidId {
    return new this(value);
  }

  static fromString(value: string): UuidId {
    return new this(value);
  }

  static nil(): UuidId {
    return new this("00000000-0000-0000-0000-000000000000");
  }

  static fromBytes(value: BytesLike): UuidId {
    const bytes = bytesFrom(value, 16, "uuid id");
    const hex = bytesToHex(bytes);
    return new this(
      `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(
        16,
        20,
      )}-${hex.slice(20)}`,
    );
  }

  asUuid(): string {
    return this.value;
  }

  asBytes(): Uint8Array {
    return uuidToBytes(this.value);
  }

  get bytes(): Uint8Array {
    return this.asBytes();
  }

  serdeValue(): string {
    return this.value;
  }

  isNil(): boolean {
    return this.value === "00000000-0000-0000-0000-000000000000";
  }

  equals(other: UuidId | string): boolean {
    return this.value === (other instanceof UuidId ? other.value : normalizeUuid(other));
  }

  toString(): string {
    return this.value;
  }
}

export class RequestId extends UuidId {}
export class UserId extends UuidId {}
export class QuoteId extends UuidId {}
export class ClientQuoteId extends UuidId {}
export class PositionId extends UuidId {}
export class ContestId extends UuidId {}

export const MathError = {
  Overflow: "Overflow",
  Underflow: "Underflow",
  DivisionByZero: "DivisionByZero",
} as const;
export type MathError = (typeof MathError)[keyof typeof MathError];

export const MarketType = {
  Sports: "sports",
  Culture: "culture",
  Crypto: "crypto",
  Politics: "politics",
  Earnings: "earnings",
  Entertainment: "entertainment",
  Esports: "esports",
  Weather: "weather",
  Mentions: "mentions",
  Extra: "extra",
  Other: "other",
} as const;
/** Open category slug; known constants above are conveniences, not a closed union. */
export type MarketType = string;

export const TradingChannel = {
  Rfq: "rfq",
  Contest: "contest",
} as const;
export type TradingChannel = (typeof TradingChannel)[keyof typeof TradingChannel];

export const MarketStatus = {
  Pending: "PENDING",
  Open: "OPEN",
  Frozen: "FROZEN",
  Disputed: "DISPUTED",
  PendingResolution: "PENDING_RESOLUTION",
  Resolved: "RESOLVED",
  Voided: "VOIDED",
} as const;
export type MarketStatus = (typeof MarketStatus)[keyof typeof MarketStatus];

export function marketStatusIsTradeable(status: MarketStatus): boolean {
  return status === MarketStatus.Open;
}

export function marketStatusIsTerminal(status: MarketStatus): boolean {
  return status === MarketStatus.Resolved || status === MarketStatus.Voided;
}

export function marketStatusIsVisible(status: MarketStatus): boolean {
  return status !== MarketStatus.Pending;
}

export function marketStatusCanTransitionTo(status: MarketStatus, target: MarketStatus): boolean {
  if (target === MarketStatus.Voided && !marketStatusIsTerminal(status)) {
    return true;
  }
  switch (status) {
    case MarketStatus.Pending:
      return target === MarketStatus.Open;
    case MarketStatus.Open:
      return target === MarketStatus.Frozen;
    case MarketStatus.Frozen:
      return (
        target === MarketStatus.PendingResolution ||
        target === MarketStatus.Resolved ||
        target === MarketStatus.Voided ||
        target === MarketStatus.Disputed
      );
    case MarketStatus.Disputed:
      return (
        target === MarketStatus.PendingResolution ||
        target === MarketStatus.Resolved ||
        target === MarketStatus.Voided
      );
    case MarketStatus.PendingResolution:
      return target === MarketStatus.Resolved || target === MarketStatus.Voided;
    case MarketStatus.Resolved:
    case MarketStatus.Voided:
      return false;
  }
}

export const Outcome = {
  Yes: "YES",
  No: "NO",
} as const;
export type Outcome = (typeof Outcome)[keyof typeof Outcome];

export function outcomeOpposite(outcome: Outcome): Outcome {
  return outcome === Outcome.Yes ? Outcome.No : Outcome.Yes;
}

export enum Asset {
  BTC = 0,
  ETH = 1,
  SOL = 2,
}

export namespace Asset {
  export const COUNT = 3;
  export const ALL = [Asset.BTC, Asset.ETH, Asset.SOL] as const;

  export function fromU8(value: number): Asset | undefined {
    switch (checkU8(value, "asset")) {
      case 0:
        return Asset.BTC;
      case 1:
        return Asset.ETH;
      case 2:
        return Asset.SOL;
      default:
        return undefined;
    }
  }

  export function ticker(asset: Asset): string {
    return Asset[asset];
  }

  export function parseSymbol(raw: string): Asset | undefined {
    const symbol = raw.trim().toUpperCase();
    return ALL.find((asset) => ticker(asset) === symbol);
  }

  export function serdeValue(asset: Asset): string {
    return ticker(asset);
  }
}

export enum Direction {
  Up = 0,
  Down = 1,
}

export namespace Direction {
  export function fromU8(value: number): Direction | undefined {
    switch (checkU8(value, "direction")) {
      case 0:
        return Direction.Up;
      case 1:
        return Direction.Down;
      default:
        return undefined;
    }
  }

  export function predictsHigher(direction: Direction): boolean {
    return direction === Direction.Up;
  }

  export function fromPredictsHigher(prediction: boolean): Direction {
    return prediction ? Direction.Up : Direction.Down;
  }

  export function opposite(direction: Direction): Direction {
    return direction === Direction.Up ? Direction.Down : Direction.Up;
  }

  export function serdeValue(direction: Direction): string {
    return Direction[direction];
  }
}

export class Duration {
  static readonly ONE_MINUTE_SECS = 60;
  static readonly FIVE_MINUTES_SECS = 5 * 60;
  static readonly FIFTEEN_MINUTES_SECS = 15 * 60;
  static readonly ONE_HOUR_SECS = 60 * 60;
  static readonly FOUR_HOURS_SECS = 4 * 60 * 60;
  static readonly ONE_DAY_SECS = 24 * 60 * 60;
  static readonly VALID_SECONDS = new Set([
    Duration.ONE_MINUTE_SECS,
    Duration.FIVE_MINUTES_SECS,
    Duration.FIFTEEN_MINUTES_SECS,
    Duration.ONE_HOUR_SECS,
    Duration.FOUR_HOURS_SECS,
    Duration.ONE_DAY_SECS,
  ]);

  static readonly ONE_MINUTE = new Duration(Duration.ONE_MINUTE_SECS);
  static readonly FIVE_MINUTES = new Duration(Duration.FIVE_MINUTES_SECS);
  static readonly FIFTEEN_MINUTES = new Duration(Duration.FIFTEEN_MINUTES_SECS);
  static readonly ONE_HOUR = new Duration(Duration.ONE_HOUR_SECS);
  static readonly FOUR_HOURS = new Duration(Duration.FOUR_HOURS_SECS);
  static readonly ONE_DAY = new Duration(Duration.ONE_DAY_SECS);

  readonly seconds: number;

  constructor(seconds: number) {
    this.seconds = checkU32(seconds, "duration seconds");
  }

  static fromSecs(seconds: number): Duration | undefined {
    return Duration.VALID_SECONDS.has(seconds) ? new Duration(seconds) : undefined;
  }

  isValid(): boolean {
    return Duration.VALID_SECONDS.has(this.seconds);
  }

  asSecs(): number {
    return this.seconds;
  }

  asMins(): number {
    return Math.trunc(this.seconds / 60);
  }

  expiryFromNow(): bigint {
    return Timestamp.now().asMillis() + BigInt(this.seconds) * 1000n;
  }

  serdeValue(): number {
    return this.seconds;
  }

  toString(): string {
    if (this.seconds === Duration.ONE_MINUTE_SECS) return "1m";
    if (this.seconds === Duration.FIVE_MINUTES_SECS) return "5m";
    if (this.seconds === Duration.FIFTEEN_MINUTES_SECS) return "15m";
    if (this.seconds === Duration.ONE_HOUR_SECS) return "1h";
    if (this.seconds === Duration.FOUR_HOURS_SECS) return "4h";
    if (this.seconds === Duration.ONE_DAY_SECS) return "1d";
    return `${this.seconds}s`;
  }
}

export class Odds {
  static readonly BASIS_POINTS = 10_000;
  static readonly EVEN_VALUE = 10_000;
  static readonly MIN_VALUE = 10_001;
  static readonly MAX_VALUE = 10_000_000;
  static readonly EVEN = new Odds(Odds.EVEN_VALUE);
  static readonly MIN = new Odds(Odds.MIN_VALUE);
  static readonly MAX = new Odds(Odds.MAX_VALUE);

  readonly value: number;

  constructor(value: number | bigint) {
    this.value = checkU32(value, "odds");
  }

  static fromDecimal(whole: number, fractionalBps: number): Odds {
    return new Odds(whole * Odds.BASIS_POINTS + fractionalBps);
  }

  toDecimal(): [number, number] {
    return [Math.trunc(this.value / Odds.BASIS_POINTS), this.value % Odds.BASIS_POINTS];
  }

  toF64(): number {
    return this.value / Odds.BASIS_POINTS;
  }

  isValid(): boolean {
    return this.value > Odds.EVEN.value && this.value <= Odds.MAX.value;
  }

  private payoutMicros(wagerMicros: number | bigint | string): bigint {
    const wager = checkU64(wagerMicros, "wager_micros");
    return (wager * BigInt(this.value)) / BigInt(Odds.BASIS_POINTS);
  }

  checkedCalculatePayout(wagerMicros: number | bigint | string): bigint | undefined {
    const payout = this.payoutMicros(wagerMicros);
    return payout <= U64_MAX ? payout : undefined;
  }

  calculatePayout(wagerMicros: number | bigint | string): bigint {
    return this.checkedCalculatePayout(wagerMicros) ?? U64_MAX;
  }

  checkedCalculateProfit(wagerMicros: number | bigint | string): bigint | undefined {
    const wager = checkU64(wagerMicros, "wager_micros");
    const profit = this.payoutMicros(wager) - wager;
    return profit >= 0n && profit <= U64_MAX ? profit : undefined;
  }

  calculateProfit(wagerMicros: number | bigint | string): bigint {
    return (
      this.checkedCalculateProfit(wagerMicros) ??
      (this.value <= Odds.BASIS_POINTS ? 0n : U64_MAX)
    );
  }

  checkedCalculateMmLiability(fillMicros: number | bigint | string): bigint | undefined {
    return this.checkedCalculateProfit(fillMicros);
  }

  serdeValue(): number {
    return this.value;
  }

  toString(): string {
    const [whole, fractionalBps] = this.toDecimal();
    return `${whole}.${fractionalBps.toString().padStart(4, "0")}x`;
  }
}

export class Amount {
  static readonly MICROS_PER_DOLLAR = 1_000_000;
  static readonly ZERO = new Amount(0);

  readonly micros: bigint;

  constructor(micros: number | bigint | string) {
    this.micros = checkU64(micros, "amount micros");
  }

  static zero(): Amount {
    return Amount.ZERO;
  }

  static fromDollars(dollars: number | bigint | string): Amount {
    const value = checkU64(dollars, "dollars") * BigInt(Amount.MICROS_PER_DOLLAR);
    return new Amount(value > U64_MAX ? U64_MAX : value);
  }

  static fromMicro(micros: number | bigint | string): Amount {
    return new Amount(micros);
  }

  fixedMul(other: Amount): Amount {
    const scaled = (this.micros * other.micros) / BigInt(Amount.MICROS_PER_DOLLAR);
    if (scaled > U64_MAX) {
      throw new ArithmeticError(MathError.Overflow);
    }
    return new Amount(scaled);
  }

  fixedDiv(other: Amount): Amount {
    if (other.micros === 0n) {
      throw new ArithmeticError(MathError.DivisionByZero);
    }
    const scaled = (this.micros * BigInt(Amount.MICROS_PER_DOLLAR)) / other.micros;
    if (scaled > U64_MAX) {
      throw new ArithmeticError(MathError.Overflow);
    }
    return new Amount(scaled);
  }

  fixedMulDiv(mul: Amount, div: Amount): Amount {
    if (div.micros === 0n) {
      throw new ArithmeticError(MathError.DivisionByZero);
    }
    const scaled = (this.micros * mul.micros) / div.micros;
    if (scaled > U64_MAX) {
      throw new ArithmeticError(MathError.Overflow);
    }
    return new Amount(scaled);
  }

  asMicros(): bigint {
    return this.micros;
  }

  asNumber(): number {
    return toSafeNumber(this.micros, "amount micros");
  }

  toF64(): number {
    return Number(this.micros) / Amount.MICROS_PER_DOLLAR;
  }

  saturatingSub(other: Amount): Amount {
    return new Amount(this.micros > other.micros ? this.micros - other.micros : 0n);
  }

  saturatingAdd(other: Amount): Amount {
    const sum = this.micros + other.micros;
    return new Amount(sum > U64_MAX ? U64_MAX : sum);
  }

  isValidBet(): boolean {
    return this.micros >= BigInt(MIN_BET_MICROS);
  }

  serdeValue(): number | bigint {
    return this.micros <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(this.micros) : this.micros;
  }

  toString(): string {
    return `$${this.toF64().toFixed(2)}`;
  }
}

export class ArithmeticError extends Error {
  readonly code: MathError;

  constructor(code: MathError) {
    super(code);
    this.name = "ArithmeticError";
    this.code = code;
  }
}

export class Timestamp {
  static readonly ZERO = new Timestamp(0);

  readonly millis: bigint;

  constructor(millis: number | bigint | string) {
    this.millis = checkU64(millis, "timestamp millis");
  }

  static now(): Timestamp {
    return new Timestamp(BigInt(Date.now()));
  }

  static fromSecs(seconds: number | bigint | string): Timestamp | undefined {
    const checkedSeconds = checkU64(seconds, "timestamp seconds");
    // BigInt does not overflow, so enforce Rust's checked_mul contract before
    // constructing a timestamp outside the u64 wire domain.
    if (checkedSeconds > U64_MAX / 1000n) {
      return undefined;
    }
    return new Timestamp(checkedSeconds * 1000n);
  }

  static fromMillis(millis: number | bigint | string): Timestamp {
    return new Timestamp(millis);
  }

  asSecs(): bigint {
    return this.millis / 1000n;
  }

  asMillis(): bigint {
    return this.millis;
  }

  asNumber(): number {
    return toSafeNumber(this.millis, "timestamp millis");
  }

  isExpired(current: Timestamp): boolean {
    return this.millis < current.millis;
  }

  addMillis(ms: number | bigint | string): Timestamp | undefined {
    const checkedMillis = checkU64(ms, "millis");
    if (this.millis > U64_MAX - checkedMillis) {
      return undefined;
    }
    return new Timestamp(this.millis + checkedMillis);
  }

  millisUntil(current: Timestamp): bigint {
    return this.millis > current.millis ? this.millis - current.millis : 0n;
  }

  serdeValue(): number | bigint {
    return this.millis <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(this.millis) : this.millis;
  }

  toString(): string {
    return `${this.millis.toString()}ms`;
  }
}

export enum OrderType {
  IOC = 1,
  FOK = 2,
}

export namespace OrderType {
  export function fromU8(value: number): OrderType | undefined {
    switch (checkU8(value, "order_type")) {
      case 1:
        return OrderType.IOC;
      case 2:
        return OrderType.FOK;
      default:
        return undefined;
    }
  }

  export function requiresFullFill(orderType: OrderType): boolean {
    return orderType === OrderType.FOK;
  }

  export function allowsPartialFill(orderType: OrderType): boolean {
    return orderType === OrderType.IOC;
  }

  export function serdeValue(orderType: OrderType): string {
    return OrderType[orderType];
  }
}

function uuidToBytes(uuid: string): Uint8Array {
  return bytesFrom(uuid.replaceAll("-", ""), 16, "uuid id");
}

export function u64SerdeValue(value: number | bigint | string): number | string {
  const checked = checkU64(value, "u64");
  return checked <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(checked) : checked.toString();
}
