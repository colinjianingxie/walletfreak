"""Pydantic models for card pipeline validation."""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional


class Benefit(BaseModel):
    benefit_id: str
    short_description: str = ""
    description: str = ""
    additional_details: Optional[str] = None
    benefit_category: list[str] = Field(default_factory=list)
    benefit_main_category: str = ""
    benefit_type: str = ""
    numeric_value: float = 0.0
    numeric_type: Optional[str] = None
    dollar_value: Optional[int | float] = None
    time_category: str = ""
    enrollment_required: bool = False
    effective_date: Optional[str] = None
    # Metadata (set by dehydrator, not LLM)
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    is_active: bool = True

    @field_validator('benefit_category')
    @classmethod
    def categories_not_empty(cls, v):
        if not v:
            raise ValueError('benefit_category must not be empty')
        return v


class EarningRate(BaseModel):
    rate_id: str
    multiplier: float = 1.0
    category: list[str] = Field(default_factory=list)
    currency: str = "points"
    additional_details: Optional[str] = None
    is_default: bool = False
    # Metadata
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    is_active: bool = True

    @field_validator('multiplier')
    @classmethod
    def multiplier_non_negative(cls, v):
        if v < 0:
            raise ValueError('multiplier must be >= 0')
        return v

    @field_validator('category')
    @classmethod
    def category_not_empty(cls, v):
        if not v:
            raise ValueError('category must not be empty')
        return v


class SignUpBonus(BaseModel):
    offer_id: str = "offer"
    value: int | float = 0
    terms: str = ""
    currency: str = "Points"
    spend_amount: int | float = 0
    duration_months: int = 0
    effective_date: Optional[str] = None
    # Metadata
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    is_active: bool = True


class CardQuestion(BaseModel):
    question_id: str
    short_desc: str = ""
    question: str = ""
    question_type: str = "multiple_choice"
    choices: list[str] = Field(default_factory=list)
    weights: list[float] = Field(default_factory=list)
    benefit_category: str | list[str] = ""

    @model_validator(mode='after')
    def choices_weights_same_length(self):
        if self.choices and self.weights and len(self.choices) != len(self.weights):
            raise ValueError(
                f'choices ({len(self.choices)}) and weights ({len(self.weights)}) must have same length'
            )
        return self


class ActiveIndices(BaseModel):
    benefits: list[str] = Field(default_factory=list)
    earning_rates: list[str] = Field(default_factory=list)
    sign_up_bonus: list[str] = Field(default_factory=list)
    card_questions: list[str] = Field(default_factory=list)


class CardHeader(BaseModel):
    slug_id: str = Field(alias='slug-id')
    name: str = ""
    issuer: str = ""
    image_url: str = ""
    annual_fee: int | float = 0
    application_link: str = ""
    min_credit_score: int = 670
    max_credit_score: int = 850
    is_524: bool = False
    freak_verdict: str = ""
    show_in_calculators: Optional[bool] = None
    referral_links: Optional[list] = None
    loyalty_program: Optional[str] = None
    points_value_cpp: Optional[float] = None
    active_indices: ActiveIndices = Field(default_factory=ActiveIndices)
    # Deprecation fields
    is_active: bool = True
    deprecated_at: Optional[str] = None
    superseded_by: Optional[list[str]] = None
    deprecation_reason: Optional[str] = None

    model_config = {'populate_by_name': True}


class CardData(BaseModel):
    """Fully hydrated card for LLM context."""
    slug_id: str = Field(alias='slug-id')
    name: str = ""
    issuer: str = ""
    image_url: str = ""
    application_link: str = ""
    annual_fee: int | float = 0
    is_524: bool = False
    min_credit_score: Optional[int] = None
    max_credit_score: Optional[int] = None
    freak_verdict: Optional[str] = None
    benefits: Optional[list[Benefit]] = None
    earning_rates: Optional[list[EarningRate]] = None
    sign_up_bonus: Optional[list[SignUpBonus]] = None
    questions: Optional[list[CardQuestion]] = None

    model_config = {'populate_by_name': True}


# --- Changelog models ---

class FieldChange(BaseModel):
    field: str
    old: object = None
    new: object = None


class ItemChange(BaseModel):
    action: str  # "created", "updated", "deprecated", "cosmetic_update"
    item_id: str
    old_vid: Optional[str] = None
    new_vid: Optional[str] = None
    changes: list[FieldChange] = Field(default_factory=list)


class ChangelogEntry(BaseModel):
    slug: str
    timestamp: str
    run_id: str = ""
    header_changes: list[FieldChange] = Field(default_factory=list)
    benefits_changes: list[ItemChange] = Field(default_factory=list)
    earning_rates_changes: list[ItemChange] = Field(default_factory=list)
    sign_up_bonus_changes: list[ItemChange] = Field(default_factory=list)
    summary: str = ""
