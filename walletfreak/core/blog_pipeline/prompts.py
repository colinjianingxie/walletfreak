"""Prompt templates for automated blog article generation."""

import random
from datetime import date

# Topic categories used to encourage variety across runs.
_TOPIC_CATEGORIES = [
    "sign-up bonuses",
    "credit card comparisons",
    "points and miles strategy",
    "cash back optimization",
    "new card launches",
    "credit card benefit changes",
    "hotel loyalty programs",
    "travel planning with points",
    "transfer partner deals",
    "business credit cards",
    "credit score and approval tips",
    "annual fee analysis",
    "dining and grocery rewards",
    "gas and commuting rewards",
    "student and starter cards",
    "premium card showdowns",
    "credit card regulatory news",
    "points valuations and devaluations",
    "limited-time promotions",
    "trip report and redemption stories",
]


def build_topic_discovery_prompt(today: date | None = None,
                                  recent_titles: list[str] | None = None) -> str:
    """Build a prompt that asks Grok to find a trending credit card topic.

    A random category hint is included to encourage the model to explore
    different areas of credit-card content across successive runs.
    Recent article titles are injected so the model avoids repeating topics.
    """
    today = today or date.today()
    # Pick 3 random categories to nudge the model toward variety
    hints = random.sample(_TOPIC_CATEGORIES, k=3)
    hints_str = ", ".join(hints)

    # Build deduplication block from recent articles
    dedup_block = ""
    if recent_titles:
        titles_list = "\n".join(f"- {t}" for t in recent_titles)
        dedup_block = f"""

CRITICAL — AVOID DUPLICATE TOPICS: We have already published these articles recently. You MUST pick a COMPLETELY DIFFERENT topic. Do NOT write about any subject even loosely related to these:
{titles_list}

If the top trending story is already covered above, find the NEXT most interesting story on a different subject."""

    return f"""Search the web for the most recent and newsworthy credit card news as of {today.strftime('%B %d, %Y')}.

You should cover the FULL breadth of credit card content. Explore a wide variety of topics, such as:

**Sign-up Bonuses & Promotions**
- New or increased sign-up bonus offers
- Limited-time welcome offers or spending bonuses
- Referral bonus changes

**Card Launches & Product Changes**
- Brand-new credit card launches or major card refreshes
- Benefit additions, removals, or devaluations
- Annual fee changes

**Points, Miles & Rewards Strategy**
- Best ways to earn and redeem points for maximum value
- Points and miles valuation updates
- Cash back vs. points debates and strategy

**Transfer Partners & Loyalty Programs**
- New transfer partner additions
- Bonus transfer promotions (e.g., 30% transfer bonus to airline/hotel)
- Hotel loyalty program updates (earning, elite status changes)
- Airline loyalty program changes

**Travel Planning & Redemptions**
- How to plan trips using points and miles
- Sweet-spot award redemptions (flights, hotels)
- Travel portal vs. transfer partner booking comparisons

**Credit Card Comparisons & Guides**
- Head-to-head card comparisons (e.g., Sapphire Preferred vs. Venture X)
- Best cards for specific categories (dining, groceries, gas, streaming)
- Best starter or student credit cards
- Best business credit cards

**Industry & Regulatory News**
- CFPB rulings, late fee changes, interest rate regulations
- Issuer policy changes (Chase 5/24, Amex pop-up, etc.)
- Credit score tips and approval strategies

**Category Spend Optimization**
- Maximizing rewards on dining, groceries, gas, travel, online shopping
- Quarterly bonus category strategies
- Stacking deals with shopping portals

Today's focus hint (pick from these if something newsworthy fits, but you may choose ANY credit card topic): {hints_str}
{dedup_block}

Pick the single most interesting and timely topic that credit card enthusiasts would want to read about right now.

Return valid JSON (no markdown fences):
{{"topic": "concise topic title", "angle": "the specific angle or hook for the article", "keywords": ["keyword1", "keyword2", "keyword3"], "category": "credit-cards or travel or rewards-strategy or industry-news", "experience_level": "beginner or intermediate or advanced"}}"""


def build_article_generation_prompt(topic: str, angle: str, keywords: list[str],
                                     category: str, experience_level: str,
                                     card_names: list[str]) -> str:
    """Build a prompt that asks Grok to write a full blog article."""
    cards_str = ", ".join(card_names[:50])  # Cap to avoid huge prompts
    keywords_str = ", ".join(keywords)

    return f"""Write a blog article for WalletFreak ("The Ledger") about: {topic}
Angle: {angle}
Keywords: {keywords_str}

Style guidelines:
- Data-driven and authoritative but conversational — like a knowledgeable friend who is a credit card expert
- Use specific numbers, card names, dates, and actionable advice
- Reference real programs, point values, and redemption strategies where relevant
- Include a compelling opening that hooks the reader with a clear value proposition
- End with clear, actionable takeaways the reader can use immediately
- If comparing cards or strategies, use concrete numbers and real-world examples
- Avoid generic filler — every paragraph should deliver value

Here are credit cards in our database you can reference where relevant (don't force them in): {cards_str}

Format requirements:
- Use Markdown with ## headings (not # or ###)
- Use bullet lists, bold for emphasis, and numbered lists where comparing options
- Do NOT include images or image links in the body
- Do NOT include word counts, "(Word count: X)" lines, or any meta-commentary about the article itself
- Length: 800-1500 words (aim for a {experience_level}-level audience)

Return valid JSON (no markdown fences):
{{"title": "compelling article title", "excerpt": "2-3 sentence summary that hooks readers", "content": "full markdown article body", "tags": "{category}, news or guide or analysis", "vendor": "primary card issuer mentioned (Chase, Amex, Capital One, etc) or empty string if multiple/none", "experience_level": "{experience_level}", "read_time": "short or medium or long based on actual length"}}"""
