from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils.text import slugify
from core.services import db
from django.conf import settings
from django.http import JsonResponse
import json

from django.contrib.auth import logout

def admin_logout_view(request):
    """
    Custom logout view for admin that signs out of Firebase.
    """
    logout(request)  # Clear Django session
    context = {
        'firebase_config': json.dumps(settings.FIREBASE_CLIENT_CONFIG)
    }
    return render(request, 'custom_admin/logout.html', context)

@staff_member_required
def admin_dashboard(request):
    return render(request, 'custom_admin/dashboard.html')

@staff_member_required
def admin_card_list(request):
    cards = db.get_cards()
    
    # Check permissions for Update button
    uid = request.session.get('uid')
    if not uid and request.user.is_authenticated:
        uid = request.user.username
        
    user_profile = db.get_user_profile(uid) if uid else {}
    email = user_profile.get('email', '').lower()
    is_super = user_profile.get('is_super_staff', False)
    
    is_prompt_admin = (email == 'colinjianingxie@gmail.com' and is_super)
    
    return render(request, 'custom_admin/card_list.html', {
        'cards': cards,
        'is_prompt_admin': is_prompt_admin
    })

@staff_member_required
def admin_card_edit(request, card_id):
    card = db.get_card_by_slug(card_id)
    
    if not card:
        messages.error(request, 'Card not found')
        return redirect('admin_card_list')
    
    # Pre-process benefits for display if needed, though template handles json string
    if isinstance(card.get('benefits'), list):
         card['benefits_json'] = json.dumps(card['benefits'], indent=2)
    else:
         card['benefits_json'] = "[]"

    # Check permissions for the template (Prompt Gen button)
    uid = request.session.get('uid')
    if not uid and request.user.is_authenticated:
        uid = request.user.username
        
    user_profile = db.get_user_profile(uid) if uid else {}
    email = user_profile.get('email', '').lower()
    is_super = user_profile.get('is_super_staff', False)
    
    # Strict check for the specific user
    is_prompt_admin = (email == 'colinjianingxie@gmail.com' and is_super)
    
    return render(request, 'custom_admin/card_edit.html', {
        'card': card,
        'is_prompt_admin': is_prompt_admin
    })

@staff_member_required
def admin_generate_prompt(request, card_id):
    """
    Generate AI prompt for card updates.
    Restricted to specific super staff.
    """
    # 1. Check User Email & Super Staff Status
    uid = request.session.get('uid')
    if not uid and request.user.is_authenticated:
        uid = request.user.username
        
    if not uid:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    user_profile = db.get_user_profile(uid)
    email = user_profile.get('email', '').lower()
    is_super = user_profile.get('is_super_staff', False)
    
    # Hardcoded restriction as per requirements
    if email != 'colinjianingxie@gmail.com' or not is_super:
        return JsonResponse({'error': 'Unauthorized: Restricted access'}, status=403)
        
    # 2. Get card to ensure it exists (and get slug)
    card = db.get_card_by_slug(card_id)
    if not card:
        return JsonResponse({'error': 'Card not found'}, status=404)
        
    # Slug might be the ID or a field
    slug = card_id # In FirestoreProxy, card_id is the primary key and usually the slug for cards
    
    # 3. Generate Prompt
    from .utils import PromptGenerator
    generator = PromptGenerator()
    try:
        # Check if minimum prompt is requested
        is_minimum = request.GET.get('min', '').lower() in ('1', 'true', 'yes')
        
        if is_minimum:
            prompt_text = generator.generate_minimum_prompt(slug)
        else:
            prompt_text = generator.generate_prompt(slug)
            
        seed_command = f"python manage.py seed_db --cards={slug}"
        return JsonResponse({'prompt': prompt_text, 'seed_command': seed_command})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@staff_member_required
def admin_run_grok_update(request, card_id):
    """
    Run the Grok update command + seed_db for a specific card.
    """
    # 1. Check User Email & Super Staff Status
    uid = request.session.get('uid')
    if not uid and request.user.is_authenticated:
        uid = request.user.username
        
    if not uid:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    user_profile = db.get_user_profile(uid)
    email = user_profile.get('email', '').lower()
    is_super = user_profile.get('is_super_staff', False)
    
    if email != 'colinjianingxie@gmail.com' or not is_super:
        return JsonResponse({'error': 'Unauthorized: Restricted access'}, status=403)
        
    # 2. Run Command
    from django.core.management import call_command
    import io
    from contextlib import redirect_stdout
    
    try:
        # Capture stdout to return as message
        f = io.StringIO()
        with redirect_stdout(f):
            call_command('update_cards_grok', cards=card_id, auto_seed=False)
        
        output = f.getvalue()
        return JsonResponse({'success': True, 'message': output})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@staff_member_required
def admin_generate_bulk_prompt(request):
    """
    Generate AI prompt for multiple cards.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        slug_ids = data.get('card_ids', [])
        
        if not slug_ids:
            return JsonResponse({'error': 'No cards selected'}, status=400)
            
        # Check permissions
        uid = request.session.get('uid')
        if not uid and request.user.is_authenticated:
            uid = request.user.username
            
        if not uid:
             return JsonResponse({'error': 'Unauthorized'}, status=403)
             
        user_profile = db.get_user_profile(uid)
        email = user_profile.get('email', '').lower()
        is_super = user_profile.get('is_super_staff', False)
        
        if email != 'colinjianingxie@gmail.com' or not is_super:
            return JsonResponse({'error': 'Unauthorized: Restricted access'}, status=403)
            
        from .utils import PromptGenerator
        generator = PromptGenerator()
        prompt_text = generator.generate_prompt(slug_ids)
        
        seed_cmd_slugs = ",".join(slug_ids)
        seed_command = f"python manage.py seed_db --cards={seed_cmd_slugs}"
        
        return JsonResponse({'prompt': prompt_text, 'seed_command': seed_command})
        
    except Exception as e:
         return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@staff_member_required
def admin_generate_new_prompt(request):
    """
    Generate AI prompt for new card(s) by slug-id.
    Accepts POST with JSON body containing 'slug_id' (can be comma-separated).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        slug_id_input = data.get('slug_id', '').strip()
        
        if not slug_id_input:
            return JsonResponse({'error': 'No slug-id provided'}, status=400)
        
        # Parse comma-separated slugs
        slug_ids = [s.strip() for s in slug_id_input.split(',') if s.strip()]
        
        if not slug_ids:
            return JsonResponse({'error': 'No valid slug-ids provided'}, status=400)
            
        # Check permissions
        uid = request.session.get('uid')
        if not uid and request.user.is_authenticated:
            uid = request.user.username
            
        if not uid:
             return JsonResponse({'error': 'Unauthorized'}, status=403)
             
        user_profile = db.get_user_profile(uid)
        email = user_profile.get('email', '').lower()
        is_super = user_profile.get('is_super_staff', False)
        
        if email != 'colinjianingxie@gmail.com' or not is_super:
            return JsonResponse({'error': 'Unauthorized: Restricted access'}, status=403)
            
        from .utils import PromptGenerator
        generator = PromptGenerator()
        prompt_text = generator.generate_prompt(slug_ids)
        
        seed_command = f"python manage.py seed_db --cards={','.join(slug_ids)}"
        
        return JsonResponse({
            'prompt': prompt_text, 
            'seed_command': seed_command,
            'slug_ids': slug_ids,
            'count': len(slug_ids)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@staff_member_required
def admin_save_card_json(request):
    """
    Save card JSON data to file(s).
    Accepts POST with JSON body containing 'slug_id' (comma-separated) and 'json_data' (array of JSONs).
    If multiple slug_ids, expects json_data to be a JSON array with matching count.
    """
    import os
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        slug_id_input = data.get('slug_id', '').strip()
        json_data = data.get('json_data', '').strip()
        
        if not slug_id_input:
            return JsonResponse({'error': 'No slug-id provided'}, status=400)
        if not json_data:
            return JsonResponse({'error': 'No JSON data provided'}, status=400)
        
        # Parse comma-separated slugs
        slug_ids = [s.strip() for s in slug_id_input.split(',') if s.strip()]
        
        if not slug_ids:
            return JsonResponse({'error': 'No valid slug-ids provided'}, status=400)
            
        # Check permissions
        uid = request.session.get('uid')
        if not uid and request.user.is_authenticated:
            uid = request.user.username
            
        if not uid:
             return JsonResponse({'error': 'Unauthorized'}, status=403)
             
        user_profile = db.get_user_profile(uid)
        email = user_profile.get('email', '').lower()
        is_super = user_profile.get('is_super_staff', False)
        
        if email != 'colinjianingxie@gmail.com' or not is_super:
            return JsonResponse({'error': 'Unauthorized: Restricted access'}, status=403)
        
        cards_dir = os.path.join(settings.BASE_DIR, 'walletfreak_credit_cards')
        
        # Handle multiple slug-ids
        if len(slug_ids) > 1:
            # Expect json_data to be a JSON array
            try:
                parsed_jsons = json.loads(json_data)
            except json.JSONDecodeError as e:
                return JsonResponse({'error': f'Invalid JSON array: {str(e)}'}, status=400)
            
            if not isinstance(parsed_jsons, list):
                return JsonResponse({
                    'error': f'For {len(slug_ids)} slug-ids, expected a JSON array with {len(slug_ids)} objects. '
                             f'Wrap your JSONs in square brackets: [{{...}}, {{...}}]'
                }, status=400)
            
            if len(parsed_jsons) != len(slug_ids):
                return JsonResponse({
                    'error': f'Mismatch: {len(slug_ids)} slug-ids provided but {len(parsed_jsons)} JSON objects found. '
                             f'Expected exactly {len(slug_ids)} JSON objects.'
                }, status=400)
            
            # Validate each JSON object has the correct slug-id
            saved_files = []
            for i, (slug_id, card_json) in enumerate(zip(slug_ids, parsed_jsons)):
                if not isinstance(card_json, dict):
                    return JsonResponse({
                        'error': f'Item {i+1} is not a valid JSON object'
                    }, status=400)
                
                # Verify the slug-id in the JSON matches (if present)
                json_slug = card_json.get('slug-id', '')
                if json_slug and json_slug != slug_id:
                    return JsonResponse({
                        'error': f'JSON object {i+1} has slug-id "{json_slug}" but expected "{slug_id}"'
                    }, status=400)
                
                filepath = os.path.join(cards_dir, f'{slug_id}.json')
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(card_json, f, indent=4, ensure_ascii=False)
                saved_files.append(f'{slug_id}.json')
            
            files_list = ', '.join(saved_files)
            return JsonResponse({
                'success': True, 
                'message': f'Saved {len(saved_files)} files: {files_list}',
                'files': saved_files
            })
        else:
            # Single slug-id - expect a single JSON object
            slug_id = slug_ids[0]
            try:
                parsed_json = json.loads(json_data)
            except json.JSONDecodeError as e:
                return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
            
            # If it's a list with one item, unwrap it
            if isinstance(parsed_json, list):
                if len(parsed_json) == 1:
                    parsed_json = parsed_json[0]
                else:
                    return JsonResponse({
                        'error': f'For single slug-id, expected 1 JSON object but found array with {len(parsed_json)} items'
                    }, status=400)
            
            if not isinstance(parsed_json, dict):
                return JsonResponse({'error': 'Expected a JSON object'}, status=400)
            
            filepath = os.path.join(cards_dir, f'{slug_id}.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(parsed_json, f, indent=4, ensure_ascii=False)
            
            return JsonResponse({
                'success': True, 
                'message': f'Saved to {slug_id}.json',
                'filepath': filepath
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
