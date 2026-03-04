"""
Niche Research Agent
Analyzes market niches, identifies high-ROI opportunities, evaluates competition,
and recommends the optimal niche based on commission potential and buyer intent.
"""

from typing import Any

from .base_agent import BaseAgent, AgentResult
from config.settings import AgencyConfig, Niche, NICHE_CONFIGS, REVENUE_TARGETS


class NicheResearchAgent(BaseAgent):

    def __init__(self, config: AgencyConfig, llm_client: Any = None):
        super().__init__("NicheResearchAgent", config, llm_client)

    @property
    def system_prompt(self) -> str:
        return """You are an expert Niche Research Analyst for an affiliate marketing agency.
Your role is to analyze market niches and identify the highest-ROI opportunities.

Your expertise includes:
- Market size and growth trend analysis
- Competition level assessment (low/medium/high)
- Commission structure evaluation (recurring vs one-time, high-ticket vs volume)
- Buyer intent keyword identification
- Seasonal trend analysis
- Content gap identification in each niche

When analyzing a niche, always provide:
1. Market opportunity score (1-10)
2. Competition difficulty score (1-10, lower is better)
3. Commission potential score (1-10)
4. Content opportunity score (1-10)
5. Overall recommendation score (weighted average)
6. Top 10 buyer-intent keywords
7. Content gaps you've identified
8. Recommended sub-niches for quick wins

Always prioritize niches with:
- Recurring commission programs (SaaS, subscriptions)
- High buyer intent (people ready to purchase)
- Manageable competition for a new entrant
- Evergreen demand (not purely seasonal)"""

    def execute(self, task: str = "analyze_all", context: dict[str, Any] | None = None) -> AgentResult:
        self.log(f"Starting niche research: {task}")

        if task == "analyze_all":
            output = self.analyze_all_niches()
        elif task == "deep_dive":
            niche = (context or {}).get("niche", self.config.selected_niche)
            output = self.deep_dive_niche(niche)
        elif task == "find_keywords":
            niche = (context or {}).get("niche", self.config.selected_niche)
            output = self.find_buyer_intent_keywords(niche)
        elif task == "competitor_analysis":
            niche = (context or {}).get("niche", self.config.selected_niche)
            output = self.analyze_competitors(niche)
        else:
            output = self.analyze_all_niches()

        return AgentResult(
            agent_name=self.name,
            task=task,
            output=output,
            success=True,
        )

    def analyze_all_niches(self) -> dict[str, Any]:
        """Score and rank all available niches."""
        self.log("Analyzing all available niches...")

        analyses = {}
        for niche, niche_config in NICHE_CONFIGS.items():
            score = self._score_niche(niche, niche_config)
            analyses[niche.value] = score

        # Rank by overall score
        ranked = sorted(analyses.items(), key=lambda x: x[1]["overall_score"], reverse=True)

        recommendation = ranked[0][0] if ranked else None

        prompt = f"""Analyze these affiliate marketing niches and provide a recommendation.
Niche scores: {ranked}

Consider that this is a 30-day plan targeting $500-$2000/month revenue.
The marketer has AI/tech skills and is interested in the AI/SaaS space.
Provide your top recommendation and reasoning."""

        llm_analysis = self.call_llm(prompt)

        return {
            "niche_scores": dict(ranked),
            "recommended_niche": recommendation,
            "llm_analysis": llm_analysis,
            "revenue_targets": {
                tier: {
                    "monthly_revenue": f"${t.monthly_revenue[0]}-${t.monthly_revenue[1]}",
                    "required_traffic": f"{t.monthly_traffic[0]}-{t.monthly_traffic[1]} visitors",
                }
                for tier, t in REVENUE_TARGETS.items()
            },
        }

    def deep_dive_niche(self, niche: Niche) -> dict[str, Any]:
        """Perform a deep analysis of a specific niche."""
        niche_config = NICHE_CONFIGS[niche]
        self.log(f"Deep diving into: {niche_config.name}")

        prompt = f"""Perform a deep analysis of the "{niche_config.name}" niche for affiliate marketing.

Known programs: {', '.join(niche_config.example_programs)}
Commission range: {niche_config.commission_range}
Key keywords: {', '.join(niche_config.keywords)}

Provide:
1. Detailed market analysis (size, growth, trends)
2. Top 5 sub-niches with the least competition
3. Content strategy recommendation (which formats convert best)
4. Monetization timeline (when to expect first commissions)
5. Risk factors and how to mitigate them
6. Quick-win opportunities for the first 7 days"""

        analysis = self.call_llm(prompt)

        return {
            "niche": niche.value,
            "niche_name": niche_config.name,
            "programs": niche_config.example_programs,
            "keywords": niche_config.keywords,
            "buyer_intent_phrases": niche_config.buyer_intent_phrases,
            "deep_analysis": analysis,
        }

    def find_buyer_intent_keywords(self, niche: Niche) -> dict[str, Any]:
        """Generate buyer-intent keywords for the selected niche."""
        niche_config = NICHE_CONFIGS[niche]
        self.log(f"Finding buyer-intent keywords for: {niche_config.name}")

        prompt = f"""Generate 30 high buyer-intent keywords for the "{niche_config.name}" affiliate niche.

Existing keyword seeds: {', '.join(niche_config.keywords)}
Buyer intent templates: {', '.join(niche_config.buyer_intent_phrases)}
Programs to reference: {', '.join(niche_config.example_programs)}

Organize keywords into categories:
1. "Best X" keywords (listicle opportunities)
2. "X vs Y" keywords (comparison opportunities)
3. "X review" keywords (review opportunities)
4. "How to" keywords (tutorial opportunities)
5. "Is X worth it" keywords (buyer-decision content)

For each keyword, estimate:
- Search intent strength (high/medium/low)
- Competition level (high/medium/low)
- Content format recommendation
- Estimated monthly search volume range"""

        keywords = self.call_llm(prompt)

        return {
            "niche": niche.value,
            "keyword_research": keywords,
            "seed_keywords": niche_config.keywords,
            "intent_templates": niche_config.buyer_intent_phrases,
        }

    def analyze_competitors(self, niche: Niche) -> dict[str, Any]:
        """Analyze top competitors in the niche."""
        niche_config = NICHE_CONFIGS[niche]
        self.log(f"Analyzing competitors in: {niche_config.name}")

        prompt = f"""Analyze the competitive landscape for affiliate marketing in the "{niche_config.name}" niche.

Identify:
1. Top 5 affiliate content creators/sites in this niche
2. Their primary content strategies and platforms
3. Content gaps they're NOT covering (our opportunities)
4. Their estimated traffic and authority levels
5. How a new entrant can differentiate
6. Low-competition long-tail opportunities they're missing
7. Recommended positioning strategy for a newcomer"""

        competitor_analysis = self.call_llm(prompt)

        return {
            "niche": niche.value,
            "competitor_analysis": competitor_analysis,
        }

    def _score_niche(self, niche: Niche, config: Any) -> dict[str, Any]:
        """Score a niche across multiple dimensions."""
        # Scoring heuristics based on niche characteristics
        scores = {
            Niche.AI_SAAS: {"market": 9, "competition": 6, "commission": 9, "content": 9},
            Niche.ONLINE_EDUCATION: {"market": 8, "competition": 7, "commission": 8, "content": 7},
            Niche.WEB_HOSTING: {"market": 7, "competition": 8, "commission": 8, "content": 6},
            Niche.PERSONAL_FINANCE: {"market": 9, "competition": 9, "commission": 7, "content": 7},
            Niche.HEALTH_WELLNESS: {"market": 8, "competition": 7, "commission": 6, "content": 8},
        }

        s = scores.get(niche, {"market": 5, "competition": 5, "commission": 5, "content": 5})

        # Competition is inverse (lower competition = higher opportunity)
        competition_opportunity = 10 - s["competition"]

        overall = (
            s["market"] * 0.25
            + competition_opportunity * 0.25
            + s["commission"] * 0.30
            + s["content"] * 0.20
        )

        return {
            "market_opportunity": s["market"],
            "competition_difficulty": s["competition"],
            "commission_potential": s["commission"],
            "content_opportunity": s["content"],
            "overall_score": round(overall, 2),
        }
