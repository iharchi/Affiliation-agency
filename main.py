"""
Affiliate Marketing Agency — Main Entry Point
Run AI agents on-demand to execute affiliate marketing tasks.

Usage:
    python main.py                                              # Interactive mode
    python main.py --agent niche_research --task analyze_all    # Run specific agent task
    python main.py --agent content_creation --task write_review product="Jasper AI"
    python main.py --agents                                     # List all agents
    python main.py --tasks niche_research                       # List tasks for an agent
    python main.py --integrations                               # Check integration status
"""

import argparse
import json
import os
from typing import Any

from config.settings import AgencyConfig, Niche, Platform
from config.integrations import load_all_integrations, print_integration_status
from agents.orchestrator import AgencyOrchestrator, AGENT_TASKS
from dashboard import (
    AgentTracker, ContentQueue,
    render_dashboard, render_content_review, render_queue_list,
)


def setup_llm_client() -> Any:
    """Set up the LLM client based on available API keys."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and not api_key.startswith("your_"):
        try:
            import anthropic
            return anthropic.Anthropic(api_key=api_key)
        except ImportError:
            print("[Setup] anthropic package not installed. Run: pip install anthropic")

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and not api_key.startswith("your_"):
        try:
            import openai
            return openai.OpenAI(api_key=api_key)
        except ImportError:
            print("[Setup] openai package not installed. Run: pip install openai")

    print("[Setup] No API keys found. Running in demo mode (placeholder outputs).")
    print("[Setup] Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env for live LLM responses.")
    return None


def print_result(result: Any, indent: int = 2) -> None:
    """Pretty-print an agent result."""
    if hasattr(result, "output"):
        print(f"\n{'='*60}")
        print(f"Agent: {result.agent_name}")
        print(f"Task: {result.task}")
        print(f"Success: {result.success}")
        print(f"{'='*60}")
        print(json.dumps(result.output, indent=indent, default=str))
    else:
        print(json.dumps(result, indent=indent, default=str))


def print_agents_help() -> None:
    """Print all agents and their tasks."""
    print("\n  AVAILABLE AGENTS & TASKS")
    print("  " + "=" * 60)
    for agent_name, tasks in AGENT_TASKS.items():
        print(f"\n  {agent_name}")
        print("  " + "-" * 40)
        for task, desc in tasks.items():
            print(f"    {task:<25s} {desc}")
    print()


def interactive_mode(orchestrator: AgencyOrchestrator,
                     tracker: AgentTracker, content_queue: ContentQueue) -> None:
    """Run the agency in interactive mode."""
    print("\n" + "=" * 60)
    print("  AFFILIATE MARKETING AGENCY — AI Agent System")
    print("  On-Demand Agent Execution")
    print("=" * 60)
    print(f"\n  Niche: {orchestrator.config.selected_niche.value}")
    print(f"  Target: {orchestrator.config.revenue_target} tier")

    commands = """
  Commands:
    status              — View agency status
    agents              — List all agents and tasks
    tasks <agent>       — List tasks for a specific agent
    run <agent> <task>  — Run a specific agent task
    batch               — Run multiple tasks (enter JSON)
    integrations        — Check integration status
    dashboard / db      — View live agent dashboard
    queue               — List content awaiting review
    review <ID>         — View content item in detail
    approve <ID>        — Approve a content item
    reject <ID> [reason] — Reject content with feedback
    export              — Export approved content to file
    quit                — Exit
    """
    print(commands)

    while True:
        try:
            user_input = input("\nagency> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        parts = user_input.split()
        command = parts[0].lower()

        if command == "quit":
            print("Goodbye!")
            break
        elif command == "status":
            print_result(orchestrator.get_status())
        elif command == "agents":
            print_agents_help()
        elif command == "tasks" and len(parts) >= 2:
            tasks = orchestrator.list_tasks(parts[1])
            if "error" in tasks:
                print(f"  {tasks['error']}")
            else:
                print(f"\n  Tasks for {parts[1]}:")
                print("  " + "-" * 40)
                for task, desc in tasks.items():
                    print(f"    {task:<25s} {desc}")
                print()
        elif command == "integrations":
            print_integration_status()

        # ── Dashboard & Content Review commands ──
        elif command in ("dashboard", "db"):
            print(render_dashboard(tracker, content_queue, orchestrator.config))
        elif command == "queue":
            status_filter = parts[1] if len(parts) >= 2 else None
            print(render_queue_list(content_queue, status_filter))
        elif command == "review" and len(parts) >= 2:
            try:
                item_id = int(parts[1])
                item = content_queue.get(item_id)
                if item:
                    print(render_content_review(item))
                else:
                    print(f"  Content item #{item_id} not found.")
            except ValueError:
                print("  Usage: review <ID>")
        elif command == "approve" and len(parts) >= 2:
            try:
                item_id = int(parts[1])
                if content_queue.approve(item_id):
                    print(f"  Content #{item_id} APPROVED.")
                else:
                    print(f"  Content item #{item_id} not found.")
            except ValueError:
                print("  Usage: approve <ID>")
        elif command == "reject" and len(parts) >= 2:
            try:
                item_id = int(parts[1])
                feedback = " ".join(parts[2:]) if len(parts) > 2 else ""
                if content_queue.reject(item_id, feedback):
                    print(f"  Content #{item_id} REJECTED.{f' Feedback: {feedback}' if feedback else ''}")
                else:
                    print(f"  Content item #{item_id} not found.")
            except ValueError:
                print("  Usage: reject <ID> [reason]")
        elif command == "export":
            path = content_queue.export_approved()
            print(f"  Exported to: {path}")

        # ── Execution commands ──
        elif command == "run" and len(parts) >= 3:
            agent_name = parts[1]
            task = parts[2]
            context = {}
            if len(parts) > 3:
                for p in parts[3:]:
                    if "=" in p:
                        k, v = p.split("=", 1)
                        context[k] = v
            result = orchestrator.execute_task(agent_name, task, context or None)
            print_result(result)
        elif command == "batch":
            print("  Enter task list as JSON (one per line, empty line to run):")
            print('  Format: [{"agent": "...", "task": "...", "context": {...}}, ...]')
            lines = []
            while True:
                try:
                    line = input("  ... ")
                    if not line.strip():
                        break
                    lines.append(line)
                except (EOFError, KeyboardInterrupt):
                    break
            if lines:
                try:
                    tasks = json.loads("\n".join(lines))
                    results = orchestrator.run_batch(tasks)
                    for r in results:
                        print_result(r)
                except json.JSONDecodeError as e:
                    print(f"  Invalid JSON: {e}")
        else:
            print(f"Unknown command: {user_input}")
            print(commands)


def main() -> None:
    parser = argparse.ArgumentParser(description="Affiliate Marketing Agency — AI Agent System")
    parser.add_argument("--agent", type=str, help="Run a specific agent")
    parser.add_argument("--task", type=str, default="", help="Task for the agent")
    parser.add_argument("--agents", action="store_true", help="List all agents and tasks")
    parser.add_argument("--tasks", type=str, help="List tasks for a specific agent")
    parser.add_argument("--integrations", action="store_true", help="Check integration status")
    parser.add_argument("--niche", type=str, default="ai_saas_tools", help="Niche selection")
    parser.add_argument("--target", type=str, default="moderate", choices=["conservative", "moderate", "aggressive"])

    args, extra = parser.parse_known_args()

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Quick info commands
    if args.agents:
        print_agents_help()
        return

    if args.tasks:
        tasks = AGENT_TASKS.get(args.tasks)
        if tasks:
            print(f"\n  Tasks for {args.tasks}:")
            for task, desc in tasks.items():
                print(f"    {task:<25s} {desc}")
            print()
        else:
            print(f"  Unknown agent: {args.tasks}")
        return

    if args.integrations:
        print_integration_status()
        return

    # Configure
    niche_map = {n.value: n for n in Niche}
    selected_niche = niche_map.get(args.niche, Niche.AI_SAAS)

    config = AgencyConfig(
        selected_niche=selected_niche,
        revenue_target=args.target,
    )

    llm_client = setup_llm_client()

    # Initialize SQLite persistence
    from utils.persistence import init_db
    db_conn = init_db()
    print(f"[Setup] Database initialized at data/agency.db")

    # Initialize dashboard components with persistence
    tracker = AgentTracker(db_conn=db_conn)
    content_queue = ContentQueue(db_conn=db_conn)

    orchestrator = AgencyOrchestrator(config, llm_client, tracker=tracker,
                                      content_queue=content_queue, db_conn=db_conn)

    if args.agent and args.task:
        # Parse extra context args: key=value pairs
        context = {}
        for p in extra:
            if "=" in p:
                k, v = p.split("=", 1)
                context[k] = v
        result = orchestrator.execute_task(args.agent, args.task, context or None)
        print_result(result)
    else:
        interactive_mode(orchestrator, tracker, content_queue)


if __name__ == "__main__":
    main()
