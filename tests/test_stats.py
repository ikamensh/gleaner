"""Property tests for backend.stats — the shared counters/stats core.

Every backend (cloud, mock, local vault, ops rebuild) derives its counters
from counter_deltas/apply_deltas, so these properties are the contract:
replayed counters must add up, deduplicate, and feed build_* without error.
"""

from backend import stats


def _meta(msg=4, tools=None, first="2026-03-20T10:00:00Z", last="2026-03-20T10:05:00Z", project="proj"):
    tools = tools if tools is not None else {"Read": 2}
    return {
        "project": project,
        "message_count": msg,
        "tool_use_count": sum(tools.values()),
        "tool_counts": tools,
        "first_timestamp": first,
        "last_timestamp": last,
    }


def _replay(sessions):
    counters: dict = {}
    for sid, meta, prov in sessions:
        stats.apply_deltas(counters, stats.counter_deltas(sid, meta, prov))
    return counters


class TestCounterReplay:
    def test_totals_add_up(self):
        """Replaying N sessions sums counts exactly."""
        c = _replay([
            ("s1", _meta(msg=10, tools={"Read": 3}), {"user": "alice"}),
            ("s2", _meta(msg=20, tools={"Read": 1, "Edit": 2}), {"user": "alice"}),
        ])
        assert c["global"]["total_sessions"] == 2
        assert c["global"]["total_messages"] == 30
        assert c["global"]["tool_usage"] == {"Read": 4, "Edit": 2}
        assert c["user:alice"]["total_sessions"] == 2

    def test_project_users_deduplicated(self):
        """The union op never lists a user twice under a project."""
        c = _replay([
            ("s1", _meta(), {"user": "alice"}),
            ("s2", _meta(), {"user": "alice"}),
            ("s3", _meta(), {"user": "bob"}),
        ])
        assert sorted(c["global:projects"]["proj"]["users"]) == ["alice", "bob"]

    def test_last_session_follows_replay_order(self):
        """Replaying oldest-first leaves last_session_id on the newest session."""
        older = _meta(first="2026-03-19T10:00:00Z", last="2026-03-19T10:01:00Z")
        newer = _meta(first="2026-03-20T10:00:00Z", last="2026-03-20T10:01:00Z")
        c = _replay([("old", older, {"user": "a"}), ("new", newer, {"user": "a"})])
        assert c["user:a"]["last_session_id"] == "new"
        assert c["user:a"]["last_active"] == "2026-03-20T10:00:00Z"

    def test_anonymous_sessions_count_globally_only(self):
        """Sessions without a user still hit global totals but no user docs."""
        c = _replay([("s1", _meta(), {})])
        assert c["global"]["total_sessions"] == 1
        assert "global:users" not in c
        assert not any(k.startswith("user:") for k in c)

    def test_none_timestamps_do_not_crash(self):
        """Legacy docs may carry None timestamps; deltas must still apply."""
        meta = _meta()
        meta["first_timestamp"] = None
        meta["last_timestamp"] = None
        c = _replay([("s1", meta, {"user": "a"})])
        assert c["global"]["total_sessions"] == 1


class TestBuildStats:
    def test_replayed_counters_feed_user_stats(self):
        """build_user_stats consumes replayed counters without error."""
        c = _replay([("s1", _meta(msg=10), {"user": "alice"})])
        out = stats.build_user_stats("alice", c["user:alice"], [], None)
        assert out["total_sessions"] == 1
        assert out["avg_messages_per_session"] == 10
        assert out["tool_usage"] == {"Read": 2}

    def test_replayed_counters_feed_global_stats(self):
        """build_global_stats consumes replayed counters without error."""
        c = _replay([
            ("s1", _meta(), {"user": "alice"}),
            ("s2", _meta(project="other"), {"user": "bob"}),
        ])
        user_counters = {k.split(":", 1)[1]: v for k, v in c.items() if k.startswith("user:")}
        out = stats.build_global_stats(
            c["global"], c["global:users"], c["global:projects"],
            c["global:daily"], user_counters, [],
        )
        assert out["total_sessions"] == 2
        assert out["unique_users"] == 2
        assert out["unique_projects"] == 2
        assert len(out["timeline"]) == 30

    def test_empty_shapes(self):
        """No data yields the documented empty response shapes."""
        u = stats.build_user_stats("nobody", None, [], None)
        assert u["total_sessions"] == 0 and u["heatmap"] == []
        g = stats.build_global_stats(None, {}, {}, {}, {}, [])
        assert g["total_sessions"] == 0 and g["timeline"] == []
