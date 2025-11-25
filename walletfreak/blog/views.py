from django.shortcuts import render, Http404
from core.services import db

def blog_list(request):
    blogs = db.get_blogs()
    return render(request, 'blog/blog_list.html', {'blogs': blogs})

def blog_detail(request, slug):
    blog = db.get_blog_by_slug(slug)
    if not blog:
        raise Http404("Post not found")
    return render(request, 'blog/blog_detail.html', {'blog': blog})
