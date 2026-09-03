import { privateKeyToAccount } from "viem/accounts";

import {
  bytesFrom,
  bytesToHex,
  checkU64,
  decodeBase64NoPad,
  encodeBase64NoPad,
} from "./bytes.js";
import {
  BroadcastRfqRequest,
  MAX_RFQ_LEGS,
  QuoteResponse,
  RFQ_PROTOCOL_VERSION,
} from "./rfq.js";
import { Address, Amount, ClientQuoteId, Odds, RequestId } from "./types.js";
import { ClientMessage } from "./ws.js";

export const AUTH_DOMAIN = "longshot.xyz";
const AUTH_CHALLENGE_ID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

export class MmDecodeError extends Error {
  readonly kind?: string;
  readonly expected?: number;
  readonly actual?: number;

  constructor(
    message: string,
    fields: { kind?: string; expected?: number; actual?: number } = {},
  ) {
    super(message);
    this.name = "MmDecodeError";
    this.kind = fields.kind;
    this.expected = fields.expected;
    this.actual = fields.actual;
  }
}

export type PrivateKey = `0x${string}`;

export function parseAuthChallengeId(challengeId: string): string {
  if (!AUTH_CHALLENGE_ID_PATTERN.test(challengeId)) {
    throw new Error("challenge ID must be canonical lowercase RFC 4122 UUIDv4 text");
  }
  return challengeId;
}

export function buildAuthMessage(
  authAddress: Address | string,
  challengeId: string,
  timestampMs: number | bigint | string,
): string {
  const address = Address.fromEvm(authAddress).toChecksum();
  const canonicalChallengeId = parseAuthChallengeId(challengeId);
  const timestamp = checkU64(timestampMs, "timestamp_ms");
  return `Longshot Market Maker WebSocket Authentication\n\nVersion: 1\nDomain: ${AUTH_DOMAIN}\nAuth Address: ${address}\nChallenge ID: ${canonicalChallengeId}\nTimestamp: ${timestamp}`;
}

export async function signAuthResponse(
  challengeId: string,
  timestampMs: number | bigint | string,
  signingKey: PrivateKey,
): Promise<Uint8Array> {
  const account = privateKeyToAccount(signingKey);
  const signature = await account.signMessage({
    message: buildAuthMessage(account.address, challengeId, timestampMs),
  });
  return bytesFrom(signature, 65, "signature");
}

export async function authResponseMessage(
  challengeId: string,
  timestampMs: number | bigint | string,
  signingKey: PrivateKey,
): Promise<ClientMessage> {
  const account = privateKeyToAccount(signingKey);
  return ClientMessage.authResponse(
    account.address,
    bytesToHex(await signAuthResponse(challengeId, timestampMs, signingKey)),
  );
}

export async function signQuoteResponse(
  quote: QuoteResponse,
  signingKey: PrivateKey,
): Promise<QuoteResponse> {
  const account = privateKeyToAccount(signingKey);
  const signature = await account.signMessage({
    message: { raw: bytesToHex(quote.signedDataBytes(), true) as `0x${string}` },
  });
  return new QuoteResponse({
    requestId: quote.requestId,
    odds: quote.odds,
    maxFillMicros: quote.maxFillMicros,
    clientQuoteId: quote.clientQuoteId,
    reserved: quote.reserved,
    signature: bytesFrom(signature, 65, "signature"),
  });
}

export async function signedQuoteResponse(
  requestId: RequestId,
  odds: Odds,
  maxFill: Amount,
  signingKey: PrivateKey,
  clientQuoteId?: ClientQuoteId,
): Promise<QuoteResponse> {
  return signQuoteResponse(QuoteResponse.new(requestId, odds, maxFill, clientQuoteId), signingKey);
}

export function encodeQuoteResponse(quote: QuoteResponse): string {
  return encodeBase64NoPad(quote.toBytes());
}

export function decodeQuoteResponse(data: string): QuoteResponse {
  const decoded = decodeBase64Payload(data);
  if (decoded.length !== QuoteResponse.SIZE) {
    throw new MmDecodeError(
      `invalid quote response payload size: expected ${QuoteResponse.SIZE} bytes, got ${decoded.length}`,
      { kind: "quote response", expected: QuoteResponse.SIZE, actual: decoded.length },
    );
  }
  return QuoteResponse.fromBytes(decoded);
}

export function quoteResponseMessage(quote: QuoteResponse): ClientMessage {
  return ClientMessage.quote(encodeQuoteResponse(quote));
}

export function decodeBroadcastRfq(data: string): BroadcastRfqRequest {
  const decoded = decodeBase64Payload(data);
  if (decoded.length !== BroadcastRfqRequest.SIZE) {
    throw new MmDecodeError(
      `invalid broadcast RFQ payload size: expected ${BroadcastRfqRequest.SIZE} bytes, got ${decoded.length}`,
      { kind: "broadcast RFQ", expected: BroadcastRfqRequest.SIZE, actual: decoded.length },
    );
  }
  const request = BroadcastRfqRequest.fromBytes(decoded);
  if (request.protocolVersion !== RFQ_PROTOCOL_VERSION) {
    throw new MmDecodeError(
      `unsupported RFQ protocol version: expected ${RFQ_PROTOCOL_VERSION}, got ${request.protocolVersion}`,
      { expected: RFQ_PROTOCOL_VERSION, actual: request.protocolVersion },
    );
  }
  if (request.legCount < 1 || request.legCount > MAX_RFQ_LEGS) {
    throw new MmDecodeError(
      `invalid broadcast RFQ leg count: expected 1..=${MAX_RFQ_LEGS}, got ${request.legCount}`,
    );
  }
  return request;
}

function decodeBase64Payload(data: string): Uint8Array {
  try {
    return decodeBase64NoPad(data);
  } catch (error) {
    throw new MmDecodeError(`invalid base64 payload: ${(error as Error).message}`);
  }
}
