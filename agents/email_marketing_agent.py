"""
Email Marketing Agent
Manages email list building, lead magnet creation, nurture sequences,
newsletter campaigns, and email-driven affiliate conversions.
"""

from typing import Any

from .base_agent import BaseAgent, AgentResult
from config.settings import AgencyConfig, NICHE_CONFIGS


class EmailMarketingAgent(BaseAgent):

    def __init__(self, config: AgencyConfig, llm_client: Any = None):
        super().__init__("EmailMarketingAgent", config, llm_client)

    @property
    def system_prompt(self) -> str:
        return """You are an expert Email Marketing Strategist for an affiliate marketing agency.
Your role is to build email lists, create nurture sequences, and drive affiliate revenue through email.

Your expertise includes:
- Lead magnet creation (checklists, templates, guides, mini-courses)
- Landing page copy optimization
- Welcome/nurture email sequence design
- Newsletter strategy for consistent affiliate revenue
- Segmentation and personalization
- A/B testing subject lines and content

Email marketing principles:
1. Your email list is your most valuable long-term asset
2. Provide 80% value, 20% promotion in every email
3. One CTA per email (don't overwhelm with choices)
4. Subject lines determine open rates — test aggressively
5. The P.S. line is the second most-read part of any email
6. Segment your list by interest and engagement level
7. Always include FTC affiliate disclosure
8. Send at least 1 email/week to stay top of mind

Email types that drive affiliate revenue:
- Welcome sequence (5-7 emails introducing you and your top recommendations)
- Product spotlight emails (deep dive into one affiliate product)
- Comparison emails (help subscribers choose between options)
- "What I'm using this week" roundups
- Exclusive deal/discount announcements
- Case study / results emails"""

    def execute(self, task: str = "setup", context: dict[str, Any] | None = None) -> AgentResult:
        self.log(f"Starting email marketing: {task}")
        ctx = context or {}

        task_map = {
            "setup": lambda: self.setup_email_system(),
            "lead_magnet": lambda: self.create_lead_magnet(ctx.get("magnet_type", "checklist")),
            "welcome_sequence": lambda: self.create_welcome_sequence(),
            "newsletter": lambda: self.plan_newsletter(ctx.get("topic", "")),
            "landing_page": lambda: self.write_landing_page_copy(ctx.get("offer", "")),
        }

        handler = task_map.get(task, lambda: self.setup_email_system())
        output = handler()

        return AgentResult(agent_name=self.name, task=task, output=output, success=True)

    def setup_email_system(self) -> dict[str, Any]:
        """Set up the complete email marketing system from Day 1."""
        niche_config = NICHE_CONFIGS[self.config.selected_niche]
        self.log("Setting up email marketing system...")

        prompt = f"""Design a complete email marketing system for our affiliate marketing agency.

Niche: {niche_config.name}
Tool: {self.config.email_tool} (free tier)
Goal: Start capturing emails from Day 1, monetize by Week 3

Provide:
1. SYSTEM SETUP:
   - Email tool configuration checklist
   - Custom domain email setup
   - Deliverability best practices

2. LEAD MAGNET IDEAS (top 3 for our niche):
   - What to create
   - Why it converts
   - How to deliver it

3. LANDING PAGE STRUCTURE:
   - Headline formula
   - Bullet points for the offer
   - Social proof elements
   - CTA button text

4. TAGGING & SEGMENTATION:
   - How to tag subscribers by interest
   - Segments to create from day 1
   - Automation triggers

5. COMPLIANCE:
   - CAN-SPAM requirements
   - GDPR considerations
   - Unsubscribe process"""

        system = self.call_llm(prompt)

        return {"email_tool": self.config.email_tool, "setup_plan": system, "niche": niche_config.name}

    def create_lead_magnet(self, magnet_type: str) -> dict[str, Any]:
        """Create a lead magnet to capture email subscribers."""
        niche_config = NICHE_CONFIGS[self.config.selected_niche]
        self.log(f"Creating lead magnet: {magnet_type}")

        prompt = f"""Create a complete lead magnet for our affiliate marketing agency.

Niche: {niche_config.name}
Type: {magnet_type} (checklist / template / guide / mini-course / toolkit)
Programs to subtly feature: {', '.join(niche_config.example_programs[:3])}

Provide the COMPLETE content for a lead magnet:

1. TITLE: Compelling, specific, outcome-focused
2. SUBTITLE: Clarifies what they'll get
3. INTRODUCTION: Why this resource exists (2-3 paragraphs)
4. MAIN CONTENT:
   - If checklist: 15-25 actionable items with brief explanations
   - If template: Complete fillable template with instructions
   - If guide: 5-7 chapters/sections with practical advice
   - If toolkit: Curated list of 10-20 recommended tools
5. AFFILIATE INTEGRATION:
   - Naturally recommend 2-3 affiliate products within the content
   - Include [AFFILIATE_LINK] placeholders
6. CTA: What to do next (visit your blog, follow on social, try a recommended tool)
7. ABOUT SECTION: Brief bio building credibility

Make it genuinely valuable — something people would happily pay $20+ for."""

        lead_magnet = self.call_llm(prompt)

        return {"type": magnet_type, "niche": niche_config.name, "lead_magnet": lead_magnet}

    def create_welcome_sequence(self) -> dict[str, Any]:
        """Create a 7-email welcome/nurture sequence."""
        niche_config = NICHE_CONFIGS[self.config.selected_niche]
        self.log("Creating welcome email sequence...")

        prompt = f"""Write a complete 7-email welcome sequence for new subscribers.

Niche: {niche_config.name}
Programs to feature: {', '.join(niche_config.example_programs)}

SEQUENCE OVERVIEW:
- Email 1 (Day 0): Welcome + deliver lead magnet + set expectations
- Email 2 (Day 1): Your story + why you're passionate about this niche
- Email 3 (Day 3): Best tip/insight + first soft affiliate mention
- Email 4 (Day 5): Product spotlight — your #1 recommendation (main affiliate push)
- Email 5 (Day 7): Case study / results from using recommended tools
- Email 6 (Day 10): Common mistakes in {niche_config.name} + how to avoid them
- Email 7 (Day 14): Roundup of your best content + resources page link

For EACH email, provide:
1. Subject line (+ A/B variant)
2. Preview text
3. Complete email body copy
4. CTA (button text + link description)
5. P.S. line
6. Affiliate products mentioned (if any)

Rules:
- Emails 1-2: NO affiliate links (build trust first)
- Emails 3-5: Introduce affiliate products naturally
- Emails 6-7: Full affiliate recommendations with links
- Every email: Genuine value that stands on its own"""

        sequence = self.call_llm(prompt)

        return {"sequence_length": 7, "niche": niche_config.name, "welcome_sequence": sequence}

    def plan_newsletter(self, topic: str) -> dict[str, Any]:
        """Plan a weekly newsletter issue."""
        niche_config = NICHE_CONFIGS[self.config.selected_niche]
        self.log(f"Planning newsletter: {topic}")

        prompt = f"""Plan a weekly newsletter issue for our affiliate marketing audience.

Topic: {topic or f'Weekly {niche_config.name} Roundup'}
Niche: {niche_config.name}

Newsletter structure:
1. SUBJECT LINE: High-open-rate formula (curiosity + benefit)
2. INTRO: Personal anecdote or timely hook (3-4 sentences)
3. MAIN STORY: One valuable insight, tutorial, or discovery (200-300 words)
4. TOOL SPOTLIGHT: Featured affiliate product with honest mini-review (100 words)
5. QUICK LINKS: 3-5 curated links (mix of your content + others)
6. TIP OF THE WEEK: One actionable takeaway
7. CTA: One clear action (try a tool, read an article, reply to email)
8. P.S.: Teaser for next week or secondary CTA

Include:
- [AFFILIATE_LINK] placeholders
- FTC disclosure note
- Unsubscribe reminder"""

        newsletter = self.call_llm(prompt)

        return {"topic": topic, "newsletter_plan": newsletter}

    def write_landing_page_copy(self, offer: str) -> dict[str, Any]:
        """Write high-converting landing page copy for email opt-in."""
        niche_config = NICHE_CONFIGS[self.config.selected_niche]
        self.log(f"Writing landing page: {offer}")

        prompt = f"""Write high-converting landing page copy for an email opt-in.

Offer: {offer or f'Free {niche_config.name} Toolkit'}
Niche: {niche_config.name}

Provide:
1. HEADLINE: Clear benefit + specific outcome
2. SUBHEADLINE: Clarify what they get
3. HERO SECTION: 2-3 sentences of compelling copy
4. BULLET POINTS: 5-7 specific things included in the lead magnet
5. SOCIAL PROOF: Testimonial templates / subscriber count
6. CTA BUTTON: Action-oriented text (not just "Submit")
7. OBJECTION HANDLERS: Brief text addressing "Is this really free?" and privacy
8. ABOVE-THE-FOLD LAYOUT: Describe the visual arrangement

Optimize for:
- Mobile-first design
- Single CTA (email capture only)
- Fast load time
- Trust signals"""

        landing_page = self.call_llm(prompt)

        return {"offer": offer, "landing_page_copy": landing_page}
