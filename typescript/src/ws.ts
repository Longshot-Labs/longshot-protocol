import { Asset, RequestId } from "./types.js";
import type { WideInteger } from "./types.js";

export const QuoteResultStatus = {
  Filled: "filled",
  NotFilled: "not_filled",
  Rejected: "rejected",
  SelectedFailed: "selected_failed",
} as const;
export type QuoteResultStatus = (typeof QuoteResultStatus)[keyof typeof QuoteResultStatus];

export const QuoteDeclineReason = {
  SportsCombinationUnsupported: "sports_combination_unsupported",
} as const;
export type QuoteDeclineReason =
  (typeof QuoteDeclineReason)[keyof typeof QuoteDeclineReason];

export type RfqSubscription =
  | { type: "all" }
  | { type: "binary_event" }
  | { type: "price_strike"; asset: string };

export const RfqSubscription = {
  all(): RfqSubscription {
    return { type: "all" };
  },
  binaryEvent(): RfqSubscription {
    return { type: "binary_event" };
  },
  priceStrike(asset: Asset | string): RfqSubscription {
    // String inputs are a convenience API, but the wire value must still match
    // Rust's closed Asset enum rather than forwarding arbitrary client text.
    const parsed = typeof asset === "string" ? Asset.parseSymbol(asset) : Asset.fromU8(asset);
    if (parsed === undefined) {
      throw new RangeError("unsupported asset");
    }
    return {
      type: "price_strike",
      asset: Asset.serdeValue(parsed),
    };
  },
};

export type ClientMessage =
  | { type: "auth" }
  | { type: "auth_response"; wallet_address: string; signature: string }
  | { type: "quote"; data: string }
  | { type: "quote_decline"; request_id: string; reason: QuoteDeclineReason }
  | { type: "pong" }
  | { type: "subscribe"; protocol_version: number; subscriptions: RfqSubscription[] };

export const ClientMessage = {
  auth(): ClientMessage {
    return { type: "auth" };
  },
  authResponse(walletAddress: string, signature: string): ClientMessage {
    return { type: "auth_response", wallet_address: walletAddress, signature };
  },
  quote(data: string): ClientMessage {
    return { type: "quote", data };
  },
  quoteDecline(requestId: RequestId, reason: QuoteDeclineReason): ClientMessage {
    return { type: "quote_decline", request_id: requestId.serdeValue(), reason };
  },
  pong(): ClientMessage {
    return { type: "pong" };
  },
  subscribe(protocolVersion: number, subscriptions: RfqSubscription[]): ClientMessage {
    return { type: "subscribe", protocol_version: protocolVersion, subscriptions };
  },
};

export type ServerMessage =
  | { type: "auth_challenge"; challenge_id: string; timestamp_ms: WideInteger }
  | { type: "auth_result"; success: boolean; error?: string | null; session_token?: string | null }
  | { type: "rfq"; data: string }
  | { type: "subscribed"; protocol_version: number }
  | {
      type: "quote_ack";
      request_id: string;
      quote_id: string;
      client_quote_id?: string | null;
      accepted: boolean;
      error?: string | null;
    }
  | {
      type: "quote_result";
      request_id: string;
      quote_id: string;
      client_quote_id?: string | null;
      status: QuoteResultStatus;
      position_id?: string | null;
      fill_amount?: string | null;
      fill_odds?: number | null;
      filled_at_ms?: WideInteger | null;
      reason?: string | null;
    }
  | { type: "ping"; timestamp: WideInteger }
  | { type: "error"; code: string; message: string }
  | { type: "rate_limit"; retry_after_ms: WideInteger };

export const ServerMessage = {
  authChallenge(challengeId: string, timestampMs: WideInteger): ServerMessage {
    return { type: "auth_challenge", challenge_id: challengeId, timestamp_ms: timestampMs };
  },
  authResult(success: boolean, error?: string | null, sessionToken?: string | null): ServerMessage {
    return { type: "auth_result", success, error, session_token: sessionToken };
  },
  rfq(data: string): ServerMessage {
    return { type: "rfq", data };
  },
  subscribed(protocolVersion: number): ServerMessage {
    return { type: "subscribed", protocol_version: protocolVersion };
  },
  quoteAck(fields: Omit<Extract<ServerMessage, { type: "quote_ack" }>, "type">): ServerMessage {
    return { type: "quote_ack", ...fields };
  },
  quoteResult(
    fields: Omit<Extract<ServerMessage, { type: "quote_result" }>, "type">,
  ): ServerMessage {
    return { type: "quote_result", ...fields };
  },
  ping(timestamp: WideInteger): ServerMessage {
    return { type: "ping", timestamp };
  },
  error(code: string, message: string): ServerMessage {
    return { type: "error", code, message };
  },
  rateLimit(retryAfterMs: WideInteger): ServerMessage {
    return { type: "rate_limit", retry_after_ms: retryAfterMs };
  },
};
