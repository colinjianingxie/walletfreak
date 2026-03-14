"""Category hierarchy loader — deduplicated from update_cards_grok.py."""

import os
import json


def load_category_hierarchy(data_dir: str) -> str:
    """Load categories_list.json and format as a hierarchy string for LLM prompts.

    Args:
        data_dir: Path to walletfreak_data/ directory.

    Returns:
        Formatted string like "- **Dining**: Fine Dining, Fast Food, ..."
    """
    json_path = os.path.join(data_dir, 'categories_list.json')
    if not os.path.exists(json_path):
        return "No categories found."

    with open(json_path, 'r') as f:
        data = json.load(f)

    lines = []
    for item in data:
        parent = item.get('CategoryName')
        children = item.get('CategoryNameDetailed', [])
        if children:
            lines.append(f"- **{parent}**: {', '.join(children)}")
        else:
            lines.append(f"- **{parent}**")

    return "\n".join(lines)


def load_valid_categories(data_dir: str) -> set[str]:
    """Load a flat set of all valid category names (parents + children).

    Args:
        data_dir: Path to walletfreak_data/ directory.

    Returns:
        Set of all valid category strings.
    """
    json_path = os.path.join(data_dir, 'categories_list.json')
    if not os.path.exists(json_path):
        return set()

    with open(json_path, 'r') as f:
        data = json.load(f)

    categories = set()
    for item in data:
        parent = item.get('CategoryName')
        if parent:
            categories.add(parent)
        for child in item.get('CategoryNameDetailed', []):
            categories.add(child)

    return categories
