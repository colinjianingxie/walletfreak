# Blog Management System Guide

## Overview
A complete blog management system has been implemented with editor permissions, allowing designated users to create, edit, and publish blog posts.

## Features Implemented

### 1. User Permissions
- **`is_super_staff`**: Full admin access (existing)
- **`is_editor`**: Can create, edit, and publish blog posts (new)
- Both permissions can be toggled in the admin user management interface

### 2. Blog Model
Located in `walletfreak/blog/models.py`

**Fields:**
- `title`: Blog post title
- `slug`: URL-friendly slug (auto-generated from title)
- `content`: Full blog content (supports HTML/Markdown)
- `excerpt`: Short description for previews
- `author_uid`: Firebase UID of the author
- `author_name`: Display name of the author
- `status`: Draft, Published, or Archived
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `published_at`: Publication timestamp (auto-set when published)
- `featured_image`: URL for featured image
- `tags`: Comma-separated tags

### 3. Admin Panel Features

#### Blog List (`/custom-admin/blogs/`)
- View all blog posts with filtering by status (Draft, Published, Archived)
- Quick publish button for draft posts
- Edit and delete actions
- Shows author, creation date, and publication date

#### Create Blog (`/custom-admin/blogs/create/`)
- Rich form for creating new blog posts
- Auto-generates slug from title
- Set status (draft/published/archived)
- Add featured image and tags

#### Edit Blog (`/custom-admin/blogs/<id>/edit/`)
- Edit existing blog posts
- Update slug if title changes
- Change status and publish posts

### 4. Public Blog Pages

#### Blog List (`/blog/`)
- Displays all published blog posts
- Featured post with large card
- Recent posts in sidebar
- Responsive design

#### Blog Detail (`/blog/<slug>/`)
- Full blog post view
- Only shows published posts to public

### 5. Front Page Integration
The landing page (`/`) now displays the 3 most recent published blog posts in a dedicated section with:
- Featured images
- Author and publication date
- Excerpt or truncated content
- "View All Articles" button

## URL Structure

### Admin URLs (require editor or super_staff permission)
- `/custom-admin/blogs/` - List all blogs
- `/custom-admin/blogs/create/` - Create new blog
- `/custom-admin/blogs/<id>/edit/` - Edit blog
- `/custom-admin/blogs/<id>/delete/` - Delete blog
- `/custom-admin/blogs/<id>/publish/` - Quick publish

### Public URLs
- `/blog/` - Public blog list (published only)
- `/blog/<slug>/` - Individual blog post

### User Management
- `/custom-admin/users/` - Manage user permissions
- `/custom-admin/users/<uid>/toggle-editor/` - Toggle editor permission

## Firestore Structure

### Users Collection
```json
{
  "users": {
    "<uid>": {
      "name": "User Name",
      "email": "user@example.com",
      "is_super_staff": false,
      "is_editor": true
    }
  }
}
```

### Blogs Collection
```json
{
  "blogs": {
    "<blog_id>": {
      "title": "Blog Title",
      "slug": "blog-title",
      "content": "Full content...",
      "excerpt": "Short description",
      "author_uid": "firebase_uid",
      "author_name": "Author Name",
      "status": "published",
      "featured_image": "https://...",
      "tags": "credit cards, rewards",
      "created_at": "timestamp",
      "updated_at": "timestamp",
      "published_at": "timestamp"
    }
  }
}
```

## How to Use

### Granting Editor Permission
1. Log in as super_staff admin
2. Navigate to `/custom-admin/users/`
3. Find the user you want to make an editor
4. Check the "Editor" checkbox
5. Permission is saved automatically

### Creating a Blog Post
1. Log in as editor or super_staff
2. Navigate to `/custom-admin/blogs/`
3. Click "Create New Blog"
4. Fill in the form:
   - Title (required)
   - Content (required)
   - Excerpt (optional but recommended)
   - Featured Image URL (optional)
   - Tags (optional)
   - Status (Draft/Published/Archived)
5. Click "Create Blog Post"

### Publishing a Draft
1. Go to `/custom-admin/blogs/`
2. Find the draft post
3. Click "Publish" button for quick publish, or
4. Click "Edit" and change status to "Published"

### Filtering Blogs
1. Go to `/custom-admin/blogs/`
2. Use the status dropdown to filter by:
   - All
   - Draft
   - Published
   - Archived
3. Click "Filter" button

## Security
- Only users with `is_editor=true` or `is_super_staff=true` can access blog management
- Public can only view published blogs
- Draft and archived blogs are hidden from public view
- Permission checks are enforced at the view level

## Database Migrations
Run these commands to set up the blog database:
```bash
cd walletfreak
python manage.py makemigrations blog
python manage.py migrate
```

## Notes
- Slugs are auto-generated from titles but can be updated
- Changing a title will update the slug (with duplicate checking)
- Published date is automatically set when status changes to "published"
- The system supports both Firestore (for production) and Django ORM (for the Blog model)