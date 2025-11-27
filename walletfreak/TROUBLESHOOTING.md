# Troubleshooting Guide

## Common Issues and Solutions

### 1. "ValueError: The view didn't return an HttpResponse object"

**Issue**: The `toggle_benefit_usage` function was incomplete and didn't return a response.

**Solution**: Fixed in the latest update. The function now properly returns either a JsonResponse for AJAX requests or redirects to the dashboard.

### 2. Benefits showing incorrect text (e.g., "000/calendar year)")

**Issue**: CSV parser wasn't handling commas within quoted fields correctly.

**Solution**: Updated the CSV parser to use `csv.QUOTE_MINIMAL` which properly handles commas in descriptions.

**To apply the fix**:
```bash
cd walletfreak
python manage.py seed_db
```

This will re-import all cards with properly parsed benefit descriptions.

### 3. Template showing `{{ benefit.card_name }}` literally

**Possible Causes**:
1. Browser caching old template
2. Django template cache needs clearing
3. Server needs restart

**Solutions**:
1. **Hard refresh browser**: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
2. **Clear Django cache**:
   ```bash
   python manage.py collectstatic --clear
   ```
3. **Restart development server**:
   - Stop the server (Ctrl+C)
   - Start it again: `python manage.py runserver`

### 4. Benefits not tracking properly

**Check**:
1. Ensure cards were seeded with the new structure:
   ```bash
   python manage.py seed_db
   ```
2. Verify benefit IDs are in format `benefit_0`, `benefit_1`, etc.
3. Check that benefits have `dollar_value` field (not `amount`)

### 5. CSV Parsing Issues

**If you see truncated or incorrect benefit descriptions**:

1. Check the CSV file encoding (should be UTF-8)
2. Ensure all fields with commas are properly quoted
3. Re-run the parser:
   ```bash
   cd walletfreak
   python core/management/commands/parse_benefits_csv.py
   ```

### 6. Admin Portal Issues

**Cannot edit cards**:
- Ensure you're logged in as a super staff user
- Check that the URLs are correctly configured in `custom_admin/urls.py`

**JSON validation errors**:
- Benefits must be valid JSON array
- Each benefit must have: `description`, `category`, `dollar_value`, `effective_date`
- Use the example format provided in the create/edit forms

## Verification Steps

### 1. Verify CSV Parsing
```bash
cd walletfreak
python core/management/commands/parse_benefits_csv.py
```
Should output: "Parsed 83 cards"

### 2. Verify Database Seeding
```bash
python manage.py seed_db
```
Should show each card being seeded with benefit counts

### 3. Verify Dashboard
1. Navigate to `/dashboard/`
2. Check that benefits show:
   - Card name (not `{{ benefit.card_name }}`)
   - Benefit description
   - Dollar amount
   - Input field for custom amounts
   - Toggle button

### 4. Verify Admin Portal
1. Navigate to `/custom-admin/cards/`
2. Should see list of all cards with benefit counts
3. Click "Edit" on any card
4. Should see JSON editor with benefits

## Data Structure Reference

### Correct Benefit Format in Firestore
```json
{
  "description": "5x points on travel",
  "category": "Permanent",
  "dollar_value": null,
  "effective_date": "2025-11-27"
}
```

### Correct Benefit Format with Dollar Value
```json
{
  "description": "$300 annual travel credit",
  "category": "Annually (calendar year)",
  "dollar_value": 300,
  "effective_date": "2025-11-27"
}
```

## Reset and Start Fresh

If you need to completely reset:

1. **Clear Firestore data** (via Firebase Console or admin portal)
2. **Re-seed database**:
   ```bash
   python manage.py seed_db
   ```
3. **Clear browser cache** and hard refresh
4. **Restart development server**

## Getting Help

If issues persist:
1. Check Django logs for errors
2. Check browser console for JavaScript errors
3. Verify Firestore data structure matches expected format
4. Ensure all dependencies are installed: `pip install -r requirements.txt`