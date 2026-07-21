"""Tests for Codex rollout parsing, discovery, and vault normalization.

Codex's transcript format (payload-wrapped response_item lines) is unlike
Claude Code / Cursor, so these tests pin down that:
  - genuine user/assistant turns are counted, injected preambles are not;
  - tool calls (function_call / local_shell_call / custom_tool_call) count;
  - the topic is the first real prompt, not the AGENTS.md injection;
  - discovery round-trips a session id to its rollout file;
  - vault normalization coerces unknown roles instead of crashing
    (regression: NormalizedEntry rejected Claude's summary/tool_result lines).
"""

import json
from pathlib import Path

from gleaner.sources.codex import (
    _encode_project,
    find_all_codex_sessions,
    find_codex_session_file,
    parse_codex_transcript,
)
from gleaner.vault import normalize_entry

TS = "2026-06-24T10:00:00.000Z"
SID = "019ef913-00d0-7911-9dd3-9947f20e65f6"


def _meta(cwd="/Users/me/code-republic/proj"):
    return {"timestamp": TS, "type": "session_meta",
            "payload": {"session_id": SID, "cwd": cwd}}


def _msg(role, text, ts=TS):
    block = "output_text" if role == "assistant" else "input_text"
    return {"timestamp": ts, "type": "response_item",
            "payload": {"type": "message", "role": role,
                        "content": [{"type": block, "text": text}]}}


def _call(name="shell"):
    return {"timestamp": TS, "type": "response_item",
            "payload": {"type": "function_call", "name": name, "arguments": "{}"}}


def _write_rollout(dir_: Path, lines, session_id=SID) -> Path:
    day = dir_ / "2026" / "06" / "24"
    day.mkdir(parents=True, exist_ok=True)
    path = day / f"rollout-2026-06-24T10-00-00-{session_id}.jsonl"
    path.write_text("\n".join(json.dumps(o) for o in lines) + "\n")
    return path


# Full, realistic rollout: developer + AGENTS.md preamble, one real prompt,
# reasoning, a tool call + its output, one assistant reply.
FULL = [
    _meta(),
    {"timestamp": TS, "type": "event_msg",
     "payload": {"type": "thread_goal_updated", "goal": {"objective": "Goal text"}}},
    _msg("developer", "<permissions instructions>\nFilesystem sandboxing..."),
    _msg("user", "# AGENTS.md instructions for /Users/me/code-republic/proj\n..."),
    _msg("user", "Refactor the parser to share logic.", ts="2026-06-24T10:01:00.000Z"),
    {"timestamp": TS, "type": "response_item",
     "payload": {"type": "reasoning", "content": [{"type": "text", "text": "thinking"}]}},
    _call("shell"),
    {"timestamp": TS, "type": "response_item",
     "payload": {"type": "function_call_output", "output": "ok"}},
    _msg("assistant", "Done.", ts="2026-06-24T10:02:00.000Z"),
]


class TestParse:
    def test_counts_only_real_turns(self, tmp_path):
        meta = parse_codex_transcript(_write_rollout(tmp_path, FULL))
        assert meta["user_message_count"] == 1  # AGENTS.md + developer excluded
        assert meta["assistant_message_count"] == 1
        assert meta["message_count"] == 2
        assert meta["worthless"] is False

    def test_tool_calls_counted(self, tmp_path):
        meta = parse_codex_transcript(_write_rollout(tmp_path, FULL))
        assert meta["tool_use_count"] == 1
        assert meta["tool_counts"] == {"shell": 1}

    def test_topic_is_first_real_prompt(self, tmp_path):
        meta = parse_codex_transcript(_write_rollout(tmp_path, FULL))
        assert meta["topic"] == "Refactor the parser to share logic."

    def test_timestamps_span_the_session(self, tmp_path):
        meta = parse_codex_transcript(_write_rollout(tmp_path, FULL))
        assert meta["first_timestamp"] == TS
        assert meta["last_timestamp"] == "2026-06-24T10:02:00.000Z"

    def test_topic_falls_back_to_goal(self, tmp_path):
        """With no real user prompt, the thread goal objective is the topic."""
        lines = [_meta(),
                 {"timestamp": TS, "type": "event_msg",
                  "payload": {"type": "thread_goal_updated",
                              "goal": {"objective": "Ship the feature"}}},
                 _msg("user", "# AGENTS.md instructions for /x\n..."),
                 _msg("assistant", "working")]
        meta = parse_codex_transcript(_write_rollout(tmp_path, lines))
        assert meta["topic"] == "Ship the feature"

    def test_injection_only_session_is_worthless(self, tmp_path):
        lines = [_meta(),
                 _msg("developer", "<permissions instructions>..."),
                 _msg("user", "# AGENTS.md instructions for /x\n...")]
        meta = parse_codex_transcript(_write_rollout(tmp_path, lines))
        assert meta["worthless"] is True
        assert meta["user_message_count"] == 0

    def test_local_shell_and_custom_tool_names(self, tmp_path):
        lines = [_meta(), _msg("user", "do it"),
                 {"timestamp": TS, "type": "response_item",
                  "payload": {"type": "local_shell_call"}},
                 {"timestamp": TS, "type": "response_item",
                  "payload": {"type": "custom_tool_call", "name": "apply_patch"}}]
        meta = parse_codex_transcript(_write_rollout(tmp_path, lines))
        assert meta["tool_counts"] == {"local_shell": 1, "apply_patch": 1}


class TestDiscovery:
    def test_roundtrip_id_to_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("gleaner.sources.codex.SESSIONS_DIR", tmp_path)
        path = _write_rollout(tmp_path, FULL)
        sessions = find_all_codex_sessions()
        assert sessions == [(SID, _encode_project("/Users/me/code-republic/proj"), path)]
        assert find_codex_session_file(SID) == path

    def test_project_filter(self, tmp_path, monkeypatch):
        monkeypatch.setattr("gleaner.sources.codex.SESSIONS_DIR", tmp_path)
        _write_rollout(tmp_path, FULL)
        assert find_all_codex_sessions("code-republic")  # substring of encoded cwd
        assert find_all_codex_sessions("nonexistent") == []

    def test_encode_project_matches_claude_scheme(self):
        assert _encode_project("/Users/me/code-republic/gleaner") == "-Users-me-code-republic-gleaner"


class TestVaultNormalization:
    def test_codex_message_normalized(self):
        out = normalize_entry(_msg("assistant", "hello"))
        assert out["role"] == "assistant"
        assert out["content"] == [{"type": "text", "text": "hello"}]

    def test_codex_tool_call_normalized(self):
        out = normalize_entry(_call("shell"))
        assert out["role"] == "unknown"
        assert out["content"] == [{"type": "tool_use", "name": "shell"}]

    def test_unknown_role_coerced_not_crashed(self):
        """Regression: Claude summary/tool_result/system lines must not raise."""
        for t in ("summary", "tool_result", "system"):
            out = normalize_entry({"type": t, "message": {"content": "x"}})
            assert out["role"] == "unknown"
