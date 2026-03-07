"""
Link Tracker Utility
Manages affiliate link creation, UTM parameters, click tracking, and link auditing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse


@dataclass
class AffiliateLink:
    program: str
    base_url: str
    affiliate_tag: str
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    utm_content: str = ""
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class LinkTracker:
    """Manages affiliate links with UTM tracking and performance metrics."""

    def __init__(self, db_conn: Any = None):
        self.db_conn = db_conn
        self.links: dict[str, AffiliateLink] = {}
        self._load_from_db()

    def _load_from_db(self) -> None:
        if not self.db_conn:
            return
        from utils.persistence import load_affiliate_links
        for link_id, data in load_affiliate_links(self.db_conn).items():
            self.links[link_id] = AffiliateLink(
                program=data["program"], base_url=data["base_url"],
                affiliate_tag=data["affiliate_tag"],
                utm_source=data.get("utm_source", ""),
                utm_medium=data.get("utm_medium", ""),
                utm_campaign=data.get("utm_campaign", ""),
                utm_content=data.get("utm_content", ""),
                clicks=data.get("clicks", 0),
                conversions=data.get("conversions", 0),
                revenue=data.get("revenue", 0.0),
                created_at=data.get("created_at", ""),
            )

    def create_link(
        self,
        link_id: str,
        program: str,
        base_url: str,
        affiliate_tag: str,
        source: str = "website",
        medium: str = "affiliate",
        campaign: str = "",
        content: str = "",
    ) -> str:
        """Create a tracked affiliate link with UTM parameters."""
        link = AffiliateLink(
            program=program,
            base_url=base_url,
            affiliate_tag=affiliate_tag,
            utm_source=source,
            utm_medium=medium,
            utm_campaign=campaign,
            utm_content=content,
        )
        self.links[link_id] = link
        if self.db_conn:
            from utils.persistence import save_affiliate_link
            save_affiliate_link(self.db_conn, link_id, program, base_url,
                                affiliate_tag, source, medium, campaign, content)
        return self.build_url(link)

    def build_url(self, link: AffiliateLink) -> str:
        """Build the full tracked URL with UTM parameters."""
        parsed = urlparse(link.base_url)
        params = parse_qs(parsed.query)

        # Add affiliate tag
        if link.affiliate_tag:
            params["ref"] = [link.affiliate_tag]

        # Add UTM parameters
        if link.utm_source:
            params["utm_source"] = [link.utm_source]
        if link.utm_medium:
            params["utm_medium"] = [link.utm_medium]
        if link.utm_campaign:
            params["utm_campaign"] = [link.utm_campaign]
        if link.utm_content:
            params["utm_content"] = [link.utm_content]

        # Flatten params for urlencode
        flat_params = {k: v[0] for k, v in params.items()}
        new_query = urlencode(flat_params)

        return urlunparse(parsed._replace(query=new_query))

    def record_click(self, link_id: str) -> bool:
        if link_id in self.links:
            self.links[link_id].clicks += 1
            if self.db_conn:
                from utils.persistence import update_link_clicks
                update_link_clicks(self.db_conn, link_id)
            return True
        return False

    def record_conversion(self, link_id: str, revenue: float) -> bool:
        if link_id in self.links:
            self.links[link_id].conversions += 1
            self.links[link_id].revenue += revenue
            if self.db_conn:
                from utils.persistence import update_link_conversion
                update_link_conversion(self.db_conn, link_id, revenue)
            return True
        return False

    def get_performance(self, link_id: str) -> dict[str, Any] | None:
        link = self.links.get(link_id)
        if not link:
            return None
        return {
            "link_id": link_id,
            "program": link.program,
            "clicks": link.clicks,
            "conversions": link.conversions,
            "revenue": round(link.revenue, 2),
            "epc": round(link.revenue / link.clicks, 2) if link.clicks > 0 else 0,
            "conversion_rate": round(link.conversions / link.clicks * 100, 2) if link.clicks > 0 else 0,
        }

    def get_all_performance(self) -> list[dict[str, Any]]:
        return [self.get_performance(lid) for lid in self.links if self.get_performance(lid)]

    def get_top_performers(self, metric: str = "revenue", limit: int = 5) -> list[dict[str, Any]]:
        all_perf = self.get_all_performance()
        return sorted(all_perf, key=lambda x: x.get(metric, 0), reverse=True)[:limit]
