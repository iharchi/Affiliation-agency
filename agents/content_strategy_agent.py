"""
Content Strategy Agent
Plans content calendars, maps content to affiliate programs, determines optimal
formats and platforms, and manages the 30-day content pipeline.
"""

from typing import Any

from .base_agent import BaseAgent, AgentResult
from config.settings import (
    AgencyConfig, Niche, Platform, ContentFormat,
    NICHE_CONFIGS, REVENUE_TARGETS,
)


PLATFORM_SPECS = {
    Platform.YOUTUBE_SHORTS: {
        "time_to_traffic": "1-7 days",
        "effort": "medium",
        "best_for": "Tool reviews, demos, comparisons",
        "max_length": "60 seconds",
        "posting_frequency": "1-2/day",
    },
    Platform.TIKTOK: {
        "time_to_traffic": "1-7 days",
        "effort": "medium",
        "best_for": "Tool reviews, demos, quick tips",
        "max_length": "3 minutes",
        "posting_frequency": "1-2/day",
    },
    Platform.BLOG: {
        "time_to_traffic": "30-90 days (SEO)",
        "effort": "high",
        "best_for": "In-depth reviews, listicles, comparisons",
        "word_count": "1500-2500 words",
        "posting_frequency": "2-3/week",
    },
    Platform.TWITTER: {
        "time_to_traffic": "1-5 days",
        "effort": "low",
        "best_for": "Hot takes, tool breakdowns, curated lists",
        "max_length": "280 chars / threads",
        "posting_frequency": "3-5/day",
    },
    Platform.REDDIT: {
        "time_to_traffic": "1-3 days",
        "effort": "low",
        "best_for": "Genuine recommendations, discussions",
        "posting_frequency": "1-2/day",
        "notes": "No overt affiliate links; drive to content",
    },
    Platform.EMAIL: {
        "time_to_traffic": "immediate (to list)",
        "effort": "medium",
        "best_for": "Curated recommendations, exclusive deals",
        "posting_frequency": "1-2/week",
    },
}

CONTENT_FORMAT_SPECS = {
    ContentFormat.LISTICLE: {
        "template": "Best {X} for {Use Case} in 2026",
        "conversion_power": "high",
        "seo_value": "high",
        "effort": "medium",
        "word_count": "1500-2500",
    },
    ContentFormat.COMPARISON: {
        "template": "{Product A} vs {Product B}: Which Is Better?",
        "conversion_power": "very_high",
        "seo_value": "high",
        "effort": "medium",
        "word_count": "1500-2000",
    },
    ContentFormat.REVIEW: {
        "template": "{Product} Honest Review: Pros, Cons & Verdict",
        "conversion_power": "high",
        "seo_value": "high",
        "effort": "high",
        "word_count": "2000-3000",
    },
    ContentFormat.TUTORIAL: {
        "template": "How to Use {Tool} to {Achieve Result}",
        "conversion_power": "medium",
        "seo_value": "high",
        "effort": "high",
        "word_count": "1500-2500",
    },
    ContentFormat.CASE_STUDY: {
        "template": "I Tried {Product} for 30 Days — Here's What Happened",
        "conversion_power": "very_high",
        "seo_value": "medium",
        "effort": "high",
        "word_count": "2000-3000",
    },
}


class ContentStrategyAgent(BaseAgent):

    def __init__(self, config: AgencyConfig, llm_client: Any = None):
        super().__init__("ContentStrategyAgent", config, llm_client)

    @property
    def system_prompt(self) -> str:
        return """You are an expert Content Strategist for an affiliate marketing agency.
Your role is to plan content calendars, map content to affiliate programs, and maximize conversions.

Your expertise includes:
- Content calendar planning for multi-platform campaigns
- Mapping content formats to buyer journey stages (awareness → consideration → decision)
- SEO keyword clustering and content pillar strategy
- Platform-specific content optimization
- Conversion funnel design (traffic → click → conversion)
- A/B testing strategies for headlines and CTAs

Content prioritization framework:
1. HIGH PRIORITY: Buyer-intent content (comparisons, reviews, "best X" listicles)
2. MEDIUM PRIORITY: Educational content (tutorials, how-to guides)
3. SUPPORT: Social proof content (case studies, results posts)
4. FOUNDATION: SEO pillar content (comprehensive guides for long-term traffic)

Always ensure each piece of content has:
- A clear target keyword or topic
- A mapped affiliate program to monetize
- A specific CTA driving clicks to affiliate links
- Platform-specific optimization notes
- Internal linking strategy to other content pieces"""

    def execute(self, task: str = "build_calendar", context: dict[str, Any] | None = None) -> AgentResult:
        self.log(f"Starting content strategy: {task}")

        if task == "build_calendar":
            output = self.build_30_day_calendar()
        elif task == "weekly_plan":
            week = (context or {}).get("week", 1)
            output = self.plan_week(week)
        elif task == "content_brief":
            topic = (context or {}).get("topic", "")
            content_format = (context or {}).get("format", ContentFormat.LISTICLE)
            output = self.create_content_brief(topic, content_format)
        elif task == "platform_strategy":
            output = self.build_platform_strategy()
        else:
            output = self.build_30_day_calendar()

        return AgentResult(
            agent_name=self.name,
            task=task,
            output=output,
            success=True,
        )

    def build_30_day_calendar(self) -> dict[str, Any]:
        """Build the complete 30-day content calendar aligned with the business plan."""
        niche = self.config.selected_niche
        niche_config = NICHE_CONFIGS[niche]
        self.log("Building 30-day content calendar...")

        calendar = {
            "week_1": {
                "theme": "Foundation & First Content",
                "days": {
                    "1-2": {"tasks": ["Niche research finalization", "Affiliate program sign-ups"], "deliverables": ["5+ affiliate accounts active"]},
                    "3": {"tasks": ["Set up website/blog", "Create link-in-bio page"], "deliverables": ["Live website", "Central affiliate link hub"]},
                    "4-5": {"tasks": [f"Write first 'Best {niche_config.name} Tools in 2026' listicle"], "deliverables": ["1 published SEO article (1,500-2,000 words)"]},
                    "5-6": {"tasks": ["Record 3-5 short-form videos (tool demos, tips)"], "deliverables": ["3-5 TikToks / YouTube Shorts"]},
                    "7": {"tasks": ["Create email lead magnet + landing page"], "deliverables": ["Email capture system live"]},
                },
            },
            "week_2": {
                "theme": "Scale Content & Build Audience",
                "days": {
                    "8-9": {"tasks": ["Write detailed single-product review"], "deliverables": ["1 in-depth review article"]},
                    "9-10": {"tasks": ["Create comparison post (Tool A vs Tool B)"], "deliverables": ["1 comparison article"]},
                    "10-12": {"tasks": ["Daily short-form videos (1-2/day)"], "deliverables": ["7-10 total shorts"]},
                    "12-13": {"tasks": ["Write 'How I Use [Tool]' tutorial post"], "deliverables": ["1 tutorial/case study article"]},
                    "14": {"tasks": ["Value-driven threads on Twitter/X and Reddit"], "deliverables": ["3+ community posts"]},
                },
            },
            "week_3": {
                "theme": "Optimize & Amplify",
                "days": {
                    "15-16": {"tasks": ["Analyze analytics — which content gets clicks?"], "deliverables": ["Data-driven pivot decisions"]},
                    "16-17": {"tasks": ["Double down on winning content formats"], "deliverables": ["3+ pieces in top format"]},
                    "18-19": {"tasks": ["Guest post or collaborate with creator"], "deliverables": ["1 guest post or collab"]},
                    "19-20": {"tasks": ["Create resources page (curated affiliate links)"], "deliverables": ["Evergreen resources page live"]},
                    "21": {"tasks": ["First email to list with value + affiliate rec"], "deliverables": ["First email campaign sent"]},
                },
            },
            "week_4": {
                "theme": "Push for Revenue & Systematize",
                "days": {
                    "22-23": {"tasks": ["Write high-intent buyer content"], "deliverables": ["2 buyer-intent articles"]},
                    "24-25": {"tasks": ["Create YouTube long-form video (8-15 min)"], "deliverables": ["1 YouTube video published"]},
                    "26-27": {"tasks": ["Retarget: update and reshare best content"], "deliverables": ["Refreshed content with better CTAs"]},
                    "28-29": {"tasks": ["Build content production system"], "deliverables": ["Repeatable weekly workflow documented"]},
                    "30": {"tasks": ["Full audit: revenue, traffic, conversions"], "deliverables": ["Month 1 report + Month 2 plan"]},
                },
            },
        }

        prompt = f"""Review this 30-day content calendar for the "{niche_config.name}" affiliate niche
and enhance it with specific content titles and topics.

Calendar structure: {calendar}
Available programs: {', '.join(niche_config.example_programs)}
Target keywords: {', '.join(niche_config.keywords[:5])}

For each week, suggest:
1. Specific article titles with target keywords
2. Short-form video topics (for TikTok/YT Shorts)
3. Social media post angles
4. Which affiliate programs to feature in each content piece
5. Internal linking opportunities between pieces"""

        enhanced = self.call_llm(prompt)

        return {
            "calendar": calendar,
            "enhanced_plan": enhanced,
            "niche": niche.value,
            "content_formats": {f.value: CONTENT_FORMAT_SPECS[f] for f in ContentFormat},
            "platform_specs": {p.value: PLATFORM_SPECS[p] for p in self.config.primary_platforms + self.config.secondary_platforms if p in PLATFORM_SPECS},
        }

    def plan_week(self, week: int) -> dict[str, Any]:
        """Generate a detailed plan for a specific week."""
        niche_config = NICHE_CONFIGS[self.config.selected_niche]
        self.log(f"Planning Week {week}...")

        week_themes = {
            1: "Foundation & First Content",
            2: "Scale Content & Build Audience",
            3: "Optimize & Amplify",
            4: "Push for Revenue & Systematize",
        }

        prompt = f"""Create a detailed day-by-day content plan for Week {week} ({week_themes.get(week, 'Growth')}).

Niche: {niche_config.name}
Programs: {', '.join(niche_config.example_programs)}

For each day, specify:
1. Primary content task (article, video, or social post)
2. Target keyword or topic
3. Affiliate program(s) to feature
4. Platform(s) to publish on
5. Estimated time to complete
6. Success metric for that day"""

        plan = self.call_llm(prompt)

        return {
            "week": week,
            "theme": week_themes.get(week, "Growth"),
            "detailed_plan": plan,
        }

    def create_content_brief(self, topic: str, content_format: ContentFormat) -> dict[str, Any]:
        """Create a detailed content brief for a specific piece."""
        niche_config = NICHE_CONFIGS[self.config.selected_niche]
        format_spec = CONTENT_FORMAT_SPECS[content_format]
        self.log(f"Creating content brief: {topic}")

        prompt = f"""Create a detailed content brief for this affiliate marketing article:

Topic: {topic}
Format: {content_format.value} ({format_spec['template']})
Niche: {niche_config.name}
Target word count: {format_spec.get('word_count', '1500-2000')}

Include:
1. Working title (SEO-optimized)
2. Target primary keyword and 5 secondary keywords
3. Detailed outline with H2/H3 headings
4. Affiliate programs to feature (with placement notes)
5. CTA strategy (where and how to place affiliate links)
6. Competitor content to reference or outperform
7. Unique angle or hook to differentiate
8. Internal links to suggest
9. Meta description draft
10. Social media teasers (for Twitter, Reddit, TikTok)"""

        brief = self.call_llm(prompt)

        return {
            "topic": topic,
            "format": content_format.value,
            "format_spec": format_spec,
            "brief": brief,
        }

    def build_platform_strategy(self) -> dict[str, Any]:
        """Define the multi-platform distribution strategy."""
        self.log("Building platform strategy...")

        platforms = {}
        for platform in self.config.primary_platforms + self.config.secondary_platforms:
            if platform in PLATFORM_SPECS:
                platforms[platform.value] = {
                    **PLATFORM_SPECS[platform],
                    "tier": "primary" if platform in self.config.primary_platforms else "secondary",
                }

        prompt = f"""Design a multi-platform content distribution strategy for our affiliate marketing agency.

Platforms: {platforms}
Niche: {NICHE_CONFIGS[self.config.selected_niche].name}

For each platform, provide:
1. Content repurposing strategy (how to adapt blog content for this platform)
2. Optimal posting times and frequency
3. Affiliate link placement best practices (each platform has different rules)
4. Growth tactics specific to this platform
5. Metrics to track
6. How this platform feeds into the others (cross-promotion)"""

        strategy = self.call_llm(prompt)

        return {
            "platforms": platforms,
            "strategy": strategy,
        }
