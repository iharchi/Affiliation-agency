"""
Sprint Workflow
Manages the 4-week sprint structure of the 30-day business plan.
Each sprint has defined themes, deliverables, and success criteria.
"""

from dataclasses import dataclass, field
from typing import Any

from config.settings import AgencyConfig


@dataclass
class SprintMilestone:
    name: str
    description: str
    day: int
    completed: bool = False


@dataclass
class Sprint:
    week: int
    theme: str
    goal: str
    milestones: list[SprintMilestone] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)
    kpis: dict[str, str] = field(default_factory=dict)


SPRINTS = [
    Sprint(
        week=1,
        theme="Foundation & First Content",
        goal="Set up all systems and publish first content pieces",
        milestones=[
            SprintMilestone("Niche Selected", "Final niche chosen with keyword research", 2),
            SprintMilestone("Programs Active", "5+ affiliate accounts signed up", 2),
            SprintMilestone("Website Live", "Blog/website with About page published", 3),
            SprintMilestone("Link Hub Created", "Linktree or Stan Store with all affiliate links", 3),
            SprintMilestone("First Article", "1 SEO listicle published (1,500-2,000 words)", 5),
            SprintMilestone("First Videos", "3-5 short-form videos published", 6),
            SprintMilestone("Email System Live", "Lead magnet + landing page capturing emails", 7),
        ],
        deliverables=[
            "5+ affiliate accounts active",
            "Live website with About page",
            "Link-in-bio hub for affiliate links",
            "1 published SEO article (1,500-2,000 words)",
            "3-5 TikToks / YouTube Shorts published",
            "Email capture system live with lead magnet",
        ],
        kpis={
            "affiliate_accounts": "5+",
            "articles_published": "1",
            "videos_published": "3-5",
            "email_system": "live",
        },
    ),
    Sprint(
        week=2,
        theme="Scale Content & Build Audience",
        goal="Triple content output and start building engaged audience",
        milestones=[
            SprintMilestone("Product Review", "In-depth review of top product published", 9),
            SprintMilestone("Comparison Post", "Tool A vs Tool B comparison live", 10),
            SprintMilestone("Video Library", "7-10 total short-form videos published", 12),
            SprintMilestone("Tutorial Content", "How-to tutorial or case study published", 13),
            SprintMilestone("Community Presence", "3+ value-driven posts on Reddit/Twitter", 14),
        ],
        deliverables=[
            "1 in-depth review article",
            "1 comparison article",
            "7-10 total shorts published",
            "1 tutorial/case study article",
            "3+ community posts with soft affiliate mentions",
        ],
        kpis={
            "total_articles": "4+",
            "total_videos": "10+",
            "community_posts": "3+",
            "first_affiliate_clicks": "target: 50+",
        },
    ),
    Sprint(
        week=3,
        theme="Optimize & Amplify",
        goal="Analyze data, double down on winners, and expand reach",
        milestones=[
            SprintMilestone("Analytics Review", "Data-driven content pivot decisions made", 16),
            SprintMilestone("Winning Format", "3+ pieces in top-performing format", 17),
            SprintMilestone("Collaboration", "1 guest post or creator collab published", 19),
            SprintMilestone("Resources Page", "Evergreen resources page live on site", 20),
            SprintMilestone("First Email Campaign", "First value email sent to subscribers", 21),
        ],
        deliverables=[
            "Data-driven content pivot decisions",
            "3+ pieces in top-performing content format",
            "1 guest post or collaboration",
            "Evergreen resources page live",
            "First email campaign sent to list",
        ],
        kpis={
            "traffic_growth": "50%+ week-over-week",
            "email_subscribers": "50+",
            "affiliate_clicks": "100+",
            "first_conversions": "target: 1-5",
        },
    ),
    Sprint(
        week=4,
        theme="Push for Revenue & Systematize",
        goal="Maximize conversions and build repeatable systems",
        milestones=[
            SprintMilestone("Buyer Intent Content", "2 high-intent articles published", 23),
            SprintMilestone("YouTube Long-Form", "1 YouTube video (8-15 min) published", 25),
            SprintMilestone("Content Refreshed", "Best content updated with improved CTAs", 27),
            SprintMilestone("Production System", "Repeatable weekly content workflow documented", 29),
            SprintMilestone("Month 1 Audit", "Complete revenue, traffic, and conversion report", 30),
        ],
        deliverables=[
            "2 buyer-intent articles",
            "1 YouTube long-form video",
            "Refreshed content with improved CTAs",
            "Documented weekly production workflow",
            "Month 1 report + Month 2 plan",
        ],
        kpis={
            "monthly_revenue": "$50-$2,000+ (tier dependent)",
            "total_content_pieces": "20+",
            "email_subscribers": "100+",
            "affiliate_clicks": "200+",
            "conversion_rate": "1-5%",
        },
    ),
]


class SprintWorkflow:
    """Manages sprint execution and milestone tracking."""

    def __init__(self, config: AgencyConfig):
        self.config = config
        self.sprints = [Sprint(
            week=s.week,
            theme=s.theme,
            goal=s.goal,
            milestones=[SprintMilestone(m.name, m.description, m.day) for m in s.milestones],
            deliverables=list(s.deliverables),
            kpis=dict(s.kpis),
        ) for s in SPRINTS]

    def get_current_sprint(self) -> Sprint:
        week = self.config.current_week
        idx = min(week - 1, len(self.sprints) - 1)
        return self.sprints[idx]

    def complete_milestone(self, week: int, milestone_name: str) -> bool:
        sprint = self.sprints[week - 1] if week <= len(self.sprints) else None
        if not sprint:
            return False
        for m in sprint.milestones:
            if m.name == milestone_name:
                m.completed = True
                return True
        return False

    def get_progress(self) -> dict[str, Any]:
        progress = {}
        for sprint in self.sprints:
            total = len(sprint.milestones)
            completed = sum(1 for m in sprint.milestones if m.completed)
            progress[f"week_{sprint.week}"] = {
                "theme": sprint.theme,
                "milestones_total": total,
                "milestones_completed": completed,
                "progress_pct": round(completed / total * 100, 1) if total > 0 else 0,
                "pending": [m.name for m in sprint.milestones if not m.completed],
            }
        return progress

    def get_today_focus(self) -> dict[str, Any]:
        day = self.config.current_day
        sprint = self.get_current_sprint()

        # Find milestones due today or overdue
        due = [m for m in sprint.milestones if m.day <= day and not m.completed]
        upcoming = [m for m in sprint.milestones if m.day > day][:3]

        return {
            "day": day,
            "week": sprint.week,
            "theme": sprint.theme,
            "overdue_milestones": [{"name": m.name, "due_day": m.day} for m in due],
            "upcoming_milestones": [{"name": m.name, "due_day": m.day} for m in upcoming],
            "sprint_goal": sprint.goal,
        }
