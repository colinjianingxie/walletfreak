"""Prompt templates for automated blog article generation."""

from datetime import date


def build_topic_discovery_prompt(today: date | None = None) -> str:
    """Build a prompt that asks Grok to find a trending credit card / travel topic."""
    today = today or date.today()
    return f"""Search the web for the most recent and newsworthy credit card or credit card travel news as of {today.strftime('%B %d, %Y')}.

Consider topics like:
- New credit card launches or refreshes
- Sign-up bonus increases or limited-time offers
- Benefit changes, devaluations, or improvements
- Travel deals, lounge openings, or airport experience changes
- Airline or hotel loyalty program changes
- Transfer partner additions or bonus transfer promotions
- Regulatory changes affecting credit cards or rewards

Pick the single most interesting and timely topic that credit card enthusiasts would want to read about right now.

Return valid JSON (no markdown fences):
{{"topic": "concise topic title", "angle": "the specific angle or hook for the article", "keywords": ["keyword1", "keyword2", "keyword3"], "category": "credit-cards or travel", "experience_level": "beginner or intermediate or advanced"}}"""


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
- Data-driven and authoritative but conversational — like a knowledgeable friend who works in credit cards
- Use specific numbers, card names, dates, and actionable advice
- Reference real programs, point values, and redemption strategies
- Include a compelling opening that hooks the reader
- End with clear, actionable takeaways

Here are credit cards in our database you can reference where relevant (don't force them in): {cards_str}

Format requirements:
- Use Markdown with ## headings (not # or ###)
- Use bullet lists, bold for emphasis, and numbered lists where comparing options
- Do NOT include images or image links in the body
- Do NOT include word counts, "(Word count: X)" lines, or any meta-commentary about the article itself
- Length: 800-1500 words (aim for a {experience_level}-level audience)

Return valid JSON (no markdown fences):
{{"title": "compelling article title", "excerpt": "2-3 sentence summary that hooks readers", "content": "full markdown article body", "tags": "{category}, news or guide or analysis", "vendor": "primary card issuer mentioned (Chase, Amex, Capital One, etc) or empty string if multiple/none", "experience_level": "{experience_level}", "read_time": "short or medium or long based on actual length"}}"""
