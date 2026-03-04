"""
Agency Orchestrator
Central coordinator that manages all agents, routes tasks, orchestrates the 30-day
business plan workflow, and ensures agents collaborate effectively.
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


class AgencyOrchestrator:
    """
    Central orchestrator for the Affiliate Marketing Agency.
    Coordinates all agents through the 30-day business plan.
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

    def run_day(self, day: int) -> dict[str, Any]:
        """Execute all tasks for a specific day in the 30-day plan."""
        self.config.current_day = day
        self.config.current_week = (day - 1) // 7 + 1

        self._log(f"=== DAY {day} (Week {self.config.current_week}) ===")

        day_plan = self._get_day_tasks(day)
        results = {}

        for task_name, task_config in day_plan.items():
            agent_name = task_config["agent"]
            agent_task = task_config["task"]
            context = task_config.get("context", {})

            self._log(f"Running: {task_name} → {agent_name}.{agent_task}")

            # Track agent status
            if self.tracker:
                self.tracker.mark_running(agent_name, agent_task)

            agent = self.agents[agent_name]
            result = agent.execute(agent_task, context)
            results[task_name] = result
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
            if self.content_queue and agent_task in CONTENT_TASKS:
                body = ""
                title = task_name
                content_type = agent_task.replace("write_", "")
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
                    title = result.output.get("topic", result.output.get("product", result.output.get("offer", task_name)))
                    content_type = result.output.get("type", content_type)
                elif isinstance(result.output, str):
                    body = result.output
                self.content_queue.add(
                    title=str(title) or task_name,
                    content_type=str(content_type),
                    agent=agent_name,
                    task=agent_task,
                    body=str(body),
                    day=day,
                )

        return {
            "day": day,
            "week": self.config.current_week,
            "tasks_completed": len(results),
            "results": {k: v.output for k, v in results.items()},
        }

    def run_week(self, week: int) -> dict[str, Any]:
        """Execute all tasks for a specific week."""
        self._log(f"=== WEEK {week} ===")
        start_day = (week - 1) * 7 + 1
        end_day = min(start_day + 6, 30)

        weekly_results = {}
        for day in range(start_day, end_day + 1):
            weekly_results[f"day_{day}"] = self.run_day(day)

        # Generate weekly report
        report = self.agents["seo_analytics"].execute(
            "weekly_report", {"week": week}
        )
        weekly_results["weekly_report"] = report.output

        return weekly_results

    def run_full_plan(self) -> dict[str, Any]:
        """Execute the complete 30-day business plan."""
        self._log("=== STARTING 30-DAY AFFILIATE MARKETING PLAN ===")

        results = {}
        for week in range(1, 5):
            results[f"week_{week}"] = self.run_week(week)

        # Final monthly report
        monthly_report = self.agents["revenue_tracking"].execute("monthly_report")
        results["monthly_report"] = monthly_report.output

        self._log("=== 30-DAY PLAN COMPLETE ===")
        return results

    def execute_task(self, agent_name: str, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        """Execute a specific task on a specific agent."""
        if agent_name not in self.agents:
            return AgentResult(
                agent_name=agent_name,
                task=task,
                output=None,
                success=False,
                errors=[f"Unknown agent: {agent_name}. Available: {list(self.agents.keys())}"],
            )

        result = self.agents[agent_name].execute(task, context)
        self.execution_log.append(result)
        return result

    def get_status(self) -> dict[str, Any]:
        """Get the current status of the agency."""
        return {
            "current_day": self.config.current_day,
            "current_week": self.config.current_week,
            "selected_niche": self.config.selected_niche.value,
            "revenue_target": self.config.revenue_target,
            "agents": list(self.agents.keys()),
            "tasks_completed": len(self.execution_log),
            "primary_platforms": [p.value for p in self.config.primary_platforms],
            "secondary_platforms": [p.value for p in self.config.secondary_platforms],
        }

    def _get_day_tasks(self, day: int) -> dict[str, dict[str, Any]]:
        """Map each day to its specific tasks from the 30-day plan."""

        day_tasks: dict[int, dict[str, dict[str, Any]]] = {
            # Week 1: Foundation & First Content
            1: {
                "niche_analysis": {"agent": "niche_research", "task": "analyze_all"},
                "niche_deep_dive": {"agent": "niche_research", "task": "deep_dive", "context": {"niche": self.config.selected_niche}},
            },
            2: {
                "keyword_research": {"agent": "niche_research", "task": "find_keywords", "context": {"niche": self.config.selected_niche}},
                "program_signup": {"agent": "affiliate_scout", "task": "signup_checklist"},
                "program_portfolio": {"agent": "affiliate_scout", "task": "build_portfolio"},
            },
            3: {
                "content_calendar": {"agent": "content_strategy", "task": "build_calendar"},
                "platform_strategy": {"agent": "content_strategy", "task": "platform_strategy"},
                "email_setup": {"agent": "email_marketing", "task": "setup"},
            },
            4: {
                "listicle_brief": {"agent": "content_strategy", "task": "content_brief", "context": {"topic": "Best tools", "format": ContentFormat.LISTICLE}},
                "write_listicle": {"agent": "content_creation", "task": "write_listicle", "context": {"topic": ""}},
            },
            5: {
                "seo_optimize_listicle": {"agent": "seo_analytics", "task": "keyword_research"},
                "video_scripts": {"agent": "content_creation", "task": "write_video_script", "context": {"topic": "Tool demo", "platform": Platform.YOUTUBE_SHORTS}},
            },
            6: {
                "more_video_scripts": {"agent": "content_creation", "task": "write_video_script", "context": {"topic": "Quick tips", "platform": Platform.TIKTOK}},
                "social_posts": {"agent": "content_creation", "task": "write_social_post", "context": {"topic": "Launch content", "platform": Platform.TWITTER}},
            },
            7: {
                "lead_magnet": {"agent": "email_marketing", "task": "lead_magnet", "context": {"magnet_type": "checklist"}},
                "landing_page": {"agent": "email_marketing", "task": "landing_page", "context": {"offer": "Free toolkit"}},
                "posting_schedule": {"agent": "social_distribution", "task": "schedule"},
            },
            # Week 2: Scale Content & Build Audience
            8: {
                "review_brief": {"agent": "content_strategy", "task": "content_brief", "context": {"topic": "Top pick review", "format": ContentFormat.REVIEW}},
                "write_review": {"agent": "content_creation", "task": "write_review", "context": {"product": ""}},
            },
            9: {
                "comparison_article": {"agent": "content_creation", "task": "write_comparison", "context": {"product_a": "", "product_b": ""}},
            },
            10: {
                "daily_videos": {"agent": "content_creation", "task": "write_video_script", "context": {"topic": "Tool comparison", "platform": Platform.YOUTUBE_SHORTS}},
                "distribution": {"agent": "social_distribution", "task": "distribute", "context": {"content_title": "Review article"}},
            },
            11: {
                "more_videos": {"agent": "content_creation", "task": "write_video_script", "context": {"topic": "Tips and tricks", "platform": Platform.TIKTOK}},
                "viral_hooks": {"agent": "social_distribution", "task": "viral_hooks", "context": {"topic": ""}},
            },
            12: {
                "tutorial_article": {"agent": "content_creation", "task": "write_tutorial", "context": {"tool": "", "goal": ""}},
            },
            13: {
                "case_study": {"agent": "content_creation", "task": "write_case_study", "context": {"product": "", "duration": "2 weeks"}},
            },
            14: {
                "reddit_engagement": {"agent": "social_distribution", "task": "engage", "context": {"platform": Platform.REDDIT}},
                "twitter_threads": {"agent": "content_creation", "task": "write_social_post", "context": {"topic": "Value thread", "platform": Platform.TWITTER}},
                "kpi_check": {"agent": "seo_analytics", "task": "track_kpis", "context": {"metrics": {}}},
            },
            # Week 3: Optimize & Amplify
            15: {
                "analytics_review": {"agent": "seo_analytics", "task": "track_kpis", "context": {"metrics": {}}},
                "revenue_check": {"agent": "revenue_tracking", "task": "dashboard"},
            },
            16: {
                "optimization": {"agent": "revenue_tracking", "task": "optimize"},
                "content_repurpose": {"agent": "social_distribution", "task": "repurpose", "context": {"original_content": "", "source_format": "blog"}},
            },
            17: {
                "double_down_content": {"agent": "content_creation", "task": "write_listicle", "context": {"topic": "Advanced tools"}},
            },
            18: {
                "competitor_analysis": {"agent": "seo_analytics", "task": "competitor_seo", "context": {"competitor_url": ""}},
            },
            19: {
                "guest_post_content": {"agent": "content_creation", "task": "write_tutorial", "context": {"tool": "", "goal": ""}},
            },
            20: {
                "resources_page": {"agent": "content_creation", "task": "write_listicle", "context": {"topic": "Complete resources guide"}},
            },
            21: {
                "first_email": {"agent": "email_marketing", "task": "newsletter", "context": {"topic": "First newsletter"}},
                "welcome_sequence": {"agent": "email_marketing", "task": "welcome_sequence"},
                "weekly_report_3": {"agent": "seo_analytics", "task": "weekly_report", "context": {"week": 3}},
            },
            # Week 4: Push for Revenue & Systematize
            22: {
                "buyer_intent_1": {"agent": "content_creation", "task": "write_review", "context": {"product": ""}},
            },
            23: {
                "buyer_intent_2": {"agent": "content_creation", "task": "write_comparison", "context": {"product_a": "", "product_b": ""}},
            },
            24: {
                "youtube_long": {"agent": "content_creation", "task": "write_video_script", "context": {"topic": "Complete review", "platform": Platform.YOUTUBE_LONG}},
            },
            25: {
                "seo_audit": {"agent": "seo_analytics", "task": "optimize_content", "context": {"content": "", "target_keyword": ""}},
                "link_audit": {"agent": "seo_analytics", "task": "link_audit", "context": {"links": []}},
            },
            26: {
                "content_refresh": {"agent": "social_distribution", "task": "repurpose", "context": {"original_content": "best performing", "source_format": "blog"}},
            },
            27: {
                "email_campaign": {"agent": "email_marketing", "task": "newsletter", "context": {"topic": "Best picks roundup"}},
                "distribution_push": {"agent": "social_distribution", "task": "distribute", "context": {"content_title": "Best content reshare"}},
            },
            28: {
                "program_analysis": {"agent": "revenue_tracking", "task": "program_performance"},
                "forecast": {"agent": "revenue_tracking", "task": "forecast"},
            },
            29: {
                "portfolio_optimize": {"agent": "affiliate_scout", "task": "optimize_portfolio"},
                "content_system": {"agent": "content_strategy", "task": "weekly_plan", "context": {"week": 5}},
            },
            30: {
                "monthly_report": {"agent": "revenue_tracking", "task": "monthly_report"},
                "final_kpis": {"agent": "seo_analytics", "task": "track_kpis", "context": {"metrics": {}}},
                "month_2_plan": {"agent": "content_strategy", "task": "build_calendar"},
            },
        }

        return day_tasks.get(day, {
            "daily_content": {"agent": "content_creation", "task": "write_social_post", "context": {"topic": f"Day {day} content", "platform": Platform.TWITTER}},
        })

    def _log(self, message: str) -> None:
        print(f"[Orchestrator] {message}")
