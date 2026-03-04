"""
Web Dashboard — Flask server for the Affiliate Agency dashboard.
Provides a browser-based UI for monitoring agents and reviewing content.

Usage:
    python web_dashboard.py                # Start on port 8080
    python web_dashboard.py --port 9000    # Custom port
"""

import argparse
import json
import os
import threading
from dataclasses import asdict
from typing import Any

from flask import Flask, jsonify, render_template, request

from config.settings import AgencyConfig, Niche
from agents.orchestrator import AgencyOrchestrator
from workflows.sprint_workflow import SprintWorkflow
from dashboard import AgentTracker, ContentQueue

app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static",
)

# ── Shared state (initialized in main) ──────────────────────────────────────
tracker: AgentTracker = AgentTracker()
content_queue: ContentQueue = ContentQueue()
orchestrator: AgencyOrchestrator | None = None
workflow: SprintWorkflow | None = None

# Background job tracking
_job_lock = threading.Lock()
_current_job: dict[str, Any] = {"running": False, "day": None, "error": None}


# ── Pages ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("dashboard.html")


# ── API: Dashboard data ─────────────────────────────────────────────────────

@app.route("/api/dashboard")
def api_dashboard():
    """Return full dashboard state as JSON."""
    config = orchestrator.config if orchestrator else AgencyConfig()
    agents_list = []
    for a in tracker.agents.values():
        agents_list.append({
            "name": a.name,
            "display_name": a.display_name,
            "status": a.status,
            "current_task": a.current_task,
            "tasks_completed": a.tasks_completed,
            "tasks_failed": a.tasks_failed,
            "last_run": a.last_run,
            "last_result_preview": a.last_result_preview,
        })

    progress = workflow.get_progress() if workflow else {}
    focus = workflow.get_today_focus() if workflow else {}
    summary = content_queue.summary()

    with _job_lock:
        job = dict(_current_job)

    return jsonify({
        "config": {
            "current_day": config.current_day,
            "current_week": config.current_week,
            "niche": config.selected_niche.value,
            "revenue_target": config.revenue_target,
        },
        "agents": agents_list,
        "content_summary": summary,
        "sprint_progress": progress,
        "today_focus": focus,
        "job": job,
    })


# ── API: Content queue ──────────────────────────────────────────────────────

@app.route("/api/content")
def api_content_list():
    """List content items, optionally filtered by status."""
    status = request.args.get("status")
    items = content_queue.list_by_status(status)
    return jsonify([{
        "id": i.id,
        "title": i.title,
        "content_type": i.content_type,
        "agent": i.agent,
        "task": i.task,
        "status": i.status,
        "created_at": i.created_at,
        "feedback": i.feedback,
        "day": i.day,
        "word_count": i.word_count,
    } for i in items])


@app.route("/api/content/<int:item_id>")
def api_content_detail(item_id: int):
    """Get a single content item with full body."""
    item = content_queue.get(item_id)
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "id": item.id,
        "title": item.title,
        "content_type": item.content_type,
        "agent": item.agent,
        "task": item.task,
        "body": item.body,
        "status": item.status,
        "created_at": item.created_at,
        "feedback": item.feedback,
        "day": item.day,
        "word_count": item.word_count,
    })


@app.route("/api/content/<int:item_id>/approve", methods=["POST"])
def api_approve(item_id: int):
    if content_queue.approve(item_id):
        return jsonify({"ok": True, "status": "approved"})
    return jsonify({"error": "Not found"}), 404


@app.route("/api/content/<int:item_id>/reject", methods=["POST"])
def api_reject(item_id: int):
    data = request.get_json(silent=True) or {}
    feedback = data.get("feedback", "")
    if content_queue.reject(item_id, feedback):
        return jsonify({"ok": True, "status": "rejected", "feedback": feedback})
    return jsonify({"error": "Not found"}), 404


@app.route("/api/content/export", methods=["POST"])
def api_export():
    path = content_queue.export_approved()
    return jsonify({"path": path})


# ── API: Run tasks (background) ─────────────────────────────────────────────

def _run_day_background(day: int) -> None:
    """Execute a day's tasks in a background thread."""
    global _current_job
    try:
        result = orchestrator.run_day(day)
        with _job_lock:
            _current_job = {"running": False, "day": day, "error": None,
                            "tasks_completed": result.get("tasks_completed", 0)}
    except Exception as e:
        with _job_lock:
            _current_job = {"running": False, "day": day, "error": str(e)}
        # Mark any running agents as error
        for a in tracker.agents.values():
            if a.status == "running":
                tracker.mark_error(a.name, str(e))


@app.route("/api/run/day/<int:day>", methods=["POST"])
def api_run_day(day: int):
    global _current_job
    if not orchestrator:
        return jsonify({"error": "Orchestrator not initialized"}), 500

    with _job_lock:
        if _current_job["running"]:
            return jsonify({"error": "A job is already running",
                            "current_day": _current_job["day"]}), 409

        _current_job = {"running": True, "day": day, "error": None}

    thread = threading.Thread(target=_run_day_background, args=(day,), daemon=True)
    thread.start()

    return jsonify({"ok": True, "message": f"Day {day} started in background"})


@app.route("/api/run/agent", methods=["POST"])
def api_run_agent():
    if not orchestrator:
        return jsonify({"error": "Orchestrator not initialized"}), 500
    data = request.get_json(silent=True) or {}
    agent_name = data.get("agent", "")
    task = data.get("task", "")
    context = data.get("context")
    if not agent_name or not task:
        return jsonify({"error": "agent and task required"}), 400

    def _run():
        global _current_job
        try:
            if tracker:
                tracker.mark_running(agent_name, task)
            result = orchestrator.execute_task(agent_name, task, context)
            if tracker:
                if result.success:
                    tracker.mark_done(agent_name, str(result.output)[:120])
                else:
                    tracker.mark_error(agent_name, "; ".join(result.errors))
            with _job_lock:
                _current_job = {"running": False, "day": None, "error": None}
        except Exception as e:
            if tracker:
                tracker.mark_error(agent_name, str(e))
            with _job_lock:
                _current_job = {"running": False, "day": None, "error": str(e)}

    with _job_lock:
        if _current_job["running"]:
            return jsonify({"error": "A job is already running"}), 409
        _current_job = {"running": True, "day": None, "error": None}

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify({"ok": True, "message": f"Agent {agent_name}.{task} started"})


@app.route("/api/job")
def api_job_status():
    with _job_lock:
        return jsonify(_current_job)


# ── Bootstrap ───────────────────────────────────────────────────────────────

def setup_llm_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            return anthropic.Anthropic(api_key=api_key, timeout=120.0)
        except ImportError:
            pass
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            import openai
            return openai.OpenAI(api_key=api_key, timeout=120.0)
        except ImportError:
            pass
    return None


def create_app(niche: str = "ai_saas_tools", target: str = "moderate") -> Flask:
    global tracker, content_queue, orchestrator, workflow

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    niche_map = {n.value: n for n in Niche}
    selected_niche = niche_map.get(niche, Niche.AI_SAAS)

    config = AgencyConfig(selected_niche=selected_niche, revenue_target=target)
    llm_client = setup_llm_client()

    tracker = AgentTracker()
    content_queue = ContentQueue()
    orchestrator = AgencyOrchestrator(config, llm_client, tracker=tracker, content_queue=content_queue)
    workflow = SprintWorkflow(config)

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Affiliate Agency Web Dashboard")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--niche", type=str, default="ai_saas_tools")
    parser.add_argument("--target", type=str, default="moderate")
    args = parser.parse_args()

    create_app(args.niche, args.target)
    print(f"\n  Dashboard running at http://localhost:{args.port}\n")
    app.run(host="0.0.0.0", port=args.port, debug=True)
