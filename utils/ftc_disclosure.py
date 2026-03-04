"""
FTC Disclosure Generator
Ensures all affiliate content includes proper FTC-compliant disclosures.
"""

DISCLOSURES = {
    "standard": (
        "Disclosure: Some of the links in this article are affiliate links. "
        "This means that, at no additional cost to you, I may earn a commission "
        "if you click through and make a purchase. I only recommend products I "
        "genuinely believe in."
    ),
    "short": (
        "This post contains affiliate links. I may earn a commission at no cost to you."
    ),
    "detailed": (
        "Affiliate Disclosure: This content contains affiliate links. When you "
        "buy through these links, I may earn a commission at no extra cost to you. "
        "I only recommend products and services I've personally used or thoroughly "
        "researched. My opinions are my own and are not influenced by commissions. "
        "Thank you for supporting my work!"
    ),
    "video": (
        "Some links in the description are affiliate links. If you purchase "
        "through them, I earn a small commission at no extra cost to you. "
        "Thanks for supporting the channel!"
    ),
    "email": (
        "Note: This email contains affiliate recommendations. If you purchase "
        "through my links, I may earn a commission at no additional cost to you. "
        "I only share products I genuinely recommend."
    ),
    "social": (
        "#ad | Contains affiliate links"
    ),
}


def get_disclosure(content_type: str = "standard") -> str:
    """Return the appropriate FTC disclosure for the content type."""
    return DISCLOSURES.get(content_type, DISCLOSURES["standard"])


def wrap_content_with_disclosure(content: str, content_type: str = "standard") -> str:
    """Prepend FTC disclosure to content."""
    disclosure = get_disclosure(content_type)
    return f"{disclosure}\n\n---\n\n{content}"
