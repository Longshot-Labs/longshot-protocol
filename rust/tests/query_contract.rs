use longshot_protocol::api::{
    ChatMentionCandidatesQuery, ConfirmPositionQuery, MarketCurrentQuery, MarketLookupQuery,
    PnlHistoryScopedQuery, PositionsByMarketsQuery, TakerPnlQuery, TopOfBookHistoryQuery,
    VaultContributorsQuery, VaultEventsQuery, VaultIdQuery, VaultPnlHistoryQuery,
    VaultPositionsQuery,
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
    assert_missing_required::<ChatMentionCandidatesQuery>();
    assert_missing_required::<MarketLookupQuery>();
    assert_missing_required::<MarketCurrentQuery>();
    assert_missing_required::<TopOfBookHistoryQuery>();
    assert_missing_required::<TakerPnlQuery>();
    assert_missing_required::<PositionsByMarketsQuery>();
    assert_missing_required::<ConfirmPositionQuery>();
    assert_missing_required::<VaultIdQuery>();
    assert_missing_required::<VaultPnlHistoryQuery>();
    assert_missing_required::<VaultPositionsQuery>();
    assert_missing_required::<VaultEventsQuery>();
    assert_missing_required::<VaultContributorsQuery>();

    assert_accepts::<ChatMentionCandidatesQuery>(json!({"chat_id": "room-id"}));
    assert_accepts::<MarketLookupQuery>(
        json!({"asset": "BTC", "duration_secs": 300, "window_start_ms": 1}),
    );
    assert_accepts::<MarketCurrentQuery>(json!({"asset": "BTC", "duration_secs": 300}));
    assert_accepts::<TopOfBookHistoryQuery>(json!({"market_ids": "1,2"}));
    assert_accepts::<TakerPnlQuery>(json!({"wallet": "wallet"}));
    assert_accepts::<PositionsByMarketsQuery>(json!({"market_ids": "1,2"}));
    assert_accepts::<ConfirmPositionQuery>(json!({"position_id": "position", "accept": true}));
    assert_accepts::<VaultIdQuery>(json!({"vault_id": "vault"}));
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
}
