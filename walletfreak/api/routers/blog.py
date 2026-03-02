from ninja import Router, Query
from django.http import JsonResponse
from core.services import db
from api.auth_middleware import BearerAuth
from ninja import Schema
from typing import Optional
import json
import ast

router = Router(tags=["blog"])


def parse_string_list(value):
    """Parse Firestore fields stored as stringified Python lists.
    e.g. "['Reviews', 'Strategy', 'Tips']" -> ['Reviews', 'Strategy', 'Tips']
    """
    if isinstance(value, list):
        return value
    if not isinstance(value, str) or not value.strip():
        return []
    s = value.strip()
    if s.startswith("[") and s.endswith("]"):
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if item]
        except (ValueError, SyntaxError):
            pass
    # Fallback: treat as single value
    return [s] if s else []


class BlogListParams(Schema):
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None
    category: Optional[str] = None
    tag: Optional[str] = None
    saved: bool = False


def normalize_post(post, uid=None, saved_ids=None):
    """Normalize blog post fields for consistent mobile API response."""
    # Map Firestore field names to what the mobile app expects
    post["upvotes"] = post.get("upvote_count", 0) or 0
    post["downvotes"] = post.get("downvote_count", 0) or 0
    post["comment_count"] = post.get("comment_count", 0) or 0
    post["image_url"] = post.get("featured_image", "") or post.get("image_url", "") or ""

    # Parse stringified list fields from Firestore
    post["tags"] = parse_string_list(post.get("tags", []))
    post["category"] = post.get("category", "")

    # Check if user has upvoted
    if uid:
        users_upvoted = post.get("users_upvoted", [])
        post["user_vote"] = "up" if uid in users_upvoted else None
    else:
        post["user_vote"] = None

    # Check if user has saved this post
    if saved_ids is not None:
        post["is_saved"] = post.get("id") in saved_ids
    else:
        post["is_saved"] = False

    return post


@router.get("/", auth=BearerAuth())
def blog_list(request, params: Query[BlogListParams]):
    """Get blog posts list."""
    uid = request.auth

    try:
        posts = db.get_blogs(status='published')
    except Exception:
        posts = []

    # Extract unique categories and tags from all posts before filtering
    # Parse stringified list fields from Firestore (e.g. "['Reviews', 'Strategy']")
    all_categories = sorted(set(
        cat
        for p in posts
        for cat in parse_string_list(p.get("category", ""))
        if cat
    ))
    all_tags = sorted(set(
        tag
        for p in posts
        for tag in parse_string_list(p.get("tags", []))
        if tag
    ))

    # Get user saved post IDs (always fetch to populate is_saved)
    saved_ids = set()
    try:
        saved_ids = set(db.get_user_saved_post_ids(uid))
    except Exception:
        pass

    # Filter
    if params.search:
        q = params.search.lower()
        posts = [p for p in posts if q in p.get("title", "").lower()]

    if params.category:
        posts = [
            p for p in posts
            if params.category in parse_string_list(p.get("category", ""))
        ]

    if params.tag:
        tag_lower = params.tag.lower()
        posts = [
            p for p in posts
            if any(tag_lower in t.lower() for t in parse_string_list(p.get("tags", [])))
        ]

    if params.saved:
        posts = [p for p in posts if p.get("id") in saved_ids]

    # Normalize posts
    posts = [normalize_post(p, uid, saved_ids) for p in posts]

    # Paginate
    total = len(posts)
    start = (params.page - 1) * params.page_size
    end = start + params.page_size

    return {
        "posts": posts[start:end],
        "total": total,
        "page": params.page,
        "has_next": end < total,
        "categories": all_categories,
        "tags": all_tags,
    }


@router.get("/{slug}/", auth=BearerAuth())
def blog_detail(request, slug: str):
    """Get blog post detail with comments."""
    uid = request.auth
    try:
        post = db.get_blog_by_slug(slug)
        if not post:
            return JsonResponse({"error": "Post not found"}, status=404)

        # Get saved IDs
        saved_ids = set()
        try:
            saved_ids = set(db.get_user_saved_post_ids(uid))
        except Exception:
            pass

        # Normalize fields
        post = normalize_post(post, uid, saved_ids)

        # Get comments
        try:
            comments = db.get_blog_comments(post["id"])
            post["comments"] = comments
        except Exception:
            post["comments"] = []

        return post
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/{slug}/vote/", auth=BearerAuth())
def vote_post(request, slug: str):
    uid = request.auth
    try:
        body = json.loads(request.body)
        vote_type = body.get("vote_type", "")
        post = db.get_blog_by_slug(slug)
        if not post:
            return JsonResponse({"error": "Post not found"}, status=404)

        post_id = post["id"]

        if vote_type in ("up", "upvote"):
            # Check if already voted
            existing = db.get_user_vote_on_blog(uid, post_id)
            if existing == "upvote":
                # Toggle off - remove vote
                db.remove_user_vote_on_blog(uid, post_id)
            else:
                # Add upvote
                db.add_user_vote_on_blog(uid, post_id, "upvote")
        elif vote_type in ("down", "downvote"):
            # Remove upvote if exists
            existing = db.get_user_vote_on_blog(uid, post_id)
            if existing == "upvote":
                db.remove_user_vote_on_blog(uid, post_id)

        # Return updated counts
        updated_post = db.get_blog_by_slug(slug)
        return {
            "success": True,
            "upvotes": updated_post.get("upvote_count", 0) or 0,
            "downvotes": updated_post.get("downvote_count", 0) or 0,
            "user_vote": "up" if uid in updated_post.get("users_upvoted", []) else None,
        }
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/{slug}/comment/", auth=BearerAuth())
def add_comment(request, slug: str):
    uid = request.auth
    try:
        body = json.loads(request.body)
        content = body.get("content")
        if not content:
            return JsonResponse({"error": "Content required"}, status=400)
        post = db.get_blog_by_slug(slug)
        if not post:
            return JsonResponse({"error": "Post not found"}, status=404)
        db.add_blog_comment(uid, post["id"], content)
        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/{slug}/save/", auth=BearerAuth())
def save_post(request, slug: str):
    uid = request.auth
    try:
        post = db.get_blog_by_slug(slug)
        if not post:
            return JsonResponse({"error": "Post not found"}, status=404)
        db.save_post_for_user(uid, post["id"])
        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.delete("/{slug}/save/", auth=BearerAuth())
def unsave_post(request, slug: str):
    uid = request.auth
    try:
        post = db.get_blog_by_slug(slug)
        if not post:
            return JsonResponse({"error": "Post not found"}, status=404)
        db.unsave_post_for_user(uid, post["id"])
        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
