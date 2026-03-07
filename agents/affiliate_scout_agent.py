"""
Affiliate Program Scout Agent
Discovers, evaluates, and recommends affiliate programs. Manages sign-up tracking,
commission comparison, and program portfolio optimization.
"""

from typing import Any

from .base_agent import BaseAgent, AgentResult
from config.settings import AgencyConfig, Niche, AFFILIATE_PROGRAMS, NICHE_CONFIGS


class AffiliateProgramScoutAgent(BaseAgent):

    def __init__(self, config: AgencyConfig, llm_client: Any = None, db_conn: Any = None):
        super().__init__("AffiliateProgramScoutAgent", config, llm_client, db_conn)
        self.program_portfolio: list[dict[str, Any]] = []
        if self.db_conn:
            from utils.persistence import load_portfolio
            self.program_portfolio = load_portfolio(self.db_conn)

    @property
    def system_prompt(self) -> str:
        return """You are an expert Affiliate Program Scout for a performance marketing agency.
Your role is to discover, evaluate, and recommend the most profitable affiliate programs.

Your expertise includes:
- Evaluating commission structures (recurring vs one-time, percentage vs flat rate)
- Assessing cookie duration and attribution models
- Comparing programs across networks (Impact, ShareASale, CJ, direct programs)
- Identifying high-ticket opportunities ($100+ per conversion)
- Negotiating higher commission tiers based on performance data
- Portfolio diversification strategy (mix of recurring + high-ticket + volume)

When evaluating programs, always consider:
1. Commission rate and type (recurring preferred for stable income)
2. Cookie duration (longer = more attributed conversions)
3. Product-market fit with our content and audience
4. Conversion rate reputation (some programs convert much better)
5. Payment terms and minimum thresholds
6. Promotional restrictions (some programs limit certain channels)
7. EPC (Earnings Per Click) benchmark data

Always recommend a diversified portfolio:
- 2-3 high-ticket programs ($100+/sale) for big wins
- 2-3 recurring commission programs for stable monthly income
- 1-2 high-volume low-ticket programs for consistent baseline revenue"""

    def execute(self, task: str = "build_portfolio", context: dict[str, Any] | None = None) -> AgentResult:
        self.log(f"Starting affiliate scouting: {task}")

        if task == "build_portfolio":
            output = self.build_program_portfolio()
        elif task == "evaluate_program":
            program_name = (context or {}).get("program_name", "")
            output = self.evaluate_program(program_name)
        elif task == "find_programs":
            niche = (context or {}).get("niche", self.config.selected_niche)
            output = self.find_programs_for_niche(niche)
        elif task == "optimize_portfolio":
            output = self.optimize_portfolio()
        elif task == "signup_checklist":
            output = self.generate_signup_checklist()
        else:
            output = self.build_program_portfolio()

        return AgentResult(
            agent_name=self.name,
            task=task,
            output=output,
            success=True,
        )

    def build_program_portfolio(self) -> dict[str, Any]:
        """Build an optimized portfolio of affiliate programs for the selected niche."""
        niche = self.config.selected_niche
        self.log(f"Building program portfolio for: {niche.value}")

        # Filter programs for the selected niche
        niche_programs = [p for p in AFFILIATE_PROGRAMS if p.niche == niche]

        # Also include Amazon (universal)
        amazon = [p for p in AFFILIATE_PROGRAMS if p.name == "Amazon Associates"]
        all_programs = niche_programs + amazon

        # Categorize by commission type
        recurring = [p for p in all_programs if p.commission_type == "recurring"]
        high_ticket = [p for p in all_programs if p.commission_type == "one_time" and "100" in p.commission_range]
        volume = [p for p in all_programs if p not in recurring and p not in high_ticket]

        portfolio = {
            "niche": niche.value,
            "total_programs": len(all_programs),
            "recurring_income": [
                {
                    "name": p.name,
                    "network": p.network,
                    "commission": p.commission_range,
                    "cookie_days": p.cookie_duration_days,
                }
                for p in recurring
            ],
            "high_ticket": [
                {
                    "name": p.name,
                    "network": p.network,
                    "commission": p.commission_range,
                    "cookie_days": p.cookie_duration_days,
                }
                for p in high_ticket
            ],
            "volume_plays": [
                {
                    "name": p.name,
                    "network": p.network,
                    "commission": p.commission_range,
                    "cookie_days": p.cookie_duration_days,
                }
                for p in volume
            ],
        }

        prompt = f"""Review this affiliate program portfolio and provide strategic recommendations:

Portfolio: {portfolio}
Target niche: {NICHE_CONFIGS[niche].name}
Revenue goal: $500-$2,000/month within 30 days

Recommend:
1. Which 3-5 programs to prioritize for Week 1 sign-ups
2. Expected commission timeline (when will first payments arrive)
3. Programs missing from our portfolio that we should add
4. Optimal content-to-program mapping (which content type sells which program best)
5. Commission negotiation opportunities after initial results"""

        strategy = self.call_llm(prompt)

        portfolio["strategy"] = strategy
        self.program_portfolio = all_programs
        if self.db_conn:
            from utils.persistence import save_portfolio
            save_portfolio(self.db_conn, self.program_portfolio)
        return portfolio

    def evaluate_program(self, program_name: str) -> dict[str, Any]:
        """Deep evaluation of a specific affiliate program."""
        self.log(f"Evaluating program: {program_name}")

        program = next((p for p in AFFILIATE_PROGRAMS if p.name.lower() == program_name.lower()), None)

        prompt = f"""Evaluate the affiliate program "{program_name}" for our affiliate marketing agency.

{"Known details: " + str({"commission": program.commission_range, "network": program.network, "cookie_days": program.cookie_duration_days, "type": program.commission_type}) if program else "Research this program and provide details."}

Provide:
1. Commission structure breakdown
2. Cookie duration and attribution model
3. Conversion rate estimates
4. Best content types for promoting this program
5. Pros and cons vs competitors
6. Estimated earnings potential at 100, 500, and 1000 monthly clicks
7. Sign-up requirements and approval tips"""

        evaluation = self.call_llm(prompt)

        return {
            "program_name": program_name,
            "evaluation": evaluation,
            "in_portfolio": program is not None,
        }

    def find_programs_for_niche(self, niche: Niche) -> dict[str, Any]:
        """Discover affiliate programs available in a given niche."""
        niche_config = NICHE_CONFIGS[niche]
        self.log(f"Finding programs for niche: {niche_config.name}")

        prompt = f"""Find and recommend affiliate programs for the "{niche_config.name}" niche.

Known programs: {', '.join(niche_config.example_programs)}

Discover additional programs and for each provide:
1. Program name and network
2. Commission rate and type
3. Cookie duration
4. Minimum payout threshold
5. Application requirements
6. Our rating (1-10) based on earning potential

Organize into tiers:
- Tier 1: Must-join programs (highest potential)
- Tier 2: Strong secondary programs
- Tier 3: Supplemental programs for diversification"""

        programs = self.call_llm(prompt)

        return {
            "niche": niche.value,
            "discovered_programs": programs,
            "known_programs": niche_config.example_programs,
        }

    def optimize_portfolio(self) -> dict[str, Any]:
        """Analyze current portfolio performance and suggest optimizations."""
        self.log("Optimizing program portfolio...")

        prompt = """Analyze our current affiliate program portfolio and recommend optimizations.

Consider:
1. Are we over-indexed on any single program or network?
2. Do we have enough recurring commission programs?
3. Are there high-ticket programs we should add?
4. Should we drop any underperforming programs?
5. Commission rate negotiation opportunities
6. Seasonal program additions to consider

Provide a specific action plan for portfolio improvements."""

        optimization = self.call_llm(prompt)

        return {
            "current_portfolio_size": len(self.program_portfolio),
            "optimization_recommendations": optimization,
        }

    def generate_signup_checklist(self) -> dict[str, Any]:
        """Generate a Day 2-3 signup checklist for affiliate programs."""
        niche = self.config.selected_niche
        niche_config = NICHE_CONFIGS[niche]
        self.log("Generating signup checklist...")

        programs = [p for p in AFFILIATE_PROGRAMS if p.niche == niche]

        checklist = {
            "day_2_signups": [
                {
                    "priority": "HIGH",
                    "program": "Amazon Associates",
                    "action": "Sign up at affiliate-program.amazon.com",
                    "notes": "Universal program, low commissions but builds trust",
                },
            ],
            "day_2_3_signups": [],
            "networks_to_join": [
                {"network": "Impact", "action": "Join at impact.com/partners"},
                {"network": "ShareASale", "action": "Join at shareasale.com/join"},
                {"network": "CJ Affiliate", "action": "Join at cj.com"},
            ],
        }

        for p in programs:
            checklist["day_2_3_signups"].append({
                "priority": "HIGH" if p.commission_type == "recurring" else "MEDIUM",
                "program": p.name,
                "network": p.network,
                "commission": p.commission_range,
                "action": f"Apply via {p.network}" + (f" (cookie: {p.cookie_duration_days} days)" if p.cookie_duration_days else ""),
            })

        return checklist
