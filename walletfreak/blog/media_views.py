from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from core.services import db

@login_required
def media_library(request):
    """Media asset library (editors only)"""
    uid = request.session.get('uid')
    if not uid or not db.can_manage_blogs(uid):
        return HttpResponseForbidden("You don't have permission to access media library")
    
    # Get all media assets
    assets = db.list_media_assets(limit=100)
    
    return render(request, 'blog/media_library.html', {
        'assets': assets,
        'is_editor': True
    })

@login_required
@require_POST
def upload_media(request):
    """Upload a media file (editors only)"""
    uid = request.session.get('uid')
    if not uid or not db.can_manage_blogs(uid):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
    
    file_obj = request.FILES['file']
    
    # Validate file type
    allowed_types = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
        'video/mp4', 'video/webm', 'video/quicktime'
    ]
    
    if file_obj.content_type not in allowed_types:
        return JsonResponse({'success': False, 'error': 'Unsupported file type'}, status=400)
    
    # Validate file size (max 50MB)
    if file_obj.size > 50 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'File too large (max 50MB)'}, status=400)
    
    try:
        # Upload to Google Cloud Storage
        asset = db.upload_media_asset(
            file_obj=file_obj,
            filename=file_obj.name,
            content_type=file_obj.content_type,
            uploaded_by_uid=uid
        )
        
        return JsonResponse({
            'success': True,
            'asset': {
                'id': asset['id'],
                'url': asset['url'],
                'filename': asset['filename'],
                'content_type': asset['content_type']
            }
        })
    except Exception as e:
        print(f"Upload error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def delete_media(request, asset_id):
    """Delete a media asset (editors only)"""
    uid = request.session.get('uid')
    if not uid or not db.can_manage_blogs(uid):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        success = db.delete_media_asset(asset_id)
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Asset not found'}, status=404)
    except Exception as e:
        print(f"Delete error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
