/**
 * Dashboard Utilities
 */

function showLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) loader.style.display = 'flex';
}

function hideLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) loader.style.display = 'none';
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'error' ? 'error_outline' : 'check_circle';
    toast.innerHTML = `<span class="material-icons">${icon}</span><span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(100%)';
        toast.style.transition = 'all 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Handle window resize to switch between mobile and desktop modal layouts
function handleModalResize() {
    const modal = document.getElementById('manage-wallet-modal');
    if (modal && modal.style.display === 'flex') {
        const isMobile = window.innerWidth <= 768;

        const modalSidebar = document.querySelector('.modal-sidebar');
        // Check if sidebar is currently visible to determine if we are coming from Desktop
        // We use offsetParent as a proxy for visibility (null if display:none)
        const wasDesktop = modalSidebar && modalSidebar.offsetParent !== null;

        if (isMobile) {
            // SWITCH TO MOBILE

            if (wasDesktop) {
                // We just crossed from Desktop to Mobile -> SYNC STATE
                const desktopStackTab = document.getElementById('tab-stack');
                const isDesktopStackActive = desktopStackTab && desktopStackTab.classList.contains('active');

                if (isDesktopStackActive) {
                    showMobileMyStackScreen();
                } else {
                    // Add Tab was active
                    if (typeof selectedAddCard !== 'undefined' && selectedAddCard) {
                        showMobileCardDetail(selectedAddCard);
                    } else {
                        showMobileAddNewScreen();
                    }
                }
            }

            // Apply Mobile Layout (Hide Desktop)
            const contentStack = document.getElementById('content-stack');
            const contentAdd = document.getElementById('content-add');

            if (contentStack) contentStack.style.display = 'none';
            if (contentAdd) contentAdd.style.display = 'none';
            if (modalSidebar) modalSidebar.style.display = 'none';

            // Ensure a mobile screen is shown if none (fallback)
            const mobileStack = document.getElementById('mobile-my-stack-screen');
            const mobileAdd = document.getElementById('mobile-add-new-screen');
            const mobileDetail = document.getElementById('mobile-card-detail-screen');

            const isAnyMobileVisible = (mobileStack && mobileStack.style.display !== 'none') ||
                (mobileAdd && mobileAdd.style.display !== 'none') ||
                (mobileDetail && mobileDetail.style.display !== 'none');

            if (!isAnyMobileVisible) {
                showMobileMyStackScreen(); // Default fallback
            }

        } else {
            // SWITCH TO DESKTOP

            if (!wasDesktop) {
                // We just crossed from Mobile to Desktop -> SYNC STATE
                const mobileAdd = document.getElementById('mobile-add-new-screen');
                const mobileDetail = document.getElementById('mobile-card-detail-screen');

                // Check if we were on any Add-related screen
                const isMobileAddActive = mobileAdd && mobileAdd.classList.contains('active');
                const isMobileDetailVisible = mobileDetail && mobileDetail.style.display !== 'none';

                if (isMobileAddActive || isMobileDetailVisible) {
                    switchTab('add');
                    if (typeof selectedAddCard !== 'undefined' && selectedAddCard) {
                        if (typeof selectCardForPreview === 'function') {
                            selectCardForPreview(selectedAddCard, null);
                        }
                    }
                } else {
                    // Default/Stack
                    switchTab('stack');
                }
            }

            // Apply Desktop Layout
            if (modalSidebar) modalSidebar.style.display = 'flex';

            // Hide Mobile Screens
            const mobileScreens = ['mobile-my-stack-screen', 'mobile-add-new-screen', 'mobile-card-detail-screen'];
            mobileScreens.forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    el.style.display = 'none';
                    el.classList.remove('active');
                }
            });
        }
    }
}

window.addEventListener('resize', handleModalResize);
