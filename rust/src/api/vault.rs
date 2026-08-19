//! Public vault API query contracts.

use serde::{Deserialize, Serialize};

/// Query params that identify a public vault.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
pub struct VaultIdQuery {
    pub vault_id: String,
}

/// Query params for `GET /v1/vault/pnl_history`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
pub struct VaultPnlHistoryQuery {
    pub vault_id: String,
    pub range: Option<String>,
    pub metric: Option<String>,
}

/// Query params for `GET /v1/vault/positions`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
pub struct VaultPositionsQuery {
    pub vault_id: String,
    pub status: Option<String>,
    pub cursor: Option<String>,
    pub limit: Option<u32>,
}

/// Query params for `GET /v1/vault/events`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
pub struct VaultEventsQuery {
    pub vault_id: String,
    pub cursor: Option<String>,
    pub limit: Option<u32>,
    /// Optional comma-separated list of event types to include
    /// (e.g. `deposit,withdrawal_filled`). When absent or empty, all event
    /// types are returned.
    pub event_type: Option<String>,
}

/// Query params for `GET /v1/vault/contributors`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
pub struct VaultContributorsQuery {
    pub vault_id: String,
    pub cursor: Option<String>,
    pub limit: Option<u32>,
    pub sort: Option<String>,
}
