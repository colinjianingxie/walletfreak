from django.shortcuts import render
from django.http import Http404
from core.services import db

def blog_list(request):
    """Display list of published blogs"""
    blogs = db.get_blogs(status='published')
    return render(request, 'blog/blog_list.html', {'blogs': blogs})

def blog_detail(request, slug):
    """Display a single blog post"""
    blog = db.get_blog_by_slug(slug)
    if not blog:
        raise Http404("Post not found")
    
    # Only show published blogs to public
    if blog.get('status') != 'published':
        raise Http404("Post not found")
    
    return render(request, 'blog/blog_detail.html', {'blog': blog})
