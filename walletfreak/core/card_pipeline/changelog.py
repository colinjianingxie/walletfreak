"""Changelog tracking for card updates."""

import os
import json
import logging
from datetime import datetime
from .models import ChangelogEntry, FieldChange, ItemChange

logger = logging.getLogger(__name__)


class ChangeTracker:
    """Accumulates changes during dehydration for a single card."""

    def __init__(self, slug: str, run_id: str = ""):
        self.slug = slug
        self.run_id = run_id
        self._header_changes: list[FieldChange] = []
        self._benefits_changes: list[ItemChange] = []
        self._earning_rates_changes: list[ItemChange] = []
        self._sign_up_bonus_changes: list[ItemChange] = []

    def record_header_change(self, field: str, old, new):
        self._header_changes.append(FieldChange(field=field, old=old, new=new))

    def record_item_created(self, section: str, item_id: str, vid: str):
        changes_list = self._get_section_list(section)
        changes_list.append(ItemChange(
            action="created",
            item_id=item_id,
            new_vid=vid,
        ))

    def record_item_updated(self, section: str, item_id: str, old_vid: str,
                            new_vid: str, changes: list[FieldChange]):
        changes_list = self._get_section_list(section)
        changes_list.append(ItemChange(
            action="updated",
            item_id=item_id,
            old_vid=old_vid,
            new_vid=new_vid,
            changes=changes,
        ))

    def record_item_deprecated(self, section: str, item_id: str, vid: str):
        changes_list = self._get_section_list(section)
        changes_list.append(ItemChange(
            action="deprecated",
            item_id=item_id,
            old_vid=vid,
        ))

    def record_cosmetic_update(self, section: str, item_id: str, vid: str,
                               changes: list[FieldChange]):
        changes_list = self._get_section_list(section)
        changes_list.append(ItemChange(
            action="cosmetic_update",
            item_id=item_id,
            old_vid=vid,
            new_vid=vid,
            changes=changes,
        ))

    def _get_section_list(self, section: str) -> list[ItemChange]:
        mapping = {
            'benefits': self._benefits_changes,
            'earning_rates': self._earning_rates_changes,
            'sign_up_bonus': self._sign_up_bonus_changes,
        }
        return mapping.get(section, self._benefits_changes)

    def has_changes(self) -> bool:
        return bool(
            self._header_changes
            or self._benefits_changes
            or self._earning_rates_changes
            or self._sign_up_bonus_changes
        )

    def finalize(self) -> ChangelogEntry:
        parts = []
        if self._header_changes:
            parts.append(f"{len(self._header_changes)} header field(s)")
        for name, changes in [
            ("benefit", self._benefits_changes),
            ("earning_rate", self._earning_rates_changes),
            ("sign_up_bonus", self._sign_up_bonus_changes),
        ]:
            if changes:
                by_action = {}
                for c in changes:
                    by_action.setdefault(c.action, 0)
                    by_action[c.action] += 1
                for action, count in by_action.items():
                    parts.append(f"{count} {name}(s) {action}")

        summary = ", ".join(parts) if parts else "no changes"

        return ChangelogEntry(
            slug=self.slug,
            timestamp=datetime.now().isoformat(timespec='seconds'),
            run_id=self.run_id,
            header_changes=self._header_changes,
            benefits_changes=self._benefits_changes,
            earning_rates_changes=self._earning_rates_changes,
            sign_up_bonus_changes=self._sign_up_bonus_changes,
            summary=summary,
        )


def save_changelog(changelog_dir: str, entry: ChangelogEntry) -> str:
    """Write a changelog entry to a JSON file.

    Returns:
        Path to the written file.
    """
    os.makedirs(changelog_dir, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"{date_str}_{entry.slug}.json"
    filepath = os.path.join(changelog_dir, filename)

    # If file already exists for today, append a counter
    if os.path.exists(filepath):
        counter = 1
        while os.path.exists(filepath):
            filename = f"{date_str}_{entry.slug}_{counter}.json"
            filepath = os.path.join(changelog_dir, filename)
            counter += 1

    with open(filepath, 'w') as f:
        json.dump(entry.model_dump(), f, indent=2, default=str)

    logger.info("Changelog saved: %s", filepath)
    return filepath


def load_changelogs(
    changelog_dir: str,
    slug: str | None = None,
    since: str | None = None,
) -> list[ChangelogEntry]:
    """Load changelog entries from the changelogs directory.

    Args:
        changelog_dir: Path to changelogs/ directory.
        slug: If provided, filter to this card slug only.
        since: If provided, only include entries on or after this date (YYYY-MM-DD).

    Returns:
        List of ChangelogEntry objects, sorted by timestamp.
    """
    if not os.path.exists(changelog_dir):
        return []

    entries = []
    for filename in sorted(os.listdir(changelog_dir)):
        if not filename.endswith('.json'):
            continue

        # Filter by slug via filename convention: {date}_{slug}.json
        if slug:
            # filename is like "2026-03-01_amex-gold.json" or "2026-03-01_amex-gold_1.json"
            parts = filename.replace('.json', '').split('_', 1)
            if len(parts) >= 2:
                file_slug = parts[1].rsplit('_', 1)[0] if '_' in parts[1] and parts[1].rsplit('_', 1)[1].isdigit() else parts[1]
                if file_slug != slug:
                    continue

        # Filter by date
        if since:
            file_date = filename[:10]  # YYYY-MM-DD prefix
            if file_date < since:
                continue

        filepath = os.path.join(changelog_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entries.append(ChangelogEntry.model_validate(data))
        except Exception as e:
            logger.warning("Failed to load changelog %s: %s", filename, e)

    return entries
