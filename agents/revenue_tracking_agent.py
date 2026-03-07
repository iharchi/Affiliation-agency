"""
Revenue Tracking & Optimization Agent
Tracks affiliate revenue, analyzes conversion funnels, optimizes commission earnings,
manages program performance, and provides financial reporting.
"""

from typing import Any

from .base_agent import BaseAgent, AgentResult
from config.settings import AgencyConfig, REVENUE_TARGETS, NICHE_CONFIGS


class RevenueTrackingAgent(BaseAgent):

    def __init__(self, config: AgencyConfig, llm_client: Any = None, db_conn: Any = None):
        super().__init__("RevenueTrackingAgent", config, llm_client, db_conn)
        self.revenue_log: list[dict[str, Any]] = []
        if self.db_conn:
            from utils.persistence import load_revenue_log
            self.revenue_log = load_revenue_log(self.db_conn)

    @property
    def system_prompt(self) -> str:
        return """You are an expert Revenue Analyst & Optimization Specialist for an affiliate marketing agency.
Your role is to track all revenue streams, analyze conversion funnels, and maximize earnings.

Your expertise includes:
- Multi-program revenue tracking and attribution
- Conversion funnel analysis (traffic → click → conversion → commission)
- Revenue per click (EPC) optimization
- Commission tier negotiation strategy
- Revenue forecasting and goal tracking
- A/B test analysis for conversion improvements
- Budget vs. revenue ROI calculations

Key financial metrics:
1. Gross Revenue: Total commissions earned
2. Revenue per Click (EPC): Target $0.50+ per click
3. Revenue per Visitor (RPV): Commissions / total site visitors
4. Revenue per Content Piece: Which content drives the most revenue
5. Program-level ROI: Revenue per program vs effort invested
6. Customer Lifetime Value (CLV): For recurring commission programs
7. Net Profit: Revenue minus costs (hosting, tools, etc.)

Revenue optimization levers:
1. Increase traffic (more visitors = more potential clicks)
2. Improve CTR (better CTAs, link placement)
3. Increase conversion rate (better product-audience match)
4. Raise average commission (higher-ticket programs, negotiated rates)
5. Add recurring revenue programs (build predictable monthly income)
6. Reduce churn on recurring programs (create sticky content)"""

    def execute(self, task: str = "dashboard", context: dict[str, Any] | None = None) -> AgentResult:
        self.log(f"Starting revenue task: {task}")
        ctx = context or {}

        task_map = {
            "dashboard": lambda: self.generate_dashboard(),
            "log_revenue": lambda: self.log_revenue_event(ctx),
            "forecast": lambda: self.revenue_forecast(),
            "optimize": lambda: self.optimization_recommendations(),
            "monthly_report": lambda: self.monthly_report(),
            "program_performance": lambda: self.analyze_program_performance(),
        }

        handler = task_map.get(task, lambda: self.generate_dashboard())
        output = handler()

        return AgentResult(agent_name=self.name, task=task, output=output, success=True)

    def generate_dashboard(self) -> dict[str, Any]:
        """Generate a real-time revenue dashboard."""
        targets = REVENUE_TARGETS[self.config.revenue_target]
        self.log("Generating revenue dashboard...")

        total_revenue = sum(e.get("amount", 0) for e in self.revenue_log)
        total_clicks = sum(e.get("clicks", 0) for e in self.revenue_log)
        total_conversions = sum(e.get("conversions", 0) for e in self.revenue_log)

        dashboard = {
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "total_clicks": total_clicks,
                "total_conversions": total_conversions,
                "epc": round(total_revenue / total_clicks, 2) if total_clicks > 0 else 0,
                "conversion_rate": round(total_conversions / total_clicks * 100, 2) if total_clicks > 0 else 0,
            },
            "targets": {
                "monthly_revenue_goal": f"${targets.monthly_revenue[0]}-${targets.monthly_revenue[1]}",
                "target_tier": targets.tier,
                "target_ctr": f"{targets.ctr[0]*100}-{targets.ctr[1]*100}%",
                "target_conversion_rate": f"{targets.conversion_rate[0]*100}-{targets.conversion_rate[1]*100}%",
            },
            "progress": {
                "revenue_vs_goal": f"{round(total_revenue / targets.monthly_revenue[0] * 100, 1) if targets.monthly_revenue[0] > 0 else 0}%",
                "days_elapsed": len(self.revenue_log) or 1,
                "days_remaining": max(0, 30 - len(self.revenue_log) or 1),
            },
            "revenue_log_entries": len(self.revenue_log),
        }

        return dashboard

    def log_revenue_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Log a revenue event (click, conversion, commission)."""
        entry = {
            "program": event.get("program", "unknown"),
            "amount": event.get("amount", 0),
            "clicks": event.get("clicks", 0),
            "conversions": event.get("conversions", 0),
            "source_content": event.get("content", ""),
            "platform": event.get("platform", ""),
        }
        self.revenue_log.append(entry)

        if self.db_conn:
            from utils.persistence import save_revenue_event
            save_revenue_event(self.db_conn, **entry)

        self.log(f"Revenue event logged: ${event.get('amount', 0)} from {event.get('program', 'unknown')}")

        return {"logged": True, "total_events": len(self.revenue_log)}

    def revenue_forecast(self) -> dict[str, Any]:
        """Forecast revenue based on current trajectory."""
        targets = REVENUE_TARGETS[self.config.revenue_target]
        self.log("Generating revenue forecast...")

        total_revenue = sum(e.get("amount", 0) for e in self.revenue_log)
        days_elapsed = max(len(self.revenue_log) or 1, 1)
        daily_rate = total_revenue / days_elapsed

        prompt = f"""Generate a revenue forecast for our affiliate marketing agency.

Current data:
- Total revenue so far: ${total_revenue:.2f}
- Daily revenue rate: ${daily_rate:.2f}
- Revenue events: {len(self.revenue_log)}
- Target: {targets.tier} tier (${targets.monthly_revenue[0]}-${targets.monthly_revenue[1]}/month)

Provide:
1. 30-day projected revenue (at current rate)
2. Required daily rate to hit minimum target
3. Likelihood of hitting each tier (conservative, moderate, aggressive)
4. Revenue acceleration strategies for remaining days
5. Programs with highest revenue potential to focus on
6. Break-even analysis (when will revenue exceed costs)
7. 90-day projection if current growth rate continues"""

        forecast = self.call_llm(prompt)

        return {
            "current_revenue": round(total_revenue, 2),
            "daily_rate": round(daily_rate, 2),
            "projected_30_day": round(daily_rate * 30, 2),
            "forecast_analysis": forecast,
        }

    def optimization_recommendations(self) -> dict[str, Any]:
        """Provide data-driven optimization recommendations."""
        self.log("Generating optimization recommendations...")

        # Analyze revenue by program
        program_revenue: dict[str, float] = {}
        for event in self.revenue_log:
            prog = event.get("program", "unknown")
            program_revenue[prog] = program_revenue.get(prog, 0) + event.get("amount", 0)

        prompt = f"""Provide revenue optimization recommendations for our affiliate agency.

Revenue by program: {program_revenue or 'No data yet - provide recommendations for getting started'}
Revenue events logged: {len(self.revenue_log)}
Budget: ${self.config.budget_monthly}/month

Provide:
1. TOP 3 IMMEDIATE ACTIONS (this week):
   - Specific, actionable steps to increase revenue

2. CONTENT OPTIMIZATION:
   - Which content types to prioritize for revenue
   - CTA improvements to increase click-through rate
   - Link placement optimization

3. PROGRAM OPTIMIZATION:
   - Which programs to double down on
   - Programs to drop or deprioritize
   - New programs to add to portfolio

4. TRAFFIC OPTIMIZATION:
   - Best traffic sources for affiliate conversions
   - Low-cost traffic acquisition strategies
   - Retargeting opportunities

5. CONVERSION OPTIMIZATION:
   - Landing page improvements
   - Email sequence optimization
   - Trust-building strategies

6. SCALING PLAN:
   - When to reinvest revenue into paid traffic
   - Content production efficiency improvements
   - Automation opportunities"""

        recommendations = self.call_llm(prompt)

        return {"program_revenue": program_revenue, "recommendations": recommendations}

    def analyze_program_performance(self) -> dict[str, Any]:
        """Analyze performance by affiliate program."""
        self.log("Analyzing program performance...")

        programs: dict[str, dict[str, Any]] = {}
        for event in self.revenue_log:
            prog = event.get("program", "unknown")
            if prog not in programs:
                programs[prog] = {"revenue": 0, "clicks": 0, "conversions": 0}
            programs[prog]["revenue"] += event.get("amount", 0)
            programs[prog]["clicks"] += event.get("clicks", 0)
            programs[prog]["conversions"] += event.get("conversions", 0)

        # Calculate EPC for each program
        for prog_data in programs.values():
            prog_data["epc"] = (
                round(prog_data["revenue"] / prog_data["clicks"], 2)
                if prog_data["clicks"] > 0
                else 0
            )

        prompt = f"""Analyze affiliate program performance and recommend changes.

Program data: {programs or 'No data yet - provide setup recommendations'}

For each program:
1. Performance rating (excellent/good/average/poor)
2. EPC benchmark comparison
3. Optimization suggestions
4. Scale or cut recommendation

Overall portfolio assessment:
1. Diversification score
2. Recurring vs one-time revenue split
3. Recommended portfolio rebalancing"""

        analysis = self.call_llm(prompt)

        return {"programs": programs, "analysis": analysis}

    def monthly_report(self) -> dict[str, Any]:
        """Generate the comprehensive Month 1 report."""
        targets = REVENUE_TARGETS[self.config.revenue_target]
        total_revenue = sum(e.get("amount", 0) for e in self.revenue_log)
        self.log("Generating monthly report...")

        prompt = f"""Generate a comprehensive Month 1 Affiliate Marketing Report.

Financial Summary:
- Total Revenue: ${total_revenue:.2f}
- Target: ${targets.monthly_revenue[0]}-${targets.monthly_revenue[1]}
- Revenue events: {len(self.revenue_log)}
- Budget spent: ${self.config.budget_monthly}
- Net profit: ${total_revenue - self.config.budget_monthly:.2f}

Provide:
1. EXECUTIVE SUMMARY (1 paragraph)
2. REVENUE BREAKDOWN (by program, by content, by platform)
3. TRAFFIC ANALYSIS (sources, volume, quality)
4. CONTENT PERFORMANCE (top performers, underperformers)
5. EMAIL LIST METRICS (subscribers, open rate, click rate)
6. KEY WINS (what worked best)
7. KEY LESSONS (what to improve)
8. MONTH 2 PLAN:
   - Double content output on best channel
   - Start weekly newsletter
   - Negotiate higher commissions
   - Begin paid traffic experiments ($50-$100)
9. 90-DAY REVENUE PROJECTION
10. STRATEGIC RECOMMENDATIONS FOR SCALING"""

        report = self.call_llm(prompt)

        return {
            "month": 1,
            "total_revenue": round(total_revenue, 2),
            "target": f"${targets.monthly_revenue[0]}-${targets.monthly_revenue[1]}",
            "net_profit": round(total_revenue - self.config.budget_monthly, 2),
            "report": report,
        }
