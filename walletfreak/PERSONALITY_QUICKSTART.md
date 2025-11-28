# Personality Feature - Quick Start Guide

## Setup Instructions

### 1. Ensure Firestore Collections Exist

The personality feature requires these Firestore collections:
- `personalities` - Personality definitions
- `personality_surveys` - User survey responses
- `users` - User profiles (extended with personality fields)
- `credit_cards` - Credit card definitions

### 2. Seed Sample Personalities

Create sample personalities in Firestore. Here's an example:

```python
# Run in Django shell: python manage.py shell
from core.services import db

# Sample Personality 1: Strategic Optimizer
db.create_document('personalities', {
    'name': 'Strategic Optimizer',
    'tagline': 'Maximizing every dollar with precision',
    'description': 'You carefully plan every purchase to maximize rewards. You track benefits meticulously and always know which card to use for each transaction.',
    'icon': '🎯',
    'recommended_cards': ['chase-sapphire-reserve', 'amex-platinum', 'chase-freedom-unlimited']
}, doc_id='strategic-optimizer')

# Sample Personality 2: Travel Enthusiast
db.create_document('personalities', {
    'name': 'Travel Enthusiast',
    'tagline': 'Collecting points for the next adventure',
    'description': 'Your wallet is optimized for travel. You prioritize airline miles, hotel points, and travel perks over cashback.',
    'icon': '✈️',
    'recommended_cards': ['chase-sapphire-reserve', 'amex-platinum', 'capital-one-venture-x']
}, doc_id='travel-enthusiast')

# Sample Personality 3: Cashback Collector
db.create_document('personalities', {
    'name': 'Cashback Collector',
    'tagline': 'Simple rewards, maximum value',
    'description': 'You prefer straightforward cashback over complex point systems. Your strategy is simple but effective.',
    'icon': '💰',
    'recommended_cards': ['citi-double-cash', 'chase-freedom-unlimited', 'discover-it']
}, doc_id='cashback-collector')

# Sample Personality 4: Minimalist Spender
db.create_document('personalities', {
    'name': 'Minimalist Spender',
    'tagline': 'One card, zero complications',
    'description': 'You prefer simplicity over optimization. One or two versatile cards handle all your needs without the hassle of tracking multiple benefits.',
    'icon': '🎴',
    'recommended_cards': ['chase-sapphire-preferred', 'capital-one-quicksilver']
}, doc_id='minimalist-spender')
```

## Testing the Feature

### Test Scenario 1: New User with Cards

1. **Login** to the application
2. **Add cards** to your wallet:
   - Go to Dashboard
   - Click "Add New Card"
   - Add 2-3 cards (e.g., Chase Sapphire Reserve, Amex Platinum)
3. **Check Dashboard**:
   - Should show "Discover Your Personality" prompt
   - Should display number of cards you have
4. **Take Survey**:
   - Click "Take Survey" button
   - Should see suggested personality based on your cards
   - Answer all 5 questions
   - Optionally check "Help the community"
   - Click "Discover My Personality"
5. **View Results**:
   - Should see your assigned personality
   - Should see match score
   - Should see your survey responses
   - Should see recommended cards
6. **Return to Dashboard**:
   - Should now show your personality in the header
   - Should display personality card with details

### Test Scenario 2: Publishing Personality

1. **Complete survey** without publishing (uncheck the box)
2. **Go to results page**
3. **Check for "Help the Community" section**
4. **Click "Publish My Personality"**
5. **Verify** the section changes to "Thank you for contributing"

### Test Scenario 3: Crowd-Sourced Matching

1. **Create multiple test users** (or use different browsers/incognito)
2. **User 1**: Add cards and complete survey with publishing
3. **User 2**: Add similar cards (50%+ overlap)
4. **User 2**: Take survey
5. **Verify** User 2's suggested personality considers User 1's published data

### Test Scenario 4: Personality Updates

1. **Have an assigned personality**
2. **Add a new active card** to your wallet
3. **Check** if personality updates automatically
4. **Remove a card**
5. **Verify** personality recalculates

### Test Scenario 5: Retaking Survey

1. **Have completed survey**
2. **Go to personality results**
3. **Click "Retake Survey"**
4. **Answer questions differently**
5. **Submit**
6. **Verify** personality updates based on new answers

## URL Endpoints to Test

```
# Main dashboard (shows personality)
http://localhost:8000/dashboard/

# Personality survey
http://localhost:8000/dashboard/personality/survey/

# Personality results
http://localhost:8000/dashboard/personality/results/

# Publish personality (POST only)
http://localhost:8000/dashboard/personality/publish/
```

## Expected Behaviors

### Dashboard Display

**With Personality:**
- Purple gradient card with personality icon
- Personality name and tagline
- Match score with progress bar
- "View Full Details" button

**Without Personality (Has Cards):**
- Yellow gradient card with thinking emoji
- "What's Your Credit Card Personality?" heading
- Card count mention
- "Take Survey" button

**Without Cards:**
- Gray card with add card icon
- "Discover Your Wallet Personality" heading
- "Add Your First Card" button

### Survey Page

- Shows user's active cards
- Displays suggested personality (if available)
- 5 radio button questions
- "Help the community" checkbox
- "Discover My Personality" submit button
- "Skip for Now" link

### Results Page

- Large personality card with gradient background
- Personality icon, name, tagline, description
- Match score badge
- User's active cards grid
- Survey responses section
- Publish option (if not published)
- "Back to Dashboard" and "Retake Survey" buttons

## Debugging Tips

### Check Firestore Data

```python
# Django shell
from core.services import db

# Check personalities
personalities = db.get_personalities()
print(f"Found {len(personalities)} personalities")

# Check user's cards
uid = "your-user-id"
cards = db.get_user_cards(uid, status='active')
print(f"User has {len(cards)} active cards")

# Check user's personality
personality = db.get_user_assigned_personality(uid)
print(f"Assigned personality: {personality}")

# Check user's survey
survey = db.get_user_survey(uid)
print(f"Survey: {survey}")

# Test personality calculation
personality_id, score, total = db.calculate_personality_from_wallet(uid)
print(f"Calculated: {personality_id} with score {score}/{total}")

# Test crowd-sourced matching
card_ids = [card['card_id'] for card in cards]
crowd_data = db.get_crowd_sourced_personalities(card_ids)
print(f"Crowd-sourced data: {crowd_data}")

# Test combined suggestion
suggested = db.get_suggested_personality(uid)
print(f"Suggested: {suggested}")
```

### Common Issues

**Issue: No personality suggested**
- Check if personalities exist in Firestore
- Verify user has active cards
- Check if cards match any personality's recommended_cards

**Issue: Survey doesn't save**
- Check Firestore permissions
- Verify all required fields are present
- Check browser console for errors

**Issue: Personality doesn't update**
- Verify `recalculate_and_update_personality()` is called
- Check if cards are marked as 'active' status
- Verify Firestore write permissions

**Issue: Crowd-sourced data not working**
- Ensure surveys are published (is_published=true)
- Check if there's sufficient card overlap (50%+)
- Verify multiple users have published surveys

## Performance Considerations

### Optimization Tips

1. **Cache personality calculations** for frequently accessed users
2. **Batch Firestore reads** when possible
3. **Index Firestore fields** used in queries:
   - `personality_surveys.is_published`
   - `personality_surveys.user_id`
   - `personality_surveys.created_at`

### Monitoring

Track these metrics:
- Survey completion rate
- Publishing rate
- Average match scores
- Personality distribution
- Page load times

## Next Steps

After testing:

1. **Gather feedback** on survey questions
2. **Refine personality definitions** based on user data
3. **Add more personalities** for better coverage
4. **Implement analytics** to track feature usage
5. **Consider A/B testing** different survey approaches

## Support

If you encounter issues:

1. Check [`PERSONALITY_FEATURE.md`](./PERSONALITY_FEATURE.md) for detailed documentation
2. Review code in [`core/services.py`](./core/services.py) for service methods
3. Check [`dashboard/views.py`](./dashboard/views.py) for view logic
4. Inspect Firestore data directly in Firebase Console
5. Check Django logs for errors

## Sample Test Data Script

```python
# save as: test_personality_data.py
# run: python manage.py shell < test_personality_data.py

from core.services import db

# Create test personalities
personalities = [
    {
        'id': 'strategic-optimizer',
        'name': 'Strategic Optimizer',
        'tagline': 'Maximizing every dollar with precision',
        'description': 'You carefully plan every purchase to maximize rewards.',
        'icon': '🎯',
        'recommended_cards': ['chase-sapphire-reserve', 'amex-platinum']
    },
    {
        'id': 'travel-enthusiast',
        'name': 'Travel Enthusiast',
        'tagline': 'Collecting points for the next adventure',
        'description': 'Your wallet is optimized for travel.',
        'icon': '✈️',
        'recommended_cards': ['chase-sapphire-reserve', 'capital-one-venture-x']
    },
    {
        'id': 'cashback-collector',
        'name': 'Cashback Collector',
        'tagline': 'Simple rewards, maximum value',
        'description': 'You prefer straightforward cashback.',
        'icon': '💰',
        'recommended_cards': ['citi-double-cash', 'chase-freedom-unlimited']
    }
]

for p in personalities:
    pid = p.pop('id')
    db.create_document('personalities', p, doc_id=pid)
    print(f"Created personality: {pid}")

print("Test data created successfully!")