from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        # Register Firestore user admin
        from django.contrib import admin
        from .admin import FirestoreUserAdminSite
        
        # Create a dummy model class for admin registration
        class FirestoreUserProxy:
            class Meta:
                app_label = 'accounts'
                model_name = 'firestoreuser'
                verbose_name = 'Firestore User'
                verbose_name_plural = 'Firestore Users'
        
        # Register with admin site
        try:
            admin.site.register([FirestoreUserProxy], FirestoreUserAdminSite)
        except:
            pass  # Already registered
