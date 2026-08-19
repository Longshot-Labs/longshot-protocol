//! Public primitive types shared by the API, clients, and market-maker wire paths.
//!
//! Use these types to express assets, directions, market windows, odds,
//! amounts, timestamps, order types, and user tiers in protocol units.

use serde::{Deserialize, Serialize};
use std::fmt;
use std::ops::{Add, Sub};
use std::time::{SystemTime, UNIX_EPOCH};

/// Minimum bet amount in micro-dollars ($0.50).
///
/// `Amount::is_valid_bet` checks this public minimum.
pub const MIN_BET_MICROS: u64 = 500_000;

// =============================================================================
// ASSET
// =============================================================================

/// Supported price-market assets.
///
/// Numeric discriminants are used in RFQ binary payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[repr(u8)]
pub enum Asset {
    BTC = 0,
    ETH = 1,
    SOL = 2,
    XRP = 3,
    HYPE = 4,
}

impl Asset {
    /// Total number of supported assets.
    pub const COUNT: usize = 5;

    /// All assets in wire/discriminant order.
    pub const ALL: [Asset; 5] = [Asset::BTC, Asset::ETH, Asset::SOL, Asset::XRP, Asset::HYPE];

    /// Convert from the RFQ/API numeric representation.
    #[inline]
    pub const fn from_u8(v: u8) -> Option<Self> {
        match v {
            0 => Some(Self::BTC),
            1 => Some(Self::ETH),
            2 => Some(Self::SOL),
            3 => Some(Self::XRP),
            4 => Some(Self::HYPE),
            _ => None,
        }
    }

    /// Asset ticker symbol.
    #[inline]
    pub const fn ticker(&self) -> &'static str {
        match self {
            Asset::BTC => "BTC",
            Asset::ETH => "ETH",
            Asset::SOL => "SOL",
            Asset::XRP => "XRP",
            Asset::HYPE => "HYPE",
        }
    }

    /// Parse an asset from a ticker symbol.
    ///
    /// Parsing is case-insensitive and ignores surrounding whitespace.
    #[inline]
    pub fn parse_symbol(raw: &str) -> Option<Self> {
        let symbol = raw.trim();
        if symbol.is_empty() {
            return None;
        }

        Self::ALL
            .iter()
            .copied()
            .find(|asset| asset.ticker().eq_ignore_ascii_case(symbol))
    }
}

impl From<Asset> for u8 {
    fn from(value: Asset) -> Self {
        value as u8
    }
}

impl fmt::Display for Asset {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.ticker())
    }
}

// =============================================================================
// DIRECTION
// =============================================================================

/// Prediction direction for a leg.
///
/// For price markets, `Up` predicts the observed price is higher than the
/// strike. `Down` predicts it is not higher.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[repr(u8)]
pub enum Direction {
    Up = 0,
    Down = 1,
}

impl Direction {
    /// Convert from the RFQ/API numeric representation.
    #[inline]
    pub const fn from_u8(v: u8) -> Option<Self> {
        match v {
            0 => Some(Self::Up),
            1 => Some(Self::Down),
            _ => None,
        }
    }

    /// Returns true when this direction predicts price higher than strike.
    #[inline]
    pub const fn predicts_higher(&self) -> bool {
        matches!(self, Direction::Up)
    }

    /// Build a direction from a boolean "price higher" prediction.
    #[inline]
    pub const fn from_predicts_higher(prediction: bool) -> Self {
        if prediction {
            Direction::Up
        } else {
            Direction::Down
        }
    }

    /// Opposite direction.
    #[inline]
    pub const fn opposite(&self) -> Self {
        match self {
            Direction::Up => Direction::Down,
            Direction::Down => Direction::Up,
        }
    }
}

impl From<Direction> for u8 {
    fn from(value: Direction) -> Self {
        value as u8
    }
}

impl fmt::Display for Direction {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Direction::Up => write!(f, "UP"),
            Direction::Down => write!(f, "DOWN"),
        }
    }
}

// =============================================================================
// DURATION
// =============================================================================

/// Price-market window length in seconds.
///
/// Price-market RFQ legs use these supported window lengths.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[repr(transparent)]
pub struct Duration(pub u32);

impl Duration {
    /// 1 minute = 60 seconds.
    pub const ONE_MINUTE: Self = Self(60);

    /// 5 minutes = 300 seconds.
    pub const FIVE_MINUTES: Self = Self(5 * 60);

    /// 15 minutes = 900 seconds.
    pub const FIFTEEN_MINUTES: Self = Self(15 * 60);

    /// 1 hour = 3600 seconds.
    pub const ONE_HOUR: Self = Self(60 * 60);

    /// 4 hours = 14400 seconds.
    pub const FOUR_HOURS: Self = Self(4 * 60 * 60);

    /// 1 day = 86400 seconds.
    pub const ONE_DAY: Self = Self(24 * 60 * 60);

    /// Create from seconds when the value is a supported market window.
    #[inline]
    pub const fn from_secs(secs: u32) -> Option<Self> {
        if secs == Self::ONE_MINUTE.0
            || secs == Self::FIVE_MINUTES.0
            || secs == Self::FIFTEEN_MINUTES.0
            || secs == Self::ONE_HOUR.0
            || secs == Self::FOUR_HOURS.0
            || secs == Self::ONE_DAY.0
        {
            Some(Self(secs))
        } else {
            None
        }
    }

    /// Check whether this value is a supported market window.
    #[inline]
    pub const fn is_valid(&self) -> bool {
        self.0 == Self::ONE_MINUTE.0
            || self.0 == Self::FIVE_MINUTES.0
            || self.0 == Self::FIFTEEN_MINUTES.0
            || self.0 == Self::ONE_HOUR.0
            || self.0 == Self::FOUR_HOURS.0
            || self.0 == Self::ONE_DAY.0
    }

    /// Window length in seconds.
    #[inline]
    pub const fn as_secs(&self) -> u32 {
        self.0
    }

    /// Window length in whole minutes.
    #[inline]
    pub const fn as_mins(&self) -> u32 {
        self.0 / 60
    }

    /// Timestamp in milliseconds when this duration would expire from now.
    #[inline]
    pub fn expiry_from_now(&self) -> u64 {
        Timestamp::now().0 + (self.0 as u64 * 1000)
    }
}

impl From<Duration> for u32 {
    fn from(value: Duration) -> Self {
        value.as_secs()
    }
}

impl fmt::Display for Duration {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.0 == Self::ONE_MINUTE.0 {
            write!(f, "1m")
        } else if self.0 == Self::FIVE_MINUTES.0 {
            write!(f, "5m")
        } else if self.0 == Self::FIFTEEN_MINUTES.0 {
            write!(f, "15m")
        } else if self.0 == Self::ONE_HOUR.0 {
            write!(f, "1h")
        } else if self.0 == Self::FOUR_HOURS.0 {
            write!(f, "4h")
        } else if self.0 == Self::ONE_DAY.0 {
            write!(f, "1d")
        } else {
            write!(f, "{}s", self.0)
        }
    }
}

// =============================================================================
// ODDS
// =============================================================================

/// Fixed-point odds representation.
///
/// Stored as basis points where `10000 = 1.0x`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[repr(transparent)]
pub struct Odds(pub u32);

impl Odds {
    /// 1.0x odds (break-even, no profit).
    pub const EVEN: Self = Self(10000);

    /// Minimum viable odds (1.0001x).
    pub const MIN: Self = Self(10001);

    /// Maximum accepted odds (1000x).
    pub const MAX: Self = Self(10_000_000);

    /// Basis-point divisor.
    pub const BASIS_POINTS: u32 = 10000;

    /// Create from a decimal representation.
    ///
    /// # Example
    /// ```
    /// use longshot_protocol::types::Odds;
    /// let odds = Odds::from_decimal(2, 5000); // 2.5x
    /// assert_eq!(odds.0, 25000);
    /// ```
    #[inline]
    pub const fn from_decimal(whole: u16, fractional_bps: u16) -> Self {
        Self((whole as u32 * Self::BASIS_POINTS) + fractional_bps as u32)
    }

    /// Decimal representation as `(whole, fractional_bps)`.
    #[inline]
    pub const fn to_decimal(&self) -> (u16, u16) {
        (
            (self.0 / Self::BASIS_POINTS) as u16,
            (self.0 % Self::BASIS_POINTS) as u16,
        )
    }

    /// Convert to `f64` for display only.
    #[inline]
    pub fn to_f64(&self) -> f64 {
        self.0 as f64 / Self::BASIS_POINTS as f64
    }

    /// Check if odds are within the valid range.
    #[inline]
    pub const fn is_valid(&self) -> bool {
        self.0 > Self::EVEN.0 && self.0 <= Self::MAX.0
    }

    const fn payout_micros_u128(&self, wager_micros: u64) -> u128 {
        (wager_micros as u128 * self.0 as u128) / Self::BASIS_POINTS as u128
    }

    /// Calculate payout for a wager in micro-dollars, saturating on overflow.
    #[inline]
    pub const fn calculate_payout(&self, wager_micros: u64) -> u64 {
        match self.checked_calculate_payout(wager_micros) {
            Some(payout) => payout,
            None => u64::MAX,
        }
    }

    /// Calculate payout for a wager in micro-dollars, returning `None` on overflow.
    #[inline]
    pub const fn checked_calculate_payout(&self, wager_micros: u64) -> Option<u64> {
        let payout = self.payout_micros_u128(wager_micros);
        if payout > u64::MAX as u128 {
            None
        } else {
            Some(payout as u64)
        }
    }

    /// Calculate profit (`payout - wager`), saturating on overflow or underflow.
    #[inline]
    pub const fn calculate_profit(&self, wager_micros: u64) -> u64 {
        match self.checked_calculate_profit(wager_micros) {
            Some(profit) => profit,
            None if self.0 <= Self::BASIS_POINTS => 0,
            None => u64::MAX,
        }
    }

    /// Calculate profit (`payout - wager`), returning `None` on overflow or underflow.
    #[inline]
    pub const fn checked_calculate_profit(&self, wager_micros: u64) -> Option<u64> {
        let Some(profit) = self
            .payout_micros_u128(wager_micros)
            .checked_sub(wager_micros as u128)
        else {
            return None;
        };
        if profit > u64::MAX as u128 {
            None
        } else {
            Some(profit as u64)
        }
    }

    /// Calculate market-maker liability (`payout - fill`) with checked math.
    #[inline]
    pub const fn checked_calculate_mm_liability(&self, fill_micros: u64) -> Option<u64> {
        self.checked_calculate_profit(fill_micros)
    }
}

impl fmt::Display for Odds {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let (whole, frac) = self.to_decimal();
        write!(f, "{}.{:04}x", whole, frac)
    }
}

// =============================================================================
// AMOUNT
// =============================================================================

/// Fixed-point arithmetic failure.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MathError {
    Overflow,
    Underflow,
    DivisionByZero,
}

/// Monetary amount in micro-dollars (6 decimals).
///
/// Represents wagers, payouts, balances, fees, and limits.
#[derive(
    Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Default, Serialize, Deserialize,
)]
#[repr(transparent)]
pub struct Amount(pub u64);

impl Amount {
    /// Zero amount.
    pub const ZERO: Self = Self(0);

    /// Micro-units per dollar.
    pub const MICROS_PER_DOLLAR: u64 = 1_000_000;

    /// Create from whole dollars.
    #[inline]
    pub const fn from_dollars(dollars: u64) -> Self {
        Self(dollars.saturating_mul(Self::MICROS_PER_DOLLAR))
    }

    /// Create from micro-dollars directly.
    #[inline]
    pub const fn from_micro(micros: u64) -> Self {
        Self(micros)
    }

    /// Fixed-point multiply using micro-dollars as the scale factor.
    #[inline]
    pub const fn fixed_mul(&self, other: Self) -> Result<Self, MathError> {
        let product = (self.0 as u128).saturating_mul(other.0 as u128);
        let scaled = product / Self::MICROS_PER_DOLLAR as u128;
        if scaled > u64::MAX as u128 {
            return Err(MathError::Overflow);
        }
        Ok(Self(scaled as u64))
    }

    /// Fixed-point divide using micro-dollars as the scale factor.
    #[inline]
    pub const fn fixed_div(&self, other: Self) -> Result<Self, MathError> {
        if other.0 == 0 {
            return Err(MathError::DivisionByZero);
        }

        let numerator = (self.0 as u128).saturating_mul(Self::MICROS_PER_DOLLAR as u128);
        let scaled = numerator / other.0 as u128;
        if scaled > u64::MAX as u128 {
            return Err(MathError::Overflow);
        }
        Ok(Self(scaled as u64))
    }

    /// Fixed-point multiply-then-divide with a single widened intermediate.
    #[inline]
    pub const fn fixed_mul_div(&self, mul: Self, div: Self) -> Result<Self, MathError> {
        if div.0 == 0 {
            return Err(MathError::DivisionByZero);
        }

        let numerator = (self.0 as u128).saturating_mul(mul.0 as u128);
        let scaled = numerator / div.0 as u128;
        if scaled > u64::MAX as u128 {
            return Err(MathError::Overflow);
        }
        Ok(Self(scaled as u64))
    }

    /// Convert to `f64` for display only.
    #[inline]
    pub fn to_f64(&self) -> f64 {
        self.0 as f64 / Self::MICROS_PER_DOLLAR as f64
    }

    /// Raw amount in micro-dollars.
    #[inline]
    pub const fn as_micros(&self) -> u64 {
        self.0
    }

    /// Saturating subtraction.
    #[inline]
    pub const fn saturating_sub(&self, other: Self) -> Self {
        Self(self.0.saturating_sub(other.0))
    }

    /// Saturating addition.
    #[inline]
    pub const fn saturating_add(&self, other: Self) -> Self {
        Self(self.0.saturating_add(other.0))
    }

    /// Check if amount satisfies the minimum bet.
    #[inline]
    pub fn is_valid_bet(&self) -> bool {
        self.0 >= MIN_BET_MICROS
    }
}

impl fmt::Display for Amount {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "${:.2}", self.to_f64())
    }
}

impl Add for Amount {
    type Output = Self;
    #[inline]
    fn add(self, rhs: Self) -> Self {
        Self(self.0.saturating_add(rhs.0))
    }
}

impl Sub for Amount {
    type Output = Self;
    #[inline]
    fn sub(self, rhs: Self) -> Self {
        Self(self.0.saturating_sub(rhs.0))
    }
}

// =============================================================================
// TIMESTAMP
// =============================================================================

/// Unix timestamp in milliseconds.
///
/// Milliseconds are used for RFQ expiries, market lifecycle fields, session
/// expiry, and API timestamps.
#[derive(
    Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Default, Serialize, Deserialize,
)]
#[repr(transparent)]
pub struct Timestamp(pub u64);

impl Timestamp {
    /// Zero timestamp.
    pub const ZERO: Self = Self(0);

    /// Current wall-clock timestamp.
    #[inline]
    pub fn now() -> Self {
        Self(unix_epoch_ms_from(SystemTime::now()))
    }

    /// Create from Unix seconds, returning `None` when milliseconds overflow.
    #[inline]
    pub const fn from_secs(secs: u64) -> Option<Self> {
        match secs.checked_mul(1000) {
            Some(millis) => Some(Self(millis)),
            None => None,
        }
    }

    /// Create from Unix milliseconds.
    #[inline]
    pub const fn from_millis(millis: u64) -> Self {
        Self(millis)
    }

    /// Timestamp in whole seconds.
    #[inline]
    pub const fn as_secs(&self) -> u64 {
        self.0 / 1000
    }

    /// Timestamp in milliseconds.
    #[inline]
    pub const fn as_millis(&self) -> u64 {
        self.0
    }

    /// Check whether this timestamp is before `current`.
    #[inline]
    pub const fn is_expired(&self, current: Self) -> bool {
        self.0 < current.0
    }

    /// Add milliseconds, returning `None` on overflow.
    #[inline]
    pub const fn add_millis(&self, ms: u64) -> Option<Self> {
        match self.0.checked_add(ms) {
            Some(millis) => Some(Self(millis)),
            None => None,
        }
    }

    /// Milliseconds until this timestamp, saturating to zero for past values.
    #[inline]
    pub fn millis_until(&self, current: Self) -> u64 {
        self.0.saturating_sub(current.0)
    }
}

#[inline]
fn unix_epoch_ms_from(now: SystemTime) -> u64 {
    match now.duration_since(UNIX_EPOCH) {
        Ok(duration) => u64::try_from(duration.as_millis()).unwrap_or(u64::MAX),
        Err(_) => 0,
    }
}

impl fmt::Display for Timestamp {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}ms", self.0)
    }
}

// =============================================================================
// ORDER TYPE
// =============================================================================

/// Order execution type for RFQ requests.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[repr(u8)]
pub enum OrderType {
    /// Immediate-or-Cancel: fill available liquidity, cancel the rest.
    IOC = 1,
    /// Fill-or-Kill: complete fill or nothing.
    FOK = 2,
}

impl OrderType {
    /// Convert from the RFQ/API numeric representation.
    #[inline]
    pub const fn from_u8(v: u8) -> Option<Self> {
        match v {
            1 => Some(Self::IOC),
            2 => Some(Self::FOK),
            _ => None,
        }
    }

    /// Whether this order type requires full fill.
    #[inline]
    pub const fn requires_full_fill(&self) -> bool {
        matches!(self, OrderType::FOK)
    }

    /// Whether this order type allows partial fills.
    #[inline]
    pub const fn allows_partial_fill(&self) -> bool {
        matches!(self, OrderType::IOC)
    }
}

impl From<OrderType> for u8 {
    #[inline]
    fn from(value: OrderType) -> Self {
        match value {
            OrderType::IOC => 1,
            OrderType::FOK => 2,
        }
    }
}

impl fmt::Display for OrderType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            OrderType::IOC => write!(f, "IOC"),
            OrderType::FOK => write!(f, "FOK"),
        }
    }
}

// =============================================================================
// USER TIER
// =============================================================================

/// User tier used by RFQ pricing, throttling, and API/session responses.
#[derive(
    Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize, Default,
)]
#[repr(u8)]
pub enum UserTier {
    #[default]
    Standard = 0,
    Silver = 1,
    Gold = 2,
    Platinum = 3,
    VIP = 4,
}

impl UserTier {
    /// Convert from the RFQ/API numeric representation.
    #[inline]
    pub const fn from_u8(v: u8) -> Option<Self> {
        match v {
            0 => Some(Self::Standard),
            1 => Some(Self::Silver),
            2 => Some(Self::Gold),
            3 => Some(Self::Platinum),
            4 => Some(Self::VIP),
            _ => None,
        }
    }
}

impl fmt::Display for UserTier {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            UserTier::Standard => write!(f, "Standard"),
            UserTier::Silver => write!(f, "Silver"),
            UserTier::Gold => write!(f, "Gold"),
            UserTier::Platinum => write!(f, "Platinum"),
            UserTier::VIP => write!(f, "VIP"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_asset_from_u8() {
        assert_eq!(Asset::from_u8(0), Some(Asset::BTC));
        assert_eq!(Asset::from_u8(4), Some(Asset::HYPE));
        assert_eq!(Asset::from_u8(5), None);
    }

    #[test]
    fn test_asset_parse_symbol() {
        assert_eq!(Asset::parse_symbol("btc"), Some(Asset::BTC));
        assert_eq!(Asset::parse_symbol(" EtH\t"), Some(Asset::ETH));
        assert_eq!(Asset::parse_symbol(""), None);
        assert_eq!(Asset::parse_symbol("unknown"), None);
    }

    #[test]
    fn test_duration_validity() {
        assert!(Duration::ONE_MINUTE.is_valid());
        assert!(Duration::FIVE_MINUTES.is_valid());
        assert!(Duration::FIFTEEN_MINUTES.is_valid());
        assert!(Duration::ONE_HOUR.is_valid());
        assert!(Duration::FOUR_HOURS.is_valid());
        assert!(Duration::ONE_DAY.is_valid());
        assert!(!Duration(123).is_valid());
        assert_eq!(Duration::from_secs(60), Some(Duration::ONE_MINUTE));
        assert_eq!(Duration::from_secs(300), Some(Duration::FIVE_MINUTES));
        assert_eq!(Duration::from_secs(900), Some(Duration::FIFTEEN_MINUTES));
        assert_eq!(Duration::from_secs(3600), Some(Duration::ONE_HOUR));
        assert_eq!(Duration::from_secs(14_400), Some(Duration::FOUR_HOURS));
        assert_eq!(Duration::from_secs(86_400), Some(Duration::ONE_DAY));
        assert_eq!(Duration::from_secs(1000), None);
    }

    #[test]
    fn test_odds_calculation() {
        let odds = Odds::from_decimal(2, 5000);
        assert_eq!(odds.0, 25000);

        let wager = 100_000_000u64;
        assert_eq!(odds.calculate_payout(wager), 250_000_000);
        assert_eq!(odds.calculate_profit(wager), 150_000_000);
        assert_eq!(
            odds.checked_calculate_mm_liability(wager),
            Some(150_000_000)
        );
    }

    #[test]
    fn test_odds_calculation_handles_u64_boundaries() {
        let wager = u64::MAX / 2 + 1;
        let two_x = Odds::from_decimal(2, 0);
        assert_eq!(two_x.checked_calculate_payout(wager), None);
        assert_eq!(two_x.calculate_payout(wager), u64::MAX);
        assert_eq!(two_x.checked_calculate_profit(wager), Some(wager));
        assert_eq!(two_x.calculate_profit(wager), wager);
        assert_eq!(two_x.checked_calculate_mm_liability(wager), Some(wager));

        let three_x = Odds::from_decimal(3, 0);
        assert_eq!(three_x.checked_calculate_profit(wager), None);
        assert_eq!(three_x.calculate_profit(wager), u64::MAX);
    }

    #[test]
    fn test_odds_validity() {
        assert!(!Odds::EVEN.is_valid());
        assert!(Odds::MIN.is_valid());
        assert!(Odds::from_decimal(5, 0).is_valid());
        assert!(!Odds::from_decimal(1001, 0).is_valid());
    }

    #[test]
    fn test_amount_validation() {
        assert!(!Amount::from_micro(MIN_BET_MICROS - 10_000).is_valid_bet());
        assert!(Amount::from_micro(MIN_BET_MICROS).is_valid_bet());
        assert!(Amount::from_dollars(100).is_valid_bet());
    }

    #[test]
    fn test_timestamp() {
        let now = Timestamp::now();
        let future = now.add_millis(1000).unwrap();
        let past = Timestamp::from_millis(now.0 - 1000);

        assert!(!now.is_expired(now));
        assert!(!future.is_expired(now));
        assert!(past.is_expired(now));
        assert_eq!(
            Timestamp::from_secs(u64::MAX / 1000),
            Some(Timestamp::from_millis((u64::MAX / 1000) * 1000))
        );
        assert_eq!(Timestamp::from_secs(u64::MAX), None);
        assert_eq!(Timestamp::from_millis(u64::MAX).add_millis(1), None);
    }

    #[test]
    fn test_unix_epoch_ms_from_handles_pre_epoch_without_panic() {
        let before_epoch = UNIX_EPOCH
            .checked_sub(std::time::Duration::from_millis(1))
            .expect("pre-epoch system time should be representable");

        assert_eq!(unix_epoch_ms_from(before_epoch), 0);
    }

    #[test]
    fn test_order_type() {
        assert!(OrderType::FOK.requires_full_fill());
        assert!(!OrderType::IOC.requires_full_fill());
        assert!(OrderType::IOC.allows_partial_fill());
        assert!(!OrderType::FOK.allows_partial_fill());
    }

    #[test]
    fn test_duration_expiry_from_now() {
        let before = Timestamp::now().0;
        let expiry = Duration::FIFTEEN_MINUTES.expiry_from_now();
        let after = Timestamp::now().0;
        let duration_ms = Duration::FIFTEEN_MINUTES.0 as u64 * 1000;

        assert!(expiry >= before + duration_ms);
        assert!(expiry <= after + duration_ms);
    }

    #[test]
    fn test_amount_fixed_math() {
        let lhs = Amount::from_micro(1_500_000);
        let rhs = Amount::from_micro(2_000_000);

        assert_eq!(lhs.fixed_mul(rhs), Ok(Amount::from_micro(3_000_000)));
        assert_eq!(Amount::from_micro(3_000_000).fixed_div(rhs), Ok(lhs));
        assert_eq!(
            lhs.fixed_mul_div(rhs, Amount::from_micro(500_000)),
            Ok(Amount::from_micro(6_000_000))
        );
    }

    #[test]
    fn test_amount_fixed_math_errors() {
        assert_eq!(
            Amount::from_micro(1_000_000).fixed_div(Amount::ZERO),
            Err(MathError::DivisionByZero)
        );
        assert_eq!(
            Amount::from_micro(1_000_000)
                .fixed_mul_div(Amount::from_micro(2_000_000), Amount::ZERO),
            Err(MathError::DivisionByZero)
        );
        assert_eq!(
            Amount::from_micro(u64::MAX).fixed_mul(Amount::from_micro(u64::MAX)),
            Err(MathError::Overflow)
        );
        assert_eq!(
            Amount::from_micro(u64::MAX).fixed_div(Amount::from_micro(1)),
            Err(MathError::Overflow)
        );
    }

    #[test]
    fn test_timestamp_millis_until() {
        let now = Timestamp::from_millis(1000);
        let future = Timestamp::from_millis(2000);
        let past = Timestamp::from_millis(500);

        assert_eq!(future.millis_until(now), 1000);
        assert_eq!(past.millis_until(now), 0);
        assert_eq!(now.millis_until(now), 0);
    }

    #[test]
    fn test_amount_saturating_methods() {
        let max_amount = Amount(u64::MAX);
        assert_eq!(max_amount.saturating_add(Amount(1)).0, u64::MAX);

        let small_amount = Amount(10);
        assert_eq!(small_amount.saturating_sub(Amount(100)).0, 0);

        let a = Amount(100);
        let b = Amount(50);
        assert_eq!(a.saturating_add(b).0, 150);
        assert_eq!(a.saturating_sub(b).0, 50);
    }

    #[test]
    fn test_user_tier_ordering() {
        assert!(UserTier::Standard < UserTier::Silver);
        assert!(UserTier::Silver < UserTier::Gold);
        assert!(UserTier::Gold < UserTier::Platinum);
        assert!(UserTier::Platinum < UserTier::VIP);
        assert_eq!(UserTier::default(), UserTier::Standard);
    }

    #[test]
    fn test_direction_helpers() {
        assert_eq!(Direction::Up.opposite(), Direction::Down);
        assert_eq!(Direction::Down.opposite(), Direction::Up);
        assert_eq!(Direction::Up.opposite().opposite(), Direction::Up);
        assert!(Direction::Up.predicts_higher());
        assert!(!Direction::Down.predicts_higher());
    }

    #[test]
    fn test_display_implementations() {
        assert_eq!(format!("{}", Asset::BTC), "BTC");
        assert_eq!(format!("{}", Asset::HYPE), "HYPE");
        assert_eq!(format!("{}", Direction::Up), "UP");
        assert_eq!(format!("{}", Direction::Down), "DOWN");
        assert_eq!(format!("{}", Duration::ONE_MINUTE), "1m");
        assert_eq!(format!("{}", Duration::FIVE_MINUTES), "5m");
        assert_eq!(format!("{}", Duration::FIFTEEN_MINUTES), "15m");
        assert_eq!(format!("{}", Duration::ONE_HOUR), "1h");
        assert_eq!(format!("{}", Duration::FOUR_HOURS), "4h");
        assert_eq!(format!("{}", Duration::ONE_DAY), "1d");
        assert_eq!(format!("{}", Duration(123)), "123s");
        assert_eq!(format!("{}", Odds::from_decimal(2, 5000)), "2.5000x");
        assert_eq!(format!("{}", Amount::from_dollars(50)), "$50.00");
        assert_eq!(format!("{}", Timestamp::from_millis(1000)), "1000ms");
        assert_eq!(format!("{}", OrderType::IOC), "IOC");
        assert_eq!(format!("{}", OrderType::FOK), "FOK");
        assert_eq!(format!("{}", UserTier::VIP), "VIP");
        assert_eq!(format!("{}", UserTier::Standard), "Standard");
    }
}
