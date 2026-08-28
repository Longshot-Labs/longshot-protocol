use alloy_signer_local::PrivateKeySigner;
use base64::{engine::general_purpose::STANDARD_NO_PAD, Engine};
use longshot_protocol::api::SignedOrderJson;
use longshot_protocol::mm::{
    auth_response_message, build_auth_message, decode_broadcast_rfq, encode_quote_response,
    parse_auth_challenge_id, quote_response_message, sign_auth_response, signed_quote_response,
};
use longshot_protocol::taker::{sign_order, signed_order, OrderLeg, SignedOrder, SignedOrderError};
use longshot_protocol::types::{
    Address, Amount, Asset, Direction, Duration, MarketId, Odds, OrderType, QuoteResponse,
    RequestId, RfqLeg, RfqRequest, TakerMetadata, UserId, UserTier, MAX_RFQ_LEGS,
    RFQ_PROTOCOL_VERSION,
};
use longshot_protocol::ws::{ClientMessage, QuoteDeclineReason};
use serde_json::Value;
use std::fs;
use std::path::Path;
use uuid::Uuid;

fn fixture() -> Value {
    let fixture_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .join("fixtures/protocol/parity.json");
    let fixture = fs::read_to_string(fixture_path).unwrap();
    serde_json::from_str(&fixture).unwrap()
}

fn request_id() -> RequestId {
    RequestId::from_uuid(Uuid::parse_str("00112233-4455-6677-8899-aabbccddeeff").unwrap())
}

fn taker_id() -> UserId {
    UserId::from_uuid(Uuid::parse_str("ffeeddcc-bbaa-9988-7766-554433221100").unwrap())
}

fn rfq_leg(row: &Value) -> RfqLeg {
    let market_id = MarketId::new(row["market_id"].as_u64().unwrap());
    let start_at_ms = row["start_at_ms"].as_u64().unwrap();
    let direction = Direction::from_u8(row["direction"].as_u64().unwrap() as u8).unwrap();
    let leg_index = row["leg_index"].as_u64().unwrap() as u8;

    match row["type_tag"].as_u64().unwrap() {
        0 => RfqLeg::new_price_strike(
            market_id,
            start_at_ms,
            Asset::from_u8(row["asset"].as_u64().unwrap() as u8).unwrap(),
            direction,
            Duration::from_secs(row["price_window_secs"].as_u64().unwrap() as u32).unwrap(),
            leg_index,
        ),
        2 => RfqLeg::new_binary_event(market_id, start_at_ms, direction, leg_index),
        tag => panic!("unsupported RFQ leg type tag {tag}"),
    }
}

#[test]
fn quote_decline_uses_typed_request_id_and_closed_reason() {
    let message = ClientMessage::QuoteDecline {
        request_id: request_id(),
        reason: QuoteDeclineReason::SportsCombinationUnsupported,
    };

    let json = serde_json::to_value(&message).unwrap();
    assert_eq!(
        json,
        serde_json::json!({
            "type": "quote_decline",
            "request_id": "00112233-4455-6677-8899-aabbccddeeff",
            "reason": "sports_combination_unsupported",
        })
    );
    assert!(matches!(
        serde_json::from_value::<ClientMessage>(json).unwrap(),
        ClientMessage::QuoteDecline {
            request_id: parsed_request_id,
            reason: QuoteDeclineReason::SportsCombinationUnsupported,
        } if parsed_request_id == request_id()
    ));
}

#[test]
fn mm_signing_matches_shared_fixture() {
    let fixture = fixture();
    let auth = &fixture["auth_message"];
    let quote_case = &fixture["quote_response"];
    let case = &fixture["mm_signing"];
    let signing_key = case["private_key"]
        .as_str()
        .unwrap()
        .parse::<PrivateKeySigner>()
        .unwrap();
    let challenge_id = parse_auth_challenge_id(auth["challenge_id"].as_str().unwrap()).unwrap();
    let timestamp_ms = auth["timestamp_ms"].as_u64().unwrap();
    let auth_signature = sign_auth_response(&challenge_id, timestamp_ms, &signing_key).unwrap();
    let ClientMessage::AuthResponse {
        wallet_address,
        signature,
    } = auth_response_message(&challenge_id, timestamp_ms, &signing_key).unwrap()
    else {
        panic!("expected auth response");
    };
    let signed_quote = signed_quote_response(
        request_id(),
        Odds(quote_case["odds"].as_u64().unwrap() as u32),
        Amount::from_micro(quote_case["max_fill_micros"].as_u64().unwrap()),
        &signing_key,
    )
    .unwrap();
    let ClientMessage::Quote { data } = quote_response_message(&signed_quote) else {
        panic!("expected quote");
    };

    assert_eq!(wallet_address, case["wallet_address"].as_str().unwrap());
    assert_eq!(
        hex::encode(auth_signature),
        case["auth_signature_hex"].as_str().unwrap()
    );
    assert_eq!(signature, case["auth_signature_hex"].as_str().unwrap());
    assert_eq!(
        hex::encode(signed_quote.signature),
        case["quote_signature_hex"].as_str().unwrap()
    );
    assert_eq!(
        hex::encode(signed_quote.to_bytes()),
        case["signed_quote_bytes_hex"].as_str().unwrap()
    );
    assert_eq!(data, case["signed_quote_base64"].as_str().unwrap());
    assert!(signed_quote.verify_signature(&signing_key.address()));

    let mut tampered_quote = signed_quote;
    tampered_quote.odds = Odds::from_decimal(3, 0).0;
    assert!(!tampered_quote.verify_signature(&signing_key.address()));
}

#[test]
fn auth_message_matches_shared_fixture() {
    let fixture = fixture();
    let case = &fixture["auth_message"];
    let challenge_id = parse_auth_challenge_id(case["challenge_id"].as_str().unwrap()).unwrap();
    let timestamp_ms = case["timestamp_ms"].as_u64().unwrap();
    let wallet_address = fixture["mm_signing"]["wallet_address"]
        .as_str()
        .unwrap()
        .parse::<Address>()
        .unwrap();

    let message = build_auth_message(&wallet_address, &challenge_id, timestamp_ms);

    assert_eq!(message, case["message"].as_str().unwrap());
    assert_eq!(hex::encode(message), case["message_hex"].as_str().unwrap());
}

#[test]
fn taker_signing_bytes_match_shared_fixture() {
    let fixture = fixture();
    let case = &fixture["taker_signed_order"];
    let user = Address::from_slice(&[0x11; 20]);
    let order = SignedOrder {
        user,
        wager_micros: case["wager_micros"].as_u64().unwrap(),
        min_odds_bps: case["min_odds_bps"].as_u64().unwrap() as u32,
        legs: vec![
            OrderLeg {
                market_id: MarketId::new(42),
                direction: Direction::Down as u8,
            },
            OrderLeg {
                market_id: MarketId::new(99),
                direction: Direction::Up as u8,
            },
        ],
        nonce: case["nonce"].as_u64().unwrap(),
        expires_at_ms: case["expires_at_ms"].as_u64().unwrap(),
        order_type: OrderType::FOK,
        shield_on: case["shield_on"].as_bool().unwrap(),
        signature: [0; 65],
    };

    assert_eq!(
        hex::encode(order.replay_bytes()),
        case["replay_bytes_hex"].as_str().unwrap()
    );
    assert_eq!(
        hex::encode(order.signing_bytes(case["use_app_tokens"].as_bool().unwrap())),
        case["signing_bytes_hex"].as_str().unwrap()
    );

    let mut wire_order = SignedOrderJson::try_from(&order).unwrap();
    assert_eq!(wire_order.min_odds, 2.5);
    wire_order.min_odds = 2.00005;
    assert_eq!(
        SignedOrder::try_from(wire_order).unwrap().min_odds_bps,
        20_001
    );

    let mut invalid = order;
    for legs in [
        Vec::new(),
        vec![OrderLeg {
            market_id: MarketId::new(42),
            direction: 2,
        }],
    ] {
        invalid.legs = legs;
        assert!(invalid.try_replay_bytes().is_err());
        assert!(invalid.try_signing_bytes(true).is_err());
        assert!(SignedOrderJson::try_from(&invalid).is_err());
    }
}

#[test]
fn taker_order_signing_helper_signs_eip191_preimage() {
    let fixture = fixture();
    let case = &fixture["taker_signed_order"];
    let signing_key = PrivateKeySigner::random();
    let order = SignedOrder {
        user: signing_key.address(),
        wager_micros: case["wager_micros"].as_u64().unwrap(),
        min_odds_bps: case["min_odds_bps"].as_u64().unwrap() as u32,
        legs: vec![OrderLeg {
            market_id: MarketId::new(42),
            direction: Direction::Down as u8,
        }],
        nonce: case["nonce"].as_u64().unwrap(),
        expires_at_ms: case["expires_at_ms"].as_u64().unwrap(),
        order_type: OrderType::FOK,
        shield_on: case["shield_on"].as_bool().unwrap(),
        signature: [0; 65],
    };

    let use_app_tokens = case["use_app_tokens"].as_bool().unwrap();
    let mut signed = signed_order(order.clone(), use_app_tokens, &signing_key).unwrap();

    assert!(signed.verify_signature(use_app_tokens));
    assert!(!signed.verify_signature(!use_app_tokens));
    assert_ne!(signed.signature, [0; 65]);

    signed.wager_micros += 1;
    assert!(!signed.verify_signature(use_app_tokens));

    sign_order(&mut signed, use_app_tokens, &signing_key).unwrap();
    assert!(signed.verify_signature(use_app_tokens));
}

#[test]
fn taker_signing_rejects_more_than_max_legs() {
    let fixture = fixture();
    let case = &fixture["taker_signed_order"];
    let signing_key = PrivateKeySigner::random();
    let mut order = SignedOrder {
        user: signing_key.address(),
        wager_micros: case["wager_micros"].as_u64().unwrap(),
        min_odds_bps: case["min_odds_bps"].as_u64().unwrap() as u32,
        legs: vec![
            OrderLeg {
                market_id: MarketId::new(42),
                direction: Direction::Down as u8,
            };
            SignedOrder::MAX_LEGS
        ],
        nonce: case["nonce"].as_u64().unwrap(),
        expires_at_ms: case["expires_at_ms"].as_u64().unwrap(),
        order_type: OrderType::FOK,
        shield_on: case["shield_on"].as_bool().unwrap(),
        signature: [0; 65],
    };

    assert_eq!(SignedOrder::MAX_LEGS, 9);
    order.try_replay_bytes().unwrap();
    order.try_signing_bytes(true).unwrap();
    order.legs.push(OrderLeg {
        market_id: MarketId::new(99),
        direction: Direction::Up as u8,
    });

    assert_eq!(
        order.try_signing_bytes(true).unwrap_err(),
        SignedOrderError::TooManyLegs {
            max: SignedOrder::MAX_LEGS,
            actual: SignedOrder::MAX_LEGS + 1
        }
    );
    assert!(sign_order(&mut order, true, &signing_key).is_err());
}

#[test]
fn quote_response_matches_shared_fixture() {
    let fixture = fixture();
    let case = &fixture["quote_response"];
    let quote = QuoteResponse::new(
        request_id(),
        Odds(case["odds"].as_u64().unwrap() as u32),
        Amount::from_micro(case["max_fill_micros"].as_u64().unwrap()),
    );

    assert_eq!(
        hex::encode(quote.to_bytes()),
        case["bytes_hex"].as_str().unwrap()
    );
    assert_eq!(
        hex::encode(quote.signed_data_bytes()),
        case["signed_data_hex"].as_str().unwrap()
    );
    assert_eq!(
        encode_quote_response(&quote),
        case["base64"].as_str().unwrap()
    );
}

#[test]
fn broadcast_rfq_matches_shared_fixture() {
    let fixture = fixture();
    let case = &fixture["broadcast_rfq"];
    let address = Address::from_slice(&[0x22; 20]);
    let legs: Vec<_> = case["legs"]
        .as_array()
        .unwrap()
        .iter()
        .map(rfq_leg)
        .collect();
    let mut request = RfqRequest::new(
        request_id(),
        taker_id(),
        Amount::from_micro(case["wager_micros"].as_u64().unwrap()),
        OrderType::IOC,
        Odds(case["min_odds"].as_u64().unwrap() as u32),
        Some(TakerMetadata::new(UserTier::Gold, address)),
        &legs,
    )
    .unwrap();
    request.set_expires_at_ms(case["expires_at_ms"].as_u64().unwrap());

    let bytes = request.to_broadcast_bytes();

    assert_eq!(hex::encode(bytes), case["bytes_hex"].as_str().unwrap());
    assert_eq!(
        STANDARD_NO_PAD.encode(bytes),
        case["base64"].as_str().unwrap()
    );

    let decoded = decode_broadcast_rfq(case["base64"].as_str().unwrap()).unwrap();
    assert_eq!(decoded.protocol_version, RFQ_PROTOCOL_VERSION);
    assert_eq!(decoded.leg_count as usize, MAX_RFQ_LEGS);
    assert_eq!(decoded.active_leg_wires().len(), MAX_RFQ_LEGS);
    assert_eq!(decoded.leg(MAX_RFQ_LEGS - 1).unwrap().unwrap(), legs[8]);
    assert!(decoded.leg(MAX_RFQ_LEGS).is_none());
}
