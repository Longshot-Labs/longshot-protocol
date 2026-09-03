use longshot_protocol::api::{
    ConfirmPositionQuery, MarketCurrentQuery, MarketLookupQuery, PnlHistoryScopedQuery,
    PositionsByMarketsQuery, UserTransactionsRawQuery,
};
use serde::de::DeserializeOwned;
use serde_json::{json, Value};

fn assert_missing_required<T>()
where
    T: DeserializeOwned,
{
    assert!(
        serde_json::from_value::<T>(json!({})).is_err(),
        "{} must reject omitted required query fields",
        std::any::type_name::<T>()
    );
}

fn assert_accepts<T>(value: Value)
where
    T: DeserializeOwned,
{
    serde_json::from_value::<T>(value).unwrap_or_else(|error| {
        panic!(
            "{} rejected a valid query: {error}",
            std::any::type_name::<T>()
        )
    });
}

#[test]
fn client_query_contracts_require_route_required_fields() {
    assert_missing_required::<MarketLookupQuery>();
    assert_missing_required::<MarketCurrentQuery>();
    assert_missing_required::<PositionsByMarketsQuery>();
    assert_missing_required::<ConfirmPositionQuery>();

    assert_accepts::<MarketLookupQuery>(
        json!({"asset": "BTC", "duration_secs": 300, "window_start_ms": 1}),
    );
    assert_accepts::<MarketCurrentQuery>(json!({"asset": "BTC", "duration_secs": 300}));
    assert_accepts::<PositionsByMarketsQuery>(json!({"market_ids": "1,2"}));
    assert_accepts::<ConfirmPositionQuery>(json!({"position_id": "position", "accept": true}));
}

#[test]
fn client_query_contracts_use_semantic_scalar_types() {
    assert!(serde_json::from_value::<MarketLookupQuery>(
        json!({"asset": "BTC", "duration_secs": "300", "window_start_ms": "1"})
    )
    .is_err());
    assert!(serde_json::from_value::<MarketCurrentQuery>(
        json!({"asset": "BTC", "duration_secs": "300"})
    )
    .is_err());
    assert!(serde_json::from_value::<ConfirmPositionQuery>(
        json!({"position_id": "position", "accept": "true"})
    )
    .is_err());

    let scoped = serde_json::from_value::<PnlHistoryScopedQuery>(
        json!({"from": 1, "to": 2, "scope": "all"}),
    )
    .expect("integer PNL bounds should decode");
    assert_eq!(scoped.from, Some(1));
    assert_eq!(scoped.to, Some(2));
    assert!(serde_json::from_value::<PnlHistoryScopedQuery>(json!({"from": "1"})).is_err());

    let transactions = serde_json::from_value::<UserTransactionsRawQuery>(json!({
        "category": "withdrawal",
        "from_ms": "1",
        "to_ms": "2",
        "limit": 25,
        "cursor": "1:550e8400-e29b-41d4-a716-446655440000"
    }))
    .expect("user transaction query should decode its route wire types");
    assert_eq!(transactions.limit, Some(25));
    assert!(serde_json::from_value::<UserTransactionsRawQuery>(json!({
        "limit": "25"
    }))
    .is_err());
    assert!(serde_json::from_value::<UserTransactionsRawQuery>(json!({
        "unexpected": true
    }))
    .is_err());
}
