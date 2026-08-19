//! Public pool-image API response contracts.

/// Binary response schema for `GET /v1/pool-images/:id/raw`.
#[derive(Debug, Clone)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(value_type = String, format = Binary))]
pub struct PoolImageRawBytes(pub Vec<u8>);
