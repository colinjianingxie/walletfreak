from django.shortcuts import render, redirect
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from core.services import db
from datetime import datetime
import markdown
from .models import Blog, Vote

def blog_list(request):
    """Display list of published blogs with search and filtering"""
    # Get filter parameters
    category = request.GET.get('category')
    search_query = request.GET.get('q')
    uid = request.session.get('uid')
    
    # Handle saved posts category
    if category == 'Saved':
        if not uid:
            # If user is not logged in, show empty list
            blogs = []
        else:
            # Get user's saved posts
            saved_posts = db.get_user_saved_posts(uid)
            blogs = saved_posts if saved_posts else []
    else:
        # Get all published blogs
        blogs = db.get_blogs(status='published')
        
        # Filter by category if specified
        if category and category != 'All':
            # Map plural categories to singular tags where necessary
            tag_mapping = {
                'reviews': 'review',
                'guides': 'guide',
                'tips': 'tips',
                'news': 'news'
            }
            
            target_tag = tag_mapping.get(category.lower(), category.lower())
            
            filtered_blogs = []
            for b in blogs:
                tags = b.get('tags')
                if not tags:
                    continue
                
                if isinstance(tags, list):
                    # Check if target tag matches any tag in the list (case-insensitive)
                    if any(target_tag == str(t).lower() for t in tags):
                        filtered_blogs.append(b)
                else:
                    # Check if target tag is in the string tag
                    if target_tag in str(tags).lower():
                        filtered_blogs.append(b)
            blogs = filtered_blogs
    
    # Filter by search query if specified
    if search_query and category != 'Saved':
        query = search_query.lower()
        filtered_blogs = []
        for b in blogs:
            # Check title
            if query in b.get('title', '').lower():
                filtered_blogs.append(b)
                continue
                
            # Check excerpt
            if query in b.get('excerpt', '').lower():
                filtered_blogs.append(b)
                continue
                
            # Check tags
            tags = b.get('tags')
            if tags:
                if isinstance(tags, list):
                    if any(query in str(t).lower() for t in tags):
                        filtered_blogs.append(b)
                else:
                    if query in str(tags).lower():
                        filtered_blogs.append(b)
        blogs = filtered_blogs
    
    # Check if user is an editor
    is_editor = False
    if uid:
        is_editor = db.can_manage_blogs(uid)
    
    # Get user's saved post IDs for UI state
    user_saved_posts = []
    if uid:
        user_saved_posts = db.get_user_saved_post_ids(uid)
    
    # Add vote counts and user votes to each blog
    for blog in blogs:
        blog_id = blog.get('id')
        if blog_id:
            # Use stored counts if available, otherwise 0
            blog['upvote_count'] = blog.get('upvote_count', 0)
            blog['downvote_count'] = blog.get('downvote_count', 0)
            blog['total_score'] = blog['upvote_count'] - blog['downvote_count']
            
            if uid:
                blog['user_vote'] = db.get_user_vote_on_blog(uid, blog_id)
            else:
                blog['user_vote'] = None
    
    # Get trending posts (top 3 most upvoted published posts)
    trending_posts = []
    top_contributors = []
    
    if category != 'Saved':  # Don't show trending for saved posts view
        all_published_blogs = db.get_blogs(status='published')
        
        # Add vote counts to all published blogs for sorting
        for blog in all_published_blogs:
            blog_id = blog.get('id')
            if blog_id:
                blog['upvote_count'] = blog.get('upvote_count', 0)
                blog['total_score'] = blog.get('upvote_count', 0) - blog.get('downvote_count', 0)
        
        # Sort by upvote count (descending) and take top 3
        trending_posts = sorted(all_published_blogs, key=lambda x: x.get('upvote_count', 0), reverse=True)[:3]
        
        # Calculate top contributors by post count
        author_post_counts = {}
        for blog in all_published_blogs:
            author_uid = blog.get('author_uid')
            author_name = blog.get('author_name')
            author_username = blog.get('author_username')
            
            if author_uid:
                if author_uid not in author_post_counts:
                    # Use username if available, otherwise fallback to name
                    display_name = author_name
                    username = author_username if author_username and author_username != 'Unknown' else author_name
                    
                    author_post_counts[author_uid] = {
                        'name': display_name,
                        'username': username,
                        'post_count': 0
                    }
                author_post_counts[author_uid]['post_count'] += 1
        
        # Sort by post count and take top 3
        top_contributors = sorted(
            author_post_counts.values(),
            key=lambda x: x['post_count'],
            reverse=True
        )[:3]
    
    # Get total registered users count for the Ledger card
    total_users = db.get_total_user_count()
    
    # Check subscription status
    is_subscribed = False
    if uid:
        prefs = db.get_user_notification_preferences(uid)
        is_subscribed = prefs.get('blog_updates', {}).get('enabled', False)

    return render(request, 'blog/blog_list.html', {
        'blogs': blogs,
        'is_editor': is_editor,
        'current_category': category,
        'search_query': search_query,
        'user_saved_posts': user_saved_posts,
        'is_authenticated': bool(uid),
        'trending_posts': trending_posts,
        'top_contributors': top_contributors,
        'now': datetime.now(),
        'total_users': total_users,
        'is_subscribed': is_subscribed
    })

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

def blog_detail(request, slug):
    """Display a single blog post"""
    blog = db.get_blog_by_slug(slug)
    if not blog:
        raise Http404("Post not found")
    
    # Check if user is an editor (can view drafts)
    is_editor = False
    uid = request.session.get('uid')
    if uid:
        is_editor = db.can_manage_blogs(uid)
    
    # Only show published blogs to non-editors
    if blog.get('status') != 'published' and not is_editor:
        raise Http404("Post not found")
    
    # Fetch author profile for avatar
    if blog.get('author_uid'):
        try:
            author_profile = db.get_user_profile(blog['author_uid'])
            if author_profile:
                blog['author_profile'] = author_profile
        except Exception as e:
            print(f"Error fetching author profile: {e}")

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['extra', 'codehilite', 'fenced_code', 'tables'])
    html_content = mark_safe(md.convert(blog.get('content', '')))
    blog['html_content'] = html_content
    
    # Get voting information (upvotes only)
    blog_id = blog.get('id')
    # Use stored count
    upvote_count = blog.get('upvote_count', 0)
    user_vote = None
    
    if uid:
        user_vote = db.get_user_vote_on_blog(uid, blog_id)
    
    # Get related posts (other published posts, excluding current one)
    related_posts = []
    all_published = db.get_blogs(status='published')
    for post in all_published:
        if post.get('id') != blog_id:
            related_posts.append(post)
    
    # Limit to 3 related posts
    related_posts = related_posts[:3]
    
    # Increment view count
    db.increment_blog_view_count(blog_id)
    
    # Get comments
    raw_comments = db.get_blog_comments(blog_id)
    
    # Process comments into a tree structure
    comments_map = {c['id']: {**c, 'replies': []} for c in raw_comments}
    root_comments = []
    
    for c in raw_comments:
        comment_id = c['id']
        parent_id = c.get('parent_id')
        
        # Add basic time info if not present (it should be though)
        if 'created_at' not in c:
             c['created_at'] = datetime.now()

        if parent_id and parent_id in comments_map:
            comments_map[parent_id]['replies'].append(comments_map[comment_id])
        else:
            root_comments.append(comments_map[comment_id])
            
    # Count total comments
    total_comments = len(raw_comments)

    return render(request, 'blog/blog_detail.html', {
        'blog': blog,
        'is_editor': is_editor,
        'upvote_count': upvote_count,
        'user_vote': user_vote,
        'is_authenticated': bool(uid),
        'related_posts': related_posts,
        'comments': root_comments,
        'total_comments': total_comments
    })

@require_POST
def add_comment(request, slug):
    """Add a comment to a blog post"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        
    blog = db.get_blog_by_slug(slug)
    if not blog:
        return JsonResponse({'success': False, 'error': 'Post not found'}, status=404)
        
    content = request.POST.get('content')
    parent_id = request.POST.get('parent_id')
    
    if not content:
        return JsonResponse({'success': False, 'error': 'Content required'}, status=400)
        
    comment = db.add_blog_comment(blog['id'], uid, content, parent_id)
    
    if comment:
        return JsonResponse({
            'success': True, 
            'comment': {
                'id': comment['id'],
                'content': comment['content'],
                'created_at_formatted': 'Just now'
            }
        })
    else:
        return JsonResponse({'success': False, 'error': 'Failed to add comment'}, status=500)

@require_POST
def vote_comment(request, slug, comment_id):
    """Vote on a comment"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        
    blog = db.get_blog_by_slug(slug)
    if not blog:
        return JsonResponse({'success': False, 'error': 'Post not found'}, status=404)
        
    vote_type = request.POST.get('vote_type')
    result = db.vote_comment(blog['id'], comment_id, uid, vote_type)
    
    if result:
        return JsonResponse({'success': True, 'action': result})
    else:
        return JsonResponse({'success': False, 'error': 'Failed to vote'}, status=500)
@require_POST
def delete_comment(request, slug, comment_id):
    """Delete a comment from a blog post"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        
    blog = db.get_blog_by_slug(slug)
    if not blog:
        return JsonResponse({'success': False, 'error': 'Post not found'}, status=404)
    
    # Verify ownership or permissions
    # Need to fetch comment first to check owner
    comments = db.get_blog_comments(blog['id'])
    target_comment = next((c for c in comments if c['id'] == comment_id), None)
    
    if not target_comment:
        return JsonResponse({'success': False, 'error': 'Comment not found'}, status=404)
        
    # Check if user is author OR acts as moderator (e.g. blog author or editor)
    is_author = target_comment.get('author_uid') == uid
    can_manage = db.can_manage_blogs(uid)
    
    if not is_author and not can_manage:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
    result = db.delete_blog_comment(blog['id'], comment_id)
    
    if result:
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Failed to delete comment'}, status=500)

@login_required
def blog_create(request):
    """Create a new blog post (editors only)"""
    uid = request.session.get('uid')
    if not uid or not db.can_manage_blogs(uid):
        return HttpResponseForbidden("You don't have permission to create blog posts")
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        featured_image = request.POST.get('featured_image', '').strip()
        tags = request.POST.get('tags', '').strip()
        status = request.POST.get('status', 'draft')
        
        # Validate required fields
        if not title or not content:
            return render(request, 'blog/blog_create.html', {
                'error': 'Title and content are required',
                'form_data': request.POST
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
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        }
        
        # Set published_at if publishing
        if status == 'published':
            blog_data['published_at'] = datetime.now()
        
        # Save to Firestore
        blog_id = db.create_blog(blog_data)
        
        return redirect('blog_detail', slug=slug)
    
    return render(request, 'blog/blog_create.html')

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
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        featured_image = request.POST.get('featured_image', '').strip()
        tags = request.POST.get('tags', '').strip()
        status = request.POST.get('status', 'draft')
        
        # Validate required fields
        if not title or not content:
            return render(request, 'blog/blog_edit.html', {
                'blog': blog,
                'error': 'Title and content are required'
            })
        
        # Prepare update data
        update_data = {
            'title': title,
            'content': content,
            'excerpt': excerpt,
            'featured_image': featured_image,
            'tags': tags,
            'status': status,
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
    
    return render(request, 'blog/blog_edit.html', {'blog': blog})

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
    from google.cloud.firestore import Query
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

@require_POST
def save_post(request, slug):
    """Save a blog post for the current user"""
    try:
        # Check authentication for AJAX requests
        uid = request.session.get('uid')
        if not uid:
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        
        # Get the blog post
        blog = db.get_blog_by_slug(slug)
        if not blog:
            return JsonResponse({'success': False, 'error': 'Post not found'}, status=404)
        
        # Save the post for the user
        success = db.save_post_for_user(uid, blog['id'])
        
        return JsonResponse({'success': success})
    except Exception as e:
        print(f"Error in save_post: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def unsave_post(request, slug):
    """Unsave a blog post for the current user"""
    try:
        # Check authentication for AJAX requests
        uid = request.session.get('uid')
        if not uid:
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        
        # Get the blog post
        blog = db.get_blog_by_slug(slug)
        if not blog:
            return JsonResponse({'success': False, 'error': 'Post not found'}, status=404)
        
        # Unsave the post for the user
        success = db.unsave_post_for_user(uid, blog['id'])
        
        return JsonResponse({'success': success})
    except Exception as e:
        print(f"Error in unsave_post: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def vote_blog(request, slug):
    """Vote on a blog post (authenticated users only)"""
    try:
        # Check authentication
        uid = request.session.get('uid')
        if not uid:
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        
        # Get the blog post
        blog = db.get_blog_by_slug(slug)
        if not blog:
            return JsonResponse({'success': False, 'error': 'Post not found'}, status=404)
        
        blog_id = blog['id']
        
        # Get action (add/remove) - Default to 'add' if not specified for backward compat (though risks double count)
        action = request.POST.get('action', 'add')
        vote_type = request.POST.get('vote_type', 'upvote')
        
        if vote_type != 'upvote':
             return JsonResponse({'success': False, 'error': 'Only upvotes are allowed'}, status=400)

        if action == 'remove':
            success = db.remove_user_vote_on_blog(uid, blog_id)
            new_vote = None
        else:
            success = db.add_user_vote_on_blog(uid, blog_id, vote_type)
            new_vote = 'upvote'
        
        if success:
            # Get updated vote count (upvotes only)
            upvote_count = db.get_blog_vote_count(blog_id, 'upvote')
            
            return JsonResponse({
                'success': True,
                'user_vote': new_vote,
                'upvote_count': upvote_count
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to process vote'}, status=500)
            
    except Exception as e:
        print(f"Error in vote_blog: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def subscribe_to_blog(request):
    """Subscribe current user to blog updates"""
    try:
        uid = request.session.get('uid')
        if not uid:
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
            
        # Get current preferences or defaults
        prefs = db.get_user_notification_preferences(uid)
        
        # Update blog_updates setting
        if 'blog_updates' not in prefs:
            prefs['blog_updates'] = {}
            
        prefs['blog_updates']['enabled'] = True
        
        db.update_user_notification_preferences(uid, prefs)
        
        return JsonResponse({'success': True})
    except Exception as e:
        print(f"Error subscribing to blog: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)




