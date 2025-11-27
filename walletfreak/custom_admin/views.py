from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils.text import slugify
from core.services import db
from django.conf import settings
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
    
    if request.method == 'POST':
        # Update card data
        updated_data = {
            'name': request.POST.get('name'),
            'issuer': request.POST.get('issuer'),
            'annual_fee': float(request.POST.get('annual_fee', 0)),
            'image_url': request.POST.get('image_url', ''),
        }
        
        # Parse benefits from JSON
        benefits_json = request.POST.get('benefits', '[]')
        try:
            updated_data['benefits'] = json.loads(benefits_json)
        except json.JSONDecodeError:
            messages.error(request, 'Invalid benefits JSON format')
            return render(request, 'custom_admin/card_edit.html', {'card': card})
        
        db.update_document('credit_cards', card_id, updated_data)
        messages.success(request, f'Card "{updated_data["name"]}" updated successfully')
        return redirect('admin_card_list')
    
    # Convert benefits to JSON for editing
    card['benefits_json'] = json.dumps(card.get('benefits', []), indent=2)
    return render(request, 'custom_admin/card_edit.html', {'card': card})

@staff_member_required
def admin_card_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        issuer = request.POST.get('issuer')
        annual_fee = float(request.POST.get('annual_fee', 0))
        image_url = request.POST.get('image_url', '')
        
        # Parse benefits from JSON
        benefits_json = request.POST.get('benefits', '[]')
        try:
            benefits = json.loads(benefits_json)
        except json.JSONDecodeError:
            messages.error(request, 'Invalid benefits JSON format')
            return render(request, 'custom_admin/card_create.html')
        
        # Create card document
        card_data = {
            'name': name,
            'issuer': issuer,
            'annual_fee': annual_fee,
            'image_url': image_url,
            'benefits': benefits,
            'referral_links': [],
            'user_type': []
        }
        
        slug = slugify(name)
        db.create_document('credit_cards', card_data, doc_id=slug)
        messages.success(request, f'Card "{name}" created successfully')
        return redirect('admin_card_list')
    
    return render(request, 'custom_admin/card_create.html')

@staff_member_required
def admin_card_delete(request, card_id):
    if request.method == 'POST':
        card = db.get_document('credit_cards', card_id)
        if card:
            db.delete_document('credit_cards', card_id)
            messages.success(request, f'Card "{card["name"]}" deleted successfully')
        else:
            messages.error(request, 'Card not found')
    return redirect('admin_card_list')

@staff_member_required
def admin_personality_list(request):
    personalities = db.get_personalities()
    return render(request, 'custom_admin/personality_list.html', {'personalities': personalities})

@staff_member_required
def admin_user_list(request):
    # In a real app, we'd paginate this. For now, fetch all users (might be slow if many users)
    # Since we don't have a 'list_users' in service yet, we'll add it or just iterate
    # For this demo, let's assume we can list users or just search.
    # To keep it simple, we'll just show a search form or a limited list if possible.
    # Firestore doesn't easily "list all users" without a query.
    # Let's just list the current user for demo purposes or fetch a few.
    users = db.get_collection('users') 
    return render(request, 'custom_admin/user_list.html', {'users': users})

@staff_member_required
def toggle_super_staff(request, uid):
    if request.method == 'POST':
        is_super = request.POST.get('is_super_staff') == 'on'
        db.set_super_staff(uid, is_super)
    return redirect('admin_user_list')
