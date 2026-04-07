"""Claude Code JSONL format — raw conversation entries.

Models the type system of ~/.claude/projects/<project>/<session>.jsonl
as written by Claude Code. These are the source format before gleaner
normalizes them into NormalizedEntry / SessionMeta.

Usage::

    import json
    from pydantic import TypeAdapter
    from gleaner.cc_format import ConversationEntry

    adapter = TypeAdapter(ConversationEntry)
    with open(path) as f:
        for line in f:
            entry = adapter.validate_json(line)
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


# ── Content blocks (inside messages) ──────────────────────────


class TextBlock(BaseModel):
    type: Literal["text"]
    text: str


class ThinkingBlock(BaseModel):
    type: Literal["thinking"]
    thinking: str
    signature: str = ""


class ToolUseBlock(BaseModel):
    type: Literal["tool_use"]
    id: str
    name: str
    input: dict[str, Any]
    caller: dict[str, Any] | None = None


class ToolResultBlock(BaseModel):
    type: Literal["tool_result"]
    tool_use_id: str
    content: list[dict[str, Any]] | str | None = None


class ImageSource(BaseModel):
    type: str
    media_type: str
    data: str


class ImageBlock(BaseModel):
    type: Literal["image"]
    source: ImageSource


ContentBlock = Annotated[
    TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock | ImageBlock,
    Field(discriminator="type"),
]


# ── Messages ──────────────────────────────────────────────────


class UserPayload(BaseModel):
    """The ``message`` field inside a UserMessage entry."""

    role: Literal["user"]
    content: str | list[ContentBlock]


class AssistantPayload(BaseModel):
    """The ``message`` field inside an AssistantMessage entry."""

    role: Literal["assistant"]
    content: list[ContentBlock]
    model: str | None = None
    id: str | None = None
    type: Literal["message"] = "message"
    stop_reason: str | None = None
    stop_sequence: str | None = None
    usage: dict[str, Any] | None = None


# ── Top-level JSONL entries ───────────────────────────────────


class _EntryBase(BaseModel):
    """Common fields shared by conversation entries."""

    parentUuid: str | None = None
    isSidechain: bool = False
    uuid: str
    timestamp: str
    userType: str | None = None
    entrypoint: str | None = None
    cwd: str | None = None
    sessionId: str | None = None
    version: str | None = None
    gitBranch: str | None = None


class UserMessage(_EntryBase):
    type: Literal["user"]
    message: UserPayload
    promptId: str | None = None
    permissionMode: str | None = None


class AssistantMessage(_EntryBase):
    type: Literal["assistant"]
    message: AssistantPayload
    requestId: str | None = None


class Attachment(_EntryBase):
    type: Literal["attachment"]
    attachment: dict[str, Any]


class Progress(_EntryBase):
    type: Literal["progress"]
    data: dict[str, Any]
    toolUseID: str | None = None
    parentToolUseID: str | None = None


class SystemMessage(_EntryBase):
    type: Literal["system"]
    subtype: str
    isMeta: bool = False
    level: str | None = None
    content: str | None = None
    slug: str | None = None
    # turn_duration
    durationMs: int | None = None
    messageCount: int | None = None
    # compact_boundary
    logicalParentUuid: str | None = None
    compactMetadata: dict[str, Any] | None = None
    # stop_hook_summary
    hookCount: int | None = None
    hookInfos: list[dict[str, Any]] | None = None
    hookErrors: list[str] | None = None
    preventedContinuation: bool | None = None
    stopReason: str | None = None
    hasOutput: bool | None = None
    # api_error
    error: dict[str, Any] | None = None
    retryInMs: float | None = None


# ── Metadata entries (no uuid / conversation tree) ────────────


class PermissionMode(BaseModel):
    type: Literal["permission-mode"]
    permissionMode: str
    sessionId: str


class FileHistorySnapshot(BaseModel):
    type: Literal["file-history-snapshot"]
    messageId: str
    snapshot: dict[str, Any]
    isSnapshotUpdate: bool


class AgentName(BaseModel):
    type: Literal["agent-name"]
    agentName: str
    sessionId: str


class CustomTitle(BaseModel):
    type: Literal["custom-title"]
    customTitle: str
    sessionId: str


class LastPrompt(BaseModel):
    type: Literal["last-prompt"]
    lastPrompt: str
    sessionId: str


class QueueOperation(BaseModel):
    type: Literal["queue-operation"]
    operation: str
    timestamp: str
    sessionId: str
    content: str | None = None


# ── Discriminated union of all entry types ────────────────────

ConversationEntry = Annotated[
    UserMessage
    | AssistantMessage
    | Attachment
    | Progress
    | SystemMessage
    | PermissionMode
    | FileHistorySnapshot
    | AgentName
    | CustomTitle
    | LastPrompt
    | QueueOperation,
    Field(discriminator="type"),
]
