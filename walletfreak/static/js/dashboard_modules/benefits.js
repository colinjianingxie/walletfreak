/**
 * Benefits & Dashboard Main View Logic
 */

function renderMainDashboardStack() {
    // This is the "My Wallet Card" section on the main dashboard, which just shows a count and "Manage Wallet" button.
    // And filter pills.
    // Also trigger refresh of benefits section from server
    // refreshDashboardBenefits(); // CAUSES LOOP: fetching server loader HTML overwrites client calculation
}

let isRefreshingBenefits = false;
async function refreshDashboardBenefits() {
    if (isRefreshingBenefits) return;
    isRefreshingBenefits = true;

    // CAPTURE CURRENT ACTIVE FILTER (Move to top to avoid overwrite)
    let activeFilterId = 'all';
    const currentFilterContainer = document.getElementById('card-filters');
    if (currentFilterContainer) {
        const activePill = currentFilterContainer.querySelector('.filter-pill.active');
        if (activePill) {
            activeFilterId = activePill.getAttribute('data-card-id');
        }
    }

    try {
        // Fetch the updated dashboard HTML from server
        // This is necessary because benefit calculations (dates, used amounts, eligiblity) are complex server-side logic
        const response = await fetch(window.location.href);
        if (!response.ok) throw new Error('Failed to fetch dashboard updates');
        const text = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');

        const newAnnualValue = doc.getElementById('annual-value-card');
        const currentAnnualValue = document.getElementById('annual-value-card');
        if (newAnnualValue && currentAnnualValue) {
            currentAnnualValue.innerHTML = newAnnualValue.innerHTML;
        }

        const newFilters = doc.getElementById('card-filters-container');
        const currentFilters = document.getElementById('card-filters-container');
        if (newFilters && currentFilters) {
            currentFilters.innerHTML = newFilters.innerHTML;
        }

        const newActionNeeded = doc.getElementById('action-needed-section');
        const currentActionNeeded = document.getElementById('action-needed-section');
        if (newActionNeeded && currentActionNeeded) {
            currentActionNeeded.innerHTML = newActionNeeded.innerHTML;
        }

        const newMaxedOut = doc.getElementById('maxed-out-section');
        const currentMaxedOut = document.getElementById('maxed-out-section');
        if (newMaxedOut && currentMaxedOut) {
            currentMaxedOut.innerHTML = newMaxedOut.innerHTML;
        } else if (newMaxedOut && !currentMaxedOut) {
            // If maxed out section appeared (wasn't there before), append it after action needed
            if (currentActionNeeded) {
                currentActionNeeded.parentNode.insertBefore(newMaxedOut, currentActionNeeded.nextSibling);
            }
        } else if (!newMaxedOut && currentMaxedOut) {
            // If maxed out section disappeared
            currentMaxedOut.remove();
        }

        const newIgnored = doc.getElementById('ignored-benefits-section');
        const currentIgnored = document.getElementById('ignored-benefits-section');
        if (newIgnored && currentIgnored) {
            currentIgnored.innerHTML = newIgnored.innerHTML;
        } else if (newIgnored && !currentIgnored) {
            // If ignored section appeared, append it after maxed out or action needed
            // Ideally we append to the same container
            if (currentMaxedOut) {
                currentMaxedOut.parentNode.insertBefore(newIgnored, currentMaxedOut.nextSibling);
            } else if (currentActionNeeded) {
                currentActionNeeded.parentNode.insertBefore(newIgnored, currentActionNeeded.nextSibling);
            }
        } else if (!newIgnored && currentIgnored) {
            currentIgnored.remove();
        }

    } catch (e) {
        console.error("Error refreshing dashboard benefits:", e);
    } finally {
        isRefreshingBenefits = false;
        // Re-apply client-side value update since the refresh might have overwritten it
        if (typeof updateYtdRewardsUI === 'function') {
            updateYtdRewardsUI();
        }
        if (typeof updateCreditsUsedUI === 'function') {
            updateCreditsUsedUI();
        }
        if (typeof updateTotalAnnualFeeUI === 'function') {
            updateTotalAnnualFeeUI();
        }
        if (typeof updateNetPerformanceUI === 'function') {
            updateNetPerformanceUI();
        }
    }

    // We can update the "My Stack" COUNT on the main dashboard easily.
    const stackCount = document.querySelector('.my-stack-count, div[style*="font-size: 3rem"]'); // Basic selector guess
    if (stackCount && typeof walletCards !== 'undefined') stackCount.textContent = walletCards.length;

    // RESTORE FILTER STATE AFTER SERVER REFRESH
    // The server HTML has already rendered the correct filter pills.
    // We just need to restore the active state and re-apply the filter logic.
    const filterContainer = document.getElementById('card-filters');
    if (filterContainer) {
        // Remove 'active' from all pills (server default is 'All Cards')
        const allPills = filterContainer.querySelectorAll('.filter-pill');
        allPills.forEach(pill => pill.classList.remove('active'));

        // Find the pill that matches our saved activeFilterId
        const targetPill = filterContainer.querySelector(`.filter-pill[data-card-id="${activeFilterId}"]`);
        if (targetPill) {
            targetPill.classList.add('active');
            // Apply the filter to hide/show benefit cards
            filterBenefits(activeFilterId);
        } else {
            // Fallback: activate 'All Cards' and show all
            const allCardsPill = filterContainer.querySelector('.filter-pill[data-card-id="all"]');
            if (allCardsPill) allCardsPill.classList.add('active');
            filterBenefits('all');
        }

        // Sync visibility (hide pills for cards with no benefits)
        syncFilterVisibility();
    }

    // Issues: The benefit cards themselves won't appear until refresh because they are server-rendered.
    // For now, updating the list in the modal is the primary goal. 
    // The main dashboard will be stale regarding the NEW card's benefits until refresh.
    // We can show a toast "Refresh to see new benefits".
}
