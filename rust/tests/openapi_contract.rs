#![cfg(feature = "openapi")]

use longshot_protocol::api::{
    PositionDetailResponse, PositionSummary, ProfitCapConfigResponse, ProfitCapOverrideResponse,
    PublicReferralDepositMatchOffer, QueuedWithdrawalResponse, RfqEstimateResponse,
    UserAvailableBalanceResponse, UserTransactionCategory, UserTransactionResponse,
    UserTransactionStatus, UserTransactionUnit, UserTransactionsResponse, WithdrawalStage,
};
use longshot_protocol::types::MarketType;
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

fn assert_required_nullable_string_properties<T>(field_names: &[&str])
where
    T: for<'schema> ToSchema<'schema>,
{
    let schema = serde_json::to_value(T::schema().1).expect("schema should serialize");
    let required = schema["required"]
        .as_array()
        .expect("struct schema should contain required fields");

    assert_string_properties::<T>(field_names);
    for field_name in field_names {
        assert!(
            required.iter().any(|value| value == *field_name),
            "{field_name} must be required because the wire key is always present"
        );
        assert_eq!(
            schema["properties"][*field_name].get("nullable"),
            Some(&Value::Bool(true)),
            "{field_name} must allow null until the position resolves"
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

#[test]
fn wire_integer_openapi_fields_are_decimal_strings() {
    // These values intentionally cross JavaScript's safe-integer boundary: the
    // string wire format preserves exact micros, so OpenAPI must promise strings too.
    let balance = UserAvailableBalanceResponse {
        available_micros: 9_007_199_254_740_993,
        pending_custodial_deposit_micros: 2,
        credited_custodial_deposit_micros: 3,
        deposit_withdrawal_min_micros: 4,
        withdrawal_max_micros: 10_000_000_000,
    };
    let wire = serde_json::to_value(balance).expect("balance should serialize");
    assert_eq!(wire["available_micros"], "9007199254740993");

    assert_string_properties::<UserAvailableBalanceResponse>(&[
        "available_micros",
        "pending_custodial_deposit_micros",
        "credited_custodial_deposit_micros",
        "deposit_withdrawal_min_micros",
        "withdrawal_max_micros",
    ]);
    assert_string_properties::<QueuedWithdrawalResponse>(&["amount_micros"]);
    assert_string_properties::<PublicReferralDepositMatchOffer>(&["match_limit_micros"]);
    assert_string_properties::<UserTransactionResponse>(&["amount_micros"]);
}

#[test]
fn position_outcome_fields_are_required_and_nullable() {
    let fields = [
        "refunded_app_token_micros",
        "net_payout_micros",
        "pnl_micros",
    ];

    // Serde requires these keys even though their values remain null until the
    // corresponding outcome exists. Keep OpenAPI aligned with that wire shape.
    assert_required_nullable_string_properties::<PositionSummary>(&fields);
    assert_required_nullable_string_properties::<PositionDetailResponse>(&fields);
}

#[test]
fn public_profit_cap_contract_is_exported() {
    let document: Value = serde_json::from_str(include_str!("../../fixtures/api/openapi.json"))
        .expect("public OpenAPI fixture should parse");

    assert!(document["paths"]["/v1/mm/profit_caps"]["get"].is_object());
    for schema in ["ProfitCapConfigResponse", "ProfitCapOverrideResponse"] {
        assert!(
            document["components"]["schemas"][schema].is_object(),
            "{schema} must remain public"
        );
    }

    let response = ProfitCapConfigResponse {
        default_max_profit_micros: 9_007_199_254_740_993,
        overrides: vec![ProfitCapOverrideResponse {
            market_type: MarketType::from(MarketType::SPORTS),
            max_profit_micros: u64::MAX,
        }],
    };
    let wire = serde_json::to_value(response).expect("profit caps should serialize");
    assert_eq!(wire["default_max_profit_micros"], 9_007_199_254_740_993_u64);
    assert_eq!(wire["overrides"][0]["max_profit_micros"], u64::MAX);
}

#[test]
fn user_transactions_preserve_wire_amounts_and_omit_optional_details() {
    let wire = serde_json::to_value(UserTransactionsResponse {
        items: vec![UserTransactionResponse {
            id: "ledger-event".to_owned(),
            category: UserTransactionCategory::Withdrawal,
            title: "Withdrawal".to_owned(),
            detail: None,
            status: UserTransactionStatus::Completed,
            occurred_at_ms: 1_700_000_000_000,
            amount_micros: -9_007_199_254_740_993,
            unit: UserTransactionUnit::Usdc,
            funding: None,
            network: None,
            wallet_address: None,
            tx_hash: Some("0xabc".to_owned()),
            source: None,
            expires_at_ms: None,
            reason: None,
            reference: None,
            withdrawal_stage: Some(WithdrawalStage::Completed),
            available_at_ms: None,
            submission_tx_hash: None,
        }],
        next_cursor: None,
    })
    .expect("transaction response should serialize");

    assert_eq!(wire["items"][0]["amount_micros"], "-9007199254740993");
    assert_eq!(wire["items"][0]["category"], "withdrawal");
    assert_eq!(wire["items"][0]["status"], "completed");
    assert!(wire["items"][0].get("detail").is_none());
    assert_eq!(wire["next_cursor"], Value::Null);
}

#[test]
fn uuid_openapi_fields_are_inline_string_formats() {
    assert_uuid_property::<RfqEstimateResponse>("request_id");
    assert_uuid_property::<QueuedWithdrawalResponse>("operation_id");
}
