"""
SEO & Analytics Agent
Handles keyword research, on-page SEO optimization, performance tracking,
link analytics, and data-driven content decisions.
"""

from typing import Any

from .base_agent import BaseAgent, AgentResult
from config.settings import AgencyConfig, NICHE_CONFIGS


class SEOAnalyticsAgent(BaseAgent):

    def __init__(self, config: AgencyConfig, llm_client: Any = None):
        super().__init__("SEOAnalyticsAgent", config, llm_client)
        self.kpi_history: list[dict[str, Any]] = []

    @property
    def system_prompt(self) -> str:
        return """You are an expert SEO & Analytics Specialist for an affiliate marketing agency.
Your role is to optimize content for search engines and track performance metrics.

Your expertise includes:
- Keyword research and clustering (buyer-intent keywords prioritized)
- On-page SEO optimization (titles, meta descriptions, headings, internal linking)
- Content performance analysis (traffic, CTR, conversions, EPC)
- Link tracking and attribution (UTM parameters, link management)
- Competitor SEO analysis
- Technical SEO audits

Key metrics you track (KPIs):
1. Traffic: Total visitors across all platforms
2. Click-Through Rate (CTR): % of visitors who click affiliate links
3. Conversions: Completed purchases/sign-ups from affiliate links
4. Revenue per Click (EPC): Total commissions / total clicks (target: $0.50+)
5. Email List Growth: New subscribers per week
6. Content Output: Articles, videos, and social posts published
7. Keyword Rankings: Position tracking for target keywords

SEO optimization priorities:
1. Target keywords in title, H1, first paragraph, and 2-3 subheadings
2. Meta description under 155 characters with keyword and CTA
3. Internal links to 2-3 related articles
4. External links to authoritative sources
5. Image alt text with keywords
6. URL slug with primary keyword
7. Schema markup for reviews and comparisons"""

    def execute(self, task: str = "keyword_research", context: dict[str, Any] | None = None) -> AgentResult:
        self.log(f"Starting SEO/analytics task: {task}")
        ctx = context or {}

        task_map = {
            "keyword_research": lambda: self.keyword_research(ctx.get("seed_keywords", [])),
            "optimize_content": lambda: self.optimize_content(ctx.get("content", ""), ctx.get("target_keyword", "")),
            "track_kpis": lambda: self.track_kpis(ctx.get("metrics", {})),
            "weekly_report": lambda: self.generate_weekly_report(ctx.get("week", self.config.current_week)),
            "competitor_seo": lambda: self.analyze_competitor_seo(ctx.get("competitor_url", "")),
            "link_audit": lambda: self.audit_affiliate_links(ctx.get("links", [])),
        }

        handler = task_map.get(task, lambda: self.keyword_research([]))
        output = handler()

        return AgentResult(agent_name=self.name, task=task, output=output, success=True)

    def keyword_research(self, seed_keywords: list[str]) -> dict[str, Any]:
        """Perform keyword research for the selected niche."""
        niche_config = NICHE_CONFIGS[self.config.selected_niche]
        seeds = seed_keywords or niche_config.keywords
        self.log(f"Researching keywords from {len(seeds)} seeds...")

        prompt = f"""Perform comprehensive keyword research for affiliate marketing.

Niche: {niche_config.name}
Seed keywords: {', '.join(seeds)}
Buyer intent templates: {', '.join(niche_config.buyer_intent_phrases)}

Deliver:
1. TOP 20 BUYER-INTENT KEYWORDS (sorted by conversion potential):
   For each: keyword, estimated monthly volume, difficulty (1-100), intent type, recommended content format

2. KEYWORD CLUSTERS (group related keywords into content pillars):
   - Cluster name
   - Primary keyword
   - Supporting keywords (5-8 per cluster)
   - Recommended pillar content piece

3. LONG-TAIL OPPORTUNITIES (low competition, high intent):
   10 long-tail keywords with estimated difficulty under 30

4. CONTENT GAP KEYWORDS:
   Keywords competitors rank for that we should target

5. TRENDING KEYWORDS:
   5 rising search terms in this niche"""

        research = self.call_llm(prompt)

        return {
            "niche": niche_config.name,
            "seed_keywords": seeds,
            "research": research,
        }

    def optimize_content(self, content: str, target_keyword: str) -> dict[str, Any]:
        """Optimize a piece of content for SEO."""
        self.log(f"Optimizing content for: {target_keyword}")

        prompt = f"""Optimize this affiliate marketing content for SEO.

Target keyword: {target_keyword}
Content (first 500 chars): {content[:500]}...

Provide:
1. Optimized title tag (under 60 characters, keyword at start)
2. Meta description (under 155 characters, includes keyword and CTA)
3. Recommended H2/H3 heading structure with keyword variations
4. Internal linking suggestions (what related content to link to)
5. Image alt text suggestions
6. URL slug recommendation
7. Schema markup type (Review, Product, FAQ, HowTo)
8. Keyword density check (target: 1-2% for primary, 0.5-1% for secondary)
9. Readability score estimate
10. Specific improvement suggestions"""

        optimization = self.call_llm(prompt)

        return {
            "target_keyword": target_keyword,
            "optimization": optimization,
        }

    def track_kpis(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Track and analyze KPIs for the affiliate marketing campaign."""
        self.log("Tracking KPIs...")

        kpi_snapshot = {
            "traffic": metrics.get("traffic", 0),
            "affiliate_clicks": metrics.get("clicks", 0),
            "conversions": metrics.get("conversions", 0),
            "revenue": metrics.get("revenue", 0.0),
            "email_subscribers": metrics.get("subscribers", 0),
            "content_published": metrics.get("content_count", 0),
            "ctr": 0.0,
            "epc": 0.0,
            "conversion_rate": 0.0,
        }

        # Calculate derived metrics
        if kpi_snapshot["traffic"] > 0:
            kpi_snapshot["ctr"] = round(kpi_snapshot["affiliate_clicks"] / kpi_snapshot["traffic"] * 100, 2)
        if kpi_snapshot["affiliate_clicks"] > 0:
            kpi_snapshot["epc"] = round(kpi_snapshot["revenue"] / kpi_snapshot["affiliate_clicks"], 2)
            kpi_snapshot["conversion_rate"] = round(kpi_snapshot["conversions"] / kpi_snapshot["affiliate_clicks"] * 100, 2)

        self.kpi_history.append(kpi_snapshot)

        prompt = f"""Analyze these affiliate marketing KPIs and provide actionable insights:

Current metrics: {kpi_snapshot}
Historical data points: {len(self.kpi_history)}

Benchmarks:
- Target CTR: 5-8%
- Target EPC: $0.50+
- Target conversion rate: 2-5%

Provide:
1. Performance assessment (on track / needs improvement / critical)
2. Top 3 areas to improve immediately
3. Specific tactics to improve each weak metric
4. What's working well (to double down on)
5. Projected end-of-month revenue at current trajectory"""

        analysis = self.call_llm(prompt)

        return {"kpis": kpi_snapshot, "analysis": analysis, "history_length": len(self.kpi_history)}

    def generate_weekly_report(self, week: int) -> dict[str, Any]:
        """Generate a comprehensive weekly performance report."""
        self.log(f"Generating Week {week} report...")

        prompt = f"""Generate a Week {week} affiliate marketing performance report.

Week themes:
- Week 1: Foundation & First Content
- Week 2: Scale Content & Build Audience
- Week 3: Optimize & Amplify
- Week 4: Push for Revenue & Systematize

For Week {week}, provide:
1. EXECUTIVE SUMMARY: One paragraph status update
2. CONTENT METRICS: Published pieces, views, engagement
3. AFFILIATE METRICS: Clicks, conversions, revenue
4. SEO PROGRESS: Rankings, organic traffic trends
5. EMAIL LIST: Growth rate, open rates, click rates
6. TOP PERFORMING CONTENT: What drove the most revenue
7. UNDERPERFORMING CONTENT: What needs improvement
8. NEXT WEEK PRIORITIES: Top 5 actions for improvement
9. REVENUE PROJECTION: Updated monthly estimate"""

        report = self.call_llm(prompt)

        return {"week": week, "report": report}

    def analyze_competitor_seo(self, competitor_url: str) -> dict[str, Any]:
        """Analyze a competitor's SEO strategy."""
        self.log(f"Analyzing competitor SEO: {competitor_url}")

        prompt = f"""Analyze the SEO strategy of this affiliate marketing competitor: {competitor_url or '[competitor in our niche]'}

Provide:
1. Estimated domain authority and traffic
2. Top ranking keywords (what they rank for)
3. Content strategy (types, frequency, word counts)
4. Backlink profile estimate
5. Content gaps we can exploit
6. Keywords they rank for that we should target
7. What they do well that we should emulate
8. Weaknesses we can capitalize on"""

        analysis = self.call_llm(prompt)

        return {"competitor": competitor_url, "seo_analysis": analysis}

    def audit_affiliate_links(self, links: list[dict[str, str]]) -> dict[str, Any]:
        """Audit affiliate link placement and performance."""
        self.log("Auditing affiliate links...")

        prompt = f"""Audit these affiliate link placements for optimization:

Links: {links or '[Review all content for link placement optimization]'}

Check for:
1. Link density (max 1 per 200 words)
2. Placement at decision points (not random)
3. CTA clarity and persuasiveness
4. FTC disclosure compliance
5. Broken or expired links
6. UTM parameter consistency
7. Link cloaking recommendations
8. A/B test suggestions for CTAs"""

        audit = self.call_llm(prompt)

        return {"audit": audit, "links_reviewed": len(links)}
