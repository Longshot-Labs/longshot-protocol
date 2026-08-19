//! Shared position identity response types.

use serde::{Deserialize, Serialize};

use crate::types::MarketType;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PrimaryLegIdentityResponse {
    pub market_type: MarketType,
    pub market_id: u64,
    pub label: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub asset: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub duration_secs: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub duration_label: Option<String>,
}
