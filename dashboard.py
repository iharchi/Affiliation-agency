"""
Agency Dashboard & Content Approval System
Provides a visual dashboard of agent activity and a content review/approval workflow.
"""

import json
import os
import textwrap
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any


# ── Content Queue ────────────────────────────────────────────────────────────

@dataclass
class ContentItem:
    id: int
    title: str
    content_type: str          # listicle, review, comparison, video_script, etc.
    agent: str                 # which agent produced it
    task: str                  # original task name
    body: str                  # the generated content
    status: str = "pending"    # pending | approved | rejected | revised
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    feedback: str = ""
    day: int = 0
    word_count: int = 0


class ContentQueue:
    """Stores generated content for review and approval."""

    def __init__(self, data_dir: str = "data"):
        self.items: list[ContentItem] = []
        self._next_id = 1
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def add(self, title: str, content_type: str, agent: str, task: str,
            body: str, day: int = 0, **_kwargs: Any) -> ContentItem:
        item = ContentItem(
            id=self._next_id,
            title=title,
            content_type=content_type,
            agent=agent,
            task=task,
            body=body,
            day=day,
            word_count=len(body.split()),
        )
        self._next_id += 1
        self.items.append(item)
        return item

    def get(self, item_id: int) -> ContentItem | None:
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def approve(self, item_id: int) -> bool:
        item = self.get(item_id)
        if item:
            item.status = "approved"
            return True
        return False

    def reject(self, item_id: int, feedback: str = "") -> bool:
        item = self.get(item_id)
        if item:
            item.status = "rejected"
            item.feedback = feedback
            return True
        return False

    def list_by_status(self, status: str | None = None) -> list[ContentItem]:
        if status is None:
            return self.items
        return [i for i in self.items if i.status == status]

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {"pending": 0, "approved": 0, "rejected": 0, "revised": 0, "total": 0}
        for item in self.items:
            counts[item.status] = counts.get(item.status, 0) + 1
            counts["total"] += 1
        return counts

    def export_approved(self, filepath: str | None = None) -> str:
        """Export all approved content to a file."""
        approved = self.list_by_status("approved")
        if not approved:
            return "No approved content to export."
        path = filepath or os.path.join(self.data_dir, f"approved_content_{datetime.now().strftime('%Y%m%d_%H%M')}.md")
        with open(path, "w") as f:
            for item in approved:
                f.write(f"# {item.title}\n")
                f.write(f"**Type:** {item.content_type} | **Agent:** {item.agent} | **Day:** {item.day}\n\n")
                f.write(item.body)
                f.write("\n\n---\n\n")
        return path


# ── Agent Tracker ────────────────────────────────────────────────────────────

@dataclass
class AgentStatus:
    name: str
    display_name: str
    status: str = "idle"           # idle | running | done | error
    current_task: str = ""
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_run: str = ""
    last_result_preview: str = ""


class AgentTracker:
    """Tracks real-time status of all agents."""

    AGENT_DISPLAY = {
        "niche_research": "Niche Research",
        "affiliate_scout": "Affiliate Scout",
        "content_strategy": "Content Strategy",
        "content_creation": "Content Creation",
        "seo_analytics": "SEO & Analytics",
        "social_distribution": "Social Distribution",
        "email_marketing": "Email Marketing",
        "revenue_tracking": "Revenue Tracking",
    }

    def __init__(self):
        self.agents: dict[str, AgentStatus] = {}
        for key, display in self.AGENT_DISPLAY.items():
            self.agents[key] = AgentStatus(name=key, display_name=display)

    def mark_running(self, agent_name: str, task: str) -> None:
        if agent_name in self.agents:
            a = self.agents[agent_name]
            a.status = "running"
            a.current_task = task

    def mark_done(self, agent_name: str, result_preview: str = "") -> None:
        if agent_name in self.agents:
            a = self.agents[agent_name]
            a.status = "done"
            a.tasks_completed += 1
            a.last_run = datetime.now().strftime("%H:%M:%S")
            a.current_task = ""
            a.last_result_preview = result_preview[:120] if result_preview else ""

    def mark_error(self, agent_name: str, error: str = "") -> None:
        if agent_name in self.agents:
            a = self.agents[agent_name]
            a.status = "error"
            a.tasks_failed += 1
            a.last_run = datetime.now().strftime("%H:%M:%S")
            a.current_task = ""
            a.last_result_preview = f"ERROR: {error[:100]}" if error else "ERROR"

    @property
    def total_completed(self) -> int:
        return sum(a.tasks_completed for a in self.agents.values())

    def reset_all(self) -> None:
        for a in self.agents.values():
            a.status = "idle"
            a.current_task = ""


# ── Dashboard Renderer ──────────────────────────────────────────────────────

STATUS_ICONS = {
    "idle": "  ",
    "running": ">>",
    "done": "OK",
    "error": "!!",
}

CONTENT_STATUS_ICONS = {
    "pending": "[?]",
    "approved": "[+]",
    "rejected": "[-]",
    "revised": "[~]",
}


def render_dashboard(tracker: AgentTracker, content_queue: ContentQueue,
                     config: Any, workflow: Any = None) -> str:
    """Render a full-width text dashboard."""
    w = 72
    lines: list[str] = []

    def hr(char: str = "─") -> str:
        return char * w

    def header(title: str) -> str:
        pad = w - len(title) - 4
        return f"┌─ {title} " + "─" * max(pad, 0) + "┐"

    def footer() -> str:
        return "└" + "─" * (w - 2) + "┘"

    def row(left: str, right: str = "") -> str:
        inner = w - 4
        if right:
            gap = inner - len(left) - len(right)
            return f"│ {left}{' ' * max(gap, 1)}{right} │"
        text = left[:inner].ljust(inner)
        return f"│ {text} │"

    # ── Title ──
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append("")
    lines.append(header("AFFILIATE AGENCY DASHBOARD"))
    lines.append(row(f"Niche: {config.selected_niche.value}", now))
    lines.append(row(f"Target: {config.revenue_target}", f"Tasks run: {tracker.total_completed}"))
    lines.append(footer())

    # ── Agent Status ──
    lines.append("")
    lines.append(header("AGENT STATUS"))
    lines.append(row(
        f"{'Agent':<24s} {'Status':<10s} {'Done':>4s}  {'Last':>8s}  Task / Preview",
    ))
    lines.append(row(hr()))
    for a in tracker.agents.values():
        icon = STATUS_ICONS.get(a.status, "  ")
        info = a.current_task if a.status == "running" else a.last_result_preview
        info_short = (info[:22] + "..") if len(info) > 24 else info
        line = f"[{icon}] {a.display_name:<20s} {a.status:<10s} {a.tasks_completed:>4d}  {a.last_run:>8s}  {info_short}"
        lines.append(row(line))
    lines.append(footer())

    # ── Content Queue ──
    summary = content_queue.summary()
    lines.append("")
    lines.append(header("CONTENT QUEUE"))
    lines.append(row(
        f"Total: {summary['total']}",
        f"Pending: {summary['pending']}  Approved: {summary['approved']}  Rejected: {summary['rejected']}"
    ))
    lines.append(row(hr()))

    recent = content_queue.items[-8:] if content_queue.items else []
    if recent:
        lines.append(row(f"{'ID':>3s}  {'Status':<10s} {'Type':<16s} Title"))
        for item in recent:
            icon = CONTENT_STATUS_ICONS.get(item.status, "[ ]")
            title_short = (item.title[:34] + "..") if len(item.title) > 36 else item.title
            lines.append(row(f"{item.id:>3d}  {icon} {item.status:<6s} {item.content_type:<16s} {title_short}"))
    else:
        lines.append(row("No content generated yet. Run 'run <agent> <task>' to start."))
    lines.append(footer())

    # ── Commands ──
    lines.append("")
    lines.append("  Dashboard commands:")
    lines.append("    dashboard / db       — Refresh this dashboard")
    lines.append("    queue                — List all content in queue")
    lines.append("    review <ID>          — View content item for review")
    lines.append("    approve <ID>         — Approve content item")
    lines.append("    reject <ID> [reason] — Reject content with feedback")
    lines.append("    export               — Export approved content to file")
    lines.append("")

    return "\n".join(lines)


def render_content_review(item: ContentItem) -> str:
    """Render a single content item for detailed review."""
    w = 72
    lines: list[str] = []

    lines.append("")
    lines.append("=" * w)
    lines.append(f"  CONTENT REVIEW — Item #{item.id}")
    lines.append("=" * w)
    lines.append(f"  Title:    {item.title}")
    lines.append(f"  Type:     {item.content_type}")
    lines.append(f"  Agent:    {item.agent}")
    lines.append(f"  Task:     {item.task}")
    lines.append(f"  Words:    {item.word_count}")
    lines.append(f"  Status:   {item.status.upper()}")
    lines.append(f"  Created:  {item.created_at}")
    if item.feedback:
        lines.append(f"  Feedback: {item.feedback}")
    lines.append("-" * w)
    lines.append("")

    # Wrap long lines for readability
    for line in item.body.split("\n"):
        if len(line) > w:
            for wrapped in textwrap.wrap(line, width=w):
                lines.append(wrapped)
        else:
            lines.append(line)

    lines.append("")
    lines.append("-" * w)
    lines.append("  Actions:  approve <ID>  |  reject <ID> [reason]")
    lines.append("=" * w)

    return "\n".join(lines)


def render_queue_list(content_queue: ContentQueue, status_filter: str | None = None) -> str:
    """Render the content queue as a table."""
    items = content_queue.list_by_status(status_filter)
    if not items:
        return f"\n  No content items{f' with status={status_filter}' if status_filter else ''}.\n"

    lines = [
        "",
        f"  {'ID':>3s}  {'Status':<10s} {'Type':<16s} {'Agent':<20s} {'Words':>5s}  Title",
        "  " + "─" * 90,
    ]
    for item in items:
        icon = CONTENT_STATUS_ICONS.get(item.status, "[ ]")
        title_short = (item.title[:32] + "..") if len(item.title) > 34 else item.title
        lines.append(
            f"  {item.id:>3d}  {icon} {item.status:<6s} {item.content_type:<16s} {item.agent:<20s} {item.word_count:>5d}  {title_short}"
        )
    lines.append(f"\n  Total: {len(items)} items")
    lines.append("")
    return "\n".join(lines)
