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

# Blog Management Views
def blog_permission_required(view_func):
    """Decorator to check if user can manage blogs (super_staff or editor)"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin:login')
        
        # Get Firebase UID from session
        uid = request.session.get('firebase_uid')
        if not uid or not db.can_manage_blogs(uid):
            messages.error(request, 'You do not have permission to manage blogs')
            return redirect('admin_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

@blog_permission_required
def admin_blog_list(request):
    """List all blogs with filtering options"""
    status_filter = request.GET.get('status', '')
    
    if status_filter:
        blogs = db.get_blogs(status=status_filter)
    else:
        blogs = db.get_blogs()
    
    # Convert Firestore timestamps to datetime for template
    from datetime import datetime
    for blog in blogs:
        if blog.get('created_at'):
            blog['created_at'] = blog['created_at']
        if blog.get('published_at'):
            blog['published_at'] = blog['published_at']
    
    context = {
        'blogs': blogs,
        'status_filter': status_filter,
    }
    return render(request, 'custom_admin/blog_list.html', context)

@blog_permission_required
def admin_blog_create(request):
    """Create a new blog post"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        excerpt = request.POST.get('excerpt', '')
        featured_image = request.POST.get('featured_image', '')
        tags = request.POST.get('tags', '')
        status = request.POST.get('status', 'draft')
        
        # Get author info from session
        uid = request.session.get('firebase_uid')
        user_profile = db.get_user_profile(uid)
        author_name = user_profile.get('name', 'Unknown') if user_profile else 'Unknown'
        
        # Generate slug from title
        slug = slugify(title)
        
        # Check if slug already exists
        existing = db.get_blog_by_slug(slug)
        if existing:
            messages.error(request, f'A blog with slug "{slug}" already exists')
            return render(request, 'custom_admin/blog_create.html', {
                'title': title,
                'content': content,
                'excerpt': excerpt,
                'featured_image': featured_image,
                'tags': tags,
                'status': status,
            })
        
        from firebase_admin import firestore
        from datetime import datetime
        
        blog_data = {
            'title': title,
            'slug': slug,
            'content': content,
            'excerpt': excerpt,
            'author_uid': uid,
            'author_name': author_name,
            'status': status,
            'featured_image': featured_image,
            'tags': tags,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
        }
        
        # Set published_at if status is published
        if status == 'published':
            blog_data['published_at'] = firestore.SERVER_TIMESTAMP
        
        blog_id = db.create_blog(blog_data)
        messages.success(request, f'Blog "{title}" created successfully')
        return redirect('admin_blog_list')
    
    return render(request, 'custom_admin/blog_create.html')

@blog_permission_required
def admin_blog_edit(request, blog_id):
    """Edit an existing blog post"""
    blog = db.get_blog_by_id(blog_id)
    
    if not blog:
        messages.error(request, 'Blog not found')
        return redirect('admin_blog_list')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        excerpt = request.POST.get('excerpt', '')
        featured_image = request.POST.get('featured_image', '')
        tags = request.POST.get('tags', '')
        status = request.POST.get('status', 'draft')
        
        from firebase_admin import firestore
        
        updated_data = {
            'title': title,
            'content': content,
            'excerpt': excerpt,
            'featured_image': featured_image,
            'tags': tags,
            'status': status,
            'updated_at': firestore.SERVER_TIMESTAMP,
        }
        
        # Update slug if title changed
        new_slug = slugify(title)
        if new_slug != blog.get('slug'):
            # Check if new slug already exists
            existing = db.get_blog_by_slug(new_slug)
            if existing and existing['id'] != blog_id:
                messages.error(request, f'A blog with slug "{new_slug}" already exists')
                return render(request, 'custom_admin/blog_edit.html', {'blog': blog})
            updated_data['slug'] = new_slug
        
        # Set published_at if status changed to published and wasn't published before
        if status == 'published' and blog.get('status') != 'published':
            updated_data['published_at'] = firestore.SERVER_TIMESTAMP
        
        db.update_blog(blog_id, updated_data)
        messages.success(request, f'Blog "{title}" updated successfully')
        return redirect('admin_blog_list')
    
    return render(request, 'custom_admin/blog_edit.html', {'blog': blog})

@blog_permission_required
def admin_blog_delete(request, blog_id):
    """Delete a blog post"""
    if request.method == 'POST':
        blog = db.get_blog_by_id(blog_id)
        if blog:
            db.delete_blog(blog_id)
            messages.success(request, f'Blog "{blog["title"]}" deleted successfully')
        else:
            messages.error(request, 'Blog not found')
    return redirect('admin_blog_list')

@blog_permission_required
def admin_blog_publish(request, blog_id):
    """Quick publish action for a blog"""
    if request.method == 'POST':
        blog = db.get_blog_by_id(blog_id)
        if blog:
            from firebase_admin import firestore
            update_data = {
                'status': 'published',
                'updated_at': firestore.SERVER_TIMESTAMP,
            }
            if not blog.get('published_at'):
                update_data['published_at'] = firestore.SERVER_TIMESTAMP
            
            db.update_blog(blog_id, update_data)
            messages.success(request, f'Blog "{blog["title"]}" published successfully')
        else:
            messages.error(request, 'Blog not found')
    return redirect('admin_blog_list')

@staff_member_required
def toggle_editor(request, uid):
    """Toggle editor permission for a user"""
    if request.method == 'POST':
        is_editor = request.POST.get('is_editor') == 'on'
        db.set_editor(uid, is_editor)
        messages.success(request, 'Editor permission updated')
    return redirect('admin_user_list')
    return redirect('admin_user_list')
