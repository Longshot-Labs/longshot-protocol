//! Market-maker protocol helpers.

use alloy_primitives::eip191_hash_message;
use alloy_signer::{Result as SignerResult, SignerSync};
use alloy_signer_local::PrivateKeySigner;
use base64::{engine::general_purpose::STANDARD_NO_PAD, Engine};

use crate::types::{
    Address, Amount, BroadcastRfqRequest, ClientQuoteId, Odds, QuoteResponse, RequestId,
    MAX_RFQ_LEGS, RFQ_PROTOCOL_VERSION,
};
use crate::ws::ClientMessage;
use uuid::{Uuid, Variant, Version};

/// Fixed domain bound into MM WebSocket authentication messages.
pub const AUTH_DOMAIN: &str = "longshot.xyz";

/// Error returned when a server-supplied MM authentication challenge ID is invalid.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AuthChallengeIdError {
    /// The value was not a UUID.
    InvalidUuid,
    /// The UUID was not encoded as canonical lowercase hyphenated text.
    NonCanonical,
    /// The UUID did not use the RFC 4122 variant.
    InvalidVariant,
    /// The UUID was not version 4.
    InvalidVersion,
}

impl std::fmt::Display for AuthChallengeIdError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidUuid => f.write_str("challenge ID must be a UUID"),
            Self::NonCanonical => {
                f.write_str("challenge ID must be lowercase canonical hyphenated UUID text")
            }
            Self::InvalidVariant => f.write_str("challenge ID must use the RFC 4122 variant"),
            Self::InvalidVersion => f.write_str("challenge ID must be a UUIDv4"),
        }
    }
}

impl std::error::Error for AuthChallengeIdError {}

/// Parse the canonical UUIDv4 used by an MM WebSocket authentication challenge.
pub fn parse_auth_challenge_id(value: &str) -> Result<Uuid, AuthChallengeIdError> {
    let challenge_id = Uuid::parse_str(value).map_err(|_| AuthChallengeIdError::InvalidUuid)?;
    if challenge_id.hyphenated().to_string() != value {
        return Err(AuthChallengeIdError::NonCanonical);
    }
    if challenge_id.get_variant() != Variant::RFC4122 {
        return Err(AuthChallengeIdError::InvalidVariant);
    }
    if challenge_id.get_version() != Some(Version::Random) {
        return Err(AuthChallengeIdError::InvalidVersion);
    }
    Ok(challenge_id)
}

/// Error returned when a protocol helper cannot decode a fixed-size MM payload.
#[derive(Debug)]
pub enum MmDecodeError {
    /// The payload was not valid base64 using Longshot's unpadded standard alphabet.
    Base64(base64::DecodeError),
    /// The decoded payload did not match the expected fixed wire size.
    WrongSize {
        /// Payload kind being decoded.
        kind: &'static str,
        /// Required byte length.
        expected: usize,
        /// Actual decoded byte length.
        actual: usize,
    },
    /// The decoded RFQ declared a leg count outside the public protocol range.
    InvalidLegCount {
        /// Actual leg count declared by the payload.
        actual: u8,
    },
    /// The RFQ payload was encoded for a different binary protocol version.
    UnsupportedProtocolVersion {
        /// Protocol version required by this crate release.
        expected: u8,
        /// Protocol version declared by the payload.
        actual: u8,
    },
}

impl std::fmt::Display for MmDecodeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Base64(err) => write!(f, "invalid base64 payload: {err}"),
            Self::WrongSize {
                kind,
                expected,
                actual,
            } => write!(
                f,
                "invalid {kind} payload size: expected {expected} bytes, got {actual}"
            ),
            Self::InvalidLegCount { actual } => write!(
                f,
                "invalid broadcast RFQ leg count: expected 1..={MAX_RFQ_LEGS}, got {actual}"
            ),
            Self::UnsupportedProtocolVersion { expected, actual } => write!(
                f,
                "unsupported RFQ protocol version: expected {expected}, got {actual}"
            ),
        }
    }
}

impl std::error::Error for MmDecodeError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Base64(err) => Some(err),
            Self::WrongSize { .. }
            | Self::InvalidLegCount { .. }
            | Self::UnsupportedProtocolVersion { .. } => None,
        }
    }
}

/// Build the exact EIP-191 personal-message text for MM WebSocket authentication.
#[inline]
pub fn build_auth_message(
    auth_address: &Address,
    challenge_id: &Uuid,
    timestamp_ms: u64,
) -> String {
    format!(
        "Longshot Market Maker WebSocket Authentication\n\nVersion: 1\nDomain: {AUTH_DOMAIN}\nAuth Address: {}\nChallenge ID: {challenge_id}\nTimestamp: {timestamp_ms}",
        auth_address.to_checksum(None),
    )
}

/// Sign a server auth challenge with a market-maker private key.
pub fn sign_auth_response(
    challenge_id: &Uuid,
    timestamp_ms: u64,
    signing_key: &PrivateKeySigner,
) -> SignerResult<[u8; 65]> {
    let message = build_auth_message(&signing_key.address(), challenge_id, timestamp_ms);
    Ok(signing_key.sign_message_sync(message.as_bytes())?.into())
}

/// Build an `auth_response` WebSocket message for a server challenge.
pub fn auth_response_message(
    challenge_id: &Uuid,
    timestamp_ms: u64,
    signing_key: &PrivateKeySigner,
) -> SignerResult<ClientMessage> {
    Ok(ClientMessage::AuthResponse {
        wallet_address: signing_key.address().to_checksum(None),
        signature: hex::encode(sign_auth_response(challenge_id, timestamp_ms, signing_key)?),
    })
}

/// Sign a quote response with a market-maker private key.
pub fn sign_quote_response(
    quote: &mut QuoteResponse,
    signing_key: &PrivateKeySigner,
) -> SignerResult<()> {
    let msg_hash = eip191_hash_message(quote.signed_data_bytes());
    quote.signature = signing_key.sign_hash_sync(&msg_hash)?.into();
    Ok(())
}

/// Build a signed quote response with a market-maker private key.
pub fn signed_quote_response(
    request_id: RequestId,
    odds: Odds,
    max_fill: Amount,
    signing_key: &PrivateKeySigner,
) -> SignerResult<QuoteResponse> {
    let mut quote = QuoteResponse::new(request_id, odds, max_fill);
    sign_quote_response(&mut quote, signing_key)?;
    Ok(quote)
}

/// Build a signed quote response with a maker-supplied correlation ID.
pub fn signed_quote_response_with_client_quote_id(
    request_id: RequestId,
    odds: Odds,
    max_fill: Amount,
    client_quote_id: ClientQuoteId,
    signing_key: &PrivateKeySigner,
) -> SignerResult<QuoteResponse> {
    let mut quote =
        QuoteResponse::new_with_client_quote_id(request_id, odds, max_fill, client_quote_id);
    sign_quote_response(&mut quote, signing_key)?;
    Ok(quote)
}

/// Encode a quote response for the `quote.data` WebSocket field.
#[inline]
pub fn encode_quote_response(quote: &QuoteResponse) -> String {
    STANDARD_NO_PAD.encode(quote.to_bytes())
}

/// Decode a `quote.data` WebSocket field into a fixed-size quote response.
pub fn decode_quote_response(data: &str) -> Result<QuoteResponse, MmDecodeError> {
    let decoded = STANDARD_NO_PAD
        .decode(data)
        .map_err(MmDecodeError::Base64)?;
    let bytes: [u8; QuoteResponse::SIZE] =
        decoded
            .try_into()
            .map_err(|decoded: Vec<u8>| MmDecodeError::WrongSize {
                kind: "quote response",
                expected: QuoteResponse::SIZE,
                actual: decoded.len(),
            })?;
    Ok(QuoteResponse::from_bytes(&bytes))
}

/// Build a `quote` WebSocket message from a quote response.
#[inline]
pub fn quote_response_message(quote: &QuoteResponse) -> ClientMessage {
    ClientMessage::Quote {
        data: encode_quote_response(quote),
    }
}

/// Decode an `rfq.data` WebSocket field into a fixed-size broadcast RFQ.
pub fn decode_broadcast_rfq(data: &str) -> Result<BroadcastRfqRequest, MmDecodeError> {
    let decoded = STANDARD_NO_PAD
        .decode(data)
        .map_err(MmDecodeError::Base64)?;
    let bytes: [u8; BroadcastRfqRequest::SIZE] =
        decoded
            .try_into()
            .map_err(|decoded: Vec<u8>| MmDecodeError::WrongSize {
                kind: "broadcast RFQ",
                expected: BroadcastRfqRequest::SIZE,
                actual: decoded.len(),
            })?;
    let request = BroadcastRfqRequest::from_bytes(&bytes);
    if request.protocol_version != RFQ_PROTOCOL_VERSION {
        return Err(MmDecodeError::UnsupportedProtocolVersion {
            expected: RFQ_PROTOCOL_VERSION,
            actual: request.protocol_version,
        });
    }
    if !(1..=MAX_RFQ_LEGS).contains(&(request.leg_count as usize)) {
        return Err(MmDecodeError::InvalidLegCount {
            actual: request.leg_count,
        });
    }
    Ok(request)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn auth_message_layout_matches_gateway_contract() {
        let signing_key: PrivateKeySigner =
            "0x0101010101010101010101010101010101010101010101010101010101010101"
                .parse()
                .unwrap();
        let challenge_id = parse_auth_challenge_id("550e8400-e29b-41d4-a716-446655440000").unwrap();
        let message = build_auth_message(&signing_key.address(), &challenge_id, 1_735_430_000_000);

        assert_eq!(
            message,
            "Longshot Market Maker WebSocket Authentication\n\nVersion: 1\nDomain: longshot.xyz\nAuth Address: 0x1a642f0E3c3aF545E7AcBD38b07251B3990914F1\nChallenge ID: 550e8400-e29b-41d4-a716-446655440000\nTimestamp: 1735430000000"
        );
    }

    #[test]
    fn auth_challenge_id_requires_canonical_rfc4122_uuid_v4() {
        assert!(parse_auth_challenge_id("550e8400-e29b-41d4-a716-446655440000").is_ok());
        assert_eq!(
            parse_auth_challenge_id("550E8400-E29B-41D4-A716-446655440000"),
            Err(AuthChallengeIdError::NonCanonical)
        );
        assert_eq!(
            parse_auth_challenge_id("550e8400e29b41d4a716446655440000"),
            Err(AuthChallengeIdError::NonCanonical)
        );
        assert_eq!(
            parse_auth_challenge_id("550e8400-e29b-11d4-a716-446655440000"),
            Err(AuthChallengeIdError::InvalidVersion)
        );
        assert_eq!(
            parse_auth_challenge_id("550e8400-e29b-41d4-0716-446655440000"),
            Err(AuthChallengeIdError::InvalidVariant)
        );
        assert_eq!(
            parse_auth_challenge_id("not-a-uuid"),
            Err(AuthChallengeIdError::InvalidUuid)
        );
    }

    #[test]
    fn auth_response_message_hex_encodes_signature() {
        let signing_key = PrivateKeySigner::random();
        let challenge_id = Uuid::new_v4();
        let message = auth_response_message(&challenge_id, 123, &signing_key).unwrap();

        let ClientMessage::AuthResponse {
            wallet_address,
            signature,
        } = message
        else {
            panic!("expected auth response message");
        };
        assert_eq!(wallet_address, signing_key.address().to_checksum(None));
        assert_eq!(signature.len(), 130);
    }

    #[test]
    fn signed_quote_response_verifies_against_signer_address() {
        let signing_key = PrivateKeySigner::random();
        let wallet_address = signing_key.address();

        let quote = signed_quote_response(
            RequestId::new(),
            Odds::from_decimal(2, 5000),
            Amount::from_dollars(1_000),
            &signing_key,
        )
        .unwrap();

        assert!(quote.verify_signature(&wallet_address));

        let wrong_wallet_address = PrivateKeySigner::random().address();
        assert!(!quote.verify_signature(&wrong_wallet_address));
    }

    #[test]
    fn signature_verification_rejects_tampered_quote() {
        let signing_key = PrivateKeySigner::random();
        let wallet_address = signing_key.address();

        let mut quote = signed_quote_response(
            RequestId::new(),
            Odds::from_decimal(2, 0),
            Amount::from_dollars(500),
            &signing_key,
        )
        .unwrap();
        assert!(quote.verify_signature(&wallet_address));

        quote.odds = Odds::from_decimal(3, 0).0;

        assert!(!quote.verify_signature(&wallet_address));
    }

    #[test]
    fn quote_response_message_roundtrips_fixed_payload() {
        let signing_key = PrivateKeySigner::random();
        let quote = signed_quote_response(
            RequestId::new(),
            Odds::from_decimal(4, 2500),
            Amount::from_dollars(250),
            &signing_key,
        )
        .unwrap();

        let ClientMessage::Quote { data } = quote_response_message(&quote) else {
            panic!("expected quote message");
        };
        let decoded = decode_quote_response(&data).unwrap();

        assert_eq!(decoded.to_bytes(), quote.to_bytes());
    }

    #[test]
    fn decode_quote_response_rejects_wrong_size() {
        let encoded = STANDARD_NO_PAD.encode([1u8; QuoteResponse::SIZE - 1]);
        let err = decode_quote_response(&encoded).unwrap_err();

        assert!(matches!(
            err,
            MmDecodeError::WrongSize {
                kind: "quote response",
                expected: QuoteResponse::SIZE,
                actual
            } if actual == QuoteResponse::SIZE - 1
        ));
    }

    #[test]
    fn raw_rfq_parser_preserves_invalid_counts_but_public_decoder_rejects_them() {
        for actual in [0, (MAX_RFQ_LEGS + 1) as u8] {
            let mut current = [0u8; BroadcastRfqRequest::SIZE];
            current[57] = actual;
            current[58] = RFQ_PROTOCOL_VERSION;

            let raw = BroadcastRfqRequest::from_bytes(&current);
            assert_eq!(raw.leg_count, actual);
            assert_eq!(raw.to_bytes(), current);

            assert!(matches!(
                decode_broadcast_rfq(&STANDARD_NO_PAD.encode(current)),
                Err(MmDecodeError::InvalidLegCount { actual: decoded }) if decoded == actual
            ));
        }
    }

    #[test]
    fn decode_broadcast_rfq_rejects_version_one_before_decoding_legs() {
        let mut current = [0u8; BroadcastRfqRequest::SIZE];
        current[57] = 1;
        current[58] = 1;

        assert!(matches!(
            decode_broadcast_rfq(&STANDARD_NO_PAD.encode(current)),
            Err(MmDecodeError::UnsupportedProtocolVersion {
                expected: RFQ_PROTOCOL_VERSION,
                actual: 1
            })
        ));
    }

    #[test]
    fn decode_broadcast_rfq_rejects_wrong_size() {
        let encoded = STANDARD_NO_PAD.encode(vec![0u8; BroadcastRfqRequest::SIZE - 1]);
        let err = decode_broadcast_rfq(&encoded).unwrap_err();

        assert!(matches!(
            err,
            MmDecodeError::WrongSize {
                kind: "broadcast RFQ",
                expected: BroadcastRfqRequest::SIZE,
                actual
            } if actual == BroadcastRfqRequest::SIZE - 1
        ));
    }
}
