from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from core.services import db

@staff_member_required
def admin_dashboard(request):
    return render(request, 'custom_admin/dashboard.html')

@staff_member_required
def admin_card_list(request):
    cards = db.get_cards()
    return render(request, 'custom_admin/card_list.html', {'cards': cards})

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
