use longshot_protocol::api::{
    ChatMentionContext, ChatMentionNotificationPayload, FantasyResultBestEntry,
    FantasyResultGameType, FantasyResultNotificationPayload, NotificationPayload,
    PerfectSlateNotificationPayload,
};
use serde_json::json;

#[test]
fn chat_mention_uses_product_neutral_wire_contract() {
    let payload = NotificationPayload::ChatMention(ChatMentionNotificationPayload {
        chat_id: "3f2226c7-2ec4-4bde-b8f4-27f04df2bd83".into(),
        message_id: "93e06f17-3e6f-44b5-a931-aa90f0f9f73e".into(),
        chat_context: None,
        contest_id: None,
    });

    let encoded = serde_json::to_value(&payload).unwrap();
    assert_eq!(
        encoded,
        json!({
            "type": "chat_mention",
            "chat_id": "3f2226c7-2ec4-4bde-b8f4-27f04df2bd83",
            "message_id": "93e06f17-3e6f-44b5-a931-aa90f0f9f73e",
        })
    );

    let decoded: NotificationPayload = serde_json::from_value(encoded).unwrap();
    let NotificationPayload::ChatMention(mention) = decoded else {
        panic!("expected chat mention");
    };
    assert_eq!(mention.chat_id, "3f2226c7-2ec4-4bde-b8f4-27f04df2bd83");
    assert_eq!(mention.message_id, "93e06f17-3e6f-44b5-a931-aa90f0f9f73e");
    assert!(mention.chat_context.is_none());
    assert_eq!(mention.contest_id, None);
}

#[test]
fn chat_mention_accepts_legacy_routing_hints() {
    let payload: NotificationPayload = serde_json::from_value(json!({
        "type": "chat_mention",
        "chat_id": "9187ca06-569d-5bc7-8aa1-cb4dd2da71ac",
        "chat_context": "crypto_market",
        "message_id": "93e06f17-3e6f-44b5-a931-aa90f0f9f73e",
    }))
    .unwrap();
    let NotificationPayload::ChatMention(mention) = payload else {
        panic!("expected chat mention");
    };
    assert!(matches!(
        mention.chat_context,
        Some(ChatMentionContext::CryptoMarket)
    ));
    assert_eq!(mention.contest_id, None);
}

#[test]
fn fantasy_result_uses_exact_wire_contract() {
    let payload = NotificationPayload::FantasyResult(FantasyResultNotificationPayload {
        pool_image_scope_id: None,
        contest_id: "contest-outcast".into(),
        game_index: 2,
        game_type: FantasyResultGameType::Outcast,
        contest_title: "Stay With The Pack".into(),
        contest_terminal: true,
        contest_refunded: true,
        entry_count: 3,
        successful_entry_count: 2,
        held_entry_count: 1,
        credited_payout_micros: 7_500_000,
        held_payout_micros: 2_500_000,
        best_entry: Some(FantasyResultBestEntry {
            entry_index: 1,
            rank: 3,
            correct_count: Some(5),
            selection_count: Some(6),
        }),
        tiebreaker_result: Some(42),
    });

    let encoded = serde_json::to_value(&payload).unwrap();
    assert_eq!(
        encoded,
        json!({
            "type": "fantasy_result",
            "contest_id": "contest-outcast",
            "game_index": 2,
            "game_type": "outcast",
            "contest_title": "Stay With The Pack",
            "contest_terminal": true,
            "contest_refunded": true,
            "entry_count": 3,
            "successful_entry_count": 2,
            "held_entry_count": 1,
            "credited_payout_micros": 7_500_000,
            "held_payout_micros": 2_500_000,
            "best_entry": {
                "entry_index": 1,
                "rank": 3,
                "correct_count": 5,
                "selection_count": 6
            },
            "tiebreaker_result": 42
        })
    );

    let decoded: NotificationPayload = serde_json::from_value(encoded).unwrap();
    let NotificationPayload::FantasyResult(result) = decoded else {
        panic!("expected fantasy result");
    };
    assert!(result.contest_refunded);
    assert_eq!(result.held_payout_micros, 2_500_000);

    for removed in ["fantasy_win", "fantasy_settled"] {
        let error =
            serde_json::from_value::<NotificationPayload>(json!({ "type": removed })).unwrap_err();
        assert!(
            error.to_string().contains("unknown variant"),
            "{removed} failed for the wrong reason: {error}"
        );
    }
}

#[cfg(feature = "openapi")]
#[test]
fn fantasy_result_openapi_requires_contest_refunded() {
    use utoipa::ToSchema;

    let (_, schema) = FantasyResultNotificationPayload::schema();
    let schema = serde_json::to_value(schema).unwrap();
    assert_eq!(
        schema.pointer("/properties/contest_refunded/type"),
        Some(&json!("boolean"))
    );
    assert!(schema["required"]
        .as_array()
        .unwrap()
        .contains(&json!("contest_refunded")));
}

#[test]
fn perfect_slate_uses_exact_wire_contract() {
    let payload = NotificationPayload::PerfectSlate(PerfectSlateNotificationPayload {
        contest_id: "contest-perfect-slate".to_string(),
        game_index: 3,
        contest_title: "Sunday Slate".to_string(),
        winning_entry_count: 2,
        entry_indexes: vec![1, 4],
        payout_micros: 10_000_000,
        held_entry_count: 1,
        pool_micros: Some(25_000_000),
        total_winning_entry_count: Some(5),
    });

    let encoded = serde_json::to_value(&payload).unwrap();
    assert_eq!(
        encoded,
        json!({
            "type": "perfect_slate",
            "contest_id": "contest-perfect-slate",
            "game_index": 3,
            "contest_title": "Sunday Slate",
            "winning_entry_count": 2,
            "entry_indexes": [1, 4],
            "payout_micros": 10_000_000,
            "held_entry_count": 1,
            "pool_micros": 25_000_000,
            "total_winning_entry_count": 5,
        })
    );

    let decoded: NotificationPayload = serde_json::from_value(encoded).unwrap();
    let NotificationPayload::PerfectSlate(result) = decoded else {
        panic!("expected perfect slate");
    };
    assert_eq!(result.contest_id, "contest-perfect-slate");
    assert_eq!(result.entry_indexes, vec![1, 4]);
    assert_eq!(result.payout_micros, 10_000_000);
    assert_eq!(result.pool_micros, Some(25_000_000));
    assert_eq!(result.total_winning_entry_count, Some(5));
}

#[test]
fn perfect_slate_accepts_legacy_payload_without_pool_context() {
    let decoded: NotificationPayload = serde_json::from_value(json!({
        "type": "perfect_slate",
        "contest_id": "contest-perfect-slate",
        "game_index": 3,
        "contest_title": "Sunday Slate",
        "winning_entry_count": 2,
        "entry_indexes": [1, 4],
        "payout_micros": 10_000_000,
        "held_entry_count": 1,
    }))
    .unwrap();
    let NotificationPayload::PerfectSlate(result) = decoded else {
        panic!("expected perfect slate");
    };
    assert_eq!(result.pool_micros, None);
    assert_eq!(result.total_winning_entry_count, None);
    let reencoded =
        serde_json::to_value(NotificationPayload::PerfectSlate(result)).expect("serialize legacy");
    assert!(reencoded.get("pool_micros").is_none());
    assert!(reencoded.get("total_winning_entry_count").is_none());
}
