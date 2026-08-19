use serde::{Deserialize, Serialize};

/// Open user-facing market category slug.
///
/// The server validates known slugs on writes, while protocol reads preserve values
/// introduced after this crate release.
#[derive(Debug, Clone, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(transparent)]
pub struct MarketType(String);

impl MarketType {
    pub const SPORTS: &'static str = "sports";
    pub const CULTURE: &'static str = "culture";
    pub const CRYPTO: &'static str = "crypto";
    pub const POLITICS: &'static str = "politics";
    pub const EARNINGS: &'static str = "earnings";
    pub const ENTERTAINMENT: &'static str = "entertainment";
    pub const ESPORTS: &'static str = "esports";
    pub const WEATHER: &'static str = "weather";
    pub const MENTIONS: &'static str = "mentions";
    pub const EXTRA: &'static str = "extra";
    pub const OTHER: &'static str = "other";

    pub fn new(value: impl Into<String>) -> Self {
        Self(value.into())
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl From<&str> for MarketType {
    fn from(value: &str) -> Self {
        Self::new(value)
    }
}

impl From<String> for MarketType {
    fn from(value: String) -> Self {
        Self::new(value)
    }
}

impl AsRef<str> for MarketType {
    fn as_ref(&self) -> &str {
        self.as_str()
    }
}

impl std::fmt::Display for MarketType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Trading surface enabled for a market.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum TradingChannel {
    Rfq,
    Contest,
}

/// Market lifecycle status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum MarketStatus {
    /// Created, not yet open for general trading.
    Pending,
    /// Active trading allowed.
    Open,
    /// No new orders accepted. Resolution in progress.
    Frozen,
    /// Resolution challenged, under review.
    Disputed,
    /// Resolution outcome set, awaiting correction window finalization.
    PendingResolution,
    /// Final outcome determined.
    Resolved,
    /// Market cancelled. Refunds issued.
    Voided,
}

impl MarketStatus {
    /// Wire name used in query-string filters; matches the serde
    /// representation (see the round-trip test).
    pub fn as_query_token(&self) -> &'static str {
        match self {
            Self::Pending => "PENDING",
            Self::Open => "OPEN",
            Self::Frozen => "FROZEN",
            Self::Disputed => "DISPUTED",
            Self::PendingResolution => "PENDING_RESOLUTION",
            Self::Resolved => "RESOLVED",
            Self::Voided => "VOIDED",
        }
    }

    /// Returns true if the market is globally tradeable.
    pub fn is_tradeable(&self) -> bool {
        matches!(self, Self::Open)
    }

    /// Returns true if this is a terminal state.
    pub fn is_terminal(&self) -> bool {
        matches!(self, Self::Resolved | Self::Voided)
    }

    /// Returns true if the market is visible in general user browsing.
    pub fn is_visible(&self) -> bool {
        !matches!(self, Self::Pending)
    }

    /// Checks whether the lifecycle can move from this status to `target`.
    pub fn can_transition_to(&self, target: Self) -> bool {
        if target == Self::Voided && !self.is_terminal() {
            return true;
        }

        match self {
            Self::Pending => matches!(target, Self::Open),
            Self::Open => matches!(target, Self::Frozen),
            Self::Frozen => matches!(
                target,
                Self::PendingResolution | Self::Resolved | Self::Voided | Self::Disputed
            ),
            Self::Disputed => {
                matches!(
                    target,
                    Self::PendingResolution | Self::Resolved | Self::Voided
                )
            }
            Self::PendingResolution => matches!(target, Self::Resolved | Self::Voided),
            Self::Resolved => false,
            Self::Voided => false,
        }
    }

    /// Checks whether a trusted lifecycle update can move to `target`.
    pub fn can_transition_to_worker_owned(&self, target: Self) -> bool {
        self.can_transition_to(target)
            || matches!(
                (self, target),
                (Self::Pending, Self::Frozen | Self::Resolved) | (Self::Open, Self::Resolved)
            )
    }
}

impl std::fmt::Display for MarketStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Pending => write!(f, "PENDING"),
            Self::Open => write!(f, "OPEN"),
            Self::Frozen => write!(f, "FROZEN"),
            Self::Disputed => write!(f, "DISPUTED"),
            Self::PendingResolution => write!(f, "PENDING_RESOLUTION"),
            Self::Resolved => write!(f, "RESOLVED"),
            Self::Voided => write!(f, "VOIDED"),
        }
    }
}

/// Binary market outcome.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "UPPERCASE")]
pub enum Outcome {
    Yes,
    No,
}

impl Outcome {
    /// Returns the opposite outcome.
    pub const fn opposite(self) -> Self {
        match self {
            Self::Yes => Self::No,
            Self::No => Self::Yes,
        }
    }
}

impl std::fmt::Display for Outcome {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Yes => write!(f, "YES"),
            Self::No => write!(f, "NO"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn market_type_preserves_unknown_category_slugs() {
        let known = MarketType::from(MarketType::SPORTS);
        let future: MarketType = serde_json::from_str(r#""future_category""#).unwrap();

        assert_eq!(serde_json::to_string(&known).unwrap(), r#""sports""#);
        assert_eq!(future.as_str(), "future_category");
        assert_eq!(
            serde_json::to_string(&future).unwrap(),
            r#""future_category""#
        );
    }

    #[test]
    fn trading_channel_is_closed() {
        assert_eq!(
            serde_json::to_string(&TradingChannel::Contest).unwrap(),
            r#""contest""#
        );
    }

    #[test]
    fn market_status_valid_state_transitions() {
        assert!(MarketStatus::Pending.can_transition_to(MarketStatus::Open));
        assert!(MarketStatus::Open.can_transition_to(MarketStatus::Frozen));
        assert!(MarketStatus::Frozen.can_transition_to(MarketStatus::Resolved));
        assert!(MarketStatus::Open.can_transition_to(MarketStatus::Voided));
    }

    #[test]
    fn market_status_invalid_state_transitions() {
        assert!(!MarketStatus::Resolved.can_transition_to(MarketStatus::Open));
        assert!(!MarketStatus::Resolved.can_transition_to(MarketStatus::Voided));
        assert!(!MarketStatus::Voided.can_transition_to(MarketStatus::Open));
        assert!(!MarketStatus::Voided.can_transition_to(MarketStatus::Resolved));
        assert!(!MarketStatus::Voided.can_transition_to(MarketStatus::Voided));
        assert!(!MarketStatus::Pending.can_transition_to(MarketStatus::Resolved));
        assert!(!MarketStatus::Open.can_transition_to(MarketStatus::Pending));
    }

    #[test]
    fn market_status_worker_owned_catch_up_transitions_are_explicit() {
        assert!(MarketStatus::Pending.can_transition_to_worker_owned(MarketStatus::Open));
        assert!(MarketStatus::Pending.can_transition_to_worker_owned(MarketStatus::Frozen));
        assert!(MarketStatus::Pending.can_transition_to_worker_owned(MarketStatus::Resolved));
        assert!(MarketStatus::Open.can_transition_to_worker_owned(MarketStatus::Frozen));
        assert!(MarketStatus::Open.can_transition_to_worker_owned(MarketStatus::Resolved));
        assert!(MarketStatus::Frozen.can_transition_to_worker_owned(MarketStatus::Resolved));
    }

    #[test]
    fn market_status_worker_owned_transition_helper_still_rejects_invalid_targets() {
        assert!(!MarketStatus::Pending.can_transition_to_worker_owned(MarketStatus::Pending));
        assert!(
            !MarketStatus::Pending.can_transition_to_worker_owned(MarketStatus::PendingResolution)
        );
        assert!(!MarketStatus::Open.can_transition_to_worker_owned(MarketStatus::PendingResolution));
        assert!(!MarketStatus::Frozen.can_transition_to_worker_owned(MarketStatus::Open));
        assert!(!MarketStatus::Resolved.can_transition_to_worker_owned(MarketStatus::Open));
        assert!(!MarketStatus::Voided.can_transition_to_worker_owned(MarketStatus::Resolved));
        assert!(!MarketStatus::Voided.can_transition_to_worker_owned(MarketStatus::Voided));
    }

    #[test]
    fn outcome_opposite() {
        assert_eq!(Outcome::Yes.opposite(), Outcome::No);
        assert_eq!(Outcome::No.opposite(), Outcome::Yes);
    }

    #[test]
    fn market_status_query_tokens_match_serde_names() {
        for status in [
            MarketStatus::Pending,
            MarketStatus::Open,
            MarketStatus::Frozen,
            MarketStatus::Disputed,
            MarketStatus::PendingResolution,
            MarketStatus::Resolved,
            MarketStatus::Voided,
        ] {
            let serde_name = serde_json::to_value(status).unwrap();
            assert_eq!(serde_name, status.as_query_token());
        }
    }
}
