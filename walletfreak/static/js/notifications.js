document.addEventListener('DOMContentLoaded', function () {
    const bellBtn = document.querySelector('#notification-bell-btn');
    const popup = document.querySelector('#notification-popup');
    const listContainer = document.querySelector('#notification-list');
    const unreadBadge = document.querySelector('#notification-badge');

    let notifications = [];

    // Toggle Popup
    if (bellBtn) {
        bellBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            togglePopup();
        });
    }

    // Close on outside click
    document.addEventListener('click', (e) => {
        if (popup && popup.classList.contains('open') && !popup.contains(e.target) && !bellBtn.contains(e.target)) {
            popup.classList.remove('open');
        }
    });

    function togglePopup() {
        if (popup.classList.contains('open')) {
            popup.classList.remove('open');
        } else {
            popup.classList.add('open');
            fetchNotifications(); // Refresh on open
        }
    }

    // Fetch Notifications
    function fetchNotifications() {
        fetch('/notifications/api/get/')
            .then(res => res.json())
            .then(data => {
                notifications = data.notifications;
                renderNotifications();
                updateBadge(data.unread_count);
            })
            .catch(err => console.error('Error fetching notifications:', err));
    }

    // Initial Fetch (for badge)
    fetchNotifications();
    // Poll every 60 seconds
    setInterval(fetchNotifications, 60000);

    function renderNotifications() {
        if (!listContainer) return;

        listContainer.innerHTML = '';

        if (notifications.length === 0) {
            listContainer.innerHTML = `
                <div style="padding: 2rem; text-align: center; color: #94a3b8; font-size: 0.875rem;">
                    No new notifications
                </div>
            `;
            return;
        }

        notifications.forEach(notif => {
            const item = document.createElement('a');
            item.className = `notification-item ${notif.is_read ? '' : 'unread'}`;
            if (notif.link) item.href = notif.link;

            // Icon selection
            let iconSvg = '';
            let iconClass = 'icon-system';

            if (notif.type === 'blog') {
                iconClass = 'icon-blog';
                iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 7v14"></path><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"></path></svg>`;
            } else if (notif.type === 'update') {
                iconClass = 'icon-update';
                iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21v-6"></path><path d="M12 21V3"></path><path d="M19 21V9"></path></svg>`;
            } else {
                iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
            }

            const newIndicator = !notif.is_read ? `
                <div class="new-indicator">
                    <span class="new-dot"></span>
                    <span class="new-text">New update</span>
                </div>
            ` : '';

            item.innerHTML = `
                <div class="notification-content-wrapper">
                    <div class="notification-icon-box ${iconClass}">
                        ${iconSvg}
                    </div>
                    <div class="notification-text-content">
                        <div class="notification-header-row">
                            <p class="notification-subject">${notif.title}</p>
                            <span class="notification-time">${notif.created_at.split(' ')[0]}</span>
                        <p class="notification-subject">${notif.title}</p>
                        <span class="notification-time">${notif.created_at.split(' ')[0]}</span>
                        </div>
                        <p class="notification-body">${notif.message}</p>
                        ${newIndicator}
                    </div>
                </div>
            `;

            // Mark read on click
            item.addEventListener('click', (e) => {
                // If it's a link, we still want to mark read, but maybe let the default action happen?
                // Usually fetch is async so it's fine.
                if (!notif.is_read) {
                    markRead(notif.id, notif.source);
                }
            });

            listContainer.appendChild(item);
        });
    }

    function updateBadge(count) {
        if (!unreadBadge) return;
        if (count > 0) {
            unreadBadge.style.display = 'block';
        } else {
            unreadBadge.style.display = 'none';
        }
    }

    window.markAllRead = function () {
        const csrfToken = getCookie('csrftoken');
        fetch('/notifications/api/mark-read/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ all: true })
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    notifications.forEach(n => n.is_read = true);
                    renderNotifications();
                    updateBadge(0);
                }
            });
    }

    function markRead(id, source = 'personal') {
        const csrfToken = getCookie('csrftoken');
        fetch('/notifications/api/mark-read/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ id: id, source: source })
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
