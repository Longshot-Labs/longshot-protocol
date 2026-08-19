import { privateKeyToAccount } from "viem/accounts";

import {
  Amount,
  Direction,
  OrderLeg,
  OrderType,
  Odds,
  RequestId,
  SignedOrder,
  authResponseMessage,
  buildWalletAuthenticationMessage,
  buildWalletWithdrawalAuthorizationMessage,
  createRfqRequestFromSignedOrder,
  decodeApiJson,
  encodeWalletSignature,
  quoteResponseMessage,
  signOrder,
  signedQuoteResponse,
  stringifySerde,
  type ClientMessage,
  type RecentResolutionEntry,
  type UserWithdrawRequest,
  type WalletAuthRequest,
} from "../src/index.js";

type IntegerInput = number | bigint;

export interface SignedRfqExampleInput {
  signingKey: `0x${string}`;
  marketId: IntegerInput;
  direction: Direction;
  wagerMicros: IntegerInput;
  minOddsBps: number;
  nonce: IntegerInput;
  expiresAtMs: IntegerInput;
  orderType: OrderType;
  shieldOn: boolean;
  useAppTokens: boolean;
}

export interface WalletAuthExampleInput {
  signingKey: `0x${string}`;
  domain: string;
  signedAtMs: IntegerInput;
  inviteCode?: string;
  referralCode?: string;
}

export interface WalletWithdrawalExampleInput {
  signingKey: `0x${string}`;
  domain: string;
  chainId: IntegerInput;
  destinationAddress: string;
  amountMicros: IntegerInput;
  idempotencyKey: string;
  signedAtMs: IntegerInput;
}

export interface MmQuoteExampleInput {
  signingKey: `0x${string}`;
  requestId: string;
  oddsBps: number;
  maxFillMicros: IntegerInput;
}

/** Decode raw response text before JavaScript can round wide API integers. */
export function decodeRecentResolution(json: string): RecentResolutionEntry {
  return decodeApiJson<RecentResolutionEntry>(json, "RecentResolutionEntry");
}

/** Build a direct-wallet authentication request body without choosing an HTTP transport. */
export async function buildWalletAuthBody(input: WalletAuthExampleInput): Promise<string> {
  const account = privateKeyToAccount(input.signingKey);
  const message = buildWalletAuthenticationMessage(
    input.domain,
    account.address,
    input.signedAtMs,
  );
  const signature = await account.signMessage({ message });
  const request: WalletAuthRequest = {
    address: account.address,
    signature: encodeWalletSignature(signature),
    signed_at_ms: input.signedAtMs,
    invite_code: input.inviteCode,
    referral_code: input.referralCode,
  };
  return stringifySerde(request);
}

/** Construct, sign, and serialize an RFQ request body without choosing an HTTP transport. */
export async function buildSignedRfqBody(input: SignedRfqExampleInput): Promise<string> {
  const account = privateKeyToAccount(input.signingKey);
  const unsignedOrder = new SignedOrder({
    user: account.address,
    wagerMicros: input.wagerMicros,
    minOddsBps: input.minOddsBps,
    legs: [new OrderLeg({ marketId: input.marketId, direction: input.direction })],
    nonce: input.nonce,
    expiresAtMs: input.expiresAtMs,
    orderType: input.orderType,
    shieldOn: input.shieldOn,
  });

  const order = await signOrder(unsignedOrder, input.useAppTokens, input.signingKey);
  if (!(await order.verifySignature(input.useAppTokens))) {
    throw new Error("signed RFQ failed local signature verification");
  }

  // Funding selection is signed, so the request must carry the same value.
  return stringifySerde(createRfqRequestFromSignedOrder(order, input.useAppTokens));
}

/** Build a wallet-authorized withdrawal request body without choosing an HTTP transport. */
export async function buildWalletWithdrawalBody(
  input: WalletWithdrawalExampleInput,
): Promise<string> {
  const account = privateKeyToAccount(input.signingKey);
  const message = buildWalletWithdrawalAuthorizationMessage(
    input.domain,
    input.chainId,
    account.address,
    input.destinationAddress,
    input.amountMicros,
    input.idempotencyKey,
    input.signedAtMs,
  );
  const signature = await account.signMessage({ message });
  const request: UserWithdrawRequest = {
    withdraw_params: {
      amount_micros: input.amountMicros,
      destination_address: input.destinationAddress,
      idempotency_key: input.idempotencyKey,
    },
    authorization: {
      type: "wallet_signature",
      signature: encodeWalletSignature(signature),
      signed_at_ms: input.signedAtMs,
    },
  };
  return stringifySerde(request);
}

/** Answer an MM challenge using the server-supplied UUID and timestamp. */
export function buildMmAuthResponse(
  challengeId: string,
  timestampMs: IntegerInput,
  signingKey: `0x${string}`,
): Promise<ClientMessage> {
  return authResponseMessage(challengeId, timestampMs, signingKey);
}

/** Build a signed, unpadded-Base64 MM quote message. */
export async function buildMmQuoteMessage(input: MmQuoteExampleInput): Promise<ClientMessage> {
  const quote = await signedQuoteResponse(
    RequestId.fromString(input.requestId),
    new Odds(input.oddsBps),
    Amount.fromMicro(input.maxFillMicros),
    input.signingKey,
  );
  return quoteResponseMessage(quote);
}
