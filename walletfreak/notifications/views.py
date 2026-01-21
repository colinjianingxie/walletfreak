from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Notification, GlobalNotification, GlobalNotificationRead, NotificationPreference
from django.db.models import Q
import json

@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    """
    Fetch unread notifications for the user + recent global notifications.
    Merge strategy:
    1. Get personal Notifications.
    2. Get GlobalNotifications created after user joined.
    3. Filter out GlobalNotifications the user has opted out of.
    4. Calculate 'is_read' for globals by checking GlobalNotificationRead.
    5. Merge and sort.
    """
    user = request.user
    
    # 1. Personal Notifications
    personal_notifs = list(Notification.objects.filter(recipient=user).order_by('-created_at')[:20])
    
    # 2. Global Notifications (only those created after user joined)
    # Using Q object for flexibility, though simplistic filtering is sufficient here
    global_notifs_qs = GlobalNotification.objects.filter(created_at__gte=user.date_joined)
    
    # 3. Filter by Preferences
    # Get disabled types for this user
    disabled_types = NotificationPreference.objects.filter(
        user=user, 
        is_enabled=False
    ).values_list('notification_type', flat=True)
    
    if disabled_types:
        global_notifs_qs = global_notifs_qs.exclude(notification_type__in=disabled_types)
        
    global_notifs = list(global_notifs_qs.order_by('-created_at')[:20]) # Limit fetch
    
    # 4. Determine Read Status for Globals
    read_global_ids = set(GlobalNotificationRead.objects.filter(
        user=user,
        notification__in=global_notifs
    ).values_list('notification_id', flat=True))
    
    combined_data = []
    
    # Helper to format
    def format_notif(n, source, is_read_override=None):
        is_read = n.is_read if source == 'personal' else (n.id in read_global_ids)
        # Override if provided (mostly for logic clarity)
        
        return {
            'id': n.id,
            'source': source, # 'personal' or 'global'
            'title': n.title,
            'message': n.message,
            'link': n.link,
            'type': n.notification_type,
            'is_read': is_read,
            'created_at': n.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'timestamp': n.created_at.timestamp() # For sorting
        }

    for n in personal_notifs:
        combined_data.append(format_notif(n, 'personal'))
        
    for n in global_notifs:
        combined_data.append(format_notif(n, 'global'))
        
    # 5. Sort by created_at desc
    combined_data.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Slice to limit return size (e.g. top 20 total)
    combined_data = combined_data[:20]
    
    # Count unread (Approximate for performant UI, or exact?)
    # Exact unread count is tricky with merged streams without fetching all.
    # For now, we'll count unread in the fetched batch OR do a separate count query.
    # A cleaner way for the badge is to count personal unread + (total relevant globals - read globals)
    
    personal_unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
    
    total_relevant_globals = GlobalNotification.objects.filter(
        created_at__gte=user.date_joined
    ).exclude(notification_type__in=disabled_types).count()
    
    read_globals_count = GlobalNotificationRead.objects.filter(user=user).count()
    
    # This naive subtraction assumes user hasn't read globals they are now unqualified for (rare edge case)
    # and that they haven't read globals before they joined (impossible via logic).
    # However, if we expire globals, total_relevant_globals drops, but read_globals_count might stay high?
    # Better: Count unread globals directly.
    
    # Unread Globals = Globals relevant to user AND NOT IN (Read table for user)
    # This can be expensive if not careful.
    unread_globals_count = GlobalNotification.objects.filter(
        created_at__gte=user.date_joined
    ).exclude(
        notification_type__in=disabled_types
    ).exclude(
        id__in=GlobalNotificationRead.objects.filter(user=user).values('notification_id')
    ).count()
    
    total_unread = personal_unread_count + unread_globals_count

    return JsonResponse({
        'notifications': combined_data,
        'unread_count': total_unread
    })

@login_required
@require_http_methods(["POST"])
def mark_read(request):
    """
    Mark one or all notifications as read.
    Body: {'id': <id>, 'source': 'personal'|'global'} OR {'all': true}
    """
    try:
        body = json.loads(request.body)
        user = request.user
        
        if body.get('all'):
            # Mark all personal read
            Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
            
            # Mark all relevant globals read
            # Find all unread globals for this user
            disabled_types = NotificationPreference.objects.filter(user=user, is_enabled=False).values_list('notification_type', flat=True)
            
            unread_globals = GlobalNotification.objects.filter(
                created_at__gte=user.date_joined
            ).exclude(
                notification_type__in=disabled_types
            ).exclude(
                id__in=GlobalNotificationRead.objects.filter(user=user).values('notification_id')
            )
            
            # Bulk create reads
            new_reads = [
                GlobalNotificationRead(user=user, notification=g) 
                for g in unread_globals
            ]
            GlobalNotificationRead.objects.bulk_create(new_reads)
            
            return JsonResponse({'status': 'success', 'message': 'All marked as read'})
        
        notif_id = body.get('id')
        source = body.get('source', 'personal') # Default to personal for backward compat if JS not updated
        
        if notif_id:
            if source == 'global':
                try:
                    g_notif = GlobalNotification.objects.get(id=notif_id)
                    # Create read record if not exists
                    GlobalNotificationRead.objects.get_or_create(user=user, notification=g_notif)
                    return JsonResponse({'status': 'success'})
                except GlobalNotification.DoesNotExist:
                     return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)
            else:
                # Personal
                try:
                    notif = Notification.objects.get(id=notif_id, recipient=user)
                    notif.is_read = True
                    notif.save()
                    return JsonResponse({'status': 'success'})
                except Notification.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)
                
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

@login_required
def history_view(request):
    """
    Render detailed history.
    Merges sources similar to get_notifications but for the full list (or paginated).
    """
    user = request.user
    
    # Fetch Personal
    personal_qs = Notification.objects.filter(recipient=user).values(
        'id', 'title', 'message', 'link', 'notification_type', 'is_read', 'created_at'
    )
    # Augment with source
    personal_list = []
    for p in personal_qs:
        p['source'] = 'personal'
        personal_list.append(p)
        
    # Fetch Global
    disabled_types = NotificationPreference.objects.filter(user=user, is_enabled=False).values_list('notification_type', flat=True)
    
    global_qs = GlobalNotification.objects.filter(
        created_at__gte=user.date_joined
    ).exclude(
        notification_type__in=disabled_types
    ).values(
        'id', 'title', 'message', 'link', 'notification_type', 'created_at'
    )
    
    # Get read entries to determine is_read
    global_read_ids = set(GlobalNotificationRead.objects.filter(user=user).values_list('notification_id', flat=True))
    
    global_list = []
    for g in global_qs:
        g['source'] = 'global'
        g['is_read'] = g['id'] in global_read_ids
        global_list.append(g)
        
    # Merge and Sort
    # Note: If lists are huge, this in-memory merge is bad. 
    # But for < 1000 items, python is plenty fast.
    
    combined = personal_list + global_list
    combined.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render(request, 'notifications/history.html', {
        'notifications': combined
    })
