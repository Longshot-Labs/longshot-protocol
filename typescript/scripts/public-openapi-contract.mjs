export const PUBLIC_OPENAPI_OPERATIONS = Object.freeze([
  "GET /v1/access",
  "POST /v1/auth/logout",
  "POST /v1/auth/wallet",
  "GET /v1/fees",
  "GET /v1/markets",
  "GET /v1/markets/{id}",
  "GET /v1/mm/profit_caps",
  "GET /v1/mm/recent_resolutions",
  "GET /v1/mm/rfq/{id}/status",
  "GET /v1/portfolio",
  "GET /v1/portfolio/pnl",
  "GET /v1/portfolio/positions",
  "GET /v1/positions",
  "GET /v1/positions/active",
  "GET /v1/positions/{id}",
  "GET /v1/price-markets/current",
  "GET /v1/price-markets/lookup",
  "GET /v1/referrals/{code}",
  "POST /v1/rfq",
  "POST /v1/rfq/estimate",
  "POST /v1/rfq/unsigned",
  "GET /v1/rfq/{id}",
  "POST /v1/rfq/{id}/cancel",
  "GET /v1/user/available_balance",
  "POST /v1/user/confirm_position",
  "GET /v1/user/preferences",
  "PUT /v1/user/preferences",
  "GET /v1/user/profile",
  "PUT /v1/user/profile",
  "GET /v1/user/profile/check-handle",
  "GET /v1/user/reserved_balance",
  "GET /v1/user/transactions",
  "POST /v1/users/deposit",
  "GET /v1/users/deposit-wallet",
  "POST /v1/users/withdraw",
]);

export const PUBLIC_OPENAPI_COMPONENT_NAMES = Object.freeze({
  schemas: Object.freeze(words(`
    AcceptedWithdrawOperationResponse AccessResponse ActivePosition ActivePositionStatus ActivePositionsResponse
    BalanceOperationStatus BalanceOperationStatusResponse CancelResponse CheckHandleResponse CommunityPickMode
    CommunityPickRequest CreateRfqRequest CreateUnsignedRfqRequest DepositOperationResponse ErrorResponse
    EventMarket FeeScheduleResponse FeeScheduleTier LegDetail MarketId
    MarketLookupResponse MarketMetadataEntry MarketStatus MarketType MmRfqStatusResponse
    OrderLegJson Outcome PnlEventResponse PnlHistoryResponse PortfolioStatsResponse
    PositionDetailResponse PositionRole PositionSortQueryParam PositionStatusQueryParam PositionSummary
    PositionsByMarketsResponse PositionsListResponse PreferencesResponse PriceStrikeMarket ProfileResponse ProfitCapConfigResponse
    ProfitCapOverrideResponse
    PublicMarket PublicMarketResponse PublicMarketsResponse PublicReferralCodeResponse PublicReferralDepositMatchOffer
    PublicReferralInviterResponse PublicReferralStatusResponse QueuedWithdrawalResponse QuoteTolerancePreference RecentResolutionEntry
    RecentResolutionsResponse ReservedBalanceResponse RfqEstimateRequest RfqEstimateResponse RfqResponse
    RfqStatus SessionResponse SignedOrderJson TierFeeRate TradingChannel
    UnsignedRfqOrderRequest UpdatePreferencesRequest UpdateProfileRequest UserAvailableBalanceResponse UserDepositRequest
    UserDepositResponse UserDepositWalletResponse UserTransactionCategory UserTransactionFunding UserTransactionResponse
    UserTransactionStatus UserTransactionUnit UserTransactionsResponse UserWithdrawParams UserWithdrawRequest
    UserWithdrawResponse WalletAuthRequest WithdrawOperationResponse WithdrawalAuthorization WithdrawalDeliveryStatus
  `)),
  securitySchemes: Object.freeze(["bearer_auth"]),
});

// Serde contracts that are externally supported but are not named components
// in the public HTTP OpenAPI document.
export const PUBLIC_PROTOCOL_SUPPLEMENTAL_SCHEMAS = Object.freeze(words(`
  Amount Asset CheckHandleQuery ClientMessage ConfirmPositionQuery Direction Duration
  HandleAvailabilityQuery MarketCurrentQuery MarketLookupQuery Odds OrderType PnlHistoryQuery
  PnlHistoryScopedQuery PositionsByMarketsQuery PositionsQuery PublicMarketsRawQuery QuoteResultStatus
  RecentResolutionsQuery RfqSubscription ServerMessage Timestamp UserTier UserTransactionsRawQuery
`));

// Public Rust types that intentionally do not implement Serde. Every Serde
// type is closed by the OpenAPI and supplemental schema inventories above.
export const PUBLIC_PROTOCOL_NON_SERDE_TYPES = Object.freeze(words(`
  AuthChallengeIdError BroadcastRfqRequest MathError MmDecodeError OrderLeg
  OrderLegParseError ParsedOrderLeg QuoteResponse RfqLeg RfqLegType RfqLegWire
  RfqLegWireDecodeError RfqOrderJsonError SignedOrder SignedOrderError TakerMetadata TakerSignError
`));

function words(source) {
  return source.trim().split(/\s+/u);
}
