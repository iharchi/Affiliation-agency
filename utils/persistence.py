"""
SQLite Persistence Layer
Persists all agent state, execution logs, content queue, link tracking,
and sprint milestones so nothing is lost between restarts.
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Any


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "agency.db")


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str | None = None) -> sqlite3.Connection:
    """Create all tables if they don't exist and return the connection."""
    conn = _connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS agent_memory (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name  TEXT NOT NULL,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            timestamp   TEXT NOT NULL,
            metadata    TEXT DEFAULT '{}',
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS agent_results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name  TEXT NOT NULL,
            task        TEXT NOT NULL,
            output      TEXT,
            success     INTEGER NOT NULL DEFAULT 1,
            errors      TEXT DEFAULT '[]',
            metadata    TEXT DEFAULT '{}',
            timestamp   TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS execution_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name  TEXT NOT NULL,
            task        TEXT NOT NULL,
            output      TEXT,
            success     INTEGER NOT NULL DEFAULT 1,
            errors      TEXT DEFAULT '[]',
            metadata    TEXT DEFAULT '{}',
            timestamp   TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS content_queue (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT NOT NULL,
            content_type  TEXT NOT NULL,
            agent         TEXT NOT NULL,
            task          TEXT NOT NULL,
            body          TEXT NOT NULL,
            status        TEXT NOT NULL DEFAULT 'pending',
            feedback      TEXT DEFAULT '',
            day           INTEGER DEFAULT 0,
            word_count    INTEGER DEFAULT 0,
            created_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS agent_tracker (
            name              TEXT PRIMARY KEY,
            display_name      TEXT NOT NULL,
            status            TEXT NOT NULL DEFAULT 'idle',
            current_task      TEXT DEFAULT '',
            tasks_completed   INTEGER DEFAULT 0,
            tasks_failed      INTEGER DEFAULT 0,
            last_run          TEXT DEFAULT '',
            last_result_preview TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS revenue_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            program         TEXT NOT NULL,
            amount          REAL DEFAULT 0,
            clicks          INTEGER DEFAULT 0,
            conversions     INTEGER DEFAULT 0,
            source_content  TEXT DEFAULT '',
            platform        TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS kpi_history (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            traffic             INTEGER DEFAULT 0,
            affiliate_clicks    INTEGER DEFAULT 0,
            conversions         INTEGER DEFAULT 0,
            revenue             REAL DEFAULT 0,
            email_subscribers   INTEGER DEFAULT 0,
            content_published   INTEGER DEFAULT 0,
            ctr                 REAL DEFAULT 0,
            epc                 REAL DEFAULT 0,
            conversion_rate     REAL DEFAULT 0,
            created_at          TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS affiliate_links (
            link_id       TEXT PRIMARY KEY,
            program       TEXT NOT NULL,
            base_url      TEXT NOT NULL,
            affiliate_tag TEXT DEFAULT '',
            utm_source    TEXT DEFAULT '',
            utm_medium    TEXT DEFAULT '',
            utm_campaign  TEXT DEFAULT '',
            utm_content   TEXT DEFAULT '',
            clicks        INTEGER DEFAULT 0,
            conversions   INTEGER DEFAULT 0,
            revenue       REAL DEFAULT 0,
            created_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS program_portfolio (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            data        TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sprint_milestones (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            week            INTEGER NOT NULL,
            milestone_name  TEXT NOT NULL,
            completed       INTEGER NOT NULL DEFAULT 0,
            completed_at    TEXT,
            UNIQUE(week, milestone_name)
        );

        CREATE INDEX IF NOT EXISTS idx_memory_agent ON agent_memory(agent_name);
        CREATE INDEX IF NOT EXISTS idx_results_agent ON agent_results(agent_name);
        CREATE INDEX IF NOT EXISTS idx_exec_agent ON execution_log(agent_name);
        CREATE INDEX IF NOT EXISTS idx_content_status ON content_queue(status);
        CREATE INDEX IF NOT EXISTS idx_revenue_program ON revenue_log(program);
    """)
    conn.commit()
    return conn


# ── Agent Memory ─────────────────────────────────────────────────────────────

def save_memory(conn: sqlite3.Connection, agent_name: str,
                role: str, content: str, timestamp: str,
                metadata: dict | None = None) -> None:
    conn.execute(
        "INSERT INTO agent_memory (agent_name, role, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
        (agent_name, role, content, timestamp, json.dumps(metadata or {})),
    )
    conn.commit()


def load_memory(conn: sqlite3.Connection, agent_name: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT role, content, timestamp, metadata FROM agent_memory WHERE agent_name = ? ORDER BY id",
        (agent_name,),
    ).fetchall()
    return [
        {"role": r["role"], "content": r["content"],
         "timestamp": r["timestamp"], "metadata": json.loads(r["metadata"])}
        for r in rows
    ]


# ── Agent Results ────────────────────────────────────────────────────────────

def save_result(conn: sqlite3.Connection, agent_name: str, task: str,
                output: Any, success: bool, timestamp: str,
                errors: list | None = None, metadata: dict | None = None) -> None:
    conn.execute(
        "INSERT INTO agent_results (agent_name, task, output, success, errors, metadata, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (agent_name, task, json.dumps(output, default=str), int(success),
         json.dumps(errors or []), json.dumps(metadata or {}), timestamp),
    )
    conn.commit()


def load_results(conn: sqlite3.Connection, agent_name: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT agent_name, task, output, success, errors, metadata, timestamp "
        "FROM agent_results WHERE agent_name = ? ORDER BY id",
        (agent_name,),
    ).fetchall()
    return [
        {"agent_name": r["agent_name"], "task": r["task"],
         "output": json.loads(r["output"]), "success": bool(r["success"]),
         "errors": json.loads(r["errors"]), "metadata": json.loads(r["metadata"]),
         "timestamp": r["timestamp"]}
        for r in rows
    ]


# ── Execution Log ────────────────────────────────────────────────────────────

def save_execution(conn: sqlite3.Connection, agent_name: str, task: str,
                   output: Any, success: bool, timestamp: str,
                   errors: list | None = None, metadata: dict | None = None) -> None:
    conn.execute(
        "INSERT INTO execution_log (agent_name, task, output, success, errors, metadata, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (agent_name, task, json.dumps(output, default=str), int(success),
         json.dumps(errors or []), json.dumps(metadata or {}), timestamp),
    )
    conn.commit()


def load_execution_log(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT agent_name, task, output, success, errors, metadata, timestamp "
        "FROM execution_log ORDER BY id"
    ).fetchall()
    return [
        {"agent_name": r["agent_name"], "task": r["task"],
         "output": json.loads(r["output"]), "success": bool(r["success"]),
         "errors": json.loads(r["errors"]), "metadata": json.loads(r["metadata"]),
         "timestamp": r["timestamp"]}
        for r in rows
    ]


# ── Content Queue ────────────────────────────────────────────────────────────

def save_content_item(conn: sqlite3.Connection, title: str, content_type: str,
                      agent: str, task: str, body: str,
                      day: int = 0, word_count: int = 0) -> int:
    cur = conn.execute(
        "INSERT INTO content_queue (title, content_type, agent, task, body, day, word_count) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, content_type, agent, task, body, day, word_count),
    )
    conn.commit()
    return cur.lastrowid


def update_content_status(conn: sqlite3.Connection, item_id: int,
                          status: str, feedback: str = "") -> bool:
    cur = conn.execute(
        "UPDATE content_queue SET status = ?, feedback = ? WHERE id = ?",
        (status, feedback, item_id),
    )
    conn.commit()
    return cur.rowcount > 0


def load_content_items(conn: sqlite3.Connection,
                       status: str | None = None) -> list[dict[str, Any]]:
    if status:
        rows = conn.execute(
            "SELECT * FROM content_queue WHERE status = ? ORDER BY id", (status,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM content_queue ORDER BY id").fetchall()
    return [dict(r) for r in rows]


# ── Agent Tracker ────────────────────────────────────────────────────────────

def save_tracker_state(conn: sqlite3.Connection, name: str, display_name: str,
                       status: str = "idle", current_task: str = "",
                       tasks_completed: int = 0, tasks_failed: int = 0,
                       last_run: str = "", last_result_preview: str = "") -> None:
    conn.execute(
        "INSERT INTO agent_tracker (name, display_name, status, current_task, "
        "tasks_completed, tasks_failed, last_run, last_result_preview) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(name) DO UPDATE SET status=excluded.status, "
        "current_task=excluded.current_task, tasks_completed=excluded.tasks_completed, "
        "tasks_failed=excluded.tasks_failed, last_run=excluded.last_run, "
        "last_result_preview=excluded.last_result_preview",
        (name, display_name, status, current_task,
         tasks_completed, tasks_failed, last_run, last_result_preview),
    )
    conn.commit()


def load_tracker_states(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute("SELECT * FROM agent_tracker ORDER BY name").fetchall()
    return {r["name"]: dict(r) for r in rows}


# ── Revenue Log ──────────────────────────────────────────────────────────────

def save_revenue_event(conn: sqlite3.Connection, program: str, amount: float = 0,
                       clicks: int = 0, conversions: int = 0,
                       source_content: str = "", platform: str = "") -> None:
    conn.execute(
        "INSERT INTO revenue_log (program, amount, clicks, conversions, source_content, platform) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (program, amount, clicks, conversions, source_content, platform),
    )
    conn.commit()


def load_revenue_log(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM revenue_log ORDER BY id").fetchall()
    return [
        {"program": r["program"], "amount": r["amount"], "clicks": r["clicks"],
         "conversions": r["conversions"], "source_content": r["source_content"],
         "platform": r["platform"]}
        for r in rows
    ]


# ── KPI History ──────────────────────────────────────────────────────────────

def save_kpi_snapshot(conn: sqlite3.Connection, snapshot: dict[str, Any]) -> None:
    conn.execute(
        "INSERT INTO kpi_history (traffic, affiliate_clicks, conversions, revenue, "
        "email_subscribers, content_published, ctr, epc, conversion_rate) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (snapshot.get("traffic", 0), snapshot.get("affiliate_clicks", 0),
         snapshot.get("conversions", 0), snapshot.get("revenue", 0),
         snapshot.get("email_subscribers", 0), snapshot.get("content_published", 0),
         snapshot.get("ctr", 0), snapshot.get("epc", 0),
         snapshot.get("conversion_rate", 0)),
    )
    conn.commit()


def load_kpi_history(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM kpi_history ORDER BY id").fetchall()
    return [
        {"traffic": r["traffic"], "affiliate_clicks": r["affiliate_clicks"],
         "conversions": r["conversions"], "revenue": r["revenue"],
         "email_subscribers": r["email_subscribers"],
         "content_published": r["content_published"],
         "ctr": r["ctr"], "epc": r["epc"], "conversion_rate": r["conversion_rate"]}
        for r in rows
    ]


# ── Affiliate Links ──────────────────────────────────────────────────────────

def save_affiliate_link(conn: sqlite3.Connection, link_id: str,
                        program: str, base_url: str, affiliate_tag: str,
                        utm_source: str = "", utm_medium: str = "",
                        utm_campaign: str = "", utm_content: str = "") -> None:
    conn.execute(
        "INSERT INTO affiliate_links (link_id, program, base_url, affiliate_tag, "
        "utm_source, utm_medium, utm_campaign, utm_content) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(link_id) DO UPDATE SET "
        "program=excluded.program, base_url=excluded.base_url, "
        "affiliate_tag=excluded.affiliate_tag, utm_source=excluded.utm_source, "
        "utm_medium=excluded.utm_medium, utm_campaign=excluded.utm_campaign, "
        "utm_content=excluded.utm_content",
        (link_id, program, base_url, affiliate_tag,
         utm_source, utm_medium, utm_campaign, utm_content),
    )
    conn.commit()


def update_link_clicks(conn: sqlite3.Connection, link_id: str) -> bool:
    cur = conn.execute(
        "UPDATE affiliate_links SET clicks = clicks + 1 WHERE link_id = ?", (link_id,)
    )
    conn.commit()
    return cur.rowcount > 0


def update_link_conversion(conn: sqlite3.Connection, link_id: str, revenue: float) -> bool:
    cur = conn.execute(
        "UPDATE affiliate_links SET conversions = conversions + 1, revenue = revenue + ? "
        "WHERE link_id = ?",
        (revenue, link_id),
    )
    conn.commit()
    return cur.rowcount > 0


def load_affiliate_links(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute("SELECT * FROM affiliate_links ORDER BY link_id").fetchall()
    return {r["link_id"]: dict(r) for r in rows}


# ── Program Portfolio ────────────────────────────────────────────────────────

def save_portfolio(conn: sqlite3.Connection, portfolio: list[dict[str, Any]]) -> None:
    conn.execute("DELETE FROM program_portfolio")
    for item in portfolio:
        conn.execute("INSERT INTO program_portfolio (data) VALUES (?)", (json.dumps(item, default=str),))
    conn.commit()


def load_portfolio(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT data FROM program_portfolio ORDER BY id").fetchall()
    return [json.loads(r["data"]) for r in rows]


# ── Sprint Milestones ────────────────────────────────────────────────────────

def save_milestone(conn: sqlite3.Connection, week: int,
                   milestone_name: str, completed: bool) -> None:
    conn.execute(
        "INSERT INTO sprint_milestones (week, milestone_name, completed, completed_at) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(week, milestone_name) DO UPDATE SET "
        "completed=excluded.completed, completed_at=excluded.completed_at",
        (week, milestone_name, int(completed),
         datetime.now().isoformat() if completed else None),
    )
    conn.commit()


def load_milestones(conn: sqlite3.Connection) -> dict[tuple[int, str], bool]:
    rows = conn.execute("SELECT week, milestone_name, completed FROM sprint_milestones").fetchall()
    return {(r["week"], r["milestone_name"]): bool(r["completed"]) for r in rows}
