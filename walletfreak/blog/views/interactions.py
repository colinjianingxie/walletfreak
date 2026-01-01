from django.http import JsonResponse
from django.views.decorators.http import require_POST
from core.services import db

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

@require_POST
def vote_blog(request, slug):
    """Vote on a blog post (toggle upvote)"""
    try:
        # Check authentication for AJAX requests
        uid = request.session.get('uid')
        if not uid:
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        
        # Get the blog post
        blog = db.get_blog_by_slug(slug)
        if not blog:
            return JsonResponse({'success': False, 'error': 'Post not found'}, status=404)
        
        blog_id = blog['id']
        
        # Check current vote status
        current_vote = db.get_user_vote_on_blog(uid, blog_id)
        
        if current_vote == 'upvote':
            # Remove vote
            success = db.remove_user_vote_on_blog(uid, blog_id)
            action = 'removed'
        else:
            # Add upvote
            success = db.add_user_vote_on_blog(uid, blog_id, 'upvote')
            action = 'added'
            
        if success:
            # Get updated count
            new_count = db.get_blog_vote_count(blog_id, 'upvote')
            return JsonResponse({
                'success': True, 
                'action': action,
                'new_count': new_count
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to update vote'}, status=500)
            
    except Exception as e:
        print(f"Error in vote_blog: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
