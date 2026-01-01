from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden, Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.text import slugify
from core.services import db
from core.utils import get_all_card_vendors
from datetime import datetime
from google.cloud.firestore import Query

@login_required
def blog_drafts(request):
    """View all draft and archived posts (editors only)"""
    uid = request.session.get('uid')
    if not uid or not db.can_manage_blogs(uid):
        return HttpResponseForbidden("You don't have permission to view drafts")
    
    # Get all non-published blogs
    draft_blogs = db.get_blogs(status='draft')
    archived_blogs = db.get_blogs(status='archived')
    
    return render(request, 'blog/blog_drafts.html', {
        'draft_blogs': draft_blogs,
        'archived_blogs': archived_blogs,
        'is_editor': True
    })

@login_required
def blog_create(request):
    """Create a new blog post (editors only)"""
    uid = request.session.get('uid')
    if not uid or not db.can_manage_blogs(uid):
        return HttpResponseForbidden("You don't have permission to create blog posts")
    
    vendors = get_all_card_vendors()
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        featured_image = request.POST.get('featured_image', '').strip()
        tags = request.POST.get('tags', '').strip()
        status = request.POST.get('status', 'draft')
        is_premium = request.POST.get('is_premium') == 'on'
        
        # New Metadata Fields
        read_time = request.POST.get('read_time', 'medium')
        experience_level = request.POST.get('experience_level', 'intermediate')
        vendor = request.POST.get('vendor', '')
        
        # Validate required fields
        error = None
        if not title or not content:
            error = 'Title and content are required'
        elif not tags:
             error = 'At least one tag is required (Content Type)'
             
        if error:
            return render(request, 'blog/blog_create.html', {
                'error': error,
                'form_data': request.POST,
                'vendors': vendors
            })
        
        # Generate slug from title
        slug = slugify(title)
        
        # Check if slug already exists
        existing_blog = db.get_blog_by_slug(slug)
        if existing_blog:
            # Append timestamp to make unique
            slug = f"{slug}-{int(datetime.now().timestamp())}"
        
        # Get user profile for author info
        user_profile = db.get_user_profile(uid)
        author_name = user_profile.get('username') or user_profile.get('name') or 'Unknown'
        
        # Prepare blog data
        blog_data = {
            'title': title,
            'slug': slug,
            'content': content,
            'excerpt': excerpt,
            'author_uid': uid,
            # 'author_name': author_name, # Storing author_name deprecated, fetched dynamically
            'status': status,
            'featured_image': featured_image,
            'tags': tags,
            'is_premium': is_premium,
            'read_time': read_time,
            'experience_level': experience_level,
            'vendor': vendor,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        }
        
        # Set published_at if publishing
        if status == 'published':
            blog_data['published_at'] = datetime.now()
        
        # Save to Firestore
        blog_id = db.create_blog(blog_data)
        
        return redirect('blog_detail', slug=slug)
    
    return render(request, 'blog/blog_create.html', {'vendors': vendors})

@login_required
def blog_edit(request, slug):
    """Edit an existing blog post (editors only)"""
    uid = request.session.get('uid')
    if not uid or not db.can_manage_blogs(uid):
        return HttpResponseForbidden("You don't have permission to edit blog posts")
    
    # Get existing blog
    blog = db.get_blog_by_slug(slug)
    if not blog:
        raise Http404("Post not found")
        
    vendors = get_all_card_vendors()
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        featured_image = request.POST.get('featured_image', '').strip()
        tags = request.POST.get('tags', '').strip()
        status = request.POST.get('status', 'draft')
        is_premium = request.POST.get('is_premium') == 'on'
        
        # New Metadata Fields
        read_time = request.POST.get('read_time', 'medium')
        experience_level = request.POST.get('experience_level', 'intermediate')
        vendor = request.POST.get('vendor', '')
        
        # Validate required fields
        error = None
        if not title or not content:
            error = 'Title and content are required'
        elif not tags:
             error = 'At least one tag is required (Content Type)'
             
        if error:
            return render(request, 'blog/blog_edit.html', {
                'blog': blog,
                'error': error,
                'vendors': vendors
            })
        
        # Prepare update data
        update_data = {
            'title': title,
            'content': content,
            'excerpt': excerpt,
            'featured_image': featured_image,
            'tags': tags,
            'status': status,
            'is_premium': is_premium,
            'read_time': read_time,
            'experience_level': experience_level,
            'vendor': vendor,
            'updated_at': datetime.now(),
        }
        
        # Update published_at if status changed to published
        if status == 'published' and blog.get('status') != 'published':
            update_data['published_at'] = datetime.now()
        
        # Update slug if title changed
        new_slug = slugify(title)
        if new_slug != slug:
            # Check if new slug exists
            existing_blog = db.get_blog_by_slug(new_slug)
            if existing_blog and existing_blog.get('id') != blog.get('id'):
                new_slug = f"{new_slug}-{int(datetime.now().timestamp())}"
            update_data['slug'] = new_slug
            slug = new_slug
        
        # Update in Firestore
        db.update_blog(blog['id'], update_data)
        
        return redirect('blog_detail', slug=slug)
    
    return render(request, 'blog/blog_edit.html', {'blog': blog, 'vendors': vendors})

@login_required
@require_POST
def blog_delete(request, slug):
    """Delete a blog post (editors only)"""
    uid = request.session.get('uid')
    if not uid or not db.can_manage_blogs(uid):
        return HttpResponseForbidden("You don't have permission to delete blog posts")
    
    # Get existing blog
    blog = db.get_blog_by_slug(slug)
    if not blog:
        raise Http404("Post not found")
    
    # Delete from Firestore
    db.delete_blog(blog['id'])
    
    return redirect('blog_list')

@login_required
def blog_manage_status(request):
    """Manage blog post statuses (editors only)"""
    uid = request.session.get('uid')
    if not uid or not db.can_manage_blogs(uid):
        return HttpResponseForbidden("You don't have permission to manage posts")
    
    # Get all blogs
    all_blogs_ref = db.db.collection('blogs').order_by('updated_at', direction=Query.DESCENDING)
    all_blogs = [doc.to_dict() | {'id': doc.id} for doc in all_blogs_ref.stream()]
    
    return render(request, 'blog/blog_manage_status.html', {
        'all_blogs': all_blogs,
        'is_editor': True
    })

@login_required
@require_POST
def blog_quick_status_change(request, blog_id):
    """Quick status change for a blog post (editors only)"""
    uid = request.session.get('uid')
    if not uid or not db.can_manage_blogs(uid):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    new_status = request.POST.get('status')
    if new_status not in ['draft', 'published', 'archived']:
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
    
    update_data = {
        'status': new_status,
        'updated_at': datetime.now()
    }
    
    # Set published_at if changing to published
    if new_status == 'published':
        blog = db.get_blog_by_id(blog_id)
        if blog and blog.get('status') != 'published':
            update_data['published_at'] = datetime.now()
    
    db.update_blog(blog_id, update_data)
    return JsonResponse({'success': True, 'status': new_status})
