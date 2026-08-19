//! Chat API response types.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "lowercase")]
pub enum ChatGifProviderResponse {
    Giphy,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatGifAttachmentResponse {
    pub provider: ChatGifProviderResponse,
    pub id: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum ChatUserAvatarResponse {
    XAvatarUrl { url: String },
    Seed { seed: i32 },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatAuthorResponse {
    pub user_id: String,
    pub name: String,
    pub avatar: ChatUserAvatarResponse,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatReactionResponse {
    pub emoji_code: String,
    pub reactor: ChatAuthorResponse,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum ChatEmojiDisplayResponse {
    Url { value: String },
    Unicode { value: String },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatEmojiResponse {
    pub code: String,
    pub display: ChatEmojiDisplayResponse,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatEmojisResponse {
    pub emojis: Vec<ChatEmojiResponse>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatReactionUpdateResponse {
    pub message_id: String,
    /// Monotonic per-message version of `reactions`; clients should ignore
    /// updates whose `reaction_seq` is not greater than the last applied one.
    pub reaction_seq: u64,
    pub reactions: Vec<ChatReactionResponse>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatMessageResponse {
    pub message_id: String,
    pub author: ChatAuthorResponse,
    pub body: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub gif: Option<ChatGifAttachmentResponse>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub parent: Option<String>,
    pub reactions: Vec<ChatReactionResponse>,
    /// Monotonic per-message version of `body`; clients should ignore full
    /// message updates whose `edit_seq` is not greater than the last applied
    /// one for that message.
    pub edit_seq: u64,
    /// Monotonic per-message version of `reactions`; see
    /// `ChatReactionUpdateResponse::reaction_seq`.
    pub reaction_seq: u64,
    pub timestamp_ms: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatMessageEditResponse {
    pub message_id: String,
    pub body: String,
    /// Monotonic per-message version of `body`; clients should ignore edit
    /// updates whose `edit_seq` is not greater than the last applied one for
    /// that message.
    pub edit_seq: u64,
    pub timestamp_ms: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatRecentMessagesResponse {
    pub messages: Vec<ChatMessageResponse>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<String>,
    /// Whether the room currently accepts posts, edits, and reactions.
    pub writable: bool,
}

/// Shared market chat-room identifier.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatMarketRoomResponse {
    pub chat_id: String,
}

/// User eligible to be mentioned in a chat room.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatMentionCandidateResponse {
    pub user_id: String,
    pub handle: String,
}

/// Mention candidates for the requested chat room.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatMentionCandidatesResponse {
    pub candidates: Vec<ChatMentionCandidateResponse>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum ChatStreamErrorCode {
    SubscriberLagged,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatStreamErrorEvent {
    pub code: ChatStreamErrorCode,
    pub message: String,
    pub skipped: u64,
}
