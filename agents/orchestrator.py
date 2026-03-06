"""
Agency Orchestrator
Central coordinator that manages all agents and routes on-demand tasks.
Agents run when you call them — no day-gating, no schedule.
"""

from typing import Any

from .base_agent import BaseAgent, AgentResult
from .niche_research_agent import NicheResearchAgent
from .affiliate_scout_agent import AffiliateProgramScoutAgent
from .content_strategy_agent import ContentStrategyAgent
from .content_creation_agent import ContentCreationAgent
from .seo_analytics_agent import SEOAnalyticsAgent
from .social_distribution_agent import SocialDistributionAgent
from .email_marketing_agent import EmailMarketingAgent
from .revenue_tracking_agent import RevenueTrackingAgent
from config.settings import AgencyConfig, Niche, ContentFormat, Platform


# Content-producing tasks that should be queued for review
CONTENT_TASKS = {
    "write_listicle", "write_review", "write_comparison", "write_tutorial",
    "write_case_study", "write_video_script", "write_social_post", "write_email",
    "lead_magnet", "landing_page", "newsletter", "welcome_sequence",
}

# Available tasks per agent for discoverability
AGENT_TASKS = {
    "niche_research": {
        "analyze_all": "Score all niches across opportunity, competition, commissions",
        "deep_dive": "Deep analysis of a specific niche (context: niche=<Niche>)",
        "find_keywords": "Generate buyer-intent keywords (context: niche=<Niche>)",
        "competitor_analysis": "Analyze competitor landscape",
    },
    "content_strategy": {
        "build_calendar": "Build a content calendar",
        "weekly_plan": "Create a weekly content plan (context: week=<int>)",
        "content_brief": "Detailed brief for a content piece (context: topic=<str>, format=<ContentFormat>)",
        "platform_strategy": "Multi-platform distribution strategy",
    },
    "affiliate_scout": {
        "build_portfolio": "Build optimized affiliate program portfolio",
        "evaluate_program": "Deep evaluation of one program (context: program=<str>)",
        "find_programs": "Discover programs for current niche",
        "optimize_portfolio": "Optimize portfolio based on performance",
        "signup_checklist": "Generate signup checklist for programs",
    },
    "content_creation": {
        "write_listicle": "Best X for Y article (context: topic=<str>)",
        "write_review": "Product review (context: product=<str>)",
        "write_comparison": "Product A vs B comparison (context: product_a=<str>, product_b=<str>)",
        "write_tutorial": "How-to guide (context: tool=<str>, goal=<str>)",
        "write_case_study": "Experience article (context: product=<str>, duration=<str>)",
        "write_video_script": "Video script (context: topic=<str>, platform=<Platform>)",
        "write_social_post": "Social media post (context: topic=<str>, platform=<Platform>)",
        "write_email": "Email marketing copy (context: topic=<str>)",
    },
    "seo_analytics": {
        "keyword_research": "Keyword research with clustering",
        "optimize_content": "SEO optimize content (context: content=<str>, target_keyword=<str>)",
        "track_kpis": "Track and analyze KPIs (context: metrics=<dict>)",
        "weekly_report": "Weekly performance report (context: week=<int>)",
        "competitor_seo": "Competitor SEO analysis (context: competitor_url=<str>)",
        "link_audit": "Audit affiliate link placements (context: links=<list>)",
    },
    "social_distribution": {
        "distribute": "Distribution plan for content (context: content_title=<str>)",
        "repurpose": "Repurpose for multiple platforms (context: original_content=<str>, source_format=<str>)",
        "engage": "Community engagement plan (context: platform=<Platform>)",
        "schedule": "Weekly posting schedule",
        "viral_hooks": "Generate attention-grabbing hooks (context: topic=<str>)",
    },
    "email_marketing": {
        "setup": "Set up email marketing system",
        "lead_magnet": "Create lead magnet (context: magnet_type=<str>)",
        "welcome_sequence": "7-email welcome sequence",
        "newsletter": "Plan newsletter issue (context: topic=<str>)",
        "landing_page": "Write landing page copy (context: offer=<str>)",
    },
    "revenue_tracking": {
        "dashboard": "Revenue dashboard overview",
        "log_revenue": "Log revenue event (context: event=<dict>)",
        "forecast": "Revenue forecast from current data",
        "optimize": "Optimization recommendations",
        "monthly_report": "Comprehensive monthly report",
        "program_performance": "Analyze performance by program",
    },
}


class AgencyOrchestrator:
    """
    Central orchestrator for the Affiliate Marketing Agency.
    All agents run on-demand — call execute_task() with any agent and task.
    """

    def __init__(self, config: AgencyConfig | None = None, llm_client: Any = None,
                 tracker: Any = None, content_queue: Any = None):
        self.config = config or AgencyConfig()
        self.llm_client = llm_client
        self.tracker = tracker
        self.content_queue = content_queue

        # Initialize all agents
        self.agents = {
            "niche_research": NicheResearchAgent(self.config, llm_client),
            "affiliate_scout": AffiliateProgramScoutAgent(self.config, llm_client),
            "content_strategy": ContentStrategyAgent(self.config, llm_client),
            "content_creation": ContentCreationAgent(self.config, llm_client),
            "seo_analytics": SEOAnalyticsAgent(self.config, llm_client),
            "social_distribution": SocialDistributionAgent(self.config, llm_client),
            "email_marketing": EmailMarketingAgent(self.config, llm_client),
            "revenue_tracking": RevenueTrackingAgent(self.config, llm_client),
        }

        self.execution_log: list[AgentResult] = []

    def execute_task(self, agent_name: str, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        """Execute a specific task on a specific agent. This is the primary interface."""
        if agent_name not in self.agents:
            return AgentResult(
                agent_name=agent_name,
                task=task,
                output=None,
                success=False,
                errors=[f"Unknown agent: {agent_name}. Available: {list(self.agents.keys())}"],
            )

        if task not in AGENT_TASKS.get(agent_name, {}):
            available = list(AGENT_TASKS.get(agent_name, {}).keys())
            return AgentResult(
                agent_name=agent_name,
                task=task,
                output=None,
                success=False,
                errors=[f"Unknown task: {task}. Available for {agent_name}: {available}"],
            )

        self._log(f"Running: {agent_name}.{task}")

        # Track agent status
        if self.tracker:
            self.tracker.mark_running(agent_name, task)

        agent = self.agents[agent_name]
        result = agent.execute(task, context)
        self.execution_log.append(result)

        # Update tracker
        if self.tracker:
            if result.success:
                preview = ""
                if isinstance(result.output, dict):
                    preview = result.output.get("topic", result.output.get("type", str(result.output)[:80]))
                elif isinstance(result.output, str):
                    preview = result.output[:80]
                self.tracker.mark_done(agent_name, str(preview))
            else:
                self.tracker.mark_error(agent_name, "; ".join(result.errors))

        # Queue content-producing tasks for review
        if self.content_queue and task in CONTENT_TASKS:
            self._queue_content(result, agent_name, task)

        return result

    def run_batch(self, tasks: list[dict[str, Any]]) -> list[AgentResult]:
        """
        Run multiple agent tasks in sequence.
        Each item: {"agent": "agent_name", "task": "task_name", "context": {...}}
        """
        results = []
        for task_spec in tasks:
            result = self.execute_task(
                agent_name=task_spec["agent"],
                task=task_spec["task"],
                context=task_spec.get("context"),
            )
            results.append(result)
        return results

    def get_status(self) -> dict[str, Any]:
        """Get the current status of the agency."""
        return {
            "selected_niche": self.config.selected_niche.value,
            "revenue_target": self.config.revenue_target,
            "agents": list(self.agents.keys()),
            "tasks_completed": len(self.execution_log),
            "primary_platforms": [p.value for p in self.config.primary_platforms],
            "secondary_platforms": [p.value for p in self.config.secondary_platforms],
        }

    def list_agents(self) -> dict[str, list[str]]:
        """List all agents and their available tasks."""
        return {name: list(tasks.keys()) for name, tasks in AGENT_TASKS.items()}

    def list_tasks(self, agent_name: str) -> dict[str, str]:
        """List available tasks for a specific agent with descriptions."""
        if agent_name not in AGENT_TASKS:
            return {"error": f"Unknown agent: {agent_name}. Available: {list(AGENT_TASKS.keys())}"}
        return AGENT_TASKS[agent_name]

    def _queue_content(self, result: AgentResult, agent_name: str, task: str) -> None:
        """Add content-producing task output to the review queue."""
        body = ""
        title = task
        content_type = task.replace("write_", "")
        if isinstance(result.output, dict):
            body = result.output.get("content", "")
            if not body:
                body = result.output.get("script", "")
            if not body:
                body = result.output.get("lead_magnet", "")
            if not body:
                body = result.output.get("landing_page_copy", "")
            if not body:
                body = result.output.get("welcome_sequence", "")
            if not body:
                body = result.output.get("newsletter_plan", "")
            if not body:
                body = str(result.output)
            title = result.output.get("topic", result.output.get("product", result.output.get("offer", task)))
            content_type = result.output.get("type", content_type)
        elif isinstance(result.output, str):
            body = result.output
        self.content_queue.add(
            title=str(title) or task,
            content_type=str(content_type),
            agent=agent_name,
            task=task,
            body=str(body),
        )

    def _log(self, message: str) -> None:
        print(f"[Orchestrator] {message}")
