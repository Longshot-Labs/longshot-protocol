import { recoverMessageAddress } from "viem";
import { privateKeyToAccount } from "viem/accounts";

import {
  bytesFrom,
  bytesToHex,
  checkU32,
  checkU64,
  concatBytes,
  encodeBase64,
  u32LeBytes,
  u64LeBytes,
} from "./bytes.js";
import { MAX_RFQ_LEGS } from "./rfq.js";
import { Address, Direction, MarketId, OrderType, u64SerdeValue } from "./types.js";

export class SignedOrderError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SignedOrderError";
  }
}

export class TakerSignError extends Error {
  constructor(message: string, readonly cause?: unknown) {
    super(message);
    this.name = "TakerSignError";
  }
}

export interface OrderLegInput {
  marketId?: MarketId | number | bigint | string;
  market_id?: MarketId | number | bigint | string;
  direction: number;
}

export class OrderLeg {
  readonly marketId: MarketId;
  readonly direction: number;

  constructor(input: OrderLegInput) {
    const marketId = input.marketId ?? input.market_id;
    if (marketId === undefined) {
      throw new Error("market_id is required");
    }
    this.marketId = marketId instanceof MarketId ? marketId : MarketId.new(marketId);
    if (!Number.isInteger(input.direction) || input.direction < 0 || input.direction > 0xff) {
      throw new RangeError("direction must fit in u8");
    }
    this.direction = input.direction;
  }

  toBytes(): Uint8Array {
    return concatBytes(u64LeBytes(this.marketId.asU64()), Uint8Array.of(this.direction));
  }

  serdeValue(): { market_id: number | bigint; direction: number } {
    return { market_id: this.marketId.serdeValue(), direction: this.direction };
  }
}

export interface SignedOrderInput {
  user: Address | string | Uint8Array;
  wagerMicros?: number | bigint | string;
  wager_micros?: number | bigint | string;
  /** Minimum acceptable odds in basis points (`25_000 = 2.5x`). */
  minOddsBps: number;
  legs: Array<OrderLeg | OrderLegInput>;
  nonce: number | bigint | string;
  expiresAtMs?: number | bigint | string;
  expires_at_ms?: number | bigint | string;
  orderType?: OrderType | number;
  order_type?: OrderType | number;
  shieldOn?: boolean;
  shield_on?: boolean;
  signature?: Uint8Array | string | number[];
}

export class SignedOrder {
  static readonly MAX_LEGS = MAX_RFQ_LEGS;

  readonly user: Address;
  readonly wagerMicros: number | bigint | string;
  /** Signed basis-point value; HTTP `SignedOrderJson.min_odds` uses decimal odds. */
  readonly minOddsBps: number;
  readonly legs: OrderLeg[];
  readonly nonce: number | bigint | string;
  readonly expiresAtMs: number | bigint | string;
  readonly orderType: OrderType | number;
  readonly shieldOn: boolean;
  readonly signature: Uint8Array;

  constructor(input: SignedOrderInput) {
    this.user = Address.fromEvm(input.user);
    this.wagerMicros = input.wagerMicros ?? input.wager_micros ?? missing("wager_micros");
    this.minOddsBps = input.minOddsBps ?? missing("min_odds_bps");
    this.legs = input.legs.map((leg) => (leg instanceof OrderLeg ? leg : new OrderLeg(leg)));
    this.nonce = input.nonce;
    this.expiresAtMs = input.expiresAtMs ?? input.expires_at_ms ?? missing("expires_at_ms");
    this.orderType = input.orderType ?? input.order_type ?? missing("order_type");
    const shieldOn = input.shieldOn !== undefined ? input.shieldOn : input.shield_on;
    this.shieldOn = shieldOn === undefined ? false : shieldOn;
    this.signature =
      input.signature === undefined ? new Uint8Array(65) : bytesFrom(input.signature, 65, "signature");
  }

  validate(): void {
    if (typeof this.shieldOn !== "boolean") {
      throw new SignedOrderError("shield_on must be bool");
    }
    if (this.legs.length === 0) {
      throw new SignedOrderError("order must include at least one leg");
    }
    if (this.legs.length > SignedOrder.MAX_LEGS) {
      throw new SignedOrderError("order legs exceed MAX_LEGS");
    }
    this.legs.forEach((leg, index) => {
      if (Direction.fromU8(leg.direction) === undefined) {
        throw new SignedOrderError(`invalid direction ${leg.direction} at legs[${index}]`);
      }
    });
    if (this.orderType !== OrderType.IOC && this.orderType !== OrderType.FOK) {
      throw new SignedOrderError(`invalid order type: ${this.orderType}`);
    }
    checkU64(this.wagerMicros, "wager_micros");
    checkU32(this.minOddsBps, "min_odds_bps");
    checkU64(this.nonce, "nonce");
    checkU64(this.expiresAtMs, "expires_at_ms");
  }

  signingBytes(useAppTokens: boolean): Uint8Array {
    this.validate();
    if (typeof useAppTokens !== "boolean") {
      throw new SignedOrderError("use_app_tokens must be bool");
    }
    const parts = [
      this.user.asSlice(),
      u64LeBytes(this.wagerMicros),
      u32LeBytes(this.minOddsBps),
      u64LeBytes(this.nonce),
      u64LeBytes(this.expiresAtMs),
      Uint8Array.of(
        Number(this.orderType),
        this.shieldOn ? 1 : 0,
        useAppTokens ? 1 : 0,
        this.legs.length,
      ),
      ...this.legs.map((leg) => leg.toBytes()),
    ];
    return concatBytes(...parts);
  }

  /** Verify this order's EIP-191 signature and funding choice against `this.user`. */
  async verifySignature(useAppTokens: boolean): Promise<boolean> {
    try {
      const recovered = await recoverMessageAddress({
        message: { raw: bytesToHex(this.signingBytes(useAppTokens), true) as `0x${string}` },
        signature: bytesToHex(this.signature, true) as `0x${string}`,
      });
      return Address.fromEvm(recovered).equals(this.user);
    } catch {
      return false;
    }
  }

  serdeValue(): {
    user: string;
    wager_micros: number | string;
    min_odds: number;
    legs: Array<{ market_id: number | bigint; direction: "up" | "down" }>;
    nonce: number | string;
    expires_at_ms: number | string;
    order_type: number;
    shield_on: boolean;
    signature: string;
  } {
    this.validate();
    return {
      user: this.user.toChecksum(),
      wager_micros: u64SerdeValue(this.wagerMicros),
      min_odds: this.minOddsBps / 10_000,
      legs: this.legs.map((leg) => ({
        market_id: leg.marketId.serdeValue(),
        direction: serdeDirection(leg.direction),
      })),
      nonce: u64SerdeValue(this.nonce),
      expires_at_ms: u64SerdeValue(this.expiresAtMs),
      order_type: serdeOrderType(this.orderType),
      shield_on: this.shieldOn,
      signature: encodeBase64(this.signature),
    };
  }
}

export async function signOrder(
  order: SignedOrder,
  useAppTokens: boolean,
  signingKey: `0x${string}`,
): Promise<SignedOrder> {
  const account = privateKeyToAccount(signingKey);
  const signature = await account.signMessage({
    message: { raw: bytesToHex(order.signingBytes(useAppTokens), true) as `0x${string}` },
  });
  return new SignedOrder({
    user: order.user,
    wagerMicros: order.wagerMicros,
    minOddsBps: order.minOddsBps,
    legs: order.legs,
    nonce: order.nonce,
    expiresAtMs: order.expiresAtMs,
    orderType: order.orderType,
    shieldOn: order.shieldOn,
    signature: bytesFrom(signature, 65, "signature"),
  });
}

export async function signedOrder(
  order: SignedOrder,
  useAppTokens: boolean,
  signingKey: `0x${string}`,
): Promise<SignedOrder> {
  return signOrder(order, useAppTokens, signingKey);
}

function missing(name: string): never {
  throw new Error(`${name} is required`);
}

function serdeDirection(direction: number): "up" | "down" {
  const parsed = Direction.fromU8(direction);
  if (parsed === Direction.Up) {
    return "up";
  }
  if (parsed === Direction.Down) {
    return "down";
  }
  throw new RangeError("invalid direction");
}

function serdeOrderType(orderType: OrderType | number): number {
  const raw = Number(orderType);
  if (OrderType.fromU8(raw) === undefined) {
    throw new RangeError("invalid order type");
  }
  return raw;
}
