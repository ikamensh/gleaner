"""Session statistics shared by every storage backend (cloud, mock, local).

Pure functions only — no GCP imports, so the mock and local backends can use
this module without cloud dependencies. Two layers:

- counter_deltas / apply_deltas: one definition of how a session increments
  the counter docs. The cloud backend maps the deltas to Firestore ops; the
  in-memory backends apply them to nested dicts (apply_deltas). The local
  backend replays them over vault rows to build the same counters.
- build_user_stats / build_global_stats: assemble the API stats responses
  from counter docs, so every backend returns identical shapes.
"""

from datetime import date, datetime, timedelta, timezone


def duration_seconds(first_ts: str, last_ts: str) -> float:
    """Seconds between two ISO timestamps; 0.0 when missing or unparsable."""
    if not first_ts or not last_ts:
        return 0.0
    try:
        s = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
        e = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
        return max((e - s).total_seconds(), 0)
    except (ValueError, AttributeError):
        return 0.0


def session_summary(data: dict) -> dict:
    """Trim a full session doc to the shape used in recent-session lists."""
    return {
        "session_id": data.get("session_id", ""),
        "topic": data.get("topic", ""),
        "project": data.get("project", ""),
        "cwd": data.get("cwd", ""),
        "user": data.get("provenance", {}).get("user", ""),
        "message_count": data.get("message_count", 0),
        "tool_use_count": data.get("tool_use_count", 0),
        "first_timestamp": data.get("first_timestamp"),
        "last_timestamp": data.get("last_timestamp"),
        "provenance": data.get("provenance", {}),
        "transcript_size": data.get("transcript_size", 0),
    }


# --- Counter deltas -----------------------------------------------------------
# A delta set is {doc_name: {dotted_field_path: (op, value)}} with ops:
#   "inc"   — numeric increment
#   "set"   — overwrite
#   "union" — add items to a list if absent


def counter_deltas(session_id: str, metadata: dict, provenance: dict) -> dict:
    """How one new session changes the counter docs."""
    username = provenance.get("user", "")
    project = metadata.get("project", "")
    msg_count = metadata.get("message_count", 0)
    tool_count = metadata.get("tool_use_count", 0)
    tool_counts = metadata.get("tool_counts", {})
    first_ts = metadata.get("first_timestamp") or ""
    last_ts = metadata.get("last_timestamp") or ""
    date_str = first_ts[:10] if len(first_ts) >= 10 else ""
    duration = duration_seconds(first_ts, last_ts)

    # Global counters are split across 4 docs to stay under index limits.
    g = {
        "total_sessions": ("inc", 1),
        "total_messages": ("inc", msg_count),
        "total_tool_uses": ("inc", tool_count),
    }
    for tool, count in tool_counts.items():
        g[f"tool_usage.{tool}"] = ("inc", count)
    deltas = {"global": g}

    if date_str:
        deltas["global:daily"] = {date_str: ("inc", 1)}

    if username:
        rollup = {
            f"{username}.sessions": ("inc", 1),
            f"{username}.messages": ("inc", msg_count),
            f"{username}.tool_uses": ("inc", tool_count),
            f"{username}.total_duration_seconds": ("inc", duration),
        }
        if first_ts:
            rollup[f"{username}.last_active"] = ("set", first_ts)
        deltas["global:users"] = rollup

    if project:
        rollup = {
            f"{project}.sessions": ("inc", 1),
            f"{project}.messages": ("inc", msg_count),
        }
        if username:
            rollup[f"{project}.users"] = ("union", [username])
        deltas["global:projects"] = rollup

    if username:
        u = {
            "total_sessions": ("inc", 1),
            "total_messages": ("inc", msg_count),
            "total_tool_uses": ("inc", tool_count),
            "total_duration_seconds": ("inc", duration),
            "last_session_id": ("set", session_id),
            "last_active": ("set", first_ts or ""),
        }
        for tool, count in tool_counts.items():
            u[f"tool_usage.{tool}"] = ("inc", count)
        if project:
            u[f"project_usage.{project}"] = ("inc", 1)
        if date_str:
            u[f"daily.{date_str}.s"] = ("inc", 1)
            u[f"daily.{date_str}.m"] = ("inc", msg_count)
            u[f"daily.{date_str}.d"] = ("inc", duration)
        deltas[f"user:{username}"] = u

    return deltas


def apply_deltas(store: dict, deltas: dict):
    """Apply counter deltas to a {doc_name: nested dict} store in place."""
    for doc_name, fields in deltas.items():
        doc = store.setdefault(doc_name, {})
        for path, (op, value) in fields.items():
            *parents, leaf = path.split(".")
            target = doc
            for part in parents:
                target = target.setdefault(part, {})
            if op == "inc":
                target[leaf] = target.get(leaf, 0) + value
            elif op == "set":
                target[leaf] = value
            elif op == "union":
                items = target.setdefault(leaf, [])
                items.extend(v for v in value if v not in items)


# --- Stats assembly -----------------------------------------------------------


def _today() -> date:
    return datetime.now(timezone.utc).date()


def build_user_stats(
    username: str,
    counter: dict | None,
    recent: list[dict],
    last_session: dict | None,
) -> dict:
    """Personal stats response from a user counter doc + recent sessions."""
    if not counter:
        return {
            "user": username, "total_sessions": 0, "avg_messages_per_session": 0,
            "last_session": None, "week_stats": {
                "sessions": 0, "sessions_prev_week": 0, "messages": 0,
                "avg_duration_seconds": 0, "total_duration_seconds": 0,
                "active_days": 0, "most_active_project": "",
            },
            "heatmap": [], "tool_usage": {}, "project_usage": {}, "recent_sessions": [],
        }

    today = _today()
    week_start_str = (today - timedelta(days=today.weekday())).isoformat()  # Monday
    prev_week_start_str = (today - timedelta(days=today.weekday() + 7)).isoformat()
    heatmap_start = (today.replace(day=1) - timedelta(days=90)).replace(day=1)

    daily = counter.get("daily", {})

    week_sessions = 0
    week_messages = 0
    week_duration = 0.0
    week_active_days = 0
    prev_week_sessions = 0
    for date_str, day_data in daily.items():
        if not isinstance(day_data, dict):
            continue
        if date_str >= week_start_str:
            s = day_data.get("s", 0)
            week_sessions += s
            week_messages += day_data.get("m", 0)
            week_duration += day_data.get("d", 0)
            if s > 0:
                week_active_days += 1
        elif date_str >= prev_week_start_str:
            prev_week_sessions += day_data.get("s", 0)

    heatmap = []
    d = heatmap_start
    while d <= today:
        ds = d.isoformat()
        day_data = daily.get(ds, {})
        count = day_data.get("s", 0) if isinstance(day_data, dict) else 0
        heatmap.append({"date": ds, "count": count})
        d += timedelta(days=1)

    week_projects: dict[str, int] = {}
    for s in recent:
        ts = s.get("first_timestamp", "") or ""
        proj = s.get("project", "")
        if proj and ts[:10] >= week_start_str:
            week_projects[proj] = week_projects.get(proj, 0) + 1
    most_active = max(week_projects, key=week_projects.get) if week_projects else ""

    total_sessions = counter.get("total_sessions", 0)
    total_messages = counter.get("total_messages", 0)

    return {
        "user": username,
        "total_sessions": total_sessions,
        "avg_messages_per_session": round(total_messages / total_sessions) if total_sessions else 0,
        "last_session": last_session,
        "week_stats": {
            "sessions": week_sessions,
            "sessions_prev_week": prev_week_sessions,
            "messages": week_messages,
            "avg_duration_seconds": round(week_duration / week_sessions) if week_sessions else 0,
            "total_duration_seconds": round(week_duration),
            "active_days": week_active_days,
            "most_active_project": most_active,
        },
        "heatmap": heatmap,
        "tool_usage": dict(sorted(counter.get("tool_usage", {}).items(), key=lambda x: -x[1])),
        "project_usage": dict(sorted(counter.get("project_usage", {}).items(), key=lambda x: -x[1])),
        "recent_sessions": recent[:10],
    }


def build_global_stats(
    g: dict | None,
    users_map: dict,
    projects_map: dict,
    daily_map: dict,
    user_counters: dict,
    recent: list[dict],
) -> dict:
    """Aggregate stats response from the split global counter docs.

    `user_counters` maps username -> that user's counter doc (for top_project
    and active-days enrichment).
    """
    if not g:
        return {
            "total_sessions": 0, "total_messages": 0, "total_tool_uses": 0,
            "unique_users": 0, "unique_projects": 0, "avg_duration_seconds": 0,
            "active_this_week": 0, "users": [], "projects": [],
            "tool_usage": {}, "timeline": [], "user_stats": {},
            "project_stats": {}, "recent_sessions": [],
        }

    today = _today()
    week_start_str = (today - timedelta(days=today.weekday())).isoformat()

    user_stats = {}
    active_this_week = 0
    for username, info in users_map.items():
        sessions = info.get("sessions", 0)
        dur = info.get("total_duration_seconds", 0)

        uc = user_counters.get(username, {})
        project_usage = uc.get("project_usage", {})
        udaily = uc.get("daily", {})

        top_project = max(project_usage, key=project_usage.get) if project_usage else ""
        week_days = sum(
            1 for d, v in udaily.items()
            if d >= week_start_str and isinstance(v, dict) and v.get("s", 0) > 0
        )
        if week_days > 0:
            active_this_week += 1

        user_stats[username] = {
            "sessions": sessions,
            "messages": info.get("messages", 0),
            "tool_uses": info.get("tool_uses", 0),
            "last_active": info.get("last_active", ""),
            "avg_duration_seconds": round(dur / sessions) if sessions else 0,
            "top_project": top_project,
            "active_days_this_week": week_days,
        }

    project_stats = {
        name: {
            "sessions": info.get("sessions", 0),
            "messages": info.get("messages", 0),
            "users": sorted(info.get("users", [])),
        }
        for name, info in projects_map.items()
    }

    timeline = []
    for i in range(29, -1, -1):
        day = (today - timedelta(days=i)).isoformat()
        timeline.append({"date": day, "count": daily_map.get(day, 0)})

    total_dur = sum(info.get("total_duration_seconds", 0) for info in users_map.values())
    total_sess = g.get("total_sessions", 0)

    return {
        "total_sessions": total_sess,
        "total_messages": g.get("total_messages", 0),
        "total_tool_uses": g.get("total_tool_uses", 0),
        "unique_users": len(users_map),
        "unique_projects": len(projects_map),
        "avg_duration_seconds": round(total_dur / total_sess) if total_sess else 0,
        "active_this_week": active_this_week,
        "users": sorted(users_map.keys()),
        "projects": sorted(projects_map.keys()),
        "tool_usage": dict(sorted(g.get("tool_usage", {}).items(), key=lambda x: -x[1])),
        "timeline": timeline,
        "user_stats": dict(sorted(user_stats.items(), key=lambda x: -x[1]["sessions"])),
        "project_stats": dict(sorted(project_stats.items(), key=lambda x: -x[1]["sessions"])[:15]),
        "recent_sessions": recent,
    }
