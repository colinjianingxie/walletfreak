from django.shortcuts import render
from django.http import Http404
from django.core.cache import cache
from django.utils.safestring import mark_safe
from core.services import db
from datetime import datetime
import markdown
from .utils import parse_tags_helper

def blog_list(request):
    """Display list of published blogs with search and filtering"""
    # Get filter parameters
    category = request.GET.get('category')
    search_query = request.GET.get('q')
    
    # New Filter Parameters
    ecosystem_filters = request.GET.getlist('ecosystem')
    tag_filters = request.GET.getlist('tag')
    experience_filters = request.GET.getlist('experience_level')
    read_time_filters = request.GET.getlist('read_time')
    
    uid = request.session.get('uid')
    
    # Get user's saved post IDs for UI state and filtering
    user_saved_posts = []
    if uid:
        user_saved_posts = db.get_user_saved_post_ids(uid)
    
    # Saved Filter (New General Filter)
    saved_filter = request.GET.get('saved')
    
    # Default blogs query
    # Default blogs query
    if saved_filter:
        if not uid:
             blogs = []
        else:
             # Pre-filter to only saved posts
             blogs = db.get_blogs(status='published') 
             blogs = [b for b in blogs if b.get('id') in user_saved_posts]
    elif category == 'Saved':
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
        
        # Apply Filters
        target_tags = []
        if category and category not in ['All', 'Saved', 'Premium']:
            # Map plural categories to singular tags where necessary
            tag_mapping = {
                'reviews': 'review',
                'guides': 'guide',
                'tips': 'tips',
                'news': 'news',
                'strategy': 'strategy'
            }
            target_tags.append(tag_mapping.get(category.lower(), category.lower()))
            
        if tag_filters:
            target_tags.extend([t.lower() for t in tag_filters])
            
        if target_tags:
            filtered_blogs = []
            for b in blogs:
                tags = b.get('tags')
                if not tags:
                    continue
                
                blog_tags_list = parse_tags_helper(tags)
                     
                # OR logic: if any of the target tags are in blog tags
                # Use intersection
                if any(t in blog_tags_list for t in target_tags):
                     filtered_blogs.append(b)
            blogs = filtered_blogs

        # 2. Premium Filter
        if category == 'Premium':
            blogs = [b for b in blogs if b.get('is_premium')]

        # Apply Multi-select Filters
        
        # Ecosystem
        if ecosystem_filters:
             blogs = [b for b in blogs if b.get('vendor') in ecosystem_filters]
            
        # Experience Level
        if experience_filters:
            blogs = [b for b in blogs if b.get('experience_level') in experience_filters]
            
        # Read Time
        if read_time_filters:
            blogs = [b for b in blogs if b.get('read_time') in read_time_filters]
            
    # Search Filter (applied after all other filters)
    # Search Filter (applied after all other filters)
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
            
            # Check content
            if query in b.get('content', '').lower():
                filtered_blogs.append(b)
                continue

            # Check tags
            tags = b.get('tags')
            if tags:
                parsed = parse_tags_helper(tags)
                if any(query in t.lower() for t in parsed):
                    filtered_blogs.append(b)
                    continue
        blogs = filtered_blogs
    
    # Check if user is an editor
    is_editor = False
    if uid:
        is_editor = db.can_manage_blogs(uid)
    
    # user_saved_posts moved to top
    
    # Prepare Data for Sidebar
    
    # 1. Ecosystem (Vendors)
    # Check cache first
    unique_vendors = cache.get('blog_sidebar_vendors')
    sorted_tags = cache.get('blog_sidebar_tags')
    
    if not unique_vendors or not sorted_tags:
        # Get all vendors actually used in published blogs
        unique_vendors_set = set()
        all_tags_set = set()
        
        all_published_blogs_filter = db.get_blogs(status='published')
        for b in all_published_blogs_filter:
            v = b.get('vendor')
            if v:
                unique_vendors_set.add(v)
                
            t = b.get('tags')
            if t:
                # Use the helper to get clean tags
                parsed = parse_tags_helper(t)
                for tag in parsed:
                    all_tags_set.add(tag)
                    
        unique_vendors = sorted(list(unique_vendors_set))
        sorted_tags = sorted(list(all_tags_set))
        
        cache.set('blog_sidebar_vendors', unique_vendors, 60 * 60) # 1 hour
        cache.set('blog_sidebar_tags', sorted_tags, 60 * 60) # 1 hour
    
    # 3. Static Choices
    experience_levels = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    read_times = [
        ('short', 'Short (< 3m)'),
        ('medium', 'Medium (3-7m)'),
        ('long', 'Long (7m+)'),
        ('video', 'Video Only'),
    ]

    # Add vote counts and user votes to each blog
    for blog in blogs:
        blog_id = blog.get('id')
        if blog_id:
            # Use stored counts if available, otherwise 0
            blog['upvote_count'] = blog.get('upvote_count', 0)
            blog['downvote_count'] = blog.get('downvote_count', 0)
            blog['total_score'] = blog['upvote_count'] - blog['downvote_count']
            
            if uid and uid in blog.get('users_upvoted', []):
                blog['user_vote'] = 'upvote'
            else:
                blog['user_vote'] = None
                
            # Normalize tags to list for template
            tags = blog.get('tags')
            if tags:
                blog['tags'] = parse_tags_helper(tags)
                            
    # Get trending posts (top 3 most upvoted published posts)
    trending_posts = []
    top_contributors = []
    
    if category != 'Saved':  # Don't show trending for saved posts view
        # Unique cache key for trending to avoid stale data issues
        trending_cache_key = 'blog_trending_and_contributors'
        cached_trends = cache.get(trending_cache_key)
        
        if cached_trends:
            trending_posts = cached_trends['trending']
            top_contributors = cached_trends['contributors']
        else:
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
            
            # Cache for 15 minutes
            cache.set(trending_cache_key, {
                'trending': trending_posts, 
                'contributors': top_contributors
            }, 60 * 15)
    
    # Get total registered users count for the Ledger card
    total_users = db.get_total_user_count()
    
    # Check subscription status
    is_subscribed = False
    if uid:
        prefs = db.get_user_notification_preferences(uid)
        is_subscribed = prefs.get('blog_updates', {}).get('enabled', False)

    # Check if user is premium
    user_is_premium = False
    if request.session.get('uid'):
        user_is_premium = db.is_premium(request.session.get('uid'))
        
    # Also treat superusers/editors as premium for viewing purposes if needed, 
    # but sticking to strict premium check or editor check.
    # Usually editors should see everything.
    # Editors can access locked content, but that logic is handled in specific views or property checks.
    # We do NOT want to override user_is_premium here because it hides the "Premium" nav link.

    context = {
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
        'is_subscribed': is_subscribed,
        'user_is_premium': user_is_premium,
        # Sidebar Context
        'ecosystem_vendors': unique_vendors,
        'tags': sorted_tags,
        'experience_levels': experience_levels,
        'read_times': read_times,
        'active_filters': {
            'ecosystem': ecosystem_filters,
            'tag': tag_filters,
            'experience_level': experience_filters,
            'read_time': read_time_filters,
            'saved': saved_filter,
        }
    }

    if request.headers.get('HX-Request') or request.headers.get('Hx-Request'):
        return render(request, 'blog/partials/blog_list_results.html', context)

    return render(request, 'blog/blog_list.html', context)

def blog_detail(request, slug):
    """Display a single blog post"""
    blog = db.get_blog_by_slug(slug)
    if not blog:
        raise Http404("Post not found")
    
    # Parse tags robustly
    if blog.get('tags'):
        blog['tags'] = parse_tags_helper(blog['tags'])
    
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
    
    # Check for premium access
    is_premium_post = blog.get('is_premium', False)
    locked = False
    
    if is_premium_post:
        # If user is editor/super staff, they can always see it (already checked via is_editor for unpublished)
        # But here we want to check if they are premium OR staff
        if is_editor:
            # Editors can see everything
            pass
        elif uid and db.is_premium(uid):
            # Premium users can see
            pass
        else:
            # Locked for everyone else (including non-logged-in)
            locked = True
            # Don't show content
            html_content = ""
            
    blog['html_content'] = html_content
    
    # Get voting information (upvotes only)
    blog_id = blog.get('id')
    # Use stored count
    upvote_count = blog.get('upvote_count', 0)
    user_vote = None
    
    if uid:
        user_vote = db.get_user_vote_on_blog(uid, blog_id)
    
    # Get related posts (other published posts, excluding current one)
    related_posts = cache.get(f'blog_related_{blog_id}')
    if not related_posts:
        related_posts = []
        all_published = db.get_blogs(status='published')
        for post in all_published:
            if post.get('id') != blog_id:
                related_posts.append(post)
        
        # Limit to 3 related posts
        related_posts = related_posts[:3]
        
        # Cache for 1 hour
        cache.set(f'blog_related_{blog_id}', related_posts, 60 * 60)
    
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
        'comments': root_comments,
        'total_comments': total_comments,
        'locked': locked
    })
