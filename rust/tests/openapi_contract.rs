#![cfg(feature = "openapi")]

use longshot_protocol::api::{
    AcknowledgeReferralPromptRequest, ClaimReferralPromptResponse, LeaderboardPnlCaller,
    LeaderboardPnlEntry, PortfolioSummaryResponse, PublicProfileStreakHistoryResponse,
    PublicProfileStreakPicksResponse, PublicProfileSummaryResponse,
    PublicReferralDepositMatchOffer, QueuedWithdrawalResponse, RfqEstimateResponse, ShareImageRef,
    StreakHistoryResponse, StreakLeaderboardResponse, StreakLeaderboardRowResponse,
    StreakMarketResponse, StreakPickHistoryItemResponse, StreakPicksResponse,
    StreakPopularMarketResponse, StreakPopularTodayResponse, StreakRunResponse,
    StreakRunTierPayoutResponse, UserAppTokenGrantResponse, UserAvailableBalanceResponse,
    UserDepositMatchOpportunitiesResponse, UserDepositMatchOpportunityResponse,
};
use serde_json::Value;
use utoipa::ToSchema;

fn assert_string_properties<T>(field_names: &[&str])
where
    T: for<'schema> ToSchema<'schema>,
{
    let schema = serde_json::to_value(T::schema().1).expect("schema should serialize");
    let properties = schema
        .get("properties")
        .and_then(Value::as_object)
        .expect("struct schema should contain object properties");

    for field_name in field_names {
        assert_eq!(
            properties[*field_name].get("type"),
            Some(&Value::String("string".to_owned())),
            "{field_name} must be documented as the decimal string emitted by its wire-int serializer"
        );
        assert_eq!(
            properties[*field_name].get("format"),
            Some(&Value::String("int64".to_owned())),
            "{field_name} must retain its signed or unsigned 64-bit integer format"
        );
    }
}

fn assert_uuid_property<T>(field_name: &str)
where
    T: for<'schema> ToSchema<'schema>,
{
    let schema = serde_json::to_value(T::schema().1).expect("schema should serialize");
    let property = &schema["properties"][field_name];

    // UUIDs are primitives in the wire contract. Keeping them inline prevents
    // Utoipa from emitting references to a `Uuid` component that is never defined.
    assert_eq!(property.get("$ref"), None, "{field_name} must be inline");
    assert_eq!(property.get("type"), Some(&Value::String("string".into())));
    assert_eq!(property.get("format"), Some(&Value::String("uuid".into())));
}

fn assert_required_properties<T>(field_names: &[&str])
where
    T: for<'schema> ToSchema<'schema>,
{
    let schema = serde_json::to_value(T::schema().1).expect("schema should serialize");
    let required = schema
        .get("required")
        .and_then(Value::as_array)
        .expect("struct schema should contain required properties");

    for field_name in field_names {
        assert!(
            required
                .iter()
                .any(|value| value.as_str() == Some(field_name)),
            "{field_name} must be required"
        );
    }
}

#[test]
fn wire_integer_openapi_fields_are_decimal_strings() {
    // These values intentionally cross JavaScript's safe-integer boundary: the
    // string wire format preserves exact micros, so OpenAPI must promise strings too.
    let balance = UserAvailableBalanceResponse {
        available_micros: 9_007_199_254_740_993,
        pending_custodial_deposit_micros: 2,
        credited_custodial_deposit_micros: 3,
        deposit_withdrawal_min_micros: 4,
    };
    let wire = serde_json::to_value(balance).expect("balance should serialize");
    assert_eq!(wire["available_micros"], "9007199254740993");

    assert_string_properties::<LeaderboardPnlEntry>(&["pnl_micros"]);
    assert_string_properties::<LeaderboardPnlCaller>(&["pnl_micros"]);
    assert_string_properties::<PortfolioSummaryResponse>(&[
        "potential_payout_micros",
        "realized_pnl_micros",
        "biggest_win_micros",
    ]);
    assert_string_properties::<PublicProfileSummaryResponse>(&[
        "potential_payout_micros",
        "realized_pnl_micros",
        "biggest_win_micros",
    ]);
    assert_string_properties::<UserAvailableBalanceResponse>(&[
        "available_micros",
        "pending_custodial_deposit_micros",
        "credited_custodial_deposit_micros",
        "deposit_withdrawal_min_micros",
    ]);
    assert_string_properties::<QueuedWithdrawalResponse>(&["amount_micros"]);
    assert_string_properties::<PublicReferralDepositMatchOffer>(&["match_limit_micros"]);
    assert_string_properties::<ClaimReferralPromptResponse>(&["amount_micros"]);
    assert_string_properties::<UserDepositMatchOpportunityResponse>(&[
        "match_limit_micros",
        "matched_micros",
    ]);
    assert_string_properties::<UserDepositMatchOpportunitiesResponse>(&["total_available_micros"]);
    assert_string_properties::<StreakRunTierPayoutResponse>(&["payout_micros"]);
    assert_string_properties::<StreakRunResponse>(&["cash_payout_micros"]);
}

#[test]
fn uuid_openapi_fields_are_inline_string_formats() {
    assert_uuid_property::<AcknowledgeReferralPromptRequest>("claim_token");
    assert_uuid_property::<RfqEstimateResponse>("request_id");
    assert_uuid_property::<QueuedWithdrawalResponse>("operation_id");
    assert_uuid_property::<UserAppTokenGrantResponse>("grant_id");
    assert_uuid_property::<ClaimReferralPromptResponse>("claim_token");

    let schema = serde_json::to_value(ShareImageRef::schema().1).expect("schema should serialize");
    let pool_image_id = &schema["oneOf"][0]["properties"]["pool_image_id"];
    assert_eq!(
        pool_image_id.get("$ref"),
        None,
        "pool_image_id must be inline"
    );
    assert_eq!(
        pool_image_id.get("type"),
        Some(&Value::String("string".into()))
    );
    assert_eq!(
        pool_image_id.get("format"),
        Some(&Value::String("uuid".into()))
    );
}

#[test]
fn streak_nullable_present_fields_remain_required_in_openapi() {
    // These Option fields serialize as explicit null when empty. They are
    // nullable values, not omittable properties, unless serde says otherwise.
    assert_required_properties::<StreakMarketResponse>(&[
        "outcome",
        "source",
        "resolution_time_ms",
        "betting_closes_at_ms",
    ]);
    assert_required_properties::<StreakPickHistoryItemResponse>(&[
        "market_outcome",
        "betting_closes_at_ms",
        "resolved_at_ms",
    ]);
    assert_required_properties::<StreakPicksResponse>(&["contest_id", "next_cursor"]);
    assert_required_properties::<PublicProfileStreakPicksResponse>(&["contest_id", "next_cursor"]);
    assert_required_properties::<StreakRunResponse>(&[
        "end_game_index",
        "ended_at_ms",
        "failed_pick_number",
        "failed_pick",
    ]);
    assert_required_properties::<StreakHistoryResponse>(&["next_cursor"]);
    assert_required_properties::<PublicProfileStreakHistoryResponse>(&["next_cursor"]);
    assert_required_properties::<StreakPopularMarketResponse>(&["betting_closes_at_ms"]);
    assert_required_properties::<StreakPopularTodayResponse>(&["contest_id", "game_index"]);
    assert_required_properties::<StreakLeaderboardRowResponse>(&[
        "x_handle",
        "x_avatar_url",
        "current_pick",
    ]);
    assert_required_properties::<StreakLeaderboardResponse>(&["contest_id", "current_game_index"]);
}
