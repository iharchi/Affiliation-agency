"""
Affiliate Marketing Agency — Main Entry Point
Run the 30-day affiliate marketing business plan with AI agents.

Usage:
    python main.py                          # Interactive mode
    python main.py --day 1                  # Run a specific day
    python main.py --week 1                 # Run a full week
    python main.py --full                   # Run the complete 30-day plan
    python main.py --agent niche_research --task analyze_all  # Run specific agent task
"""

import argparse
import json
import os
from typing import Any

from config.settings import AgencyConfig, Niche, Platform
from agents.orchestrator import AgencyOrchestrator
from workflows.sprint_workflow import SprintWorkflow
from dashboard import (
    AgentTracker, ContentQueue,
    render_dashboard, render_content_review, render_queue_list,
)


def setup_llm_client() -> Any:
    """Set up the LLM client based on available API keys."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            return anthropic.Anthropic(api_key=api_key)
        except ImportError:
            print("[Setup] anthropic package not installed. Run: pip install anthropic")

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
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


def interactive_mode(orchestrator: AgencyOrchestrator, workflow: SprintWorkflow,
                     tracker: AgentTracker, content_queue: ContentQueue) -> None:
    """Run the agency in interactive mode."""
    print("\n" + "=" * 60)
    print("  AFFILIATE MARKETING AGENCY — AI Agent System")
    print("  30-Day Business Plan: Zero to First Commission")
    print("=" * 60)
    print(f"\n  Niche: {orchestrator.config.selected_niche.value}")
    print(f"  Target: {orchestrator.config.revenue_target} tier")
    print(f"  Day: {orchestrator.config.current_day} | Week: {orchestrator.config.current_week}")

    commands = """
  Commands:
    status          — View agency status
    day <N>         — Run day N tasks
    week <N>        — Run week N tasks
    full            — Run complete 30-day plan
    agent <name> <task> — Run a specific agent task
    progress        — View sprint progress
    focus           — View today's focus
    agents          — List all agents
    dashboard / db  — View live agent dashboard
    queue           — List content awaiting review
    review <ID>     — View content item in detail
    approve <ID>    — Approve a content item
    reject <ID> [reason] — Reject content with feedback
    export          — Export approved content to file
    quit            — Exit
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
        elif command == "progress":
            print_result(workflow.get_progress())
        elif command == "focus":
            print_result(workflow.get_today_focus())
        elif command == "agents":
            for name in orchestrator.agents:
                agent = orchestrator.agents[name]
                print(f"  {name:25s} — {agent.__class__.__name__}")

        # ── Dashboard & Content Review commands ──
        elif command in ("dashboard", "db"):
            print(render_dashboard(tracker, content_queue, orchestrator.config, workflow))
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
        elif command == "day" and len(parts) >= 2:
            try:
                day = int(parts[1])
                result = orchestrator.run_day(day)
                print_result(result)
            except ValueError:
                print("Usage: day <number>")
        elif command == "week" and len(parts) >= 2:
            try:
                week = int(parts[1])
                result = orchestrator.run_week(week)
                print_result(result)
            except ValueError:
                print("Usage: week <number>")
        elif command == "full":
            print("Running complete 30-day plan... This may take a while.")
            result = orchestrator.run_full_plan()
            print_result(result)
        elif command == "agent" and len(parts) >= 3:
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
        else:
            print(f"Unknown command: {user_input}")
            print(commands)


def main() -> None:
    parser = argparse.ArgumentParser(description="Affiliate Marketing Agency — AI Agent System")
    parser.add_argument("--day", type=int, help="Run a specific day (1-30)")
    parser.add_argument("--week", type=int, help="Run a specific week (1-4)")
    parser.add_argument("--full", action="store_true", help="Run the complete 30-day plan")
    parser.add_argument("--agent", type=str, help="Run a specific agent")
    parser.add_argument("--task", type=str, default="", help="Task for the agent")
    parser.add_argument("--niche", type=str, default="ai_saas_tools", help="Niche selection")
    parser.add_argument("--target", type=str, default="moderate", choices=["conservative", "moderate", "aggressive"])

    args = parser.parse_args()

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Configure
    niche_map = {n.value: n for n in Niche}
    selected_niche = niche_map.get(args.niche, Niche.AI_SAAS)

    config = AgencyConfig(
        selected_niche=selected_niche,
        revenue_target=args.target,
    )

    llm_client = setup_llm_client()

    # Initialize dashboard components
    tracker = AgentTracker()
    content_queue = ContentQueue()

    orchestrator = AgencyOrchestrator(config, llm_client, tracker=tracker, content_queue=content_queue)
    workflow = SprintWorkflow(config)

    if args.day:
        result = orchestrator.run_day(args.day)
        print_result(result)
    elif args.week:
        result = orchestrator.run_week(args.week)
        print_result(result)
    elif args.full:
        result = orchestrator.run_full_plan()
        print_result(result)
    elif args.agent and args.task:
        result = orchestrator.execute_task(args.agent, args.task)
        print_result(result)
    else:
        interactive_mode(orchestrator, workflow, tracker, content_queue)


if __name__ == "__main__":
    main()
