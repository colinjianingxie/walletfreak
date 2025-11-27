from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.utils.html import format_html
from .firestore_admin import firestore_admin_urls
from .services import FirestoreService


class FirestoreAdminSite(admin.AdminSite):
    """
    Custom admin site that adds Firestore management links.
    """
    site_header = "WalletFreak Administration"
    site_title = "WalletFreak Admin"
    index_title = "Welcome to WalletFreak Administration"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('firestore/', self.admin_view(self.firestore_index), name='firestore_index'),
        ] + [
            path(f'firestore/{url.pattern}', url.callback, name=url.name)
            for url in firestore_admin_urls
        ]
        return custom_urls + urls
    
    def firestore_index(self, request):
        """Custom index page showing Firestore collections"""
        from .services import FirestoreService
        db = FirestoreService()
        
        try:
            cards_count = len(db.get_cards())
        except:
            cards_count = 0
        
        try:
            personalities_count = len(db.get_personalities())
        except:
            personalities_count = 0
        
        context = {
            **self.each_context(request),
            'title': 'Firestore Data Management',
            'cards_count': cards_count,
            'personalities_count': personalities_count,
        }
        return render(request, 'admin/firestore/index.html', context)
    
    def index(self, request, extra_context=None):
        """Override index to show Firestore management directly"""
        from .services import FirestoreService
        db = FirestoreService()
        
        try:
            cards_count = len(db.get_cards())
        except:
            cards_count = 0
        
        try:
            personalities_count = len(db.get_personalities())
        except:
            personalities_count = 0
        
        context = {
            **self.each_context(request),
            'title': 'WalletFreak Administration',
            'cards_count': cards_count,
            'personalities_count': personalities_count,
            'app_list': [],  # Empty to hide default models
        }
        return render(request, 'admin/index.html', context)


# Replace the default admin site
admin.site = FirestoreAdminSite()
admin.site.site_header = "WalletFreak Administration"
admin.site.site_title = "WalletFreak Admin"
admin.site.index_title = "Welcome to WalletFreak Administration"
