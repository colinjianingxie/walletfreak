from ninja import Router, Query
from django.http import JsonResponse
from core.services import db
from api.auth_middleware import BearerAuth
from ninja import Schema
from typing import Optional
import json

router = Router(tags=["blog"])


class BlogListParams(Schema):
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None
    category: Optional[str] = None
    saved: bool = False


@router.get("/", auth=BearerAuth())
def blog_list(request, params: Query[BlogListParams]):
    """Get blog posts list."""
    uid = request.auth

    try:
        posts = db.get_blog_posts()
    except Exception:
        posts = []

    # Get user saved posts
    saved_ids = set()
    if params.saved:
        try:
            saved = db.get_user_saved_posts(uid)
            saved_ids = {s.get("post_id") for s in saved}
        except Exception:
            pass

    # Filter
    if params.search:
        q = params.search.lower()
        posts = [p for p in posts if q in p.get("title", "").lower()]

    if params.category:
        posts = [p for p in posts if p.get("category") == params.category]

    if params.saved:
        posts = [p for p in posts if p.get("id") in saved_ids]

    # Paginate
    total = len(posts)
    start = (params.page - 1) * params.page_size
    end = start + params.page_size

    return {
        "posts": posts[start:end],
        "total": total,
        "page": params.page,
        "has_next": end < total,
    }


@router.get("/{slug}/", auth=BearerAuth())
def blog_detail(request, slug: str):
    """Get blog post detail with comments."""
    uid = request.auth
    try:
        post = db.get_blog_post_by_slug(slug)
        if not post:
            return JsonResponse({"error": "Post not found"}, status=404)

        comments = db.get_blog_comments(post["id"])
        user_vote = db.get_user_blog_vote(uid, post["id"])

        post["comments"] = comments
        post["user_vote"] = user_vote
        return post
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/{slug}/vote/", auth=BearerAuth())
def vote_post(request, slug: str):
    uid = request.auth
    try:
        body = json.loads(request.body)
        vote_type = body.get("vote_type")
        post = db.get_blog_post_by_slug(slug)
        if not post:
            return JsonResponse({"error": "Post not found"}, status=404)
        db.vote_on_blog(uid, post["id"], vote_type)
        return {"success": True}
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
        post = db.get_blog_post_by_slug(slug)
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
        post = db.get_blog_post_by_slug(slug)
        if not post:
            return JsonResponse({"error": "Post not found"}, status=404)
        db.save_blog_post(uid, post["id"])
        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.delete("/{slug}/save/", auth=BearerAuth())
def unsave_post(request, slug: str):
    uid = request.auth
    try:
        post = db.get_blog_post_by_slug(slug)
        if not post:
            return JsonResponse({"error": "Post not found"}, status=404)
        db.unsave_blog_post(uid, post["id"])
        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
