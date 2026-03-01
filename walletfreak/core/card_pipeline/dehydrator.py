"""Dehydrator — splits monolithic dict into relational files with versioning.

Extracted and unified from update_cards_grok.py and ingest_card_json.py.
Adds structural vs cosmetic field classification to prevent false version bumps.
"""

import os
import json
import logging
import datetime
from dataclasses import dataclass, field

from pydantic import ValidationError
from .models import Benefit, EarningRate, SignUpBonus, FieldChange
from .changelog import ChangeTracker

logger = logging.getLogger(__name__)


# --- Structural vs Cosmetic field classification ---
# Structural fields trigger a new version when changed.
# Cosmetic fields update in-place silently (no version bump).

STRUCTURAL_FIELDS = {
    'benefits': {
        'benefit_id', 'numeric_value', 'dollar_value', 'benefit_type',
        'benefit_category', 'benefit_main_category', 'time_category',
        'enrollment_required', 'numeric_type',
    },
    'earning_rates': {
        'rate_id', 'multiplier', 'category', 'currency', 'is_default',
    },
    'sign_up_bonus': {
        'offer_id', 'value', 'spend_amount', 'duration_months', 'currency',
    },
}

COSMETIC_FIELDS = {
    'benefits': {
        'description', 'short_description', 'additional_details', 'effective_date',
    },
    'earning_rates': {
        'additional_details',
    },
    'sign_up_bonus': {
        'terms', 'effective_date',
    },
}

# Metadata fields always ignored during comparison
METADATA_KEYS = {'version', 'valid_from', 'valid_until', 'is_active'}

# Header fields allowed to be updated
HEADER_KEYS = [
    "slug-id", "name", "issuer", "image_url", "annual_fee",
    "application_link", "min_credit_score", "max_credit_score",
    "is_524", "freak_verdict", "points_value_cpp", "show_in_calculators",
    "referral_links",
]

# Pydantic model mapping for validation
SECTION_MODELS = {
    'benefits': Benefit,
    'earning_rates': EarningRate,
    'sign_up_bonus': SignUpBonus,
}


@dataclass
class DehydrationResult:
    """Result summary from a dehydration operation."""
    header_updated: bool = False
    items_created: int = 0
    items_updated: int = 0
    items_deprecated: int = 0
    cosmetic_updates: int = 0
    validation_errors: list[str] = field(default_factory=list)


def dehydrate_and_save(
    master_dir: str,
    slug: str,
    new_data: dict,
    update_types: list[str] | None = None,
    dry_run: bool = False,
    validate: bool = True,
    change_tracker: ChangeTracker | None = None,
    logger_obj=None,
) -> DehydrationResult:
    """Split monolithic JSON into relational files with versioning.

    Args:
        master_dir: Path to master_cards/ directory.
        slug: Card slug identifier.
        new_data: The new card data dict (from LLM or JSON file).
        update_types: Which components to process. None means infer from new_data keys.
        dry_run: If True, preview changes without writing files.
        validate: If True, validate items against Pydantic models before writing.
        change_tracker: Optional ChangeTracker to record changes for changelog.
        logger_obj: Optional logger for dry-run output (e.g., Django command stdout).

    Returns:
        DehydrationResult with counts of changes made.
    """
    log = logger_obj or logger
    result = DehydrationResult()

    card_dir = os.path.join(master_dir, slug)
    if not os.path.exists(card_dir):
        if dry_run:
            _log(log, f"[NEW CARD] Would create directory: {card_dir}")
        else:
            os.makedirs(card_dir)

    # --- 1. Header ---
    header_path = os.path.join(card_dir, 'header.json')
    if os.path.exists(header_path):
        with open(header_path, 'r') as f:
            header_doc = json.load(f)
    else:
        header_doc = {
            "slug-id": slug,
            "active_indices": {"benefits": [], "earning_rates": [], "sign_up_bonus": []},
        }

    # Update permissible header fields
    for key in HEADER_KEYS:
        if key in new_data:
            old_val = header_doc.get(key)
            new_val = new_data[key]
            if old_val != new_val:
                header_doc[key] = new_val
                result.header_updated = True
                if dry_run:
                    _log(log, f"[HEADER] {key}: {old_val} -> {new_val}", style='warning')
                if change_tracker:
                    change_tracker.record_header_change(key, old_val, new_val)

    # --- 2. Versioning ---
    today_str = datetime.date.today().isoformat()
    yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    # Determine which sections to process
    if update_types is not None:
        # Explicit update_types from command
        process_benefits = 'benefits' in update_types
        process_rates = 'rates' in update_types
        process_bonus = 'bonus' in update_types
        process_questions = 'questions' in update_types
    else:
        # Infer from presence in new_data (ingest_card_json behavior)
        process_benefits = 'benefits' in new_data
        process_rates = 'earning_rates' in new_data
        process_bonus = 'sign_up_bonus' in new_data
        process_questions = 'questions' in new_data

    if process_benefits:
        r = _process_sub_collection(
            card_dir, header_doc, new_data,
            key='benefits', directory='benefits',
            id_field='benefit_id', normalized_id_prefix='benefit',
            section_type='benefits',
            today_str=today_str, yesterday_str=yesterday_str,
            dry_run=dry_run, validate=validate,
            change_tracker=change_tracker, log=log,
        )
        _merge_result(result, r)

    if process_rates:
        r = _process_sub_collection(
            card_dir, header_doc, new_data,
            key='earning_rates', directory='earning_rates',
            id_field='rate_id', normalized_id_prefix='rate',
            section_type='earning_rates',
            today_str=today_str, yesterday_str=yesterday_str,
            dry_run=dry_run, validate=validate,
            change_tracker=change_tracker, log=log,
        )
        _merge_result(result, r)

    if process_bonus:
        r = _process_sub_collection(
            card_dir, header_doc, new_data,
            key='sign_up_bonus', directory='sign_up_bonus',
            id_field='offer_id', normalized_id_prefix='offer',
            section_type='sign_up_bonus',
            today_str=today_str, yesterday_str=yesterday_str,
            dry_run=dry_run, validate=validate,
            change_tracker=change_tracker, log=log,
        )
        _merge_result(result, r)

    # --- Questions (no versioning) ---
    if process_questions:
        questions = new_data.get('questions', [])
        if questions:
            q_dir = os.path.join(card_dir, 'card_questions')
            if not os.path.exists(q_dir):
                if not dry_run:
                    os.makedirs(q_dir)

            for index, q in enumerate(questions):
                q_id = q.get('question_id', f"q-{index}")
                q['question_id'] = q_id
                if dry_run:
                    _log(log, f"[QUESTIONS] Would update/create {q_id}")
                else:
                    with open(os.path.join(q_dir, f"{q_id}.json"), 'w') as f:
                        json.dump(q, f, indent=4)

    # --- 3. Save Header ---
    if not dry_run:
        with open(header_path, 'w') as f:
            json.dump(header_doc, f, indent=4)

    return result


def deprecate_card(
    master_dir: str,
    slug: str,
    deprecated_at: str,
    superseded_by: list[str] | None = None,
    reason: str = "",
) -> None:
    """Deprecate a card and cascade is_active=false to all sub-items.

    Sets header is_active to false, deprecated_at, superseded_by, deprecation_reason.
    Cascades to ALL files in benefits/, earning_rates/, and sign_up_bonus/ directories.
    """
    card_dir = os.path.join(master_dir, slug)
    header_path = os.path.join(card_dir, 'header.json')

    if not os.path.exists(header_path):
        raise FileNotFoundError(f"Card {slug} not found at {card_dir}")

    with open(header_path, 'r') as f:
        header = json.load(f)

    # Update header
    header['is_active'] = False
    header['deprecated_at'] = deprecated_at
    if superseded_by:
        header['superseded_by'] = superseded_by
    if reason:
        header['deprecation_reason'] = reason

    with open(header_path, 'w') as f:
        json.dump(header, f, indent=4)

    # Cascade to all sub-item files
    for subdir_name in ('benefits', 'earning_rates', 'sign_up_bonus'):
        subdir_path = os.path.join(card_dir, subdir_name)
        if not os.path.exists(subdir_path):
            continue
        for fname in os.listdir(subdir_path):
            if not fname.endswith('.json'):
                continue
            fpath = os.path.join(subdir_path, fname)
            with open(fpath, 'r') as f:
                item = json.load(f)
            item['is_active'] = False
            item['valid_until'] = deprecated_at
            with open(fpath, 'w') as f:
                json.dump(item, f, indent=4)

    logger.info("Deprecated card %s (as of %s)", slug, deprecated_at)


# --- Internal helpers ---

def _process_sub_collection(
    card_dir: str,
    header_doc: dict,
    new_data: dict,
    key: str,
    directory: str,
    id_field: str,
    normalized_id_prefix: str,
    section_type: str,
    today_str: str,
    yesterday_str: str,
    dry_run: bool,
    validate: bool,
    change_tracker: ChangeTracker | None,
    log,
) -> DehydrationResult:
    """Process a single sub-collection (benefits, earning_rates, or sign_up_bonus)."""
    result = DehydrationResult()

    new_items = new_data.get(key)
    if new_items is None:
        return result
    if not new_items:
        return result

    target_dir = os.path.join(card_dir, directory)
    if not os.path.exists(target_dir):
        if dry_run:
            _log(log, f"[{directory}] Would create directory", style='warning')
        else:
            os.makedirs(target_dir)

    current_indices = header_doc['active_indices'].get(directory, [])
    new_active_indices = []

    # Load current items for comparison
    current_items_map = {}  # versioned_id -> data
    base_id_map = {}  # base_id -> currently_active_versioned_id

    for vid in current_indices:
        path = os.path.join(target_dir, f"{vid}.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                item = json.load(f)
            current_items_map[vid] = item
            base_id = item.get(id_field)
            if base_id:
                base_id_map[base_id] = vid

    # Validate new items if requested
    model_cls = SECTION_MODELS.get(section_type)
    if validate and model_cls:
        for i, item in enumerate(new_items):
            try:
                model_cls.model_validate(item)
            except ValidationError as e:
                msg = f"[{directory}] Item {i} validation error: {e}"
                result.validation_errors.append(msg)
                _log(log, msg, style='error')

    structural_fields = STRUCTURAL_FIELDS.get(section_type, set())
    cosmetic_fields = COSMETIC_FIELDS.get(section_type, set())

    for index, item in enumerate(new_items):
        # Ensure item has a base ID
        base_id = item.get(id_field)
        if not base_id:
            base_id = f"{normalized_id_prefix}-{index}"
            item[id_field] = base_id

        active_vid = base_id_map.get(base_id)

        should_create_new = True
        final_vid = None

        if active_vid:
            old_item = current_items_map[active_vid]

            # Compare structural fields only for version decision
            old_structural = {
                k: v for k, v in old_item.items()
                if k in structural_fields
            }
            new_structural = {
                k: v for k, v in item.items()
                if k in structural_fields
            }

            # Also compute cosmetic diffs
            old_cosmetic = {
                k: v for k, v in old_item.items()
                if k in cosmetic_fields
            }
            new_cosmetic = {
                k: v for k, v in item.items()
                if k in cosmetic_fields
            }

            if old_structural == new_structural:
                # No structural change — no version bump
                should_create_new = False
                final_vid = active_vid

                # But silently update cosmetic fields in existing file
                if old_cosmetic != new_cosmetic:
                    cosmetic_changes = []
                    for k in cosmetic_fields:
                        if old_item.get(k) != item.get(k):
                            cosmetic_changes.append(
                                FieldChange(field=k, old=old_item.get(k), new=item.get(k))
                            )

                    # Update cosmetic fields in the existing file
                    for k in cosmetic_fields:
                        if k in item:
                            old_item[k] = item[k]

                    if not dry_run:
                        with open(os.path.join(target_dir, f"{active_vid}.json"), 'w') as f:
                            json.dump(old_item, f, indent=4)

                    result.cosmetic_updates += 1
                    if dry_run:
                        _log(log, f"[{directory}] COSMETIC {base_id}: {', '.join(c.field for c in cosmetic_changes)}")
                    if change_tracker and cosmetic_changes:
                        change_tracker.record_cosmetic_update(
                            directory, base_id, active_vid, cosmetic_changes
                        )
            else:
                # Structural change — new version
                try:
                    parts = active_vid.rsplit('-v', 1)
                    if len(parts) == 2:
                        new_v_num = int(parts[1]) + 1
                    else:
                        new_v_num = 2
                except (ValueError, IndexError):
                    new_v_num = 2

                final_vid = f"{base_id}-v{new_v_num}"

                # Compute structural diffs for changelog
                structural_changes = []
                for k in structural_fields:
                    if old_item.get(k) != item.get(k):
                        structural_changes.append(
                            FieldChange(field=k, old=old_item.get(k), new=item.get(k))
                        )

                if dry_run:
                    _log(log, f"[{directory}] UPDATE {base_id}: {active_vid} -> {final_vid}", style='warning')
                    for c in structural_changes:
                        _log(log, f"    {c.field}: {c.old} -> {c.new}")

                # Deprecate old file
                if old_item.get('valid_from') == today_str:
                    old_item['valid_until'] = today_str
                else:
                    old_item['valid_until'] = yesterday_str
                old_item['is_active'] = False

                if not dry_run:
                    with open(os.path.join(target_dir, f"{active_vid}.json"), 'w') as f:
                        json.dump(old_item, f, indent=4)

                result.items_updated += 1
                if change_tracker:
                    change_tracker.record_item_updated(
                        directory, base_id, active_vid, final_vid, structural_changes
                    )
        else:
            # New item
            final_vid = f"{base_id}-v1"
            if dry_run:
                _log(log, f"[{directory}] CREATE {final_vid}", style='success')
            result.items_created += 1
            if change_tracker:
                change_tracker.record_item_created(directory, base_id, final_vid)

        if should_create_new:
            item['valid_from'] = today_str
            item['valid_until'] = None
            item['is_active'] = True
            if not dry_run:
                with open(os.path.join(target_dir, f"{final_vid}.json"), 'w') as f:
                    json.dump(item, f, indent=4)

        new_active_indices.append(final_vid)

    # Detect deletions
    new_base_ids = {item.get(id_field) for item in new_items if item.get(id_field)}

    for vid in current_indices:
        old_item = current_items_map.get(vid)
        if old_item:
            bid = old_item.get(id_field)
            if bid and bid not in new_base_ids:
                if dry_run:
                    _log(log, f"[{directory}] DELETE {vid}", style='error')
                old_item['valid_until'] = yesterday_str
                old_item['is_active'] = False
                if not dry_run:
                    with open(os.path.join(target_dir, f"{vid}.json"), 'w') as f:
                        json.dump(old_item, f, indent=4)
                result.items_deprecated += 1
                if change_tracker:
                    change_tracker.record_item_deprecated(directory, bid, vid)

    # Update header indices
    header_doc['active_indices'][directory] = new_active_indices
    return result


def _merge_result(target: DehydrationResult, source: DehydrationResult):
    """Merge source DehydrationResult into target."""
    target.header_updated = target.header_updated or source.header_updated
    target.items_created += source.items_created
    target.items_updated += source.items_updated
    target.items_deprecated += source.items_deprecated
    target.cosmetic_updates += source.cosmetic_updates
    target.validation_errors.extend(source.validation_errors)


def _log(log_obj, message: str, style: str | None = None):
    """Log a message, supporting both Django command stdout and standard logging."""
    if hasattr(log_obj, 'write'):
        # Django management command stdout
        if style == 'warning' and hasattr(log_obj, 'style'):
            log_obj.write(log_obj.style.WARNING(message))
        elif style == 'error' and hasattr(log_obj, 'style'):
            log_obj.write(log_obj.style.ERROR(message))
        elif style == 'success' and hasattr(log_obj, 'style'):
            log_obj.write(log_obj.style.SUCCESS(message))
        else:
            log_obj.write(message)
    else:
        log_obj.info(message)
