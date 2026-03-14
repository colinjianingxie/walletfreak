from .hydrator import hydrate_card
from .dehydrator import dehydrate_and_save, deprecate_card, DehydrationResult
from .changelog import ChangeTracker, save_changelog, load_changelogs
from .categories import load_category_hierarchy, load_valid_categories
from .grok_client import GrokClient
from .prompts import build_update_prompt
from .models import CardData, Benefit, EarningRate, SignUpBonus, CardQuestion, CardHeader


def __getattr__(name):
    """Lazy import for Django-dependent modules."""
    if name == 'CardUpdatePipeline':
        from .pipeline import CardUpdatePipeline
        return CardUpdatePipeline
    if name == 'PipelineResult':
        from .pipeline import PipelineResult
        return PipelineResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    'hydrate_card',
    'dehydrate_and_save',
    'deprecate_card',
    'DehydrationResult',
    'ChangeTracker',
    'save_changelog',
    'load_changelogs',
    'load_category_hierarchy',
    'load_valid_categories',
    'GrokClient',
    'build_update_prompt',
    'CardUpdatePipeline',
    'PipelineResult',
    'CardData',
    'Benefit',
    'EarningRate',
    'SignUpBonus',
    'CardQuestion',
    'CardHeader',
]
