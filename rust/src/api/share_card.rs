//! Share-card snapshot contract.
//!
//! A client submits a [`ShareCardSnapshot`] to `POST /v1/share-cards` with
//! render hints captured at share time. The API verifies authenticated claims,
//! canonicalizes trusted identity fields, and stores the frozen snapshot used to
//! render an OpenGraph image.
//!
//! The enum is `#[serde(tag = "type")]`, so the wire shape is
//! `{ "type": "streak", "streak_count": 7, ... }`.

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::response::SurvivorEntryRoundResultResponse;

/// Upper bound on the number of price samples accepted for a price card's
/// chart. Plenty for a smooth curve; bounds payload size and render cost.
pub const MAX_CHART_POINTS: usize = 512;
/// Upper bound on the number of legs accepted for a questions card.
pub const MAX_QUESTION_LEGS: usize = 32;
/// Upper bound on the number of prediction windows on a markets card. Matches
/// the RFQ wire protocol's nine-leg maximum.
pub const MAX_MARKET_WINDOWS: usize = 9;
/// Upper bound on the per-window asset picks on a markets card (BTC/ETH/SOL).
pub const MAX_MARKET_WINDOW_PICKS: usize = 3;
/// Largest client timezone offset accepted as a render hint, in minutes
/// (UTC±14:00 covers every real offset).
pub const MAX_TZ_OFFSET_MINUTES: i16 = 14 * 60;
/// Upper bound on the number of header/settlement stat cells.
pub const MAX_SUMMARY_STATS: usize = 4;
/// Upper bound on the number of picks on a roster card (one per tier).
pub const MAX_ROSTER_SHARE_PICKS: usize = 10;
/// Upper bound on the number of child-market picks on an Event position card.
pub const MAX_EVENT_POSITION_SHARE_PICKS: usize = 9;
/// Maximum total number of Survivor pick images rendered on one share card.
pub const MAX_SURVIVOR_SHARE_PICKS: usize = 64;
/// Share-card rendering limit for Survivor rounds. This does not constrain the
/// number of rounds a Survivor contest may contain.
pub const MAX_SURVIVOR_SHARE_ROUNDS: usize = 30;
/// Upper bound on any single user-supplied text field, in chars.
pub const MAX_TEXT_LEN: usize = 200;

/// How the API should source a card image.
///
/// Pool images are referenced by `pool_image_id`; absent images use the API's
/// default visual fallback.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "source", rename_all = "snake_case")]
pub enum ShareImageRef {
    PoolImage { pool_image_id: Uuid },
}

/// Footer identity, shown on every card. The handle is rendered with an `@`
/// prefix. Client-supplied values are accepted as render hints, but the create
/// endpoint overwrites them with the authenticated user's profile handle before
/// persisting the snapshot.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ShareCardFooter {
    pub handle: String,
}

/// A labelled stat cell used in card headers / settlement summaries.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ShareStat {
    pub value: String,
    pub label: String,
}

/// Streak share card — LIVE state only (we never share the settled card).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakShareCard {
    /// Predictions made so far — the ordinal in "Nth prediction made".
    pub streak_count: u32,
    /// Total positions on the progress strip (homepage Streak ships at 25).
    pub max_streak: u32,
    /// Headline of the market the user just picked.
    pub market_title: String,
    /// Team or topic image for that market.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub market_image: Option<ShareImageRef>,
    /// The side the user chose, e.g. "87° or below".
    pub selection: String,
    /// Human date for the selection, e.g. "Jun 11".
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selection_date: Option<String>,
    /// Prize headline shown top-right, e.g. "$25K".
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub prize_label: Option<String>,
    pub footer: ShareCardFooter,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum PriceState {
    Live,
    Won,
    Lost,
}

/// Price (Crypto Dailies, BTC) share card — all states.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PriceShareCard {
    /// Contest backing this BTC prediction. Used by the API to verify that the
    /// caller owns the entry before the card is persisted.
    pub contest_id: String,
    /// Caller-owned entry index within `contest_id`.
    pub entry_index: u32,
    pub state: PriceState,
    /// e.g. "What will the price of BTC be?"
    pub question: String,
    /// e.g. "at 12pm June 13".
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub subtitle: Option<String>,
    /// The user's prediction — drawn as the dashed reference line.
    pub prediction: f64,
    /// Current price (live) or final price (settled).
    pub current_price: f64,
    /// The exact price series displayed to the user, oldest to newest. The API
    /// maps these into the chart viewport to reproduce the curve.
    pub chart_prices: Vec<f64>,
    /// Settlement summary cells (won/lost). Empty for live.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub summary: Vec<ShareStat>,
    pub footer: ShareCardFooter,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum QuestionsState {
    Pre,
    Live,
    Won,
    Lost,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum ContestType {
    #[default]
    Free,
    Paid,
}

/// Per-leg grade for card rendering.
///
/// `Pending` represents an unresolved leg. `Correct` and `Incorrect` represent
/// the displayed grade after applying live or resolved market data.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum LegGrade {
    Pending,
    Correct,
    Incorrect,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct QuestionLeg {
    pub name: String,
    /// "Yes" / "No" (the user's answer for this leg).
    pub answer: String,
    pub grade: LegGrade,
}

/// Questions (Lineups contest) share card.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct QuestionsShareCard {
    /// Contest backing this lineup. Used by the API to verify that the caller
    /// owns the entry before the card is persisted.
    pub contest_id: String,
    /// Caller-owned entry index within `contest_id`.
    pub entry_index: u32,
    pub state: QuestionsState,
    pub contest_type: ContestType,
    /// The contest question / headline.
    pub question: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub topic_image: Option<ShareImageRef>,
    pub legs: Vec<QuestionLeg>,
    /// Settlement / live summary cells. Empty when not applicable.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub summary: Vec<ShareStat>,
    pub footer: ShareCardFooter,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum MarketsState {
    #[default]
    Pre,
    Live,
    Won,
    Lost,
}

/// Window-level outcome rollup for a markets card. `Live` marks the window in
/// progress at share time; `Pending` a window that has not started (or whose
/// grade is still unknown on an early-lost parlay).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum MarketWindowOutcome {
    Pending,
    Live,
    Won,
    Lost,
    Voided,
}

/// One asset pick inside a markets-card window.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketWindowPick {
    /// Asset ticker, e.g. "BTC".
    pub asset: String,
    /// "up" | "down".
    pub direction: String,
    /// Per-leg grade; `None` while pending.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub won: Option<bool>,
    /// Signed price move over the window (close vs open strike), in basis
    /// points. `None` until the window has a measurable price.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pct_bps: Option<i32>,
}

/// One prediction window on a markets card.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketWindow {
    pub start_ms: i64,
    pub end_ms: i64,
    /// e.g. "13:05–13:10" in the sharer's timezone.
    pub time_label: String,
    pub outcome: MarketWindowOutcome,
    /// One pick per asset; single-asset cards carry exactly one.
    pub picks: Vec<MarketWindowPick>,
}

/// A per-asset price series for the markets-card chart, baked by the API at
/// share time so rendering stays a pure function of the frozen snapshot.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketChartSeries {
    pub asset: String,
    /// Oldest to newest across the position's window span.
    pub prices: Vec<f64>,
}

/// Crypto markets (RFQ parlay) share card — all states.
///
/// The client submits `position_id` (+ optional `tz_offset_minutes`) and a
/// skeleton for the rest; the API re-derives every other field from the
/// caller's stored position before persisting.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketsShareCard {
    /// Position backing this card. Used by the API to verify that the caller
    /// owns the position before the card is persisted.
    pub position_id: String,
    /// Sharer's local UTC offset in minutes (render hint for time labels).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub tz_offset_minutes: Option<i16>,
    /// All fields below are derived by the API at create time, so the wire
    /// request may omit them (serde defaults).
    #[serde(default)]
    pub state: MarketsState,
    /// True when the position spans more than one asset.
    #[serde(default)]
    pub multi_asset: bool,
    /// Distinct assets in stable BTC/ETH/SOL order.
    #[serde(default)]
    pub assets: Vec<String>,
    /// Chronological prediction windows (1..=9 once canonicalized).
    #[serde(default)]
    pub windows: Vec<MarketWindow>,
    /// e.g. "Jun 4, 2026" (first window start, sharer's timezone).
    #[serde(default)]
    pub date_label: String,
    /// e.g. "$1.00".
    #[serde(default)]
    pub wager_label: String,
    /// e.g. "312.5x".
    #[serde(default)]
    pub multiplier_label: String,
    /// e.g. "$312.50".
    #[serde(default)]
    pub payout_label: String,
    /// Single-asset won/lost price-transition line: first window's open.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub price_from: Option<f64>,
    /// …to the last graded window's close.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub price_to: Option<f64>,
    /// Per-asset chart series; empty for pre-settlement cards.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub chart: Vec<MarketChartSeries>,
    pub footer: ShareCardFooter,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum RosterShareState {
    Pre,
    Live,
    Won,
    Lost,
    /// Won with a perfect slate (every tier's top scorer + exact tiebreaker).
    Perfect,
}

/// Roster engine subtype with a card design. Unknown engine sources are
/// rejected at create time rather than degrading to a broken card.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum RosterShareKind {
    X,
    Nfl,
}

/// One pick on a roster card: the entry's selection in one tier.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct RosterSharePick {
    /// Display name: X "@handle", NFL "First Last".
    pub name: String,
    /// Avatar chip background, "#rrggbb" (kind palette).
    pub bg: String,
    /// Avatar chip foreground, "#rrggbb".
    pub fg: String,
    /// Score text for live/settled states (e.g. "7", "21.4"); omitted pre.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub points: Option<String>,
    /// Unit under the score ("posts" / "points"); omitted pre.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub unit: Option<String>,
    /// Pre/unstarted label (NFL kickoff "Sun 8:20pm"); omitted otherwise.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub tip: Option<String>,
    /// Settled: whether the pick won its tier (ties count).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub hit: Option<bool>,
}

/// Roster contest (X Daily / NFL Weekly) share card — all states.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct RosterShareCard {
    /// Contest backing this roster entry. Used by the API to verify that the
    /// caller owns the entry before the card is persisted.
    pub contest_id: String,
    /// Caller-owned entry index within `contest_id`.
    pub entry_index: u32,
    pub state: RosterShareState,
    pub contest_type: ContestType,
    pub kind: RosterShareKind,
    /// "Who will have the most posts today?" / "Who will score the most
    /// fantasy points?"
    pub prompt: String,
    /// The entry's pick per tier, in tier order (1..=MAX_ROSTER_SHARE_PICKS).
    pub picks: Vec<RosterSharePick>,
    /// Header stat cells per state. Empty when not applicable.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub summary: Vec<ShareStat>,
    /// Perfect state only: the perfect-slate bonus amount (e.g. "$500"),
    /// rendered in the bonus pill. Derived server-side.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bonus_label: Option<String>,
    pub footer: ShareCardFooter,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum SurvivorShareState {
    #[default]
    Pre,
    Live,
    Won,
    Lost,
    Voided,
}

/// Server-derived visual treatment for a Survivor card. This is presentation
/// metadata, not a Survivor contest kind.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum SurvivorSharePresentation {
    Matchup,
    #[default]
    Daily,
}

/// One round in a Survivor card. Pick images are resolved and stored by the
/// API; the snapshot carries only the number of image slots for this round.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct SurvivorShareRound {
    pub result: SurvivorEntryRoundResultResponse,
    pub pick_count: u32,
}

/// Survivor contest share card — all states.
///
/// The client may submit only `contest_id`, `entry_index`, and `footer`; the
/// API derives every other field from the caller's stored entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct SurvivorShareCard {
    /// Contest backing this Survivor entry. Used by the API to verify that the
    /// caller owns the entry before the card is persisted.
    pub contest_id: String,
    /// Caller-owned entry index within `contest_id`.
    pub entry_index: u32,
    #[serde(default)]
    pub state: SurvivorShareState,
    #[serde(default)]
    pub contest_type: ContestType,
    #[serde(default)]
    pub presentation: SurvivorSharePresentation,
    #[serde(default)]
    pub title: String,
    /// All contest rounds in game-index order once canonicalized. An empty
    /// vector is accepted as the pre-canonicalization request skeleton.
    #[serde(default)]
    pub rounds: Vec<SurvivorShareRound>,
    /// Header stat cells. Empty when not applicable.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub summary: Vec<ShareStat>,
    pub footer: ShareCardFooter,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum EventPositionShareState {
    #[default]
    Active,
    Live,
    Won,
    Lost,
    Voided,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum EventPositionSharePickGrade {
    Pending,
    Correct,
    Incorrect,
    Voided,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct EventPositionSharePick {
    /// Canonical Longshot child-market id.
    pub market_id: u64,
    /// Concise outcome label from the child market.
    pub label: String,
    /// The user's selected side (`yes` or `no`).
    pub side: String,
    pub grade: EventPositionSharePickGrade,
    /// Current selected-side decimal odds used by unsettled multi-outcome
    /// cards when the canonical market source exposes a probability.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub odds_label: Option<String>,
    /// Factual settled result (`Yes`, `No`, or `Voided`); absent while pending.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub result: Option<String>,
    /// NFL only: team tricode for the pick's chip (game-wide markets omit it).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub team_abbr: Option<String>,
}

/// Event-position share card for Culture, Mentions, and Sports markets.
///
/// On create, clients submit only `position_id`, `tz_offset_minutes`, and
/// `footer`. Every remaining field is overwritten from the authenticated
/// user's stored position and its canonical market rows.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct EventPositionShareCard {
    pub position_id: String,
    /// Sharer's local UTC offset in minutes. This is a render hint for time
    /// labels, such as an NFL kickoff. Absent values use US Eastern.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub tz_offset_minutes: Option<i16>,
    /// Server-derived event vertical (`culture`, `mentions`, or `sports`).
    /// Historical cards can predate this field.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub market_kind: Option<String>,
    #[serde(default)]
    pub state: EventPositionShareState,
    #[serde(default)]
    pub title: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub meta_label: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub market_image: Option<ShareImageRef>,
    #[serde(default)]
    pub picks: Vec<EventPositionSharePick>,
    #[serde(default)]
    pub wager_label: String,
    #[serde(default)]
    pub multiplier_label: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub payout_label: Option<String>,
    /// NFL only: matchup identity for team chips + combo/prediction heading.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub nfl: Option<NflShareMeta>,
    pub footer: ShareCardFooter,
}

/// NFL-card matchup identity (only present when `market_kind == "sports"`).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct NflShareMeta {
    pub away_abbr: String,
    pub home_abbr: String,
    #[serde(default)]
    pub combo: bool,
}

/// The tagged snapshot union persisted per share card.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum ShareCardSnapshot {
    Streak(StreakShareCard),
    Price(PriceShareCard),
    Questions(QuestionsShareCard),
    Markets(MarketsShareCard),
    Roster(RosterShareCard),
    Survivor(SurvivorShareCard),
    EventPosition(EventPositionShareCard),
}

#[derive(Debug, Serialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct CreateShareCardResponse {
    pub id: String,
    pub share_url: String,
}

impl ShareCardSnapshot {
    /// The discriminant stored in the `type` column and used for OG copy.
    pub fn type_str(&self) -> &'static str {
        match self {
            ShareCardSnapshot::Streak(_) => "streak",
            ShareCardSnapshot::Price(_) => "price",
            ShareCardSnapshot::Questions(_) => "questions",
            ShareCardSnapshot::Markets(_) => "markets",
            ShareCardSnapshot::Roster(_) => "roster",
            ShareCardSnapshot::Survivor(_) => "survivor",
            ShareCardSnapshot::EventPosition(_) => "event_position",
        }
    }

    /// Validate sizes and required fields. Rejects payloads that would blow up
    /// storage or the renderer. Returns a human-readable field name on failure.
    pub fn validate(&self) -> Result<(), &'static str> {
        let check_text = |s: &str, field: &'static str| -> Result<(), &'static str> {
            if s.chars().count() > MAX_TEXT_LEN {
                Err(field)
            } else {
                Ok(())
            }
        };
        let check_footer = |f: &ShareCardFooter| -> Result<(), &'static str> {
            check_text(&f.handle, "footer.handle")
        };
        let check_contest_id = |s: &str| -> Result<(), &'static str> {
            if uuid::Uuid::parse_str(s.trim()).is_err() {
                Err("contest_id")
            } else {
                Ok(())
            }
        };
        let check_summary = |summary: &[ShareStat]| -> Result<(), &'static str> {
            if summary.len() > MAX_SUMMARY_STATS {
                return Err("summary");
            }
            for stat in summary {
                check_text(&stat.value, "summary.value")?;
                check_text(&stat.label, "summary.label")?;
            }
            Ok(())
        };
        match self {
            ShareCardSnapshot::Streak(c) => {
                if c.max_streak == 0 || c.streak_count > c.max_streak {
                    return Err("streak_count");
                }
                check_text(&c.market_title, "market_title")?;
                check_text(&c.selection, "selection")?;
                if let Some(selection_date) = &c.selection_date {
                    check_text(selection_date, "selection_date")?;
                }
                if let Some(prize_label) = &c.prize_label {
                    check_text(prize_label, "prize_label")?;
                }
                check_footer(&c.footer)?;
            }
            ShareCardSnapshot::Price(c) => {
                check_contest_id(&c.contest_id)?;
                if c.chart_prices.len() > MAX_CHART_POINTS {
                    return Err("chart_prices");
                }
                if !c.prediction.is_finite() || !c.current_price.is_finite() {
                    return Err("price");
                }
                if c.chart_prices.iter().any(|p| !p.is_finite()) {
                    return Err("chart_prices");
                }
                check_text(&c.question, "question")?;
                if let Some(subtitle) = &c.subtitle {
                    check_text(subtitle, "subtitle")?;
                }
                check_summary(&c.summary)?;
                check_footer(&c.footer)?;
            }
            ShareCardSnapshot::Questions(c) => {
                check_contest_id(&c.contest_id)?;
                if c.legs.is_empty() || c.legs.len() > MAX_QUESTION_LEGS {
                    return Err("legs");
                }
                check_text(&c.question, "question")?;
                for leg in &c.legs {
                    check_text(&leg.name, "legs.name")?;
                    check_text(&leg.answer, "legs.answer")?;
                }
                check_summary(&c.summary)?;
                check_footer(&c.footer)?;
            }
            ShareCardSnapshot::Markets(c) => {
                check_contest_id(&c.position_id).map_err(|_| "position_id")?;
                if let Some(tz) = c.tz_offset_minutes {
                    // The offset is untrusted i16 input; unsigned_abs also handles
                    // i16::MIN without panicking or wrapping past validation.
                    if tz.unsigned_abs() > MAX_TZ_OFFSET_MINUTES as u16 {
                        return Err("tz_offset_minutes");
                    }
                }
                if c.assets.len() > MAX_MARKET_WINDOW_PICKS {
                    return Err("assets");
                }
                for asset in &c.assets {
                    check_text(asset, "assets")?;
                }
                if c.windows.len() > MAX_MARKET_WINDOWS {
                    return Err("windows");
                }
                for window in &c.windows {
                    check_text(&window.time_label, "windows.time_label")?;
                    if window.picks.len() > MAX_MARKET_WINDOW_PICKS {
                        return Err("windows.picks");
                    }
                    for pick in &window.picks {
                        check_text(&pick.asset, "windows.picks.asset")?;
                        check_text(&pick.direction, "windows.picks.direction")?;
                    }
                }
                check_text(&c.date_label, "date_label")?;
                check_text(&c.wager_label, "wager_label")?;
                check_text(&c.multiplier_label, "multiplier_label")?;
                check_text(&c.payout_label, "payout_label")?;
                for value in [c.price_from, c.price_to].into_iter().flatten() {
                    if !value.is_finite() {
                        return Err("price");
                    }
                }
                if c.chart.len() > MAX_MARKET_WINDOW_PICKS {
                    return Err("chart");
                }
                for series in &c.chart {
                    check_text(&series.asset, "chart.asset")?;
                    if series.prices.len() > MAX_CHART_POINTS {
                        return Err("chart.prices");
                    }
                    if series.prices.iter().any(|p| !p.is_finite()) {
                        return Err("chart.prices");
                    }
                }
                check_footer(&c.footer)?;
            }
            ShareCardSnapshot::Roster(c) => {
                let check_hex_color = |s: &str, field: &'static str| -> Result<(), &'static str> {
                    let mut chars = s.chars();
                    let hash = chars.next();
                    let hex: Vec<char> = chars.collect();
                    if hash != Some('#')
                        || hex.len() != 6
                        || !hex.iter().all(|character| character.is_ascii_hexdigit())
                    {
                        return Err(field);
                    }
                    Ok(())
                };
                check_contest_id(&c.contest_id)?;
                check_text(&c.prompt, "prompt")?;
                if c.picks.is_empty() || c.picks.len() > MAX_ROSTER_SHARE_PICKS {
                    return Err("picks");
                }
                for pick in &c.picks {
                    check_text(&pick.name, "picks.name")?;
                    check_hex_color(&pick.bg, "picks.bg")?;
                    check_hex_color(&pick.fg, "picks.fg")?;
                    if let Some(points) = &pick.points {
                        check_text(points, "picks.points")?;
                    }
                    if let Some(unit) = &pick.unit {
                        check_text(unit, "picks.unit")?;
                    }
                    if let Some(tip) = &pick.tip {
                        check_text(tip, "picks.tip")?;
                    }
                }
                check_summary(&c.summary)?;
                if let Some(bonus_label) = &c.bonus_label {
                    check_text(bonus_label, "bonus_label")?;
                }
                check_footer(&c.footer)?;
            }
            ShareCardSnapshot::Survivor(c) => {
                check_contest_id(&c.contest_id)?;
                check_text(&c.title, "title")?;
                if c.rounds.len() > MAX_SURVIVOR_SHARE_ROUNDS {
                    return Err("rounds");
                }
                let pick_count: u64 = c
                    .rounds
                    .iter()
                    .map(|round| u64::from(round.pick_count))
                    .sum();
                if pick_count > MAX_SURVIVOR_SHARE_PICKS as u64 {
                    return Err("rounds.pick_count");
                }
                check_summary(&c.summary)?;
                check_footer(&c.footer)?;
            }
            ShareCardSnapshot::EventPosition(c) => {
                check_contest_id(&c.position_id).map_err(|_| "position_id")?;
                if let Some(tz) = c.tz_offset_minutes {
                    if tz.unsigned_abs() > MAX_TZ_OFFSET_MINUTES as u16 {
                        return Err("tz_offset_minutes");
                    }
                }
                check_text(&c.title, "title")?;
                if let Some(meta_label) = &c.meta_label {
                    check_text(meta_label, "meta_label")?;
                }
                if c.picks.len() > MAX_EVENT_POSITION_SHARE_PICKS {
                    return Err("picks");
                }
                for pick in &c.picks {
                    check_text(&pick.label, "picks.label")?;
                    if !matches!(pick.side.as_str(), "yes" | "no") {
                        return Err("picks.side");
                    }
                    if let Some(odds_label) = &pick.odds_label {
                        check_text(odds_label, "picks.odds_label")?;
                    }
                    if let Some(result) = &pick.result {
                        check_text(result, "picks.result")?;
                    }
                }
                check_text(&c.wager_label, "wager_label")?;
                check_text(&c.multiplier_label, "multiplier_label")?;
                check_footer(&c.footer)?;
                if let Some(payout_label) = &c.payout_label {
                    check_text(payout_label, "payout_label")?;
                }
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn footer() -> ShareCardFooter {
        ShareCardFooter {
            handle: "aidan".to_string(),
        }
    }

    #[test]
    fn streak_snapshot_round_trips_with_type_tag() {
        let snap = ShareCardSnapshot::Streak(StreakShareCard {
            streak_count: 7,
            max_streak: 25,
            market_title: "NYC High Temp".to_string(),
            market_image: Some(ShareImageRef::PoolImage {
                pool_image_id: Uuid::nil(),
            }),
            selection: "87° or below".to_string(),
            selection_date: Some("Jun 11".to_string()),
            prize_label: Some("$25K".to_string()),
            footer: footer(),
        });
        let json = serde_json::to_string(&snap).expect("serialize");
        assert!(json.contains("\"type\":\"streak\""));
        let back: ShareCardSnapshot = serde_json::from_str(&json).expect("deserialize");
        assert_eq!(back, snap);
        assert_eq!(snap.type_str(), "streak");
        snap.validate().expect("valid");
    }

    #[test]
    fn event_position_snapshot_round_trips_with_type_tag() {
        let mut snap = ShareCardSnapshot::EventPosition(EventPositionShareCard {
            position_id: Uuid::nil().to_string(),
            tz_offset_minutes: Some(-300),
            market_kind: None,
            state: EventPositionShareState::Active,
            title: String::new(),
            meta_label: None,
            market_image: None,
            picks: vec![],
            wager_label: String::new(),
            multiplier_label: String::new(),
            payout_label: None,
            nfl: None,
            footer: footer(),
        });
        let json = serde_json::to_string(&snap).expect("serialize");
        assert!(json.contains("\"type\":\"event_position\""));
        assert!(json.contains("\"tz_offset_minutes\":-300"));
        let back: ShareCardSnapshot = serde_json::from_str(&json).expect("deserialize");
        assert_eq!(back, snap);
        assert_eq!(snap.type_str(), "event_position");
        snap.validate().expect("valid");
        assert!(serde_json::from_str::<ShareCardSnapshot>(
            &json.replace("event_position", "culture")
        )
        .is_err());

        let ShareCardSnapshot::EventPosition(card) = &mut snap else {
            unreachable!("event-position snapshot changed variant")
        };
        card.tz_offset_minutes = Some(MAX_TZ_OFFSET_MINUTES + 1);
        assert_eq!(snap.validate(), Err("tz_offset_minutes"));
    }

    #[test]
    fn validate_rejects_overlong_streak_and_bad_counts() {
        let bad = ShareCardSnapshot::Streak(StreakShareCard {
            streak_count: 30,
            max_streak: 25,
            market_title: "x".to_string(),
            market_image: None,
            selection: "y".to_string(),
            selection_date: None,
            prize_label: None,
            footer: footer(),
        });
        assert_eq!(bad.validate(), Err("streak_count"));
    }

    #[test]
    fn validate_rejects_nonfinite_price_and_too_many_points() {
        let bad = ShareCardSnapshot::Price(PriceShareCard {
            contest_id: Uuid::nil().to_string(),
            entry_index: 0,
            state: PriceState::Live,
            question: "BTC?".to_string(),
            subtitle: None,
            prediction: f64::NAN,
            current_price: 1.0,
            chart_prices: vec![1.0, 2.0],
            summary: vec![],
            footer: footer(),
        });
        assert_eq!(bad.validate(), Err("price"));
    }

    #[test]
    fn validate_rejects_overlong_optional_rendered_fields() {
        let bad = ShareCardSnapshot::Streak(StreakShareCard {
            streak_count: 7,
            max_streak: 25,
            market_title: "x".to_string(),
            market_image: None,
            selection: "y".to_string(),
            selection_date: Some("Jun 11".to_string()),
            prize_label: Some("x".repeat(MAX_TEXT_LEN + 1)),
            footer: footer(),
        });
        assert_eq!(bad.validate(), Err("prize_label"));
    }

    fn markets_card(windows: usize) -> MarketsShareCard {
        MarketsShareCard {
            position_id: Uuid::nil().to_string(),
            tz_offset_minutes: Some(-240),
            state: MarketsState::Live,
            multi_asset: false,
            assets: vec!["BTC".to_string()],
            windows: (0..windows)
                .map(|i| MarketWindow {
                    start_ms: 1_750_000_000_000 + i as i64 * 300_000,
                    end_ms: 1_750_000_000_000 + (i as i64 + 1) * 300_000,
                    time_label: "13:05–13:10".to_string(),
                    outcome: MarketWindowOutcome::Pending,
                    picks: vec![MarketWindowPick {
                        asset: "BTC".to_string(),
                        direction: "up".to_string(),
                        won: None,
                        pct_bps: None,
                    }],
                })
                .collect(),
            date_label: "Jun 4, 2026".to_string(),
            wager_label: "$1.00".to_string(),
            multiplier_label: "312.5x".to_string(),
            payout_label: "$312.50".to_string(),
            price_from: None,
            price_to: None,
            chart: vec![MarketChartSeries {
                asset: "BTC".to_string(),
                prices: vec![67950.0, 67960.0, 67984.0],
            }],
            footer: footer(),
        }
    }

    #[test]
    fn markets_snapshot_round_trips_with_type_tag() {
        let snap = ShareCardSnapshot::Markets(markets_card(8));
        let json = serde_json::to_string(&snap).expect("serialize");
        assert!(json.contains("\"type\":\"markets\""));
        let back: ShareCardSnapshot = serde_json::from_str(&json).expect("deserialize");
        assert_eq!(back, snap);
        assert_eq!(snap.type_str(), "markets");
        snap.validate().expect("valid");
    }

    #[test]
    fn markets_validate_bounds_windows_tz_and_chart() {
        let mut too_many = markets_card(MAX_MARKET_WINDOWS + 1);
        assert_eq!(
            ShareCardSnapshot::Markets(too_many.clone()).validate(),
            Err("windows")
        );
        too_many.windows.truncate(MAX_MARKET_WINDOWS);
        ShareCardSnapshot::Markets(too_many)
            .validate()
            .expect("nine windows are valid");

        for tz in [-MAX_TZ_OFFSET_MINUTES, MAX_TZ_OFFSET_MINUTES] {
            let mut boundary_tz = markets_card(2);
            boundary_tz.tz_offset_minutes = Some(tz);
            ShareCardSnapshot::Markets(boundary_tz)
                .validate()
                .expect("timezone boundary is valid");
        }
        for tz in [
            i16::MIN,
            -MAX_TZ_OFFSET_MINUTES - 1,
            MAX_TZ_OFFSET_MINUTES + 1,
        ] {
            let mut bad_tz = markets_card(2);
            bad_tz.tz_offset_minutes = Some(tz);
            assert_eq!(
                ShareCardSnapshot::Markets(bad_tz).validate(),
                Err("tz_offset_minutes")
            );
        }

        let mut bad_chart = markets_card(2);
        bad_chart.chart[0].prices = vec![f64::NAN];
        assert_eq!(
            ShareCardSnapshot::Markets(bad_chart).validate(),
            Err("chart.prices")
        );

        let mut bad_id = markets_card(1);
        bad_id.position_id = "not-a-uuid".to_string();
        assert_eq!(
            ShareCardSnapshot::Markets(bad_id).validate(),
            Err("position_id")
        );
    }

    fn roster_pick(name: &str) -> RosterSharePick {
        RosterSharePick {
            name: name.to_string(),
            bg: "#e31837".to_string(),
            fg: "#ffb81c".to_string(),
            points: Some("18".to_string()),
            unit: Some("points".to_string()),
            tip: None,
            hit: None,
        }
    }

    fn roster_card(picks: usize) -> RosterShareCard {
        RosterShareCard {
            contest_id: Uuid::nil().to_string(),
            entry_index: 0,
            state: RosterShareState::Live,
            contest_type: ContestType::Paid,
            kind: RosterShareKind::Nfl,
            prompt: "Who will score the most fantasy points?".to_string(),
            picks: (0..picks)
                .map(|i| roster_pick(&format!("Player {i}")))
                .collect(),
            summary: vec![ShareStat {
                value: "42".to_string(),
                label: "total PPR points".to_string(),
            }],
            bonus_label: None,
            footer: footer(),
        }
    }

    #[test]
    fn roster_snapshot_round_trips_with_type_tag() {
        let snap = ShareCardSnapshot::Roster(roster_card(4));
        let json = serde_json::to_string(&snap).expect("serialize");
        assert!(json.contains("\"type\":\"roster\""));
        assert!(json.contains("\"kind\":\"nfl\""));
        assert!(json.contains("\"state\":\"live\""));
        let back: ShareCardSnapshot = serde_json::from_str(&json).expect("deserialize");
        assert_eq!(back, snap);
        assert_eq!(snap.type_str(), "roster");
        snap.validate().expect("valid");
    }

    #[test]
    fn roster_perfect_state_and_optional_fields_round_trip() {
        let mut card = roster_card(5);
        card.state = RosterShareState::Perfect;
        card.kind = RosterShareKind::X;
        card.bonus_label = Some("$500".to_string());
        card.picks[0].hit = Some(true);
        card.picks[1].points = None;
        card.picks[1].unit = None;
        card.picks[1].tip = Some("Sun 8:20pm".to_string());
        let snap = ShareCardSnapshot::Roster(card);
        let json = serde_json::to_string(&snap).expect("serialize");
        assert!(json.contains("\"state\":\"perfect\""));
        assert!(json.contains("\"kind\":\"x\""));
        assert!(json.contains("\"bonus_label\":\"$500\""));
        let back: ShareCardSnapshot = serde_json::from_str(&json).expect("deserialize");
        assert_eq!(back, snap);
        snap.validate().expect("valid");
    }

    #[test]
    fn roster_validate_bounds_picks_and_colors() {
        assert_eq!(
            ShareCardSnapshot::Roster(roster_card(0)).validate(),
            Err("picks")
        );
        assert_eq!(
            ShareCardSnapshot::Roster(roster_card(MAX_ROSTER_SHARE_PICKS + 1)).validate(),
            Err("picks")
        );
        ShareCardSnapshot::Roster(roster_card(MAX_ROSTER_SHARE_PICKS))
            .validate()
            .expect("max picks are valid");

        let mut bad_bg = roster_card(2);
        bad_bg.picks[0].bg = "e31837".to_string();
        assert_eq!(
            ShareCardSnapshot::Roster(bad_bg).validate(),
            Err("picks.bg")
        );

        let mut bad_fg = roster_card(2);
        bad_fg.picks[1].fg = "#zzzzzz".to_string();
        assert_eq!(
            ShareCardSnapshot::Roster(bad_fg).validate(),
            Err("picks.fg")
        );

        let mut short_bg = roster_card(1);
        short_bg.picks[0].bg = "#fff".to_string();
        assert_eq!(
            ShareCardSnapshot::Roster(short_bg).validate(),
            Err("picks.bg")
        );

        let mut bad_id = roster_card(1);
        bad_id.contest_id = "not-a-uuid".to_string();
        assert_eq!(
            ShareCardSnapshot::Roster(bad_id).validate(),
            Err("contest_id")
        );

        let mut long_prompt = roster_card(1);
        long_prompt.prompt = "x".repeat(MAX_TEXT_LEN + 1);
        assert_eq!(
            ShareCardSnapshot::Roster(long_prompt).validate(),
            Err("prompt")
        );
    }

    fn survivor_card(rounds: usize) -> SurvivorShareCard {
        SurvivorShareCard {
            contest_id: Uuid::nil().to_string(),
            entry_index: 0,
            state: SurvivorShareState::Live,
            contest_type: ContestType::Paid,
            presentation: SurvivorSharePresentation::Matchup,
            title: "NBA Survivor".to_string(),
            rounds: (0..rounds)
                .map(|round_index| SurvivorShareRound {
                    result: SurvivorEntryRoundResultResponse::Pending,
                    pick_count: if round_index < 2 { 1 } else { 0 },
                })
                .collect(),
            summary: vec![],
            footer: footer(),
        }
    }

    #[test]
    fn survivor_skeleton_defaults_before_server_canonicalization() {
        let json = serde_json::json!({
            "type": "survivor",
            "contest_id": Uuid::nil(),
            "entry_index": 0,
            "footer": { "handle": "aidan" }
        });
        let snapshot: ShareCardSnapshot = serde_json::from_value(json).expect("deserialize");
        let ShareCardSnapshot::Survivor(card) = &snapshot else {
            panic!("expected Survivor snapshot");
        };
        assert_eq!(card.state, SurvivorShareState::Pre);
        assert_eq!(card.contest_type, ContestType::Free);
        assert_eq!(card.presentation, SurvivorSharePresentation::Daily);
        assert!(card.title.is_empty());
        assert!(card.rounds.is_empty());
        assert_eq!(snapshot.type_str(), "survivor");
        snapshot.validate().expect("valid request skeleton");
    }

    #[test]
    fn survivor_rounds_are_bounded_for_rendering() {
        let snapshot = ShareCardSnapshot::Survivor(survivor_card(MAX_SURVIVOR_SHARE_ROUNDS));
        let json = serde_json::to_string(&snapshot).expect("serialize");
        assert!(json.contains("\"type\":\"survivor\""));
        assert!(!json.contains("\"kind\""));
        let back: ShareCardSnapshot = serde_json::from_str(&json).expect("deserialize");
        assert_eq!(back, snapshot);
        snapshot.validate().expect("30 rounds are valid");

        assert_eq!(
            ShareCardSnapshot::Survivor(survivor_card(MAX_SURVIVOR_SHARE_ROUNDS + 1)).validate(),
            Err("rounds")
        );
        let mut too_many_picks = survivor_card(1);
        too_many_picks.rounds[0].pick_count = MAX_SURVIVOR_SHARE_PICKS as u32 + 1;
        assert_eq!(
            ShareCardSnapshot::Survivor(too_many_picks).validate(),
            Err("rounds.pick_count")
        );
    }

    #[test]
    fn validate_rejects_overlong_summary_cells() {
        let bad = ShareCardSnapshot::Questions(QuestionsShareCard {
            contest_id: Uuid::nil().to_string(),
            entry_index: 0,
            state: QuestionsState::Won,
            contest_type: ContestType::Paid,
            question: "NBA mentions?".to_string(),
            topic_image: None,
            legs: vec![QuestionLeg {
                name: "Election".to_string(),
                answer: "Yes".to_string(),
                grade: LegGrade::Correct,
            }],
            summary: vec![ShareStat {
                value: "winner".to_string(),
                label: "x".repeat(MAX_TEXT_LEN + 1),
            }],
            footer: footer(),
        });
        assert_eq!(bad.validate(), Err("summary.label"));
    }
}
