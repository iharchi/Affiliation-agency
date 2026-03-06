"""
Affiliate Marketing Agency - Configuration Settings
Central configuration for all agents, niches, programs, and workflows.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Niche(Enum):
    AI_SAAS = "ai_saas_tools"
    ONLINE_EDUCATION = "online_education"
    WEB_HOSTING = "web_hosting"
    PERSONAL_FINANCE = "personal_finance"
    HEALTH_WELLNESS = "health_wellness"


class ContentFormat(Enum):
    LISTICLE = "best_x_for_y"
    COMPARISON = "product_vs_product"
    REVIEW = "honest_review"
    TUTORIAL = "how_to_guide"
    CASE_STUDY = "i_tried_x"


class Platform(Enum):
    YOUTUBE_SHORTS = "youtube_shorts"
    TIKTOK = "tiktok"
    BLOG = "blog"
    TWITTER = "twitter_x"
    REDDIT = "reddit"
    MEDIUM = "medium"
    SUBSTACK = "substack"
    YOUTUBE_LONG = "youtube_long"
    EMAIL = "email"


@dataclass
class NicheConfig:
    name: str
    niche: Niche
    commission_range: str
    example_programs: list[str]
    keywords: list[str]
    buyer_intent_phrases: list[str]


@dataclass
class AffiliateProgram:
    name: str
    network: str
    commission_type: str  # "recurring", "one_time", "per_lead"
    commission_range: str
    cookie_duration_days: int
    niche: Niche
    signup_url: str = ""
    notes: str = ""


@dataclass
class RevenueTargets:
    tier: str  # "conservative", "moderate", "aggressive"
    monthly_traffic: tuple[int, int]
    ctr: tuple[float, float]
    conversion_rate: tuple[float, float]
    avg_commission: tuple[float, float]
    monthly_revenue: tuple[float, float]


@dataclass
class AgencyConfig:
    selected_niche: Niche = Niche.AI_SAAS
    content_per_day: int = 1
    primary_platforms: list[Platform] = field(
        default_factory=lambda: [Platform.YOUTUBE_SHORTS, Platform.TIKTOK]
    )
    secondary_platforms: list[Platform] = field(
        default_factory=lambda: [Platform.BLOG, Platform.TWITTER, Platform.REDDIT]
    )
    revenue_target: str = "moderate"
    budget_monthly: float = 45.0
    email_tool: str = "convertkit"
    link_tracker: str = "bitly"


# Pre-configured niche data
NICHE_CONFIGS = {
    Niche.AI_SAAS: NicheConfig(
        name="AI & SaaS Tools",
        niche=Niche.AI_SAAS,
        commission_range="$20–$200/mo recurring",
        example_programs=["Jasper", "Surfer SEO", "Semrush", "Notion", "Canva", "ConvertKit"],
        keywords=[
            "best ai writing tools", "ai tools for business", "saas tools review",
            "ai productivity tools", "chatgpt alternatives", "ai content creation",
        ],
        buyer_intent_phrases=[
            "best {tool} alternative", "is {tool} worth it", "{tool} vs {competitor}",
            "{tool} honest review 2026", "best ai tools for {use_case}",
        ],
    ),
    Niche.ONLINE_EDUCATION: NicheConfig(
        name="Online Education",
        niche=Niche.ONLINE_EDUCATION,
        commission_range="$50–$500 per sale",
        example_programs=["Coursera", "Skillshare", "Udemy", "MasterClass", "LinkedIn Learning"],
        keywords=[
            "best online courses", "learn coding online", "online degree programs",
            "best skillshare classes", "udemy course review",
        ],
        buyer_intent_phrases=[
            "best online course for {topic}", "is {platform} worth it",
            "{platform} vs {competitor}", "best {topic} certification",
        ],
    ),
    Niche.WEB_HOSTING: NicheConfig(
        name="Web Hosting & Domains",
        niche=Niche.WEB_HOSTING,
        commission_range="$50–$200 per signup",
        example_programs=["Bluehost", "SiteGround", "Namecheap", "Hostinger", "Cloudways"],
        keywords=[
            "best web hosting", "cheap wordpress hosting", "fastest web hosting",
            "best hosting for beginners", "web hosting comparison",
        ],
        buyer_intent_phrases=[
            "best hosting for {use_case}", "{host} vs {competitor}",
            "is {host} good for wordpress", "{host} review 2026",
        ],
    ),
    Niche.PERSONAL_FINANCE: NicheConfig(
        name="Personal Finance",
        niche=Niche.PERSONAL_FINANCE,
        commission_range="$25–$100 per lead",
        example_programs=["Credit Karma", "Wealthfront", "YNAB", "Acorns", "Betterment"],
        keywords=[
            "best budgeting apps", "best investment apps", "robo advisor review",
            "best savings accounts", "credit card comparison",
        ],
        buyer_intent_phrases=[
            "best {product} for {audience}", "is {product} safe",
            "{product} vs {competitor}", "best credit cards 2026",
        ],
    ),
    Niche.HEALTH_WELLNESS: NicheConfig(
        name="Health & Wellness",
        niche=Niche.HEALTH_WELLNESS,
        commission_range="$15–$80 per sale",
        example_programs=["Athletic Greens", "Noom", "MyFitnessPal", "Ritual", "Peloton"],
        keywords=[
            "best supplements", "best fitness apps", "healthy meal delivery",
            "best protein powder", "wellness products review",
        ],
        buyer_intent_phrases=[
            "best {product} for {goal}", "is {product} worth it",
            "{product} vs {competitor}", "best {category} 2026",
        ],
    ),
}

REVENUE_TARGETS = {
    "conservative": RevenueTargets(
        tier="conservative",
        monthly_traffic=(500, 1000),
        ctr=(0.03, 0.05),
        conversion_rate=(0.01, 0.02),
        avg_commission=(20, 50),
        monthly_revenue=(50, 200),
    ),
    "moderate": RevenueTargets(
        tier="moderate",
        monthly_traffic=(1000, 3000),
        ctr=(0.05, 0.08),
        conversion_rate=(0.02, 0.05),
        avg_commission=(30, 75),
        monthly_revenue=(200, 800),
    ),
    "aggressive": RevenueTargets(
        tier="aggressive",
        monthly_traffic=(3000, 5000),
        ctr=(0.08, 0.12),
        conversion_rate=(0.05, 0.10),
        avg_commission=(50, 150),
        monthly_revenue=(800, 2000),
    ),
}

AFFILIATE_PROGRAMS = [
    AffiliateProgram("Amazon Associates", "Amazon", "one_time", "1–10%", 24, Niche.AI_SAAS),
    AffiliateProgram("Jasper AI", "Direct", "recurring", "30%", 30, Niche.AI_SAAS),
    AffiliateProgram("Surfer SEO", "Direct", "recurring", "25%", 30, Niche.AI_SAAS),
    AffiliateProgram("Semrush", "Impact", "recurring", "$200/sale", 120, Niche.AI_SAAS),
    AffiliateProgram("Notion", "Direct", "one_time", "50%", 90, Niche.AI_SAAS),
    AffiliateProgram("Canva", "Impact", "one_time", "$36/sale", 30, Niche.AI_SAAS),
    AffiliateProgram("ConvertKit", "Direct", "recurring", "30%", 90, Niche.AI_SAAS),
    AffiliateProgram("Bluehost", "Direct", "one_time", "$65/sale", 90, Niche.WEB_HOSTING),
    AffiliateProgram("SiteGround", "Direct", "one_time", "$50–$100/sale", 60, Niche.WEB_HOSTING),
    AffiliateProgram("Coursera", "Impact", "one_time", "15–45%", 30, Niche.ONLINE_EDUCATION),
    AffiliateProgram("Skillshare", "Impact", "one_time", "$7/referral", 30, Niche.ONLINE_EDUCATION),
    AffiliateProgram("ClickFunnels", "Direct", "recurring", "30%", 45, Niche.AI_SAAS),
    AffiliateProgram("Kajabi", "Direct", "recurring", "30%", 30, Niche.ONLINE_EDUCATION),
    AffiliateProgram("HubSpot", "Impact", "one_time", "$250–$1000/sale", 90, Niche.AI_SAAS),
]
