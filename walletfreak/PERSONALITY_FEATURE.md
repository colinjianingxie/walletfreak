# Credit Card Personality Feature

## Overview

The Personality Feature allows users to discover their credit card spending personality based on the cards in their wallet. It combines card-based matching with crowd-sourced data to provide personalized insights and recommendations.

## Features

### 1. Automatic Personality Mapping
- **Card-Based Matching**: Automatically suggests personalities based on the credit cards in a user's wallet
- **Crowd-Sourced Intelligence**: Uses anonymous survey data from other users with similar card combinations
- **Dynamic Updates**: Personality recalculates when users add/remove active cards

### 2. Personality Survey
- **5-Question Survey**: Quick assessment covering:
  - Spending style (strategic, balanced, spontaneous, minimalist)
  - Travel frequency
  - Reward preferences (cashback, travel, perks, mixed)
  - Card management approach
  - Annual fee comfort level
- **Smart Suggestions**: Pre-suggests personality based on current wallet
- **Optional Publishing**: Users can contribute anonymously to crowd-sourced data

### 3. Personality Results
- **Detailed Profile**: Shows assigned personality with icon, tagline, and description
- **Match Score**: Displays how many cards match the personality
- **Survey Responses**: Review of user's survey answers
- **Recommended Cards**: Suggestions for cards that fit the personality
- **Publishing Option**: Contribute to community data

## Architecture

### Data Models

#### Personality Model (`core/models.py`)
```python
class Personality(FirestoreProxyModel):
    personality_id = CharField(primary_key=True)
    name = CharField()
    tagline = CharField()
    description = TextField()
    icon = CharField()  # Emoji icon
    survey_questions_json = TextField()
    recommended_cards_json = TextField()
```

#### PersonalitySurvey Model (`core/models.py`)
```python
class PersonalitySurvey(FirestoreProxyModel):
    survey_id = CharField(primary_key=True)
    user_id = CharField()
    personality_id = CharField()
    responses_json = TextField()  # Survey answers
    card_ids_json = TextField()   # User's cards at time of survey
    is_published = BooleanField()
    created_at = DateTimeField()
```

### Firestore Collections

#### `personalities`
```json
{
  "id": "strategic-optimizer",
  "name": "Strategic Optimizer",
  "tagline": "Maximizing every dollar",
  "description": "You carefully plan purchases...",
  "icon": "🎯",
  "recommended_cards": ["chase-sapphire-reserve", "amex-platinum"]
}
```

#### `personality_surveys`
```json
{
  "user_id": "user123",
  "personality_id": "strategic-optimizer",
  "responses": {
    "spending_style": "strategic",
    "travel_frequency": "frequent",
    "reward_preference": "travel",
    "card_management": "optimizer",
    "annual_fee_comfort": "worth_it"
  },
  "card_ids": ["chase-sapphire-reserve", "amex-gold"],
  "is_published": true,
  "created_at": "2025-11-28T12:00:00Z"
}
```

#### `users` (extended fields)
```json
{
  "uid": "user123",
  "assigned_personality": "strategic-optimizer",
  "personality_score": 2,
  "personality_assigned_at": "2025-11-28T12:00:00Z",
  "survey_completed": true,
  "survey_personality": "strategic-optimizer",
  "survey_completed_at": "2025-11-28T12:00:00Z"
}
```

### Service Methods (`core/services.py`)

#### Personality Calculation
- `calculate_personality_from_wallet(uid)`: Card-based matching
- `get_crowd_sourced_personalities(card_ids)`: Crowd-sourced matching
- `get_suggested_personality(uid)`: Combined matching (60% cards, 40% crowd)
- `recalculate_and_update_personality(uid)`: Update user's personality

#### Survey Management
- `save_personality_survey(uid, personality_id, responses, card_ids, is_published)`
- `get_user_survey(uid)`: Get user's most recent survey
- `publish_user_personality(uid)`: Mark survey as published

#### User Personality
- `update_user_personality(uid, personality_id, score)`
- `get_user_assigned_personality(uid)`: Get full personality details

## URL Routes

```python
# dashboard/urls.py
path('personality/survey/', views.personality_survey, name='personality_survey')
path('personality/submit/', views.submit_personality_survey, name='submit_personality_survey')
path('personality/results/', views.personality_results, name='personality_results')
path('personality/publish/', views.publish_personality, name='publish_personality')
```

## Views

### `personality_survey` (GET)
- Displays survey form with 5 questions
- Shows suggested personality based on current cards
- Requires at least one active card
- Redirects to dashboard if no cards

### `submit_personality_survey` (POST)
- Processes survey responses
- Saves to Firestore
- Updates user's assigned personality
- Optionally publishes for crowd-sourcing
- Redirects to results page

### `personality_results` (GET)
- Shows assigned personality details
- Displays survey responses
- Shows recommended cards
- Option to publish if not already published
- Option to retake survey

### `publish_personality` (POST)
- Marks user's survey as published
- Contributes to crowd-sourced data
- Redirects back to results

## User Flow

### First-Time User
1. User adds credit cards to wallet
2. Dashboard shows "Discover Your Personality" prompt
3. User clicks "Take Survey"
4. Survey pre-suggests personality based on cards
5. User answers 5 questions
6. User optionally agrees to publish anonymously
7. Results page shows assigned personality
8. Personality appears on dashboard

### Returning User
1. Dashboard shows assigned personality
2. User can click "View Full Details" to see results
3. User can retake survey to update personality
4. Personality updates when cards are added/removed

### Publishing Flow
1. User completes survey without publishing
2. Results page shows "Help the Community" section
3. User clicks "Publish My Personality"
4. Survey becomes part of crowd-sourced data
5. Helps other users with similar cards

## Matching Algorithm

### Card-Based Matching (60% weight)
```python
for personality in personalities:
    score = 0
    for card in personality.recommended_cards:
        if card in user_cards:
            score += 1
    # personality with highest score wins
```

### Crowd-Sourced Matching (40% weight)
```python
for published_survey in surveys:
    overlap = len(user_cards & survey_cards)
    if overlap >= len(user_cards) * 0.5:  # 50% overlap threshold
        personality_counts[survey.personality_id] += 1
```

### Combined Score
```python
combined_score = (card_score * 0.6) + (crowd_count * 0.4)
```

## Dashboard Integration

### With Personality
- Shows personality icon, name, and tagline
- Displays match score (X/Y cards match)
- Progress bar visualization
- "View Full Details" button

### Without Personality (Has Cards)
- Shows "Discover Your Personality" prompt
- Highlights number of cards in wallet
- "Take Survey" call-to-action

### Without Cards
- Shows "Add Your First Card" prompt
- Explains personality will be discovered after adding cards

## Privacy & Security

### Anonymous Publishing
- Only personality_id, responses, and card_ids are stored
- No personal information (name, email, etc.) is included
- User can choose not to publish

### Data Usage
- Published surveys used only for personality matching
- No individual survey data is displayed to other users
- Aggregate data only (counts, not details)

## Future Enhancements

### Potential Features
1. **Personality Comparison**: Compare with friends
2. **Personality Evolution**: Track changes over time
3. **Advanced Recommendations**: ML-based card suggestions
4. **Personality Badges**: Achievements and milestones
5. **Community Insights**: "X% of users with your personality have..."
6. **Personality Quiz**: Fun quiz version for engagement
7. **Social Sharing**: Share personality on social media
8. **Personality Challenges**: Gamification elements

### Technical Improvements
1. **Caching**: Cache personality calculations
2. **Background Jobs**: Recalculate personalities in background
3. **Analytics**: Track survey completion rates
4. **A/B Testing**: Test different survey questions
5. **API Endpoints**: RESTful API for mobile apps

## Testing

### Manual Testing Checklist
- [ ] Add cards and verify personality suggestion
- [ ] Complete survey and verify results
- [ ] Publish personality and verify in crowd-sourced data
- [ ] Remove cards and verify personality updates
- [ ] Retake survey and verify personality changes
- [ ] Test with no cards (should redirect)
- [ ] Test with cards but no matching personality
- [ ] Test crowd-sourced matching with multiple users

### Edge Cases
- User with no cards
- User with cards but no personality match
- User with all cards matching one personality
- User with cards matching multiple personalities
- Survey with missing responses
- Publishing already published survey

## Maintenance

### Regular Tasks
1. **Review Personalities**: Ensure personalities are up-to-date
2. **Update Recommended Cards**: Add new cards to personalities
3. **Monitor Survey Data**: Check for data quality issues
4. **Clean Old Surveys**: Archive surveys older than X months
5. **Update Questions**: Refine survey questions based on feedback

### Monitoring
- Survey completion rate
- Publishing rate
- Personality distribution
- Match score averages
- User engagement with personality feature

## Support

For questions or issues:
1. Check this documentation
2. Review code comments in `core/services.py`
3. Check Firestore data structure
4. Review view logic in `dashboard/views.py`