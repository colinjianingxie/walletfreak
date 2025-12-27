from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
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
    return render(request, 'custom_admin/card_list.html', {'cards': cards})

@staff_member_required
def admin_card_edit(request, card_id):
    card = db.get_document('credit_cards', card_id)
    
    if not card:
        messages.error(request, 'Card not found')
        return redirect('admin_card_list')
    
    # Pre-process benefits for display if needed, though template handles json string
    if isinstance(card.get('benefits'), list):
         card['benefits_json'] = json.dumps(card['benefits'], indent=2)
    else:
         card['benefits_json'] = "[]"

    # Check permissions for the template (Prompt Gen button)
    uid = request.session.get('firebase_uid')
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
    uid = request.session.get('firebase_uid')
    if not uid:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    user_profile = db.get_user_profile(uid)
    email = user_profile.get('email', '').lower()
    is_super = user_profile.get('is_super_staff', False)
    
    # Hardcoded restriction as per requirements
    if email != 'colinjianingxie@gmail.com' or not is_super:
        return JsonResponse({'error': 'Unauthorized: Restricted access'}, status=403)
        
    # 2. Get card to ensure it exists (and get slug)
    card = db.get_document('credit_cards', card_id)
    if not card:
        return JsonResponse({'error': 'Card not found'}, status=404)
        
    # Slug might be the ID or a field
    slug = card_id # In FirestoreProxy, card_id is the primary key and usually the slug for cards
    
    # 3. Generate Prompt
    from .utils import PromptGenerator
    generator = PromptGenerator()
    try:
        prompt_text = generator.generate_prompt(slug)
        return JsonResponse({'prompt': prompt_text})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
