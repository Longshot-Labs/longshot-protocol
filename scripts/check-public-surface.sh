#!/usr/bin/env bash
set -euo pipefail

protocol_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
public_sources=(
  "$protocol_root/rust/src"
  "$protocol_root/python/src/longshot_protocol"
  "$protocol_root/typescript/src"
)

forbidden_patterns=(
  '(^|[^[:alnum:]_])AdminGrant([^[:alnum:]_]|$)'
  '(^|[^[:alnum:]_])Internal([^[:alnum:]_]|$)'
  'admin_grant'
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
  'ProfitCap'
  'MaxPayoutConfigResponse'
  'HealthResponse'
  'ReadyzResponse'
  'WithdrawalPolicyResponse'
  'BettingPolicyResponse'
  'SignupPolicyResponse'
  'SignupDepositMatchPolicyResponse'
  'DepositMatchSourceResponse'
  'UserDepositMatchOpportunityResponse'
  'UserDepositMatchOpportunitiesResponse'
  'CommunityPicksRawQuery'
  'CommunityPicksResponse'
  'CommunityPickReactionResponse'
  'CommunityPickResponse'
  'CommunityProfileResponse'
  'FollowStatusResponse'
  'FollowingRawQuery'
  'MarketDisplayContextResponse'
  'NflFeaturedMatchup'
  'NflFeaturedParlay'
  'NflHubConfig'
  'NflParlayLeg'
  'PublicProfileFollowingResponse'
  'RecentContestWinnerDetailRefResponse'
  'RecentMarketWinnerDetailRefResponse'
  'RecentMarketWinnerEntryTypeResponse'
  'RecentWinner'
  'include_featured'
  'featured_only'
)

for pattern in "${forbidden_patterns[@]}"; do
  if grep -R -n -E --exclude-dir=__pycache__ --exclude='*.pyc' "$pattern" "${public_sources[@]}"; then
    echo "public protocol source contains an excluded contract" >&2
    exit 1
  fi
done

for source in \
  "$protocol_root/rust/src/api/request.rs" \
  "$protocol_root/python/src/longshot_protocol/api.py" \
  "$protocol_root/typescript/src/api.ts"; do
  if ! grep -q 'CommunityPickRequest' "$source"; then
    echo "public protocol source lost required Tail/Fade attribution" >&2
    exit 1
  fi
done

if sed -n '/pub struct EventMarket {/,/^}/p' "$protocol_root/rust/src/api/markets.rs" \
  | grep -n 'featured_slot'; then
  echo "public EventMarket contains first-party featured placement" >&2
  exit 1
fi

echo "public protocol source excludes server-only and first-party presentation contracts"
