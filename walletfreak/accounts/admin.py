from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from core.services import db


class FirestoreUser:
    """Proxy class for Firestore users to work with Django admin"""
    def __init__(self, uid, data):
        self.uid = uid
        self.id = uid
        self.name = data.get('name', 'Unknown')
        self.email = data.get('email', '')
        self.is_super_staff = data.get('is_super_staff', False)
        self.is_editor = data.get('is_editor', False)
        self.created_at = data.get('created_at')
    
    def __str__(self):
        return f"{self.name} ({self.email})"


class FirestoreUserAdmin:
    """Custom admin for managing Firestore users"""
    
    def get_urls(self):
        urls = [
            path('', self.admin_site.admin_view(self.user_list_view), name='accounts_firestoreuser_changelist'),
            path('<str:uid>/toggle-super/', self.admin_site.admin_view(self.toggle_super_staff), name='accounts_firestoreuser_toggle_super'),
            path('<str:uid>/toggle-editor/', self.admin_site.admin_view(self.toggle_editor), name='accounts_firestoreuser_toggle_editor'),
        ]
        return urls
    
    def user_list_view(self, request):
        """Display list of Firestore users with permission toggles"""
        users_data = db.get_collection('users')
        users = [FirestoreUser(user['id'], user) for user in users_data]
        
        context = {
            'users': users,
            'title': 'Firestore Users',
            'opts': type('obj', (object,), {
                'app_label': 'accounts',
                'model_name': 'firestoreuser',
                'verbose_name_plural': 'Firestore Users'
            })(),
            'has_add_permission': False,
            'has_change_permission': True,
            'has_delete_permission': False,
        }
        
        return render(request, 'admin/accounts/firestore_user_list.html', context)
    
    def toggle_super_staff(self, request, uid):
        """Toggle super_staff permission for a user"""
        if request.method == 'POST':
            is_super = request.POST.get('is_super_staff') == 'on'
            db.set_super_staff(uid, is_super)
            messages.success(request, f'Super Staff permission updated for user {uid}')
        return redirect('admin:accounts_firestoreuser_changelist')
    
    def toggle_editor(self, request, uid):
        """Toggle editor permission for a user"""
        if request.method == 'POST':
            is_editor = request.POST.get('is_editor') == 'on'
            db.set_editor(uid, is_editor)
            messages.success(request, f'Editor permission updated for user {uid}')
        return redirect('admin:accounts_firestoreuser_changelist')


# Register the custom admin
class FirestoreUserAdminSite(admin.ModelAdmin):
    """Wrapper to register FirestoreUserAdmin in Django admin"""
    
    def has_module_permission(self, request):
        return request.user.is_staff or request.user.is_superuser
    
    def get_urls(self):
        firestore_admin = FirestoreUserAdmin()
        firestore_admin.admin_site = self.admin_site
        return firestore_admin.get_urls()


# We need to register this in a way that Django admin recognizes it
# Since we don't have a real model, we'll add it via admin.site.register in the ready() method
# For now, let's create the template that will be used
