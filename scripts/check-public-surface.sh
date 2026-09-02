#!/usr/bin/env bash
set -euo pipefail

if (( $# > 2 )); then
  echo "usage: $0 [--auto|--authoritative|--lexical-only] [--source|--packed]" >&2
  exit 2
fi

mode=${1:---auto}
surface_kind=${2:---source}
if [[ "$mode" != "--auto" && "$mode" != "--authoritative" && "$mode" != "--lexical-only" ]]; then
  echo "usage: $0 [--auto|--authoritative|--lexical-only] [--source|--packed]" >&2
  exit 2
fi
if [[ "$surface_kind" != "--source" && "$surface_kind" != "--packed" ]]; then
  echo "usage: $0 [--auto|--authoritative|--lexical-only] [--source|--packed]" >&2
  exit 2
fi

protocol_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
public_sources=(
  "$protocol_root/README.md"
  "$protocol_root/CUSTOM_CLIENTS.md"
  "$protocol_root/rust/src"
  "$protocol_root/rust/README.md"
  "$protocol_root/rust/CUSTOM_CLIENTS.md"
  "$protocol_root/python/src/longshot_protocol"
  "$protocol_root/python/README.md"
  "$protocol_root/typescript/src"
  "$protocol_root/typescript/README.md"
  "$protocol_root/typescript/CUSTOM_CLIENTS.md"
)
public_tests=(
  "$protocol_root/rust/tests"
  "$protocol_root/python/tests"
  "$protocol_root/typescript/tests"
)

external_mm_guide="$protocol_root/../vault-mm/docs/THIRD_PARTY_MM_GUIDE.md"
if [[ -f "$external_mm_guide" ]]; then
  public_sources+=("$external_mm_guide")
fi

private_route_fragments=(
  '/health'
  '/readyz'
  '/v1/auth/embedded-wallet/ensure'
  '/v1/auth/session'
  '/v1/chat/'
  '/v1/community-picks'
  '/v1/contests'
  '/v1/feed'
  '/v1/leaderboard'
  '/v1/market_category_visibility'
  '/v1/market-data/'
  '/v1/mm/taker_pnl'
  '/v1/nfl_hub_config'
  '/v1/observer_access_policy'
  '/v1/og/'
  '/v1/pool-images/'
  '/v1/portfolio/fantasy'
  '/v1/portfolio/summary'
  '/v1/recent-winners'
  '/v1/rfq/estimate/batch'
  '/v1/share-cards'
  '/v1/streak'
  '/v1/u/'
  '/v1/user/app_token_grants'
  '/v1/user/available_app_token_balance'
  '/v1/user/contest_bet'
  '/v1/user/deposit_app_token'
  '/v1/user/deposit_match'
  '/v1/user/deposit_vault'
  '/v1/user/features'
  '/v1/user/following/'
  '/v1/user/grant_app_token'
  '/v1/user/notifications'
  '/v1/user/profile/x'
  '/v1/user/push/'
  '/v1/user/referral'
  '/v1/user/request_withdrawal_vault'
  '/v1/user/reserved_app_token_balance'
  '/v1/user/set_referrer'
  '/v1/user/vault/'
  '/v1/vault/'
)

private_contract_fragments=(
  'ChatId'
  'ChatMentionCandidatesQuery'
  'ChatMessageEditResponse'
  'ChatReactionUpdateResponse'
  'ChatRecentMessagesQuery'
  'ChatStreamErrorCode'
  'ChatStreamErrorEvent'
  'ChatStreamQuery'
  'ContestDetailQuery'
  'ContestLeaderboardQuery'
  'ContestPopularEntryMarketResponse'
  'ContestPopularEntryResponse'
  'ContestTopParticipantRowResponse'
  'ContestTopParticipantsQuery'
  'ContestTopParticipantsResponse'
  'CreateSessionRequest'
  'CreditsGrantedNotificationPayload'
  'CursorParseError'
  'FantasyEntriesQuery'
  'FeedFilter'
  'FeedRawQuery'
  'FeedResponse'
  'FirstPartyClientMessage'
  'FirstPartyServerMessage'
  'HighlightEntry'
  'HighlightSortResponse'
  'HighlightsRawQuery'
  'LeaderboardHighlightsResponse'
  'LeaderboardMeRawQuery'
  'LeaderboardMetricResponse'
  'LeaderboardMyRankResponse'
  'LeaderboardRawQuery'
  'LeaderboardWindow'
  'LegacyLeaderboardEntry'
  'ListContestsQuery'
  'IndicativePriceResponseItem'
  'IndicativePriceResult'
  'IndicativePricesBatchRequest'
  'IndicativePricesBatchResponse'
  'MAX_INDICATIVE_PRICE_BATCH_ITEMS'
  'MessageId'
  'NotificationStreamRawQuery'
  'NotificationsRawQuery'
  'PnlHistoryQueryParseError'
  'PoolImageRawBytes'
  'PortfolioIntegrityError'
  'PortfolioSummaryRawQuery'
  'PositionQueryParseError'
  'PrivateClientMessage'
  'PrivateServerMessage'
  'QuoteDecline'
  'ReferralsListRawQuery'
  'StreakHistoryRawQuery'
  'StreakLeaderboardRawQuery'
  'StreakPicksRawQuery'
  'UserFeaturesResponse'
  'UserReferralStatsRawQuery'
  'can_transition_to_worker_owned'
  'chat_id'
  'grant_id'
  'finalize_onboarding'
  'first_party_subscribe'
  'into_signed_order_for_session'
  'indicative_price_batch'
  'manual_probability_bps'
  'marketStatusCanTransitionToWorkerOwned'
  'onboarding_completed'
  'quoteDecline'
  'quote_decline'
  'unsignedRfqOrderRequestToSignedOrderForSession'
)

forbidden_patterns=(
  '(^|[^[:alnum:]_])Admin[A-Z][[:alnum:]_]*([^[:alnum:]_]|$)'
  '(^|[^[:alnum:]_])Internal([A-Z][[:alnum:]_]*)?([^[:alnum:]_]|$)'
  'AcknowledgeReferral[A-Z][[:alnum:]_]*'
  'AppToken[A-Z][[:alnum:]_]*'
  'Chat(Author|Edit|Emoji|Emojis|Gif|MarketRoom|Mention|Message|Post|Reaction|Recent|Stream|UserAvatar)[A-Z][[:alnum:]_]*'
  'ClaimReferral[A-Z][[:alnum:]_]*'
  'Contest(Bet|Category|Direction|Game|Leg|Market|Perfect|Roster|Status|Tiebreaker|Type|User)[A-Z][[:alnum:]_]*'
  'Fantasy[A-Z][[:alnum:]_]*'
  'Feed[A-Z][[:alnum:]_]*'
  'Leaderboard[A-Z][[:alnum:]_]*'
  'LegGrade'
  'MarketChartSeries'
  'MarketWindow'
  'Nfl[A-Z][[:alnum:]_]*'
  'Notifications?[A-Z][[:alnum:]_]*'
  'PrimaryLegIdentityResponse'
  'PublicContest[A-Z][[:alnum:]_]*'
  'PublicProfile[A-Z][[:alnum:]_]*'
  'QuestionLeg'
  'QuestionsState'
  'Referral(Level|Prompt)[A-Z][[:alnum:]_]*'
  'RfqEstimateBatch[A-Z][[:alnum:]_]*'
  'ShareCard'
  'ShareImageRef'
  'ShareStat'
  'Streak[A-Z][[:alnum:]_]*'
  'Survivor[A-Z][[:alnum:]_]*'
  'User(CreateReferral|Referral|SetReferrer)[A-Z][[:alnum:]_]*'
  'Vault[A-Z][[:alnum:]_]*'
  'WebPush[A-Z][[:alnum:]_]*'
  'WindowAssetResult'
  '(^|[^[:alnum:]_])admin_[[:alnum:]_]+'
  '(^|[^[:alnum:]_])internal_[[:alnum:]_]+'
  '/v1/admin(/|[^[:alnum:]_])'
  '"internal"'
  "'internal'"
  'git_sha'
  'InviteCode'
  'invite_code'
  'signup_access_code'
  'UserAppTokenConfigRequest'
  'UserAppTokenDepositRequest'
  'UserAppTokenGrantResponse'
  'UserAppTokenGrantsResponse'
  'UserFundedGrantAppTokenRequest'
  'UserGrantAppTokenRequest'
  'UserGrantAppTokenResponse'
  'GrantAppTokenOperationResponse'
  'AvailableAppTokenBalanceResponse'
  'ReservedAppTokenBalanceResponse'
  'AppTokenGrantCategoryResponse'
  'AppTokenGrantsRawQuery'
  'TakerPnl'
  'HealthResponse'
  'ReadyzResponse'
  'WithdrawalPolicyResponse'
  'SignupPolicyResponse'
  'SignupDepositMatchPolicyResponse'
  'DepositMatchSourceResponse'
  'UserDepositMatchOpportunityResponse'
  'UserDepositMatchOpportunitiesResponse'
  '(^|[^[:alnum:]_])AvailableBalanceResponse([^[:alnum:]_]|$)'
  'CommunityPickReactionResponse'
  'CommunityPickResponse'
  'CommunityPicksResponse'
  'CommunityProfileResponse'
  'FollowStatusResponse'
  'PublicProfileFollowingResponse'
  'RecentWinnerResponse'
  'RecentWinnersResponse'
  'RecentMarketWinnerDetailRefResponse'
  'RecentContestWinnerDetailRefResponse'
  'RecentMarketWinnerEntryTypeResponse'
  'FeaturedMarketEventReference'
  'NflFeaturedMatchup'
  'NflFeaturedParlay'
  'NflParlayLeg'
  'NflHubConfig'
  'MarketDisplayContextResponse'
  'PriceMarketDisplayContextResponse'
  'SportsMarketDisplayContextResponse'
  'MarketCandles'
  'OhlcCandle'
  '(^|[^[:alnum:]_])ChartPoint([^[:alnum:]_]|$)'
  'MarketTickStream'
  'ExternalOddsSource'
  'EventMarketSource'
  'TopOfBook'
  'ReferencePriceResponse'
  'WindowResultsResponse'
  '(^|[^[:alnum:]_])WindowResult([^[:alnum:]_]|$)'
  '(^|[^[:alnum:]_])WindowDirection([^[:alnum:]_]|$)'
  '(^|[^[:alnum:]_])PriceSource([^[:alnum:]_]|$)'
  '(^|[^[:alnum:]_])SourceStatus([^[:alnum:]_]|$)'
  'MarketFairValue'
  '(^|[^[:alnum:]_])RfqRequest([^[:alnum:]_]|$)'
  'timescale_enabled'
  'cagg_enabled'
  'storage_read'
  'publisher_'
)
forbidden_public_prose_patterns=(
  'admin[-_ ]?(curated|pool|review)'
  'anonymous[-_ ]+sentinel'
  'base[-_ ]?edge[-_ ]?pricing'
  'control[-_ ]?plane'
  'fair[-_ ]?values?'
  'in[-_ ]?memory'
  'maker[-_ ]?pipeline'
  'memory[-_ ]?only'
  'payout[-_ ]?review[-_ ]?state'
  'provider[-_ ]?(backed|control[-_ ]?plane|event[-_ ]?start)'
  'internal[-_ ]+survivor'
  'strategy[-_ ]?spec'
  '(^|[^[:alnum:]_])terry([^[:alnum:]_]|$)'
)

public_openapi="$protocol_root/fixtures/api/openapi.json"
if [[ ! -f "$public_openapi" ]]; then
  echo "public-surface audit requires the public OpenAPI fixture" >&2
  exit 1
fi
private_contract_targets=("${public_sources[@]}" "${public_tests[@]}" "$public_openapi")

for path in "${private_route_fragments[@]}"; do
  if grep -R -n -F --exclude-dir=__pycache__ --exclude='*.pyc' \
    "$path" "${private_contract_targets[@]}"; then
    echo "public protocol repository contains a confirmed private route" >&2
    exit 1
  fi
done

for symbol in "${private_contract_fragments[@]}"; do
  if grep -R -n -F --exclude-dir=__pycache__ --exclude='*.pyc' \
    "$symbol" "${private_contract_targets[@]}"; then
    echo "public protocol repository contains a confirmed private contract" >&2
    exit 1
  fi
done

for pattern in "${forbidden_patterns[@]}"; do
  if grep -R -n -E --exclude-dir=__pycache__ --exclude='*.pyc' "$pattern" "${public_sources[@]}"; then
    echo "public protocol source contains a server-only contract" >&2
    exit 1
  fi
done

for pattern in "${forbidden_public_prose_patterns[@]}"; do
  if grep -R -n -i -E --exclude-dir=__pycache__ --exclude='*.pyc' \
    "$pattern" "${private_contract_targets[@]}"; then
    echo "public protocol repository contains server-only prose" >&2
    exit 1
  fi
done

for pattern in \
  'EventMarketSource' \
  'source_market_ids' \
  'source_event_id' \
  'source:event_id'; do
  if grep -R -n -E --exclude-dir=__pycache__ --exclude='*.pyc' \
    "$pattern" "${private_contract_targets[@]}"; then
    echo "public protocol repository contains a provider-identity contract" >&2
    exit 1
  fi
done

for provider in Kalshi Manifold Polymarket; do
  if grep -R -n -i -F --exclude-dir=__pycache__ --exclude='*.pyc' \
    "$provider" "${private_contract_targets[@]}"; then
    echo "public protocol repository contains a provider-identity contract" >&2
    exit 1
  fi
done

for pattern in 'invite[ _-]?codes?' 'access[ _-]?codes?'; do
  if grep -R -n -i -E --exclude-dir=__pycache__ --exclude='*.pyc' \
    "$pattern" "${public_sources[@]}" "${public_tests[@]}"; then
    echo "public protocol repository contains removed access-code guidance" >&2
    exit 1
  fi
done

for source in \
  "$protocol_root/rust/src/api/request.rs" \
  "$protocol_root/python/src/longshot_protocol/api.py" \
  "$protocol_root/typescript/src/api.ts"; do
  for required in CommunityPickRequest CommunityPickMode CreateRfqRequest CreateUnsignedRfqRequest; do
    if ! grep -q "$required" "$source"; then
      echo "public protocol source lost required external contract $required" >&2
      exit 1
    fi
  done
done

for source in \
  "$protocol_root/rust/src/api/mm_intel.rs" \
  "$protocol_root/python/src/longshot_protocol/api.py" \
  "$protocol_root/typescript/src/api.ts"; do
  for required in ProfitCapConfigResponse ProfitCapOverrideResponse; do
    if ! grep -q "$required" "$source"; then
      echo "public protocol source lost required market-maker contract $required" >&2
      exit 1
    fi
  done
done

if ! grep -q '"/v1/mm/profit_caps"' "$public_openapi"; then
  echo "public OpenAPI lost required market-maker profit-cap route" >&2
  exit 1
fi

for source in \
  "$protocol_root/rust/src/types/rfq.rs" \
  "$protocol_root/python/src/longshot_protocol/rfq.py" \
  "$protocol_root/typescript/src/rfq.ts"; do
  if ! grep -q 'BroadcastRfqRequest' "$source"; then
    echo "public protocol source lost required market-maker RFQ broadcast contract" >&2
    exit 1
  fi
done

for pattern in "${forbidden_patterns[@]}"; do
  openapi_pattern=$pattern
  if [[ "$pattern" == '(^|[^[:alnum:]_])Internal([A-Z][[:alnum:]_]*)?([^[:alnum:]_]|$)' ]]; then
    openapi_pattern='(^|[^[:alnum:]_])Internal[A-Z][[:alnum:]_]*([^[:alnum:]_]|$)'
  fi
  if grep -E -q "$openapi_pattern" "$public_openapi"; then
    echo "public OpenAPI contains a server-only contract" >&2
    exit 1
  fi
done
for pattern in \
  '(^|[^[:alnum:]_])admin([^[:alnum:]_]|$)' \
  '(^|[^[:alnum:]_])backend([^[:alnum:]_]|$)' \
  'first[-_ ]?party' \
  'server[-_ ]?owned'; do
  if grep -i -E -q "$pattern" "$public_openapi"; then
    echo "public OpenAPI contains server-only prose" >&2
    exit 1
  fi
done

if grep -i -E -q 'https?://' "$public_openapi"; then
  echo "public OpenAPI contains an unclassified external URL" >&2
  exit 1
fi

"${PYTHON:-python3}" "$protocol_root/scripts/check-archive-secrets.py" "$public_openapi"

if [[ "$mode" == "--lexical-only" ]]; then
  echo "public protocol lexical scan passed"
  exit 0
fi

typescript_surface_check=--check-public-surface
if [[ "$surface_kind" == "--packed" ]]; then
  typescript_surface_check=--check-packed-surface
fi
node "$protocol_root/typescript/scripts/generate-serde.mjs" "$typescript_surface_check"
"${PYTHON:-python3}" "$protocol_root/python/tools/generate_serde_metadata.py" --check
"${PYTHON:-python3}" "$protocol_root/python/tools/generate_api_stub.py" --check

monorepo_openapi="$protocol_root/../fixtures/api/openapi.json"
public_openapi_generator="$protocol_root/typescript/scripts/generate-public-openapi.mjs"
if [[ -f "$monorepo_openapi" && -f "$public_openapi_generator" ]]; then
  node "$public_openapi_generator" --check
elif [[ "$mode" == "--authoritative" && "$surface_kind" == "--source" ]]; then
  echo "authoritative source audit requires the private OpenAPI fixture and public generator" >&2
  exit 1
fi

echo "public protocol source matches the closed external contract inventory"
