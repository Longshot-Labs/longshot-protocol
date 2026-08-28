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
)

for pattern in "${forbidden_patterns[@]}"; do
  if grep -R -n -E --exclude-dir=__pycache__ --exclude='*.pyc' "$pattern" "${public_sources[@]}"; then
    echo "public protocol source contains a server-only contract" >&2
    exit 1
  fi
done

echo "public protocol source excludes classified server-only contracts"
