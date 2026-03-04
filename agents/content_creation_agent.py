"""
Content Creation Agent
Generates high-quality affiliate marketing content including articles, video scripts,
social media posts, and email copy. Optimizes for conversions and SEO.
"""

from typing import Any

from .base_agent import BaseAgent, AgentResult
from config.settings import AgencyConfig, ContentFormat, Platform, NICHE_CONFIGS


class ContentCreationAgent(BaseAgent):

    def __init__(self, config: AgencyConfig, llm_client: Any = None):
        super().__init__("ContentCreationAgent", config, llm_client)

    @property
    def system_prompt(self) -> str:
        return """You are an expert Affiliate Content Creator. You write high-converting
affiliate marketing content that balances genuine value with strategic monetization.

Your writing principles:
1. HONESTY FIRST: Include genuine pros AND cons. Readers trust honest reviews.
2. EXPERIENCE-BASED: Write as if you've used the products. Share specific use cases.
3. BUYER INTENT: Address the reader's actual purchase decision, not just features.
4. SEO-OPTIMIZED: Natural keyword integration, proper heading structure, meta descriptions.
5. CTA STRATEGY: Place affiliate links at decision points, not just randomly.
6. FTC COMPLIANT: Always include clear affiliate disclosure at the top of content.

Content quality standards:
- Every article must have a compelling hook in the first 50 words
- Use specific numbers, data points, and comparisons (not vague claims)
- Include screenshots, pros/cons tables, and comparison charts where relevant
- End with a clear recommendation and primary CTA
- Internal link to 2-3 related pieces of content

Affiliate link placement rules:
- First mention of a product (contextual link)
- In the pros/verdict section (decision point)
- In comparison tables (easy click opportunity)
- Final CTA section (direct recommendation)
- NEVER more than 1 affiliate link per 200 words"""

    def execute(self, task: str = "write_listicle", context: dict[str, Any] | None = None) -> AgentResult:
        self.log(f"Starting content creation: {task}")
        ctx = context or {}

        task_map = {
            "write_listicle": lambda: self.write_listicle(ctx.get("topic", ""), ctx.get("products", [])),
            "write_review": lambda: self.write_review(ctx.get("product", "")),
            "write_comparison": lambda: self.write_comparison(ctx.get("product_a", ""), ctx.get("product_b", "")),
            "write_tutorial": lambda: self.write_tutorial(ctx.get("tool", ""), ctx.get("goal", "")),
            "write_case_study": lambda: self.write_case_study(ctx.get("product", ""), ctx.get("duration", "30 days")),
            "write_video_script": lambda: self.write_video_script(ctx.get("topic", ""), ctx.get("platform", Platform.YOUTUBE_SHORTS)),
            "write_social_post": lambda: self.write_social_posts(ctx.get("topic", ""), ctx.get("platform", Platform.TWITTER)),
            "write_email": lambda: self.write_email(ctx.get("topic", ""), ctx.get("email_type", "newsletter")),
        }

        handler = task_map.get(task, lambda: self.write_listicle(ctx.get("topic", ""), ctx.get("products", [])))
        output = handler()

        return AgentResult(agent_name=self.name, task=task, output=output, success=True)

    def write_listicle(self, topic: str, products: list[str]) -> dict[str, Any]:
        """Write a 'Best X for Y' listicle article."""
        niche_config = NICHE_CONFIGS[self.config.selected_niche]
        products = products or niche_config.example_programs
        self.log(f"Writing listicle: {topic or 'Best tools'}")

        prompt = f"""Write a complete affiliate marketing listicle article.

Topic: {topic or f"Best {niche_config.name} Tools in 2026"}
Products to feature: {', '.join(products)}

Structure:
1. SEO-optimized title
2. Affiliate disclosure statement
3. Introduction with hook (why readers need this guide)
4. Quick comparison table (product, best for, price, our rating)
5. Each product section with:
   - H2 heading: "{{rank}}. {{Product}} — Best for {{use case}}"
   - Brief overview (2-3 sentences)
   - Key features (bullet list)
   - Pros and cons (honest!)
   - Pricing info
   - [Affiliate CTA button placeholder]
6. How we chose these tools (methodology)
7. FAQ section (3-5 common questions)
8. Final verdict and top recommendation

Target: 1,800-2,200 words
Include: [AFFILIATE_LINK] placeholders where links should go
Include: Meta description (under 155 characters)"""

        article = self.call_llm(prompt)

        return {
            "type": "listicle",
            "topic": topic or f"Best {niche_config.name} Tools in 2026",
            "products": products,
            "content": article,
            "word_count_target": "1800-2200",
            "seo_notes": "Include target keyword in title, H1, first paragraph, and 2-3 H2s",
        }

    def write_review(self, product: str) -> dict[str, Any]:
        """Write an in-depth honest product review."""
        self.log(f"Writing review: {product}")

        prompt = f"""Write a comprehensive, honest affiliate review of {product}.

Structure:
1. SEO title: "{product} Review 2026: Honest Pros, Cons & Verdict"
2. Affiliate disclosure
3. TL;DR verdict box (rating out of 10, one-line verdict, best for, not for)
4. What is {product}? (brief overview)
5. Key Features Deep Dive (top 5 features with real-world usage)
6. What I Like (genuine pros with specific examples)
7. What I Don't Like (honest cons — this builds trust!)
8. Pricing Breakdown (all tiers, what you get, value analysis)
9. {product} vs Top Alternatives (brief comparison table)
10. Who Should Use {product}? (specific audience segments)
11. Who Should NOT Use {product}? (important for trust)
12. Final Verdict + Rating
13. [CTA: Try {product} with affiliate link]
14. FAQ section

Target: 2,000-2,500 words
Tone: Knowledgeable friend giving honest advice, not a sales pitch"""

        review = self.call_llm(prompt)

        return {"type": "review", "product": product, "content": review}

    def write_comparison(self, product_a: str, product_b: str) -> dict[str, Any]:
        """Write a product vs product comparison article."""
        self.log(f"Writing comparison: {product_a} vs {product_b}")

        prompt = f"""Write a detailed comparison article: {product_a} vs {product_b}.

Structure:
1. Title: "{product_a} vs {product_b}: Which Is Better in 2026?"
2. Affiliate disclosure
3. Quick verdict box (winner for different use cases)
4. Comparison table (features, pricing, ratings side-by-side)
5. Overview of each product
6. Feature-by-feature comparison (5-7 key features)
7. Pricing comparison
8. Ease of use comparison
9. Customer support comparison
10. Final Verdict: When to choose {product_a} vs {product_b}
11. CTA for both products (affiliate links)

Target: 1,500-2,000 words
People searching "{product_a} vs {product_b}" are ready to buy — optimize for conversion."""

        comparison = self.call_llm(prompt)

        return {"type": "comparison", "products": [product_a, product_b], "content": comparison}

    def write_tutorial(self, tool: str, goal: str) -> dict[str, Any]:
        """Write a 'How I Use [Tool] to [Achieve Result]' tutorial."""
        self.log(f"Writing tutorial: {tool} for {goal}")

        prompt = f"""Write a tutorial article: "How to Use {tool} to {goal}"

Structure:
1. SEO title with the keyword
2. Affiliate disclosure
3. Introduction: Why {goal} matters and how {tool} helps
4. Prerequisites (what you need before starting)
5. Step-by-step guide (5-8 clear steps with details)
6. Pro tips and advanced techniques
7. Common mistakes to avoid
8. Results you can expect
9. Alternative tools for the same goal
10. Conclusion + CTA to try {tool}

Target: 1,500-2,000 words
Include [SCREENSHOT_PLACEHOLDER] markers where screenshots should go"""

        tutorial = self.call_llm(prompt)

        return {"type": "tutorial", "tool": tool, "goal": goal, "content": tutorial}

    def write_case_study(self, product: str, duration: str) -> dict[str, Any]:
        """Write an 'I Tried [X] for [Duration]' case study."""
        self.log(f"Writing case study: {product} for {duration}")

        prompt = f"""Write a case study: "I Tried {product} for {duration} — Here's What Happened"

Structure:
1. Attention-grabbing title
2. Affiliate disclosure
3. Hook: What made me try {product} (relatable pain point)
4. My starting point (before using {product})
5. Week-by-week / day-by-day experience
6. Specific results and metrics (use realistic numbers)
7. Unexpected discoveries (positive and negative)
8. What I wish I knew before starting
9. Is {product} worth it? (honest verdict)
10. My recommendation + who it's best for
11. CTA with affiliate link

Target: 2,000-2,500 words
Tone: Personal, authentic, storytelling format — this is YOUR experience"""

        case_study = self.call_llm(prompt)

        return {"type": "case_study", "product": product, "duration": duration, "content": case_study}

    def write_video_script(self, topic: str, platform: Platform) -> dict[str, Any]:
        """Write a video script for short-form or long-form content."""
        self.log(f"Writing video script: {topic} for {platform.value}")

        is_short = platform in (Platform.YOUTUBE_SHORTS, Platform.TIKTOK)

        prompt = f"""Write a {'60-second short-form' if is_short else '8-12 minute long-form'} video script.

Topic: {topic}
Platform: {platform.value}

{"Short-form structure:" if is_short else "Long-form structure:"}
{"1. HOOK (first 3 seconds): Pattern interrupt or bold claim" if is_short else "1. HOOK (first 15 seconds): Why viewers should keep watching"}
{"2. PROBLEM: Quick pain point" if is_short else "2. INTRO: What you'll cover and who this is for"}
{"3. SOLUTION: Show the tool/tip" if is_short else "3. MAIN CONTENT: Step-by-step demonstration"}
{"4. PROOF: Quick result or demo" if is_short else "4. RESULTS: Show outcomes and data"}
{"5. CTA: Link in bio/description" if is_short else "5. COMPARISON: Brief vs alternatives"}
{"" if is_short else "6. VERDICT: Honest recommendation"}
{"" if is_short else "7. CTA: Link in description + subscribe"}

Include:
- Exact spoken words (not just bullet points)
- [VISUAL] cues for what to show on screen
- Timing markers
- CTA with affiliate link placement"""

        script = self.call_llm(prompt)

        return {
            "type": "video_script",
            "platform": platform.value,
            "format": "short_form" if is_short else "long_form",
            "topic": topic,
            "script": script,
        }

    def write_social_posts(self, topic: str, platform: Platform) -> dict[str, Any]:
        """Write social media posts for distribution."""
        self.log(f"Writing social posts: {topic} for {platform.value}")

        prompt = f"""Write social media content for {platform.value} about: {topic}

{"Write a Twitter/X thread (5-7 tweets) that:" if platform == Platform.TWITTER else "Write a Reddit post that:"}
{"- Starts with a hook tweet" if platform == Platform.TWITTER else "- Provides genuine value (not salesy)"}
{"- Shares insights and actionable tips" if platform == Platform.TWITTER else "- Includes personal experience"}
{"- Includes affiliate mention naturally in tweet 5-6" if platform == Platform.TWITTER else "- Subtly mentions the tool as part of the solution"}
{"- Ends with CTA" if platform == Platform.TWITTER else "- Links to your full review/article"}

Make it valuable enough that people would share it even without the affiliate element."""

        posts = self.call_llm(prompt)

        return {"type": "social_post", "platform": platform.value, "topic": topic, "content": posts}

    def write_email(self, topic: str, email_type: str) -> dict[str, Any]:
        """Write email marketing content."""
        self.log(f"Writing email: {topic} ({email_type})")

        prompt = f"""Write an email for our affiliate marketing list.

Topic: {topic}
Type: {email_type}

Structure:
1. Subject line (aim for 40% open rate — use curiosity or specific benefit)
2. Preview text (complements subject line)
3. Opening hook (personal, conversational)
4. Value section (insight, tip, or story — 80% of the email)
5. Affiliate recommendation (naturally woven in — 20% of the email)
6. CTA (one clear action)
7. P.S. line (often the most-read part — add a second hook or urgency)

Rules:
- Write like a knowledgeable friend, not a marketer
- One affiliate product per email maximum
- Include FTC disclosure
- Keep under 500 words"""

        email = self.call_llm(prompt)

        return {"type": "email", "email_type": email_type, "topic": topic, "content": email}
