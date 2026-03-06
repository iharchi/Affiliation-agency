"""
Integration Configuration
Loads API keys and service configs from environment variables.
Each integration reports its connection status so you know what's live.
"""

import os
from dataclasses import dataclass, field


@dataclass
class Integration:
    name: str
    env_var: str
    required: bool
    description: str
    signup_url: str = ""
    connected: bool = False
    api_key: str = ""

    def load(self) -> "Integration":
        """Load API key from environment and set connection status."""
        self.api_key = os.getenv(self.env_var, "")
        self.connected = bool(self.api_key) and not self.api_key.startswith("your_")
        return self


@dataclass
class IntegrationGroup:
    name: str
    integrations: list[Integration] = field(default_factory=list)

    @property
    def any_connected(self) -> bool:
        return any(i.connected for i in self.integrations)

    @property
    def status_summary(self) -> dict[str, bool]:
        return {i.name: i.connected for i in self.integrations}


# ── All integrations organized by category ──

LLM_INTEGRATIONS = IntegrationGroup(
    name="LLM Provider (pick one)",
    integrations=[
        Integration(
            name="Anthropic (Claude)",
            env_var="ANTHROPIC_API_KEY",
            required=True,
            description="Powers all agent intelligence. Primary LLM.",
            signup_url="https://console.anthropic.com/",
        ),
        Integration(
            name="OpenAI (GPT-4)",
            env_var="OPENAI_API_KEY",
            required=False,
            description="Alternative LLM provider. Used if Anthropic key not set.",
            signup_url="https://platform.openai.com/api-keys",
        ),
    ],
)

AFFILIATE_INTEGRATIONS = IntegrationGroup(
    name="Affiliate Networks",
    integrations=[
        Integration(
            name="Amazon Associates",
            env_var="AMAZON_ASSOCIATE_TAG",
            required=False,
            description="Amazon affiliate tracking tag for product links.",
            signup_url="https://affiliate-program.amazon.com/",
        ),
        Integration(
            name="Impact.com",
            env_var="IMPACT_API_KEY",
            required=False,
            description="Affiliate network for Semrush, Canva, Coursera, Skillshare, etc.",
            signup_url="https://impact.com/",
        ),
        Integration(
            name="ShareASale",
            env_var="SHAREASALE_API_KEY",
            required=False,
            description="Affiliate network for mid-tier programs.",
            signup_url="https://www.shareasale.com/",
        ),
        Integration(
            name="CJ Affiliate",
            env_var="CJ_API_KEY",
            required=False,
            description="Commission Junction — large affiliate network.",
            signup_url="https://www.cj.com/",
        ),
    ],
)

EMAIL_INTEGRATIONS = IntegrationGroup(
    name="Email Marketing",
    integrations=[
        Integration(
            name="ConvertKit",
            env_var="CONVERTKIT_API_KEY",
            required=False,
            description="Email list management, sequences, and newsletters.",
            signup_url="https://convertkit.com/",
        ),
        Integration(
            name="ConvertKit Secret",
            env_var="CONVERTKIT_API_SECRET",
            required=False,
            description="ConvertKit API secret for subscriber management.",
        ),
    ],
)

SOCIAL_INTEGRATIONS = IntegrationGroup(
    name="Social Media",
    integrations=[
        Integration(
            name="Twitter/X API Key",
            env_var="TWITTER_API_KEY",
            required=False,
            description="Post threads, engage with audience on Twitter/X.",
            signup_url="https://developer.twitter.com/",
        ),
        Integration(
            name="Twitter/X API Secret",
            env_var="TWITTER_API_SECRET",
            required=False,
            description="Twitter API secret for OAuth.",
        ),
        Integration(
            name="Twitter/X Access Token",
            env_var="TWITTER_ACCESS_TOKEN",
            required=False,
            description="Twitter OAuth access token for posting.",
        ),
        Integration(
            name="Twitter/X Access Secret",
            env_var="TWITTER_ACCESS_TOKEN_SECRET",
            required=False,
            description="Twitter OAuth access token secret.",
        ),
        Integration(
            name="YouTube API",
            env_var="YOUTUBE_API_KEY",
            required=False,
            description="Upload Shorts/videos, track views and engagement.",
            signup_url="https://console.cloud.google.com/",
        ),
        Integration(
            name="Reddit Client ID",
            env_var="REDDIT_CLIENT_ID",
            required=False,
            description="Reddit API for community engagement and posting.",
            signup_url="https://www.reddit.com/prefs/apps",
        ),
        Integration(
            name="Reddit Client Secret",
            env_var="REDDIT_CLIENT_SECRET",
            required=False,
            description="Reddit API secret.",
        ),
        Integration(
            name="TikTok API",
            env_var="TIKTOK_API_KEY",
            required=False,
            description="Post short-form videos to TikTok.",
            signup_url="https://developers.tiktok.com/",
        ),
    ],
)

ANALYTICS_INTEGRATIONS = IntegrationGroup(
    name="Analytics & SEO",
    integrations=[
        Integration(
            name="Google Analytics",
            env_var="GOOGLE_ANALYTICS_ID",
            required=False,
            description="Track traffic, conversions, and user behavior.",
            signup_url="https://analytics.google.com/",
        ),
        Integration(
            name="Google Search Console",
            env_var="GOOGLE_SEARCH_CONSOLE_KEY",
            required=False,
            description="Keyword rankings and search performance.",
            signup_url="https://search.google.com/search-console/",
        ),
        Integration(
            name="SEMrush",
            env_var="SEMRUSH_API_KEY",
            required=False,
            description="Keyword research, competitor analysis, site audit.",
            signup_url="https://www.semrush.com/",
        ),
    ],
)

PUBLISHING_INTEGRATIONS = IntegrationGroup(
    name="Content Publishing",
    integrations=[
        Integration(
            name="WordPress",
            env_var="WORDPRESS_API_URL",
            required=False,
            description="Publish blog posts. Set to your WP REST API URL.",
            signup_url="https://wordpress.org/",
        ),
        Integration(
            name="WordPress Auth",
            env_var="WORDPRESS_AUTH_TOKEN",
            required=False,
            description="WordPress application password or JWT token.",
        ),
    ],
)

LINK_INTEGRATIONS = IntegrationGroup(
    name="Link Tracking",
    integrations=[
        Integration(
            name="Bitly",
            env_var="BITLY_API_KEY",
            required=False,
            description="Shorten and track affiliate link clicks.",
            signup_url="https://bitly.com/",
        ),
    ],
)

ALL_GROUPS = [
    LLM_INTEGRATIONS,
    AFFILIATE_INTEGRATIONS,
    EMAIL_INTEGRATIONS,
    SOCIAL_INTEGRATIONS,
    ANALYTICS_INTEGRATIONS,
    PUBLISHING_INTEGRATIONS,
    LINK_INTEGRATIONS,
]


def load_all_integrations() -> list[IntegrationGroup]:
    """Load all integrations from environment variables."""
    for group in ALL_GROUPS:
        for integration in group.integrations:
            integration.load()
    return ALL_GROUPS


def get_integration_status() -> dict[str, dict[str, bool]]:
    """Get connection status of all integrations."""
    load_all_integrations()
    return {group.name: group.status_summary for group in ALL_GROUPS}


def print_integration_status() -> None:
    """Print a formatted integration status report."""
    groups = load_all_integrations()
    print("\n  INTEGRATION STATUS")
    print("  " + "=" * 60)
    for group in groups:
        connected = sum(1 for i in group.integrations if i.connected)
        total = len(group.integrations)
        print(f"\n  {group.name} ({connected}/{total} connected)")
        print("  " + "-" * 50)
        for i in group.integrations:
            status = "OK" if i.connected else ".."
            req = " *" if i.required else ""
            print(f"    [{status}] {i.name:<30s}{req}")
            if not i.connected and i.signup_url:
                print(f"          {i.signup_url}")
    print()
    print("  * = required")
    print("  Set values in .env file, then restart.\n")
