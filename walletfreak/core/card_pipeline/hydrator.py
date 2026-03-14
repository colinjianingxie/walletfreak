"""Hydrator — reads relational files and assembles monolithic dict for LLM context.

Extracted from update_cards_grok.py:181-261.
"""

import os
import json
import logging
from pydantic import ValidationError
from .models import CardData

logger = logging.getLogger(__name__)


def hydrate_card(
    master_dir: str,
    slug: str,
    update_types: list[str] | None = None,
    validate: bool = False,
) -> dict:
    """Read relational files for a card and re-assemble into a single dict.

    Args:
        master_dir: Path to master_cards/ directory.
        slug: Card slug identifier.
        update_types: Which components to load (header, benefits, rates, bonus, questions).
                      If None, loads all except header.
        validate: If True, validate the result against the CardData Pydantic model.

    Returns:
        Monolithic card dict suitable for LLM context or further processing.
    """
    if update_types is None:
        update_types = ['bonus', 'benefits', 'rates', 'questions']

    card_dir = os.path.join(master_dir, slug)
    header_path = os.path.join(card_dir, 'header.json')

    # New card template
    if not os.path.exists(header_path):
        data = {
            "slug-id": slug,
            "name": slug.replace('-', ' ').title(),
            "issuer": "",
            "image_url": "",
            "application_link": "",
            "is_524": False,
            "active_indices": {
                "benefits": [],
                "earning_rates": [],
                "sign_up_bonus": [],
            },
            "benefits": [] if 'benefits' in update_types else None,
            "earning_rates": [] if 'rates' in update_types else None,
            "sign_up_bonus": [] if 'bonus' in update_types else None,
            "questions": [] if 'questions' in update_types else None,
        }
        return data

    # Existing card
    with open(header_path, 'r') as f:
        data = json.load(f)

    active_indices = data.get('active_indices', {})

    def load_sub_items(directory: str, id_list: list[str]) -> list[dict]:
        items = []
        subdir_path = os.path.join(card_dir, directory)
        if not os.path.exists(subdir_path):
            return items
        for item_id in id_list:
            item_path = os.path.join(subdir_path, f"{item_id}.json")
            if os.path.exists(item_path):
                with open(item_path, 'r') as f:
                    items.append(json.load(f))
        return items

    # Only load components that will be updated
    if 'benefits' in update_types:
        data['benefits'] = load_sub_items('benefits', active_indices.get('benefits', []))
    else:
        data['benefits'] = None

    if 'rates' in update_types:
        data['earning_rates'] = load_sub_items('earning_rates', active_indices.get('earning_rates', []))
    else:
        data['earning_rates'] = None

    if 'bonus' in update_types:
        data['sign_up_bonus'] = load_sub_items('sign_up_bonus', active_indices.get('sign_up_bonus', []))
    else:
        data['sign_up_bonus'] = None

    if 'questions' in update_types:
        questions = []
        q_dir = os.path.join(card_dir, 'card_questions')
        if os.path.exists(q_dir):
            for fname in sorted(os.listdir(q_dir)):
                if fname.endswith('.json'):
                    with open(os.path.join(q_dir, fname), 'r') as f:
                        questions.append(json.load(f))
        data['questions'] = questions
    else:
        data['questions'] = None

    if validate:
        try:
            CardData.model_validate(data)
        except ValidationError as e:
            logger.warning("Hydrated card %s failed validation: %s", slug, e)

    return data
