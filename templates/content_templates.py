"""
Content Templates
Reusable templates for various affiliate content formats.
"""

LISTICLE_TEMPLATE = """# {title}

{disclosure}

{intro}

## Quick Comparison

| Tool | Best For | Price | Rating |
|------|----------|-------|--------|
{comparison_table}

{product_sections}

## How We Chose These Tools

{methodology}

## FAQ

{faq}

## Final Verdict

{verdict}
"""

REVIEW_TEMPLATE = """# {product} Review {year}: Honest Pros, Cons & Verdict

{disclosure}

## TL;DR

- **Rating:** {rating}/10
- **Best for:** {best_for}
- **Not for:** {not_for}
- **Verdict:** {one_line_verdict}

---

## What Is {product}?

{overview}

## Key Features

{features}

## What I Like (Pros)

{pros}

## What I Don't Like (Cons)

{cons}

## Pricing

{pricing}

## {product} vs Alternatives

| Feature | {product} | {alt_1} | {alt_2} |
|---------|-----------|---------|---------|
{alt_comparison}

## Who Should Use {product}?

{ideal_user}

## Who Should NOT Use {product}?

{not_ideal}

## Final Verdict: {rating}/10

{final_verdict}

[**Try {product} →**]({affiliate_link})

## FAQ

{faq}
"""

COMPARISON_TEMPLATE = """# {product_a} vs {product_b}: Which Is Better in {year}?

{disclosure}

## Quick Verdict

{quick_verdict}

## Side-by-Side Comparison

| Feature | {product_a} | {product_b} |
|---------|-------------|-------------|
{comparison_table}

## {product_a} Overview

{product_a_overview}

## {product_b} Overview

{product_b_overview}

## Feature Comparison

{feature_comparison}

## Pricing Comparison

{pricing_comparison}

## Final Verdict

{final_verdict}

- [**Try {product_a} →**]({affiliate_link_a})
- [**Try {product_b} →**]({affiliate_link_b})
"""

VIDEO_SCRIPT_SHORT = """[DURATION: 60 seconds]

[0-3s] HOOK:
{hook}

[3-10s] PROBLEM:
{problem}

[10-35s] SOLUTION:
{solution}

[35-50s] PROOF:
{proof}

[50-60s] CTA:
{cta}

---
DESCRIPTION:
{description}

HASHTAGS:
{hashtags}
"""

EMAIL_TEMPLATE = """Subject: {subject}
Preview: {preview}

---

{greeting}

{hook}

{value_section}

{affiliate_recommendation}

{cta}

{signoff}

P.S. {ps_line}

---
{disclosure}
"""
