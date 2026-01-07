from django.db import models
from django.utils import timezone
from django.db.models import Count, Q


class Blog(models.Model):
    """
    Blog model for storing blog posts in the database.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True, help_text="Short description for preview")
    
    # Author information (Firebase UID)
    author_uid = models.CharField(max_length=128)
    author_name = models.CharField(max_length=200)
    
    # Status and publishing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # SEO and metadata
    featured_image = models.URLField(blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")

    # New Metadata Fields
    READ_TIME_CHOICES = [
        ('short', 'Short (< 3m)'),
        ('medium', 'Medium (3-7m)'),
        ('long', 'Long (7m+)'),
        ('video', 'Video Only'),
    ]
    EXPERIENCE_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('whale', 'Whale'),
    ]

    read_time = models.CharField(max_length=20, choices=READ_TIME_CHOICES, default='medium')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default='intermediate')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
    
    def __str__(self):
        return self.title
    
    def to_dict(self):
        """Convert to dictionary for Firestore sync"""
        data = {
            'title': self.title,
            'slug': self.slug,
            'content': self.content,
            'excerpt': self.excerpt,
            'author_uid': self.author_uid,
            'author_name': self.author_name,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'published_at': self.published_at,
            'featured_image': self.featured_image,
            'tags': self.tags,
            'read_time': self.read_time,
            'experience_level': self.experience_level,
        }
        return data
    
    def save(self, *args, **kwargs):
        # Auto-set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def tag_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    @property
    def upvote_count(self):
        """Return the number of upvotes"""
        return self.votes.filter(vote_type='upvote').count()
    
    @property
    def downvote_count(self):
        """Return the number of downvotes"""
        return self.votes.filter(vote_type='downvote').count()
    
    @property
    def total_score(self):
        """Return the total score (upvotes - downvotes)"""
        return self.upvote_count - self.downvote_count
    
    def get_user_vote(self, user_uid):
        """Get the vote type for a specific user"""
        try:
            vote = self.votes.get(user_uid=user_uid)
            return vote.vote_type
        except Vote.DoesNotExist:
            return None


class Vote(models.Model):
    """
    Model to track individual user votes on blog posts.
    """
    VOTE_CHOICES = [
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    ]
    
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='votes')
    user_uid = models.CharField(max_length=128)  # Firebase UID
    vote_type = models.CharField(max_length=10, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('blog', 'user_uid')  # One vote per user per blog
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_uid} - {self.vote_type} on {self.blog.title}"
