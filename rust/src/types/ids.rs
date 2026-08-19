use serde::{Deserialize, Serialize};
use std::fmt;
use uuid::Uuid;

/// Market identifier.
///
/// Serializes as a numeric market ID.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(transparent)]
pub struct MarketId(pub u64);

impl MarketId {
    pub const fn new(id: u64) -> Self {
        Self(id)
    }

    pub const fn as_u64(&self) -> u64 {
        self.0
    }
}

impl From<MarketId> for u64 {
    fn from(value: MarketId) -> Self {
        value.0
    }
}

impl std::fmt::Display for MarketId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Defines UUID-backed identifiers used in API and market-maker protocol messages.
///
/// Each identifier serializes as a UUID and carries its entity name in Rust type
/// signatures.
macro_rules! define_uuid_id_type {
    ($name:ident, $doc:expr) => {
        #[doc = $doc]
        #[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
        #[repr(transparent)]
        pub struct $name(pub Uuid);

        impl $name {
            /// Create a new random ID.
            #[inline]
            pub fn new() -> Self {
                Self(Uuid::new_v4())
            }

            /// Create from an existing UUID.
            #[inline]
            pub const fn from_uuid(uuid: Uuid) -> Self {
                Self(uuid)
            }

            /// Create from raw UUID bytes.
            #[inline]
            pub fn from_bytes(bytes: [u8; 16]) -> Self {
                Self(Uuid::from_bytes(bytes))
            }

            /// Borrow the underlying UUID.
            #[inline]
            pub const fn as_uuid(&self) -> &Uuid {
                &self.0
            }

            /// Borrow the underlying UUID bytes.
            #[inline]
            pub fn as_bytes(&self) -> &[u8; 16] {
                self.0.as_bytes()
            }

            /// Create a nil (all-zero) ID.
            #[inline]
            pub const fn nil() -> Self {
                Self(Uuid::nil())
            }

            /// Check whether this ID is nil.
            #[inline]
            pub fn is_nil(&self) -> bool {
                self.0.is_nil()
            }
        }

        impl Default for $name {
            fn default() -> Self {
                Self::nil()
            }
        }

        impl fmt::Display for $name {
            fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                write!(f, "{}", self.0)
            }
        }

        impl From<Uuid> for $name {
            fn from(uuid: Uuid) -> Self {
                Self(uuid)
            }
        }

        impl From<$name> for Uuid {
            fn from(id: $name) -> Self {
                id.0
            }
        }

        impl AsRef<Uuid> for $name {
            fn as_ref(&self) -> &Uuid {
                &self.0
            }
        }
    };
}

define_uuid_id_type!(RequestId, "Unique identifier for an RFQ request.");
define_uuid_id_type!(UserId, "Unique identifier for a user.");
define_uuid_id_type!(QuoteId, "Unique identifier for a market maker quote.");
define_uuid_id_type!(
    ClientQuoteId,
    "Maker-supplied quote correlation identifier."
);
define_uuid_id_type!(PositionId, "Unique identifier for a filled position.");
define_uuid_id_type!(ContestId, "Unique identifier for a contest.");
define_uuid_id_type!(ChatId, "Unique identifier for a chat.");
define_uuid_id_type!(MessageId, "Unique identifier for a chat message.");

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn uuid_id_defaults_to_nil_not_random() {
        assert_eq!(RequestId::default(), RequestId::nil());
        assert_eq!(UserId::default(), UserId::nil());
        assert!(QuoteId::default().is_nil());
        assert!(ClientQuoteId::default().is_nil());
        assert!(PositionId::default().is_nil());
        assert!(ContestId::default().is_nil());
        assert!(ChatId::default().is_nil());
        assert!(MessageId::default().is_nil());
    }

    #[test]
    fn market_id_display_matches_numeric_wire_value() {
        assert_eq!(MarketId::new(42).to_string(), "42");
        assert_eq!(serde_json::to_string(&MarketId::new(42)).unwrap(), "42");
    }
}
