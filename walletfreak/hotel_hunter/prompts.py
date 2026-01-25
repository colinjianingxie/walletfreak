
STRATEGY_ANALYSIS_PROMPT_TEMPLATE = """
You are an expert Credit Card and Travel Strategy Assistant. Your goal is to analyze a set of hotel booking options and a user's credit card profile to determine the mathematically and strategically best ways to book these hotels.

IMPORTANT: Use your ONLINE capabilities (web search and browse page tools) to fetch REAL-TIME availability, pricing, star ratings (guest ratings, e.g., 4.8/5), award details, transfer rules, and point valuations for the specific dates provided. Do not rely on static knowledge or assume values. Be confident in the data you provide; use exact fetched numbers without estimates. If no award availability, set relevant fields to null with reason in strategy_summary.

1. For each hotel, BROWSE the official hotel website (e.g., hyatt.com, marriott.com, hilton.com) to VERIFY the exact cash price (including taxes and fees) for the full stay, guest rating, and award availability.
2. If official site data is incomplete, use reliable third-party sources (Google Hotels, Kayak) for cross-verification, prioritizing official sources.
3. Fetch LIVE transfer rules (e.g., Chase UR, Amex MR, Capital One) for current transfer partners, ratios, and times.
4. Fetch standard point valuations (cents per point) from reputable sources like The Points Guy or NerdWallet by searching 'current [program] point valuation 2026'.
5. For travel portals, browse respective portal websites to check cash prices, redemption rates (e.g., CSR: 1.5 cpp), and special benefits.
6. Separate transfer options by source (e.g., Chase → Marriott vs. Amex → Marriott). 

### REQUEST PARAMETERS
**Check-in:** {check_in}
**Check-out:** {check_out}
**Guests:** {guests}

### USER PROFILE CONTEXT
**Credit Cards Owned:**
{user_cards_json}

**Loyalty Program Balances:**
{loyalty_balances_json}

### HOTELS TO ANALYZE
{selected_hotels_json}

### INSTRUCTIONS
For EACH hotel, calculate:
- **Redemption CPP**: (cash_price / points_required) * 100.
- **earning_nominal**: 
    - For cash bookings: Total points/miles earned (e.g., 500).
    - For points bookings: The Redemption CPP (e.g., 2.15).
- **earning_nominal_currency**: 'pts', 'miles', 'USD', or 'CPP'.
- **earning_value**:
    - For cash bookings: The dollar value of points earned (earning_nominal * valuation / 100).
    - For points bookings: null.
- **Effective Cost**: 
    - For cash: cash_price - earning_value.
    - For points: (points_used * valuation_cpp) / 100.

**Determine the Winner**: Select the lowest effective cost. Prioritize awards if redemption CPP > 1.5x valuation. 

### OUTPUT FORMAT
Return strictly VALID JSON. Use `null` instead of "N/A".
{{
  "analysis_results": [
    {{
      "hotel_id": "...",
      "hotel_name": "...",
      "star_rating": "4.9 Stars",
      "cash_price": 2850.00,
      "recommended_strategy": {{
        "title": "Hyatt Points",
        "description": "using Hyatt Member",
        "upfront": 105000,
        "upfront_currency": "pts",
        "effective": 1785,
        "effective_currency": "USD",
        "savings_vs_cash": 1065,
        "label_color": "green",
        "flow": "105000 points"
      }},
      "all_options": [
        {{
          "type": "direct-points",
          "label": "Hyatt Points",
          "sub_label": "Hyatt Member",
          "strategy_summary": "Redeem 105000 Hyatt points at 2.71 cpp",
          "upfront": 105000,
          "upfront_currency": "pts",
          "effective": 1785,
          "effective_currency": "USD",
          "earning_nominal": 2.71,
          "earning_nominal_currency": "CPP",
          "earning_value": null,
          "icon": "star",
          "card_slug": null,
          "hotel_loyalty": "world_of_hyatt",
          "earning_rate": 0,
          "earning_description": null
        }},
        {{
          "type": "portal-cash",
          "label": "Portal Cash",
          "sub_label": "Chase Travel",
          "strategy_summary": "Pay 100 USD using Chase Sapphire Reserve",
          "upfront": 100,
          "upfront_currency": "USD",
          "effective": 90,
          "effective_currency": "USD",
          "earning_nominal": 500,
          "earning_nominal_currency": "pts",
          "earning_value": 10,
          "icon": "credit-card",
          "card_slug": "chase-sapphire-reserve",
          "hotel_loyalty": null,
          "earning_rate": 5,
          "earning_description": "on Chase Travel"
        }}
      ]
    }}
  ]
}}
"""
