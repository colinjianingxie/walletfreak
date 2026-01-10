/**
 * Manage Wallet Modal & Desktop Logic
 */

function openManageWalletModal(view = 'stack') {
    const modal = document.getElementById('manage-wallet-modal');
    modal.style.display = 'flex';

    // Disable body scrolling when modal is open
    document.body.style.overflow = 'hidden';

    // Check if mobile
    if (window.innerWidth <= 768) {
        // Hide desktop content (CSS will handle most of this)
        const contentStack = document.getElementById('content-stack');
        const contentAdd = document.getElementById('content-add');
        const modalSidebar = document.querySelector('.modal-sidebar');

        if (contentStack) contentStack.style.display = 'none';
        if (contentAdd) contentAdd.style.display = 'none';
        if (modalSidebar) modalSidebar.style.display = 'none';

        // Reset mobile screens
        const mobileScreens = ['mobile-my-stack-screen', 'mobile-add-new-screen', 'mobile-card-detail-screen'];
        mobileScreens.forEach(screenId => {
            const screen = document.getElementById(screenId);
            if (screen) {
                screen.classList.remove('active');
                screen.style.display = 'none';
            }
        });

        // Show the requested mobile view
        if (view === 'stack') {
            showMobileMyStackScreen();
        } else {
            showMobileAddNewScreen();
        }
    } else {
        // Desktop view
        switchTab(view);
    }
}

function closeManageWalletModal() {
    document.getElementById('manage-wallet-modal').style.display = 'none';

    // Re-enable body scrolling when modal is closed
    document.body.style.overflow = '';

    // Reset preview (desktop)
    if (typeof resetCardPreview === 'function') resetCardPreview();

    // Reset mobile screens
    const mobileScreens = ['mobile-my-stack-screen', 'mobile-add-new-screen', 'mobile-card-detail-screen'];
    mobileScreens.forEach(screenId => {
        const screen = document.getElementById(screenId);
        if (screen) {
            screen.classList.remove('active');
            screen.style.display = 'none';
        }
    });

    // Reset desktop content visibility (let CSS handle the rest)
    const contentStack = document.getElementById('content-stack');
    const contentAdd = document.getElementById('content-add');
    const modalSidebar = document.querySelector('.modal-sidebar');

    if (contentStack) contentStack.style.display = '';
    if (contentAdd) contentAdd.style.display = '';
    if (modalSidebar) modalSidebar.style.display = '';
}

function switchTab(view) {
    // Check if mobile
    if (window.innerWidth <= 768) {
        if (view === 'stack') {
            showMobileMyStackScreen();
        } else {
            showMobileAddNewScreen();
        }
        return;
    }

    // Desktop behavior
    // Update Sidebar/Tabs
    document.querySelectorAll('.modal-sidebar-item').forEach(el => el.classList.remove('active'));
    document.getElementById('tab-' + view).classList.add('active');

    // Update Content
    document.getElementById('content-stack').style.display = 'none';
    document.getElementById('content-add').style.display = 'none';

    if (view === 'stack') {
        document.getElementById('content-stack').style.display = 'flex';
    } else {
        document.getElementById('content-add').style.display = 'block';

        // Restore state
        const searchInput = document.getElementById('card-search-input');
        if (searchInput && typeof currentDesktopSearch !== 'undefined') {
            searchInput.value = currentDesktopSearch;
        }

        // Re-apply filter and search
        if (typeof currentDesktopFilter !== 'undefined') {
            if (currentDesktopFilter !== 'All' || currentDesktopSearch) {
                // If we have a filter or search, apply it
                if (currentDesktopFilter !== 'All') {
                    filterCards(currentDesktopFilter, false); // false to not clear search
                } else {
                    // specific case: just search, filter is All
                    // trigger search event manually or just call a combined filter function
                    // simplified: just re-run the search handler logic
                    filterCards('All', false);
                }
            } else {
                renderCardResults(globalAvailableCards);
            }
        }
    }
}
