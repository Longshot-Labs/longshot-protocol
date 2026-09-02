//! External profile API request and response contracts.

use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
pub struct CheckHandleQuery {
    pub handle: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct HandleAvailabilityQuery {
    pub handle: String,
}

/// Profile response for the authenticated user.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ProfileResponse {
    pub handle: String,
    pub display_name: String,
    pub avatar_seed: i32,
    /// Verified email address, if set.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub email: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_handle: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_avatar_url: Option<String>,
    pub created_at_ms: i64,
    pub updated_at_ms: i64,
    /// Vanity referral code. This is null when unset.
    pub referral_code: Option<String>,
}

/// Profile fields that the authenticated user can update.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct UpdateProfileRequest {
    /// New handle (3-30 characters, using letters, numbers, and underscores).
    pub handle: Option<String>,
    /// New display name (1-50 characters).
    pub display_name: Option<String>,
}

/// Handle availability result.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct CheckHandleResponse {
    pub available: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reason: Option<String>,
}
