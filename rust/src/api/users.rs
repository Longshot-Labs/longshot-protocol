//! Public user API query contracts.

use serde::{Deserialize, Serialize};

/// Query params for `GET /v1/user/transactions`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct UserTransactionsRawQuery {
    pub category: Option<String>,
    pub from_ms: Option<String>,
    pub to_ms: Option<String>,
    pub limit: Option<u32>,
    pub cursor: Option<String>,
}

/// Client query params for `POST /v1/user/confirm_position`.
///
/// The server keeps optional strings for custom error mapping; clients should
/// not be able to omit these required values or model `accept` as arbitrary text.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct ConfirmPositionQuery {
    pub position_id: String,
    pub accept: bool,
}
