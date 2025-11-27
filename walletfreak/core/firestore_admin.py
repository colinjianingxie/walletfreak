"""
Custom admin views for managing Firestore data without Django models.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import path
from .services import FirestoreService
import json

db = FirestoreService()


@staff_member_required
def credit_card_list(request):
    """List all credit cards from Firestore"""
    cards = db.get_cards()
    
    # Add benefit count to each card
    for card in cards:
        card['benefit_count'] = len(card.get('benefits', []))
    
    context = {
        'title': 'Credit Cards',
        'cards': cards,
        'has_permission': True,
    }
    return render(request, 'admin/firestore/credit_card_list.html', context)


@staff_member_required
def credit_card_edit(request, card_id):
    """Edit a credit card"""
    card = db.get_card_by_slug(card_id)
    
    if not card:
        messages.error(request, f'Card {card_id} not found')
        return redirect('admin:credit_card_list')
    
    if request.method == 'POST':
        try:
            # Parse benefits JSON
            benefits_json = request.POST.get('benefits_json', '[]')
            benefits = json.loads(benefits_json)
            
            # Parse personalities JSON
            personalities_json = request.POST.get('personalities_json', '[]')
            personalities = json.loads(personalities_json)
            
            # Update card data
            card_data = {
                'name': request.POST.get('name'),
                'issuer': request.POST.get('issuer', ''),
                'annual_fee': float(request.POST.get('annual_fee', 0)),
                'image_url': request.POST.get('image_url', ''),
                'apply_url': request.POST.get('apply_url', ''),
                'benefits': benefits,
                'personalities': personalities
            }
            
            db.update_document('credit_cards', card_id, card_data)
            messages.success(request, f'Successfully updated {card_data["name"]}')
            return redirect('admin:credit_card_list')
            
        except json.JSONDecodeError as e:
            messages.error(request, f'Invalid JSON format: {e}')
        except Exception as e:
            messages.error(request, f'Error saving card: {e}')
    
    # Prepare data for template
    card['benefits_json'] = json.dumps(card.get('benefits', []), indent=2)
    card['personalities_json'] = json.dumps(card.get('personalities', []), indent=2)
    
    context = {
        'title': f'Edit {card.get("name", "Card")}',
        'card': card,
        'card_id': card_id,
        'has_permission': True,
    }
    return render(request, 'admin/firestore/credit_card_edit.html', context)


@staff_member_required
def credit_card_create(request):
    """Create a new credit card"""
    if request.method == 'POST':
        try:
            card_id = request.POST.get('card_id')
            
            # Check if card already exists
            if db.get_card_by_slug(card_id):
                messages.error(request, f'Card with ID {card_id} already exists')
                return render(request, 'admin/firestore/credit_card_create.html', {
                    'title': 'Create Credit Card',
                    'has_permission': True,
                })
            
            # Parse benefits JSON
            benefits_json = request.POST.get('benefits_json', '[]')
            benefits = json.loads(benefits_json)
            
            # Parse personalities JSON
            personalities_json = request.POST.get('personalities_json', '[]')
            personalities = json.loads(personalities_json)
            
            # Create card data
            card_data = {
                'name': request.POST.get('name'),
                'issuer': request.POST.get('issuer', ''),
                'annual_fee': float(request.POST.get('annual_fee', 0)),
                'image_url': request.POST.get('image_url', ''),
                'apply_url': request.POST.get('apply_url', ''),
                'benefits': benefits,
                'personalities': personalities
            }
            
            db.create_document('credit_cards', card_data, doc_id=card_id)
            messages.success(request, f'Successfully created {card_data["name"]}')
            return redirect('admin:credit_card_list')
            
        except json.JSONDecodeError as e:
            messages.error(request, f'Invalid JSON format: {e}')
        except Exception as e:
            messages.error(request, f'Error creating card: {e}')
    
    context = {
        'title': 'Create Credit Card',
        'has_permission': True,
    }
    return render(request, 'admin/firestore/credit_card_create.html', context)


@staff_member_required
def credit_card_delete(request, card_id):
    """Delete a credit card"""
    if request.method == 'POST':
        try:
            card = db.get_card_by_slug(card_id)
            if card:
                db.delete_document('credit_cards', card_id)
                messages.success(request, f'Successfully deleted {card.get("name", card_id)}')
            else:
                messages.error(request, f'Card {card_id} not found')
        except Exception as e:
            messages.error(request, f'Error deleting card: {e}')
    
    return redirect('admin:credit_card_list')


@staff_member_required
def personality_list(request):
    """List all personalities from Firestore"""
    personalities = db.get_personalities()
    
    context = {
        'title': 'Personalities',
        'personalities': personalities,
        'has_permission': True,
    }
    return render(request, 'admin/firestore/personality_list.html', context)


@staff_member_required
def personality_edit(request, personality_id):
    """Edit a personality"""
    personality = db.get_personality_by_slug(personality_id)
    
    if not personality:
        messages.error(request, f'Personality {personality_id} not found')
        return redirect('admin:personality_list')
    
    if request.method == 'POST':
        try:
            personality_data = {
                'name': request.POST.get('name'),
                'tagline': request.POST.get('tagline', ''),
                'description': request.POST.get('description', ''),
                'icon': request.POST.get('icon', '')
            }
            
            db.update_document('personalities', personality_id, personality_data)
            messages.success(request, f'Successfully updated {personality_data["name"]}')
            return redirect('admin:personality_list')
            
        except Exception as e:
            messages.error(request, f'Error saving personality: {e}')
    
    context = {
        'title': f'Edit {personality.get("name", "Personality")}',
        'personality': personality,
        'personality_id': personality_id,
        'has_permission': True,
    }
    return render(request, 'admin/firestore/personality_edit.html', context)


# URL patterns for custom admin
firestore_admin_urls = [
    path('credit-cards/', credit_card_list, name='credit_card_list'),
    path('credit-cards/create/', credit_card_create, name='credit_card_create'),
    path('credit-cards/<str:card_id>/edit/', credit_card_edit, name='credit_card_edit'),
    path('credit-cards/<str:card_id>/delete/', credit_card_delete, name='credit_card_delete'),
    path('personalities/', personality_list, name='personality_list'),
    path('personalities/<str:personality_id>/edit/', personality_edit, name='personality_edit'),
]