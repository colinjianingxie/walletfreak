from django.contrib import admin
from django.utils.html import format_html
from .models import Blog


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_name', 'status_badge', 'created_at', 'published_at', 'action_buttons']
    list_filter = ['status', 'created_at', 'published_at']
    search_fields = ['title', 'content', 'author_name', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'published_at']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'content', 'excerpt')
        }),
        ('Author', {
            'fields': ('author_uid', 'author_name')
        }),
        ('Publishing', {
            'fields': ('status', 'published_at')
        }),
        ('Media & SEO', {
            'fields': ('featured_image', 'tags'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'draft': '#f59e0b',
            'published': '#10b981',
            'archived': '#6b7280'
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def action_buttons(self, obj):
        if obj.status == 'draft':
            return format_html(
                '<a class="button" href="/blog/{}/" target="_blank">Preview</a>',
                obj.slug
            )
        elif obj.status == 'published':
            return format_html(
                '<a class="button" href="/blog/{}/" target="_blank">View</a>',
                obj.slug
            )
        return '-'
    action_buttons.short_description = 'Actions'
    
    def save_model(self, request, obj, form, change):
        # Set author info from request user if creating new blog
        if not change:
            # Get Firebase UID from session
            uid = request.session.get('firebase_uid')
            if uid:
                obj.author_uid = uid
                from core.services import db
                user_profile = db.get_user_profile(uid)
                if user_profile:
                    obj.author_name = user_profile.get('name', 'Unknown')
            else:
                obj.author_uid = 'admin'
                obj.author_name = request.user.username or 'Admin'
        
        super().save_model(request, obj, form, change)
    
    def has_module_permission(self, request):
        # Allow access if user is super_staff or editor
        if request.user.is_superuser or request.user.is_staff:
            uid = request.session.get('firebase_uid')
            if uid:
                from core.services import db
                return db.can_manage_blogs(uid)
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return self.has_module_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)
    
    class Media:
        css = {
            'all': ('admin/css/blog_admin.css',)
        }
