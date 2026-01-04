/**
 * Dashboard Core UI Logic
 */

function updateWalletUI() {
    // 1. Render My Stack in Modal (Mobile & Desktop)
    if (typeof renderWalletStack === 'function') {
        renderWalletStack();
    }

    // 2. Update Counts
    const count = walletCards.length;
    document.querySelectorAll('.modal-sidebar .modal-sidebar-item span[style*="background: #E2E8F0"]').forEach(el => el.textContent = count);
    document.querySelectorAll('#mobile-my-stack-tab div div:last-child').forEach(el => el.textContent = count);

    // Update Dropdown Count
    document.querySelectorAll('.user-dropdown-badge').forEach(el => el.textContent = count);

    // 3. Update Available Cards (Global) for Search
    // Filter allCardsData to exclude cards currently in wallet
    if (typeof allCardsData !== 'undefined') {
        const walletCardIds = new Set(walletCards.map(c => c.card_id || c.id));
        availableCards = allCardsData.filter(card => !walletCardIds.has(card.id));

        // Refresh the search list if it's visible
        // We use applyMobileFilters() as it handles the rendering and existing filters
        if (typeof applyMobileFilters === 'function') {
            applyMobileFilters();
        }
    }

    // 4. Update Main Dashboard (Partial DOM update)
    if (typeof renderMainDashboardStack === 'function') {
        renderMainDashboardStack();
    }

    // Check if card count changed -> trigger refresh to load new benefit cards from server
    // We use a global variable to track previous state
    if (typeof lastWalletCardCount === 'undefined') {
        window.lastWalletCardCount = count;
        // Initial load often doesn't need refresh (rendered by server), 
        // OR it does if we rely on client side triggers.
        // Assuming server render is fresh on page load.
    } else if (window.lastWalletCardCount !== count) {
        window.lastWalletCardCount = count;
        if (typeof refreshDashboardBenefits === 'function') {
            refreshDashboardBenefits();
        }
    }

    // 5. Update Chase 5/24 Status
    if (typeof updateChase524UI === 'function') updateChase524UI();

    // 6. Update Total Value Extracted & YTD Rewards
    if (typeof updateYtdRewardsUI === 'function') updateYtdRewardsUI();
    if (typeof updateCreditsUsedUI === 'function') updateCreditsUsedUI();

    // 7. Update Total Annual Fees
    if (typeof updateTotalAnnualFeeUI === 'function') updateTotalAnnualFeeUI();

    // 8. Update Net Performance
    if (typeof updateNetPerformanceUI === 'function') updateNetPerformanceUI();
}

// Helper function to get active cards count dynamically
function getActiveCardsCount() {
    // Try to get the count from the desktop sidebar first (most reliable)
    const desktopCountElement = document.querySelector('.modal-sidebar .modal-sidebar-item span[style*="background: #E2E8F0"]');
    if (desktopCountElement) {
        return desktopCountElement.textContent.trim();
    }

    // Fallback: try to get from the mobile My Stack screen if it exists
    const mobileMyStackTab = document.querySelector('#mobile-my-stack-tab div div:last-child');
    if (mobileMyStackTab) {
        return mobileMyStackTab.textContent.trim();
    }

    // Final fallback: count active card elements in the DOM
    const activeCardElements = document.querySelectorAll('[data-card-id]');
    return activeCardElements.length.toString();
}
