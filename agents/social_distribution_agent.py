"""
Social Media Distribution Agent
Manages content distribution across social platforms, community engagement,
content repurposing, and cross-platform amplification.
"""

from typing import Any

from .base_agent import BaseAgent, AgentResult
from config.settings import AgencyConfig, Platform, NICHE_CONFIGS


class SocialDistributionAgent(BaseAgent):

    def __init__(self, config: AgencyConfig, llm_client: Any = None, db_conn: Any = None):
        super().__init__("SocialDistributionAgent", config, llm_client, db_conn)

    @property
    def system_prompt(self) -> str:
        return """You are an expert Social Media Strategist for an affiliate marketing agency.
Your role is to maximize content reach and engagement across all social platforms.

Your expertise includes:
- Multi-platform content distribution and scheduling
- Content repurposing (turning one piece into 5-10 platform-specific versions)
- Community engagement on Reddit, Twitter/X, and niche forums
- Short-form video optimization (TikTok, YouTube Shorts)
- Viral content mechanics and hook writing
- Cross-platform audience funneling

Platform-specific rules:
- REDDIT: Never drop affiliate links directly. Provide genuine value, link to your content.
- TWITTER/X: Threads perform best. Lead with a bold hook. Affiliate mention in tweet 5-6.
- TIKTOK: First 3 seconds = everything. Use trending sounds. CTA: "link in bio."
- YOUTUBE SHORTS: Similar to TikTok but slightly more educational tone.
- MEDIUM/SUBSTACK: Repurpose blog posts. Include affiliate links naturally.

Engagement strategy:
1. Add value in every community interaction (80% value, 20% promotion)
2. Build genuine relationships with other creators
3. Respond to every comment in the first 2 hours (algorithm boost)
4. Use trending hashtags and topics when relevant
5. Cross-promote: social drives to blog, blog captures email, email converts"""

    def execute(self, task: str = "distribute", context: dict[str, Any] | None = None) -> AgentResult:
        self.log(f"Starting social distribution: {task}")
        ctx = context or {}

        task_map = {
            "distribute": lambda: self.create_distribution_plan(ctx.get("content_title", ""), ctx.get("content_url", "")),
            "repurpose": lambda: self.repurpose_content(ctx.get("original_content", ""), ctx.get("source_format", "blog")),
            "engage": lambda: self.community_engagement_plan(ctx.get("platform", Platform.REDDIT)),
            "schedule": lambda: self.create_posting_schedule(),
            "viral_hooks": lambda: self.generate_viral_hooks(ctx.get("topic", "")),
        }

        handler = task_map.get(task, lambda: self.create_distribution_plan("", ""))
        output = handler()

        return AgentResult(agent_name=self.name, task=task, output=output, success=True)

    def create_distribution_plan(self, content_title: str, content_url: str) -> dict[str, Any]:
        """Create a multi-platform distribution plan for a piece of content."""
        niche_config = NICHE_CONFIGS[self.config.selected_niche]
        self.log(f"Creating distribution plan for: {content_title}")

        all_platforms = self.config.primary_platforms + self.config.secondary_platforms

        prompt = f"""Create a complete distribution plan for this affiliate content:

Content: {content_title or 'New affiliate article'}
URL: {content_url or '[article URL]'}
Niche: {niche_config.name}
Platforms: {', '.join(p.value for p in all_platforms)}

For EACH platform, provide:
1. Adapted version of the content (not just copy-paste)
2. Optimal posting time
3. Hashtags/tags to use
4. CTA strategy (how to drive clicks without being spammy)
5. Engagement plan for first 2 hours after posting
6. Cross-promotion hooks to other platforms

Also provide:
- A 7-day drip schedule (don't post everything at once)
- Reshare strategy (when to repost/repurpose for second wave)
- Community threads/subreddits to share in"""

        plan = self.call_llm(prompt)

        return {
            "content_title": content_title,
            "platforms": [p.value for p in all_platforms],
            "distribution_plan": plan,
        }

    def repurpose_content(self, original_content: str, source_format: str) -> dict[str, Any]:
        """Repurpose a single piece of content into multiple platform-specific versions."""
        self.log(f"Repurposing {source_format} content...")

        prompt = f"""Repurpose this {source_format} content into 5+ platform-specific pieces:

Original content (first 1000 chars): {original_content[:1000]}...

Create:
1. TWITTER/X THREAD (5-7 tweets):
   - Hook tweet, value tweets, affiliate mention, CTA tweet

2. TIKTOK/YT SHORTS SCRIPT (60 seconds):
   - 3-second hook, problem, solution demo, CTA

3. REDDIT POST:
   - Genuine value post with subtle content link
   - Suggested subreddits to post in

4. EMAIL TEASER:
   - Subject line + 3-paragraph teaser driving to full content

5. LINKEDIN POST:
   - Professional angle on the same topic

6. MEDIUM ARTICLE:
   - Adapted version with platform-specific formatting

Each version should feel NATIVE to the platform, not like a copy-paste job."""

        repurposed = self.call_llm(prompt)

        return {"source_format": source_format, "repurposed_content": repurposed}

    def community_engagement_plan(self, platform: Platform) -> dict[str, Any]:
        """Create an engagement plan for building authority in communities."""
        niche_config = NICHE_CONFIGS[self.config.selected_niche]
        self.log(f"Creating engagement plan for: {platform.value}")

        prompt = f"""Create a community engagement strategy for {platform.value}.

Niche: {niche_config.name}
Goal: Build authority and drive traffic to our affiliate content

Provide:
1. Top 10 communities/subreddits/hashtags to engage in
2. Daily engagement routine (15-30 min/day)
3. Types of value-add comments/posts to make
4. How to naturally mention our content without being spammy
5. Relationship-building strategy with other creators
6. Content ideas that perform well on this platform
7. Common mistakes to avoid (each platform has different rules about self-promotion)
8. Growth milestones to target (followers, engagement rate)"""

        engagement = self.call_llm(prompt)

        return {"platform": platform.value, "engagement_plan": engagement}

    def create_posting_schedule(self) -> dict[str, Any]:
        """Create a weekly posting schedule across all platforms."""
        self.log("Creating weekly posting schedule...")

        platforms = self.config.primary_platforms + self.config.secondary_platforms

        prompt = f"""Create an optimized weekly posting schedule for our affiliate marketing agency.

Platforms: {', '.join(p.value for p in platforms)}
Primary (daily): {', '.join(p.value for p in self.config.primary_platforms)}
Secondary (2-3x/week): {', '.join(p.value for p in self.config.secondary_platforms)}

For each day (Monday-Sunday), specify:
1. What to post on each platform
2. Best posting time (timezone: EST)
3. Content type (new content, repurposed, engagement-only)
4. Time required
5. Priority level

Include:
- Batch creation days (create multiple pieces at once)
- Engagement-only windows (comment, reply, share)
- Analytics review time
- Rest/buffer day"""

        schedule = self.call_llm(prompt)

        return {"platforms": [p.value for p in platforms], "weekly_schedule": schedule}

    def generate_viral_hooks(self, topic: str) -> dict[str, Any]:
        """Generate attention-grabbing hooks for social media content."""
        self.log(f"Generating viral hooks for: {topic}")

        prompt = f"""Generate 20 viral hooks for social media content about: {topic or 'affiliate marketing tools'}

Categories:
1. CURIOSITY HOOKS (5): Make them NEED to know more
2. CONTRARIAN HOOKS (5): Challenge common beliefs
3. STORY HOOKS (5): Start with a compelling personal angle
4. DATA HOOKS (5): Lead with surprising numbers/stats

For each hook:
- The actual hook text (first 1-2 sentences)
- Which platform it works best on
- Suggested content format (thread, video, post)
- Why it works psychologically"""

        hooks = self.call_llm(prompt)

        return {"topic": topic, "hooks": hooks}
