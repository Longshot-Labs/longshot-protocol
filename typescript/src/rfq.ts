import { recoverMessageAddress } from "viem";

import {
  type BytesLike,
  bytesFrom,
  bytesToHex,
  checkU32,
  checkU64,
  checkU8,
  readU32Le,
  readU64Le,
  U64_MAX,
  writeU32Le,
  writeU64Le,
} from "./bytes.js";
import {
  Address,
  Amount,
  Asset,
  ClientQuoteId,
  Direction,
  Duration,
  Odds,
  OrderType,
  RequestId,
  Timestamp,
  UserId,
  UserTier,
} from "./types.js";

/** Maximum RFQ legs supported by the current protocol. */
export const MAX_RFQ_LEGS = 9;
export const RFQ_TIMEOUT_MS = 500;
export const PROCESSING_BUFFER_MS = 100;
export const RFQ_PROTOCOL_VERSION = 2;
export const RFQ_LEG_TYPE_PRICE_STRIKE_TAG = 0;
// Tag 1 is retired so a v1 client cannot silently decode a binary event as Politics.
export const RFQ_LEG_TYPE_BINARY_EVENT_TAG = 2;
export const RFQ_LEG_WIRE_SIZE = 24;
export const TAKER_METADATA_WIRE_SIZE = 24;
export const BROADCAST_RFQ_REQUEST_SIZE = 280;
export const QUOTE_RESPONSE_SIZE = 113;
export const QUOTE_RESPONSE_SIGNED_DATA_SIZE = 48;

export class RfqLegWireDecodeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "RfqLegWireDecodeError";
  }
}

export class RfqRequestError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "RfqRequestError";
  }
}

export type RfqLegType =
  | { kind: "price_strike"; asset: Asset; window: Duration }
  | { kind: "binary_event" };

export const RfqLegType = {
  priceStrike(asset: Asset | number, window: Duration): RfqLegType {
    return { kind: "price_strike", asset: Number(asset) as Asset, window };
  },
  binaryEvent(): RfqLegType {
    return { kind: "binary_event" };
  },
  typeTag(legType: RfqLegType): number {
    return legType.kind === "price_strike"
      ? RFQ_LEG_TYPE_PRICE_STRIKE_TAG
      : RFQ_LEG_TYPE_BINARY_EVENT_TAG;
  },
  isPriceStrike(legType: RfqLegType): boolean {
    return legType.kind === "price_strike";
  },
  isBinaryEvent(legType: RfqLegType): boolean {
    return legType.kind === "binary_event";
  },
};

export interface RfqLegInput {
  marketId?: number | bigint | string;
  market_id?: number | bigint | string;
  startAtMs?: number | bigint | string;
  start_at_ms?: number | bigint | string;
  typeTag?: number;
  type_tag?: number;
  direction: Direction | number;
  legIndex?: number;
  leg_index?: number;
  typeValue?: number;
  type_value?: number;
  priceWindowSecs?: number;
  price_window_secs?: number;
}

export class RfqLeg {
  readonly marketId: bigint;
  readonly startAtMs: bigint;
  readonly typeTag: number;
  readonly direction: Direction | number;
  readonly legIndex: number;
  readonly typeValue: number;
  readonly priceWindowSecs: number;

  constructor(input: RfqLegInput) {
    this.marketId = checkU64(input.marketId ?? input.market_id ?? 0, "market_id");
    this.startAtMs = checkU64(input.startAtMs ?? input.start_at_ms ?? 0, "start_at_ms");
    this.typeTag = checkU8(
      input.typeTag ?? input.type_tag ?? RFQ_LEG_TYPE_PRICE_STRIKE_TAG,
      "type_tag",
    );
    this.direction = checkU8(input.direction, "direction");
    this.legIndex = checkU8(input.legIndex ?? input.leg_index ?? 0, "leg_index");
    this.typeValue = checkU8(input.typeValue ?? input.type_value ?? 0, "type_value");
    this.priceWindowSecs = checkU32(
      input.priceWindowSecs ?? input.price_window_secs ?? 0,
      "price_window_secs",
    );
  }

  static newPriceStrike(
    marketId: number | bigint | string,
    startAtMs: number | bigint | string,
    asset: Asset | number,
    direction: Direction | number,
    window: Duration,
    legIndex: number,
  ): RfqLeg {
    return RfqLeg.priceStrike(marketId, startAtMs, asset, direction, window, legIndex);
  }

  static priceStrike(
    marketId: number | bigint | string,
    startAtMs: number | bigint | string,
    asset: Asset | number,
    direction: Direction | number,
    window: Duration,
    legIndex: number,
  ): RfqLeg {
    return new RfqLeg({
      marketId,
      startAtMs,
      typeTag: RFQ_LEG_TYPE_PRICE_STRIKE_TAG,
      direction,
      legIndex,
      typeValue: checkU8(asset, "asset"),
      priceWindowSecs: window.asSecs(),
    });
  }

  static newBinaryEvent(
    marketId: number | bigint | string,
    startAtMs: number | bigint | string,
    direction: Direction | number,
    legIndex: number,
  ): RfqLeg {
    return RfqLeg.binaryEvent(marketId, startAtMs, direction, legIndex);
  }

  static binaryEvent(
    marketId: number | bigint | string,
    startAtMs: number | bigint | string,
    direction: Direction | number,
    legIndex: number,
  ): RfqLeg {
    return new RfqLeg({
      marketId,
      startAtMs,
      typeTag: RFQ_LEG_TYPE_BINARY_EVENT_TAG,
      direction,
      legIndex,
      typeValue: 0,
      priceWindowSecs: 0,
    });
  }

  static fromWireBytes(data: BytesLike): RfqLeg {
    return RfqLegWire.fromRawBytes(data).toLeg().validated();
  }

  validated(): RfqLeg {
    this.validate();
    return this;
  }

  validate(): void {
    if (Direction.fromU8(this.direction) === undefined) {
      throw new RfqLegWireDecodeError(`invalid RFQ direction: ${this.direction}`);
    }
    if (this.typeTag === RFQ_LEG_TYPE_PRICE_STRIKE_TAG) {
      if (Asset.fromU8(this.typeValue) === undefined) {
        throw new RfqLegWireDecodeError(`invalid RFQ asset: ${this.typeValue}`);
      }
      if (Duration.fromSecs(this.priceWindowSecs) === undefined) {
        throw new RfqLegWireDecodeError(
          `invalid RFQ price_window_secs: ${this.priceWindowSecs}`,
        );
      }
      return;
    }
    if (this.typeTag === RFQ_LEG_TYPE_BINARY_EVENT_TAG) {
      if (this.priceWindowSecs !== 0) {
        throw new RfqLegWireDecodeError(
          `invalid RFQ binary-event price_window_secs: ${this.priceWindowSecs}`,
        );
      }
      if (this.typeValue !== 0) {
        throw new RfqLegWireDecodeError(
          `invalid RFQ binary-event type value: ${this.typeValue}`,
        );
      }
      return;
    }
    throw new RfqLegWireDecodeError(`invalid RFQ leg type tag: ${this.typeTag}`);
  }

  legType(): RfqLegType {
    this.validate();
    if (this.typeTag === RFQ_LEG_TYPE_PRICE_STRIKE_TAG) {
      return RfqLegType.priceStrike(this.typeValue, Duration.fromSecs(this.priceWindowSecs)!);
    }
    return RfqLegType.binaryEvent();
  }

  priceAsset(): Asset | undefined {
    return this.typeTag === RFQ_LEG_TYPE_PRICE_STRIKE_TAG
      ? Asset.fromU8(this.typeValue)
      : undefined;
  }

  priceWindow(): Duration | undefined {
    return this.typeTag === RFQ_LEG_TYPE_PRICE_STRIKE_TAG
      ? Duration.fromSecs(this.priceWindowSecs)
      : undefined;
  }

  priceWindowSeconds(): number | undefined {
    return this.typeTag === RFQ_LEG_TYPE_PRICE_STRIKE_TAG ? this.priceWindowSecs : undefined;
  }

  toWireBytes(): Uint8Array {
    this.validate();
    return RfqLegWire.fromLeg(this).toBytes();
  }
}

export class RfqLegWire {
  static readonly SIZE = RFQ_LEG_WIRE_SIZE;

  readonly marketId: bigint;
  readonly startAtMs: bigint;
  readonly typeTag: number;
  readonly direction: number;
  readonly legIndex: number;
  readonly typeValue: number;
  readonly priceWindowSecs: number;

  constructor(input: RfqLegInput) {
    this.marketId = checkU64(input.marketId ?? input.market_id ?? 0, "market_id");
    this.startAtMs = checkU64(input.startAtMs ?? input.start_at_ms ?? 0, "start_at_ms");
    this.typeTag = checkU8(input.typeTag ?? input.type_tag ?? 0, "type_tag");
    this.direction = checkU8(input.direction ?? 0, "direction");
    this.legIndex = checkU8(input.legIndex ?? input.leg_index ?? 0, "leg_index");
    this.typeValue = checkU8(input.typeValue ?? input.type_value ?? 0, "type_value");
    this.priceWindowSecs = checkU32(
      input.priceWindowSecs ?? input.price_window_secs ?? 0,
      "price_window_secs",
    );
  }

  static default(): RfqLegWire {
    return new RfqLegWire({ direction: 0 });
  }

  static fromLeg(leg: RfqLeg): RfqLegWire {
    leg.validate();
    return new RfqLegWire({
      marketId: leg.marketId,
      startAtMs: leg.startAtMs,
      typeTag: leg.typeTag,
      direction: Number(leg.direction),
      legIndex: leg.legIndex,
      typeValue: leg.typeValue,
      priceWindowSecs: leg.priceWindowSecs,
    });
  }

  static fromBytes(data: BytesLike): RfqLegWire {
    // Wire decoding preserves inactive padding and future tag values; callers
    // that need a validated active leg must convert through RfqLeg instead.
    return RfqLegWire.fromRawBytes(data);
  }

  static fromRawBytes(data: BytesLike): RfqLegWire {
    const bytes = bytesFrom(data, RFQ_LEG_WIRE_SIZE, "RFQ leg wire payload");
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    return new RfqLegWire({
      marketId: readU64Le(view, 0),
      startAtMs: readU64Le(view, 8),
      typeTag: view.getUint8(16),
      direction: view.getUint8(17),
      legIndex: view.getUint8(18),
      typeValue: view.getUint8(19),
      priceWindowSecs: readU32Le(view, 20),
    });
  }

  toLeg(): RfqLeg {
    return new RfqLeg({
      marketId: this.marketId,
      startAtMs: this.startAtMs,
      typeTag: this.typeTag,
      direction: this.direction,
      legIndex: this.legIndex,
      typeValue: this.typeValue,
      priceWindowSecs: this.priceWindowSecs,
    });
  }

  toBytes(): Uint8Array {
    const bytes = new Uint8Array(RFQ_LEG_WIRE_SIZE);
    const view = new DataView(bytes.buffer);
    writeU64Le(view, 0, this.marketId);
    writeU64Le(view, 8, this.startAtMs);
    view.setUint8(16, this.typeTag);
    view.setUint8(17, this.direction);
    view.setUint8(18, this.legIndex);
    view.setUint8(19, this.typeValue);
    writeU32Le(view, 20, this.priceWindowSecs);
    return bytes;
  }
}

export class TakerMetadata {
  readonly tier: UserTier | number;
  readonly address: Address;

  constructor(tier: UserTier | number, address: Address | string | BytesLike) {
    this.tier = checkU8(tier, "tier");
    this.address = Address.fromEvm(address);
  }

  static new(tier: UserTier | number, address: Address | string | BytesLike): TakerMetadata {
    return new TakerMetadata(tier, address);
  }

  toWireBytes(): Uint8Array {
    const bytes = new Uint8Array(TAKER_METADATA_WIRE_SIZE);
    bytes[0] = 1;
    bytes[1] = Number(this.tier);
    bytes.set(this.address.asSlice(), 4);
    return bytes;
  }

  static fromWireBytes(data: BytesLike): TakerMetadata | undefined {
    const bytes = bytesFrom(data, TAKER_METADATA_WIRE_SIZE, "taker metadata wire payload");
    if (bytes[0] === 0) {
      return undefined;
    }
    return new TakerMetadata(bytes[1], bytes.slice(4, 24));
  }
}

export interface RfqRequestInput {
  requestId?: RequestId | string;
  request_id?: RequestId | string;
  takerId?: UserId | string;
  taker_id?: UserId | string;
  wagerMicros?: number | bigint | string;
  wager_micros?: number | bigint | string;
  expiresAtMs?: number | bigint | string;
  expires_at_ms?: number | bigint | string;
  takerMetadata?: TakerMetadata | null;
  taker_metadata?: TakerMetadata | null;
  minOdds?: Odds | number;
  min_odds?: Odds | number;
  orderType?: OrderType | number;
  order_type?: OrderType | number;
  legs?: RfqLeg[];
}

function validateRfqLegCount(legCount: number): void {
  if (legCount === 0) {
    throw new RfqRequestError("RFQ must include at least one leg");
  }
  if (legCount > MAX_RFQ_LEGS) {
    throw new RfqRequestError("RFQ legs exceed MAX_RFQ_LEGS");
  }
}

export class RfqRequest {
  readonly requestId: RequestId;
  readonly takerId: UserId;
  wagerMicros: bigint;
  expiresAtMs: bigint;
  takerMetadata?: TakerMetadata;
  minOddsRaw: number;
  orderTypeRaw: number;
  readonly legs: RfqLeg[];

  constructor(input: RfqRequestInput) {
    this.requestId =
      input.requestId instanceof RequestId
        ? input.requestId
        : RequestId.fromString(String(input.requestId ?? input.request_id));
    this.takerId =
      input.takerId instanceof UserId
        ? input.takerId
        : UserId.fromString(String(input.takerId ?? input.taker_id));
    this.wagerMicros = checkU64(input.wagerMicros ?? input.wager_micros ?? 0, "wager_micros");
    this.expiresAtMs = checkU64(input.expiresAtMs ?? input.expires_at_ms ?? 0, "expires_at_ms");
    this.takerMetadata = input.takerMetadata ?? input.taker_metadata ?? undefined;
    const minOdds = input.minOdds ?? input.min_odds ?? Odds.EVEN;
    this.minOddsRaw = minOdds instanceof Odds ? minOdds.value : checkU32(minOdds, "min_odds");
    this.orderTypeRaw = checkU8(input.orderType ?? input.order_type ?? 0, "order_type");
    this.legs = input.legs ?? [];
    validateRfqLegCount(this.legs.length);
  }

  static new(
    requestId: RequestId,
    takerId: UserId,
    wager: Amount,
    orderType: OrderType,
    minOdds: Odds,
    takerMetadata: TakerMetadata | undefined,
    legs: RfqLeg[],
  ): RfqRequest {
    // Match Rust's constructor fallback if the checked timestamp addition
    // reaches the u64 boundary instead of exposing an impossible expiry.
    const expiresAt =
      Timestamp.now().addMillis(RFQ_TIMEOUT_MS) ?? Timestamp.fromMillis(U64_MAX);
    return new RfqRequest({
      requestId,
      takerId,
      wagerMicros: wager.asMicros(),
      expiresAtMs: expiresAt.asMillis(),
      takerMetadata,
      minOdds,
      orderType,
      legs,
    });
  }

  wager(): Amount {
    return Amount.fromMicro(this.wagerMicros);
  }

  expiresAt(): Timestamp {
    return Timestamp.fromMillis(this.expiresAtMs);
  }

  setExpiresAtMs(ms: number | bigint | string): void {
    this.expiresAtMs = checkU64(ms, "expires_at_ms");
  }

  clampExpiresAtMs(maxMs: number | bigint | string): void {
    const max = checkU64(maxMs, "max_ms");
    if (this.expiresAtMs > max) {
      this.expiresAtMs = max;
    }
  }

  orderType(): OrderType | undefined {
    return OrderType.fromU8(this.orderTypeRaw);
  }

  isExpired(): boolean {
    return Timestamp.now().asMillis() > this.expiresAtMs;
  }

  activeLegs(): RfqLeg[] {
    return this.legs.slice(0, MAX_RFQ_LEGS);
  }

  leg(index: number): RfqLeg | undefined {
    return index >= 0 && index < Math.min(this.legs.length, MAX_RFQ_LEGS)
      ? this.legs[index]
      : undefined;
  }

  iterLegs(): IterableIterator<RfqLeg> {
    return this.legs.slice(0, MAX_RFQ_LEGS)[Symbol.iterator]();
  }

  remainingMs(): bigint {
    const now = Timestamp.now().asMillis();
    return this.expiresAtMs > now ? this.expiresAtMs - now : 0n;
  }

  getTakerMetadata(): TakerMetadata | undefined {
    return this.takerMetadata;
  }

  minOdds(): Odds {
    return new Odds(this.minOddsRaw);
  }

  takerTier(): UserTier | undefined {
    return this.takerMetadata === undefined
      ? undefined
      : UserTier.fromU8(Number(this.takerMetadata.tier));
  }

  takerAddress(): Address | undefined {
    return this.takerMetadata?.address;
  }

  toBroadcastBytes(): Uint8Array {
    validateRfqLegCount(this.legs.length);
    const bytes = new Uint8Array(BROADCAST_RFQ_REQUEST_SIZE);
    const view = new DataView(bytes.buffer);
    bytes.set(this.requestId.asBytes(), 0);
    writeU64Le(view, 16, this.wagerMicros);
    writeU64Le(view, 24, this.expiresAtMs);
    if (this.takerMetadata !== undefined) {
      bytes.set(this.takerMetadata.toWireBytes(), 32);
    }
    bytes[56] = this.orderTypeRaw;
    bytes[57] = this.legs.length;
    bytes[58] = RFQ_PROTOCOL_VERSION;
    for (let index = 0; index < this.legs.length; index += 1) {
      bytes.set(this.legs[index].toWireBytes(), 64 + index * RFQ_LEG_WIRE_SIZE);
    }
    return bytes;
  }
}

export interface BroadcastRfqRequestInput {
  requestId?: RequestId | string;
  request_id?: RequestId | string;
  wagerMicros?: number | bigint | string;
  wager_micros?: number | bigint | string;
  expiresAtMs?: number | bigint | string;
  expires_at_ms?: number | bigint | string;
  takerMetadata?: TakerMetadata | null;
  taker_metadata?: TakerMetadata | null;
  takerMetadataWireBytes?: BytesLike;
  taker_metadata_wire_bytes?: BytesLike;
  orderType?: OrderType | number;
  order_type?: OrderType | number;
  legCount?: number;
  leg_count?: number;
  protocolVersion?: number;
  protocol_version?: number;
  legs?: Array<RfqLeg | RfqLegWire>;
  reserved?: Uint8Array;
  inactiveLegBytes?: Uint8Array;
  inactive_leg_bytes?: Uint8Array;
}

export class BroadcastRfqRequest {
  static readonly SIZE = BROADCAST_RFQ_REQUEST_SIZE;

  readonly requestId: RequestId;
  readonly wagerMicros: bigint;
  readonly expiresAtMs: bigint;
  readonly takerMetadata?: TakerMetadata;
  readonly takerMetadataWireBytes: Uint8Array;
  readonly orderTypeRaw: number;
  readonly legCount: number;
  readonly protocolVersion: number;
  readonly legs: Array<RfqLeg | RfqLegWire>;
  readonly reserved: Uint8Array;
  readonly inactiveLegBytes: Uint8Array;

  constructor(input: BroadcastRfqRequestInput) {
    this.requestId =
      input.requestId instanceof RequestId
        ? input.requestId
        : RequestId.fromString(String(input.requestId ?? input.request_id));
    this.wagerMicros = checkU64(input.wagerMicros ?? input.wager_micros ?? 0, "wager_micros");
    this.expiresAtMs = checkU64(input.expiresAtMs ?? input.expires_at_ms ?? 0, "expires_at_ms");
    const takerMetadataWireBytes =
      input.takerMetadataWireBytes ?? input.taker_metadata_wire_bytes;
    if (takerMetadataWireBytes !== undefined) {
      this.takerMetadataWireBytes = bytesFrom(
        takerMetadataWireBytes,
        TAKER_METADATA_WIRE_SIZE,
        "taker metadata wire payload",
      );
      this.takerMetadata = TakerMetadata.fromWireBytes(this.takerMetadataWireBytes);
    } else {
      this.takerMetadata = input.takerMetadata ?? input.taker_metadata ?? undefined;
      this.takerMetadataWireBytes =
        this.takerMetadata?.toWireBytes() ?? new Uint8Array(TAKER_METADATA_WIRE_SIZE);
    }
    this.orderTypeRaw = checkU8(input.orderType ?? input.order_type ?? 0, "order_type");
    this.legCount = checkU8(input.legCount ?? input.leg_count ?? 0, "leg_count");
    this.legs = input.legs ?? [];
    this.protocolVersion = checkU8(
      input.protocolVersion ?? input.protocol_version ?? RFQ_PROTOCOL_VERSION,
      "protocol_version",
    );
    this.reserved = input.reserved ?? new Uint8Array(5);
    this.inactiveLegBytes = input.inactiveLegBytes ?? input.inactive_leg_bytes ?? new Uint8Array();
    if (this.reserved.length !== 5) {
      throw new Error("broadcast RFQ reserved field must be 5 bytes");
    }
  }

  static fromBytes(data: BytesLike): BroadcastRfqRequest {
    const bytes = bytesFrom(data, BROADCAST_RFQ_REQUEST_SIZE, "broadcast RFQ payload");
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const legCount = bytes[57];
    const activeLegCount = Math.min(legCount, MAX_RFQ_LEGS);
    const legs: RfqLegWire[] = [];
    for (let index = 0; index < activeLegCount; index += 1) {
      const start = 64 + index * RFQ_LEG_WIRE_SIZE;
      legs.push(RfqLegWire.fromRawBytes(bytes.slice(start, start + RFQ_LEG_WIRE_SIZE)));
    }
    return new BroadcastRfqRequest({
      requestId: RequestId.fromBytes(bytes.slice(0, 16)),
      wagerMicros: readU64Le(view, 16),
      expiresAtMs: readU64Le(view, 24),
      takerMetadataWireBytes: bytes.slice(32, 56),
      orderType: bytes[56],
      legCount,
      protocolVersion: bytes[58],
      legs,
      reserved: bytes.slice(59, 64),
      inactiveLegBytes: bytes.slice(64 + activeLegCount * RFQ_LEG_WIRE_SIZE),
    });
  }

  toBytes(): Uint8Array {
    const activeLegCount = Math.min(this.legCount, MAX_RFQ_LEGS);
    const activeLegs = this.legs.slice(0, activeLegCount);
    if (activeLegs.length !== activeLegCount) {
      throw new Error("broadcast RFQ active legs shorter than leg_count");
    }
    const bytes = new Uint8Array(BROADCAST_RFQ_REQUEST_SIZE);
    const view = new DataView(bytes.buffer);
    bytes.set(this.requestId.asBytes(), 0);
    writeU64Le(view, 16, this.wagerMicros);
    writeU64Le(view, 24, this.expiresAtMs);
    bytes.set(this.takerMetadataWireBytes, 32);
    bytes[56] = this.orderTypeRaw;
    bytes[57] = this.legCount;
    bytes[58] = this.protocolVersion;
    bytes.set(this.reserved, 59);
    for (let index = 0; index < activeLegs.length; index += 1) {
      bytes.set(legToWire(activeLegs[index]).toBytes(), 64 + index * RFQ_LEG_WIRE_SIZE);
    }
    if (this.inactiveLegBytes.length > 0) {
      const expected = RFQ_LEG_WIRE_SIZE * (MAX_RFQ_LEGS - activeLegCount);
      if (this.inactiveLegBytes.length !== expected) {
        throw new Error("broadcast RFQ inactive leg bytes have wrong length");
      }
      bytes.set(this.inactiveLegBytes, 64 + activeLegCount * RFQ_LEG_WIRE_SIZE);
    }
    return bytes;
  }

  wager(): Amount {
    return Amount.fromMicro(this.wagerMicros);
  }

  expiresAt(): Timestamp {
    return Timestamp.fromMillis(this.expiresAtMs);
  }

  orderType(): OrderType | undefined {
    return OrderType.fromU8(this.orderTypeRaw);
  }

  isExpired(): boolean {
    return Timestamp.now().asMillis() > this.expiresAtMs;
  }

  activeLegWires(): RfqLegWire[] {
    const activeLegCount = Math.min(this.legCount, MAX_RFQ_LEGS);
    return this.legs.slice(0, activeLegCount).map((leg) => legToWire(leg));
  }

  legWire(index: number): RfqLegWire | undefined {
    const wires = this.legs.slice(0, this.legCount).map((leg) => legToWire(leg));
    return index >= 0 && index < wires.length ? wires[index] : undefined;
  }

  iterLegWires(): IterableIterator<RfqLegWire> {
    return this.legs
      .slice(0, this.legCount)
      .map((leg) => legToWire(leg))
      [Symbol.iterator]();
  }

  leg(index: number): RfqLeg | undefined {
    if (index < 0 || index >= Math.min(this.legCount, this.legs.length)) {
      return undefined;
    }
    return legToTyped(this.legs[index]);
  }

  iterLegs(): IterableIterator<RfqLeg> {
    return this.legs
      .slice(0, this.legCount)
      .map((leg) => legToTyped(leg))
      [Symbol.iterator]();
  }

  remainingMs(): bigint {
    const now = Timestamp.now().asMillis();
    return this.expiresAtMs > now ? this.expiresAtMs - now : 0n;
  }

  getTakerMetadata(): TakerMetadata | undefined {
    return this.takerMetadata;
  }

  takerTier(): UserTier | undefined {
    return this.takerMetadata === undefined
      ? undefined
      : UserTier.fromU8(Number(this.takerMetadata.tier));
  }

  takerAddress(): Address | undefined {
    return this.takerMetadata?.address;
  }
}

export interface QuoteResponseInput {
  requestId?: RequestId | string;
  request_id?: RequestId | string;
  odds: Odds | number;
  maxFillMicros?: number | bigint | string;
  max_fill_micros?: number | bigint | string;
  clientQuoteId?: ClientQuoteId | string;
  client_quote_id?: ClientQuoteId | string;
  signature?: BytesLike;
  reserved?: BytesLike;
}

export class QuoteResponse {
  static readonly SIZE = QUOTE_RESPONSE_SIZE;
  static readonly SIGNED_DATA_SIZE = QUOTE_RESPONSE_SIGNED_DATA_SIZE;

  readonly requestId: RequestId;
  odds: number;
  readonly maxFillMicros: bigint;
  readonly clientQuoteId: ClientQuoteId;
  readonly signature: Uint8Array;
  readonly reserved: Uint8Array;

  constructor(input: QuoteResponseInput) {
    this.requestId =
      input.requestId instanceof RequestId
        ? input.requestId
        : RequestId.fromString(String(input.requestId ?? input.request_id));
    this.odds = input.odds instanceof Odds ? input.odds.value : checkU32(input.odds, "odds");
    this.maxFillMicros = checkU64(
      input.maxFillMicros ?? input.max_fill_micros ?? 0,
      "max_fill_micros",
    );
    const clientQuoteId = input.clientQuoteId ?? input.client_quote_id;
    this.clientQuoteId =
      clientQuoteId instanceof ClientQuoteId
        ? clientQuoteId
        : clientQuoteId === undefined || clientQuoteId === null
          ? ClientQuoteId.nil() as ClientQuoteId
          : ClientQuoteId.fromString(String(clientQuoteId)) as ClientQuoteId;
    this.signature =
      input.signature === undefined ? new Uint8Array(65) : bytesFrom(input.signature, 65);
    this.reserved = input.reserved === undefined ? new Uint8Array(4) : bytesFrom(input.reserved, 4);
  }

  static new(
    requestId: RequestId,
    odds: Odds,
    maxFill: Amount,
    clientQuoteId?: ClientQuoteId,
  ): QuoteResponse {
    return new QuoteResponse({
      requestId,
      odds,
      maxFillMicros: maxFill.asMicros(),
      clientQuoteId,
      signature: new Uint8Array(65),
    });
  }

  static fromBytes(data: BytesLike): QuoteResponse {
    const bytes = bytesFrom(data, QUOTE_RESPONSE_SIZE, "quote response payload");
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    return new QuoteResponse({
      requestId: RequestId.fromBytes(bytes.slice(0, 16)),
      odds: readU32Le(view, 16),
      maxFillMicros: readU64Le(view, 20),
      clientQuoteId: ClientQuoteId.fromBytes(bytes.slice(28, 44)) as ClientQuoteId,
      reserved: bytes.slice(44, 48),
      signature: bytes.slice(48, 113),
    });
  }

  static fromSlice(data: BytesLike): QuoteResponse | undefined {
    const bytes = bytesFrom(data);
    return bytes.length === QUOTE_RESPONSE_SIZE ? QuoteResponse.fromBytes(bytes) : undefined;
  }

  signedDataBytes(): Uint8Array {
    return this.toBytes().slice(0, QUOTE_RESPONSE_SIGNED_DATA_SIZE);
  }

  toBytes(): Uint8Array {
    const bytes = new Uint8Array(QUOTE_RESPONSE_SIZE);
    const view = new DataView(bytes.buffer);
    bytes.set(this.requestId.asBytes(), 0);
    writeU32Le(view, 16, this.odds);
    writeU64Le(view, 20, this.maxFillMicros);
    bytes.set(this.clientQuoteId.asBytes(), 28);
    bytes.set(this.reserved, 44);
    bytes.set(this.signature, 48);
    return bytes;
  }

  meetsMinOdds(minOdds: Odds): boolean {
    return this.odds >= minOdds.value;
  }

  maxFill(): Amount {
    return Amount.fromMicro(this.maxFillMicros);
  }

  clientQuoteIdOption(): ClientQuoteId | undefined {
    return this.clientQuoteId.isNil() ? undefined : this.clientQuoteId;
  }

  async verifySignature(walletAddress: Address): Promise<boolean> {
    try {
      const recovered = await recoverMessageAddress({
        message: { raw: bytesToHex(this.signedDataBytes(), true) as `0x${string}` },
        signature: bytesToHex(this.signature, true) as `0x${string}`,
      });
      return Address.fromEvm(recovered).equals(walletAddress);
    } catch {
      return false;
    }
  }
}

function legToWire(leg: RfqLeg | RfqLegWire): RfqLegWire {
  return leg instanceof RfqLegWire ? leg : RfqLegWire.fromLeg(leg);
}

function legToTyped(leg: RfqLeg | RfqLegWire): RfqLeg {
  const typed = leg instanceof RfqLegWire ? leg.toLeg() : leg;
  typed.validate();
  return typed;
}
