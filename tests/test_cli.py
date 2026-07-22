"""Tests for the `gleaner sessions` CLI command."""

import sys
import pytest
import pyarrow as pa
import pyarrow.parquet as pq

from gleaner.cli import main


def _write_index(vault_dir, rows):
    vault_dir.mkdir(parents=True, exist_ok=True)
    if rows:
        table = pa.Table.from_pylist(rows)
        pq.write_table(table, vault_dir / "index.parquet")
    else:
        # Create an empty parquet table with the proper schema
        schema = pa.schema([
            ("session_id", pa.string()),
            ("ide", pa.string()),
            ("project", pa.string()),
            ("topic", pa.string()),
            ("cwd", pa.string()),
            ("source", pa.string()),
            ("task_type", pa.string()),
            ("user", pa.string()),
            ("host", pa.string()),
            ("platform", pa.string()),
            ("message_count", pa.int64()),
            ("user_message_count", pa.int64()),
            ("assistant_message_count", pa.int64()),
            ("tool_use_count", pa.int64()),
            ("tool_counts_json", pa.string()),
            ("first_timestamp", pa.string()),
            ("last_timestamp", pa.string()),
            ("transcript_size", pa.int64()),
            ("ingested_at", pa.string()),
            ("origin", pa.string()),
        ])
        table = pa.Table.from_batches([], schema=schema)
        pq.write_table(table, vault_dir / "index.parquet")


@pytest.fixture
def mock_vault(tmp_path, monkeypatch):
    """Redirect VAULT_DIR to tmp_path for deterministic CLI tests."""
    import gleaner.vault as gvault
    monkeypatch.setattr(gvault, "VAULT_DIR", tmp_path)
    return tmp_path


def test_sessions_no_vault(mock_vault, monkeypatch, capsys):
    """If no index.parquet exists, print a helpful message and return."""
    monkeypatch.setattr(sys, "argv", ["gleaner", "sessions"])
    main()
    out = capsys.readouterr().out
    assert "No sessions found in the local vault." in out


def test_sessions_empty_vault(mock_vault, monkeypatch, capsys):
    """If index.parquet is empty, print a helpful message."""
    _write_index(mock_vault, [])
    monkeypatch.setattr(sys, "argv", ["gleaner", "sessions"])
    main()
    out = capsys.readouterr().out
    assert "No sessions found in the local vault." in out


def test_sessions_list_all_and_ordering(mock_vault, monkeypatch, capsys):
    """Verify that all sessions are listed newest-first with correct fields."""
    rows = [
        {
            "session_id": "s1_id_very_long_uuid_value",
            "ide": "claude_code",
            "project": "project-alpha",
            "last_timestamp": "2026-07-22T10:00:00.000Z",
            "message_count": 5,
        },
        {
            "session_id": "s2_id_very_long_uuid_value",
            "ide": "cursor",
            "project": "project-beta",
            "last_timestamp": "2026-07-22T12:00:00.000Z",
            "message_count": 12,
        },
        {
            "session_id": "s3_id_very_long_uuid_value",
            "ide": "codex",
            "project": "project-gamma-very-long-name-exceeding-columns",
            "last_timestamp": "2026-07-22T08:00:00.000Z",
            "message_count": 2,
        },
    ]
    _write_index(mock_vault, rows)

    monkeypatch.setattr(sys, "argv", ["gleaner", "sessions"])
    main()
    out = capsys.readouterr().out.strip().split("\n")

    # Verify headers are present
    assert "SESSION ID" in out[0]
    assert "SOURCE" in out[0]
    assert "PROJECT" in out[0]
    assert "LAST UPDATED" in out[0]
    assert "MESSAGES" in out[0]

    # Verify 3 rows are listed (excluding header and separator lines)
    data_lines = out[2:]
    assert len(data_lines) == 3

    # Verify newest-first order: s2 (12:00), s1 (10:00), s3 (08:00)
    # Row 1 (s2): cursor, project-beta, last updated, 12 messages
    assert "s2_id_very_l" in data_lines[0]
    assert "cursor" in data_lines[0]
    assert "project-beta" in data_lines[0]
    assert "2026-07-22 12:00:00" in data_lines[0]
    assert "12" in data_lines[0]

    # Row 2 (s1): claude, project-alpha, last updated, 5 messages
    assert "s1_id_very_l" in data_lines[1]
    assert "claude" in data_lines[1]
    assert "project-alpha" in data_lines[1]
    assert "2026-07-22 10:00:00" in data_lines[1]
    assert "5" in data_lines[1]

    # Row 3 (s3): codex, project-gamma... (truncated), last updated, 2 messages
    assert "s3_id_very_l" in data_lines[2]
    assert "codex" in data_lines[2]
    assert "project-gamma-very-l..." in data_lines[2]
    assert "2026-07-22 08:00:00" in data_lines[2]
    assert "2" in data_lines[2]


def test_sessions_filtering_by_source(mock_vault, monkeypatch, capsys):
    """Verify source filtering working properly with --source flag."""
    rows = [
        {
            "session_id": "s1",
            "ide": "claude_code",
            "project": "project-alpha",
            "last_timestamp": "2026-07-22T10:00:00Z",
            "message_count": 5,
        },
        {
            "session_id": "s2",
            "ide": "cursor",
            "project": "project-beta",
            "last_timestamp": "2026-07-22T12:00:00Z",
            "message_count": 12,
        },
    ]
    _write_index(mock_vault, rows)

    # Test filtering by claude
    monkeypatch.setattr(sys, "argv", ["gleaner", "sessions", "--source", "claude"])
    main()
    out = capsys.readouterr().out.strip().split("\n")
    data_lines = out[2:]
    assert len(data_lines) == 1
    assert "claude" in data_lines[0]
    assert "cursor" not in data_lines[0]

    # Test filtering by cursor
    monkeypatch.setattr(sys, "argv", ["gleaner", "sessions", "--source", "cursor"])
    main()
    out = capsys.readouterr().out.strip().split("\n")
    data_lines = out[2:]
    assert len(data_lines) == 1
    assert "cursor" in data_lines[0]
    assert "claude" not in data_lines[0]


def test_sessions_limit(mock_vault, monkeypatch, capsys):
    """Verify limit flag constrains output correctly."""
    rows = [
        {
            "session_id": f"s{i}",
            "ide": "claude_code",
            "project": "proj",
            "last_timestamp": f"2026-07-22T10:0{i}:00Z",
            "message_count": i,
        }
        for i in range(5)
    ]
    _write_index(mock_vault, rows)

    monkeypatch.setattr(sys, "argv", ["gleaner", "sessions", "--limit", "2"])
    main()
    out = capsys.readouterr().out.strip().split("\n")
    data_lines = out[2:]
    assert len(data_lines) == 2
