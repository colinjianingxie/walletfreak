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
    if (stackCount) stackCount.textContent = walletCards.length;

    // Creating new Filter Pills
    const filterContainer = document.getElementById('card-filters');
    if (filterContainer) {
        // Collect all card IDs present in benefit cards currently on page
        const benefitCards = document.querySelectorAll('.benefit-card');
        const presentCardIds = new Set();
        benefitCards.forEach(card => {
            const cid = card.getAttribute('data-card-id');
            if (cid) presentCardIds.add(cid);
        });

        filterContainer.innerHTML = '';

        // Always add 'All' button
        const allBtn = document.createElement('button');
        allBtn.className = 'filter-pill active';
        allBtn.setAttribute('onclick', "filterBenefits('all')");
        allBtn.setAttribute('data-card-id', 'all');
        allBtn.innerText = 'All Cards';
        filterContainer.appendChild(allBtn);

        // Add buttons only for cards that have visible benefits
        walletCards.forEach(card => {
            if (presentCardIds.has(card.card_id)) {
                const btn = document.createElement('button');
                btn.className = 'filter-pill';
                btn.setAttribute('onclick', `filterBenefits('${card.card_id}')`);
                btn.setAttribute('data-card-id', card.card_id);

                // Construct the inner HTML to match the server-side template
                const innerHTML = `
                    <div style="position: relative; width: 32px; height: 20px; border-radius: 4px; overflow: hidden; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                        <img src="${card.image_url || '/static/img/card_placeholder.png'}" 
                             style="width: 100%; height: 100%; object-fit: cover;"
                             alt="${card.name}">
                    </div>
                    <span class="filter-pill-text" style="font-size: 0.875rem; font-weight: 700;">${card.name}</span>
                `;
                btn.innerHTML = innerHTML;

                // Add classes for styling
                btn.style.display = 'flex';
                btn.style.alignItems = 'center';
                btn.style.gap = '0.5rem';
                btn.style.transition = 'transform 0.2s';
                btn.onmouseover = function () { this.style.transform = 'scale(1.05)'; };
                btn.onmouseout = function () { this.style.transform = 'scale(1)'; };

                filterContainer.appendChild(btn);
            }
        });

        // Sync visibility final check (redundant but safe)
        syncFilterVisibility();
    }

    // Issues: The benefit cards themselves won't appear until refresh because they are server-rendered.
    // For now, updating the list in the modal is the primary goal. 
    // The main dashboard will be stale regarding the NEW card's benefits until refresh.
    // We can show a toast "Refresh to see new benefits".
}

function filterBenefits(cardId) {
    // Update active pill state
    const pills = document.querySelectorAll('.filter-pill');
    pills.forEach(pill => {
        // Use robust data attribute check
        const pillCardId = pill.getAttribute('data-card-id');
        if (pillCardId === cardId) {
            pill.classList.add('active');
        } else {
            pill.classList.remove('active');
        }
    });

    // Filter benefits
    const benefitCards = document.querySelectorAll('.benefit-card');
    let visibleCount = 0;

    benefitCards.forEach(card => {
        const cardDataId = card.getAttribute('data-card-id');

        if (cardId === 'all' || cardDataId === cardId) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
}

/**
 * Hides filter pills for cards that are NOT present in the current view (i.e. have no active benefits displayed)
 */
function syncFilterVisibility() {
    const pills = document.querySelectorAll('.filter-pill');
    const benefitCards = document.querySelectorAll('.benefit-card');

    // Collect all card IDs present in benefit cards
    const presentCardIds = new Set();
    benefitCards.forEach(card => {
        const cid = card.getAttribute('data-card-id');
        if (cid) presentCardIds.add(cid);
    });

    pills.forEach(pill => {
        const pillId = pill.getAttribute('data-card-id');
        if (pillId === 'all') return; // Always show 'All'

        if (presentCardIds.has(pillId)) {
            pill.style.display = 'inline-flex'; // or whatever the default flex display is
        } else {
            pill.style.display = 'none';
        }
    });
}

// Ensure we run this on load too
document.addEventListener('DOMContentLoaded', () => {
    syncFilterVisibility();
});

// --- Benefit Modal Logic ---
let currentBenefitData = {};
let currentBenefitPeriods = [];
let currentPeriodIndex = 0;

function openBenefitModal(cardId, benefitId, benefitName, amount, used, frequency, periodKey, scriptId, isIgnored, ytdUsed) {
    // Parse periods from json_script
    const script = document.getElementById(scriptId);
    if (script) {
        currentBenefitPeriods = JSON.parse(script.textContent);
    } else {
        // Fallback
        currentBenefitPeriods = [{ key: periodKey, label: 'Current', max_value: amount, status: 'unknown' }];
    }

    // Find index
    currentPeriodIndex = currentBenefitPeriods.findIndex(p => p.key === periodKey);
    if (currentPeriodIndex === -1) currentPeriodIndex = 0;

    currentBenefitData = {
        cardId,
        benefitId,
        benefitName,
        amount, // Base amount
        frequency,
        isIgnored: !!isIgnored,
        ytdUsed: ytdUsed || 0,
        scriptId: scriptId
    };

    updateBenefitModalUI();
    document.getElementById('benefit-modal').style.display = 'flex';
}

function updateBenefitModalUI() {
    const period = currentBenefitPeriods[currentPeriodIndex];
    // Fix: Allow 0 as valid value (don't falback to amount if 0)
    const maxVal = (period.max_value !== undefined && period.max_value !== null) ? period.max_value : currentBenefitData.amount;

    let usedVal = period.used || 0;
    if (period.status === 'full') {
        usedVal = maxVal;
    }

    // Helper: Round up to 2 decimal places
    const fmt = (num) => {
        if (num === undefined || num === null) return '0';
        return (Math.ceil(num * 100) / 100);
    };

    // Check if period is disabled (max value 0)
    const isDisabled = (maxVal === 0);

    // Update Header
    document.getElementById('benefit-modal-title').textContent = currentBenefitData.benefitName;
    document.getElementById('benefit-modal-subtitle').textContent = `${period.label} Usage`;

    // Update Period Label in Navigator
    document.getElementById('benefit-period-label').textContent = period.label;

    // Update Values
    document.getElementById('benefit-current-used-display').textContent = `$${fmt(usedVal)}`;

    if (isDisabled) {
        document.getElementById('benefit-total-value-display').innerHTML = '<span style="color: #9CA3AF; font-size: 0.8em; font-weight: 600;">DISABLED</span>';
    } else {
        document.getElementById('benefit-total-value-display').textContent = `$${fmt(maxVal)}`;
    }

    updateProgress(usedVal, maxVal);

    // Update Input
    const input = document.getElementById('benefit-amount-input');

    input.value = '';
    const remainingForPeriod = Math.max(0, maxVal - usedVal);

    if (isDisabled) {
        input.disabled = true;
        input.placeholder = "Benefit Disabled";
    } else {
        input.disabled = false;
        input.placeholder = `Remaining: $${fmt(remainingForPeriod)}`;
    }

    // Update Mark as Full / Reset Button
    const markBtn = document.getElementById('mark-full-btn');
    const resetBtn = document.getElementById('reset-benefit-btn');
    const markFullDateBtn = document.getElementById('mark-full-date-btn');

    if (markBtn && resetBtn) {
        // Reset base styles
        markBtn.style.background = 'white';
        markBtn.style.borderColor = '#E5E7EB';
        markBtn.style.color = '#1F2937';

        if (isDisabled) {
            markBtn.style.display = 'none';
            resetBtn.style.display = 'none';
            if (markFullDateBtn) markFullDateBtn.style.display = 'none';
        } else if (period.status === 'full') {
            // Show Reset Button
            markBtn.style.display = 'none';
            resetBtn.style.display = 'flex';
        } else {
            // Show Mark as Full Button
            resetBtn.style.display = 'none';
            markBtn.style.display = 'flex';

            markBtn.innerHTML = `Mark <span style="margin: 0 0.25rem;">${period.label}</span> as Full ($${fmt(remainingForPeriod)})`;
            markBtn.disabled = false;
            markBtn.style.opacity = '1';
        }
    }

    // Logic for "Mark Full To Date"
    if (markFullDateBtn) {
        let totalToMark = 0;
        let countToMark = 0;

        // Hide if Ignored
        if (currentBenefitData.isIgnored) {
            markFullDateBtn.style.display = 'none';
        } else {
            // Find the "current" period index
            let realCurrentIndex = currentBenefitPeriods.findIndex(p => p.is_current);

            if (realCurrentIndex !== -1) {
                // Iterate from 0 to realCurrentIndex
                for (let i = 0; i <= realCurrentIndex; i++) {
                    const p = currentBenefitPeriods[i];
                    // Check availability
                    if (p.max_value > 0 && p.is_available !== false) {
                        const pUsed = p.used || 0;

                        if (p.status !== 'full') {
                            // Calculate proper max and needed
                            const pMax = (p.max_value !== undefined) ? p.max_value : currentBenefitData.amount;
                            const needed = Math.max(0, pMax - pUsed);
                            if (needed > 0) {
                                totalToMark += needed;
                                countToMark++;
                            }
                        }
                    }
                }
            }

            // Show only if there is amount to mark AND it's different (greater) than the current single period mark amount
            // Or if we are viewing a past period?
            // "if the Mark as Full and Mark Full To Date values are the same, do not show the Mark Full to Date"
            // Usually Mark Full To Date is >= Mark Current.
            // If they are equal (within small float margin), hide it.
            if (countToMark > 0 && Math.abs(totalToMark - remainingForPeriod) > 0.01) {
                markFullDateBtn.style.display = 'flex';
                document.getElementById('mark-full-date-amount').textContent = `($${fmt(totalToMark)})`;
            } else {
                markFullDateBtn.style.display = 'none';
            }
        }
    }

    // Display Reset Date if available
    const resetDateEl = document.getElementById('benefit-reset-date-display');
    if (resetDateEl) {
        if (period.reset_date) {
            resetDateEl.textContent = `Resets: ${period.reset_date}`;
            resetDateEl.style.display = 'block';
        } else {
            resetDateEl.style.display = 'none';
        }
    }

    // Update Ignore Button & Input State
    const ignoreBtn = document.getElementById('benefit-ignore-btn');
    const logBtn = document.getElementById('btn-log-usage');

    if (isDisabled && logBtn) {
        logBtn.disabled = true;
        logBtn.style.opacity = '0.5';
    }

    if (ignoreBtn) {
        if (currentBenefitData.isIgnored) {
            // IGNORED STATE
            ignoreBtn.textContent = 'Unignore Benefit';
            ignoreBtn.style.color = '#3B82F6';
            ignoreBtn.style.display = 'inline-block';
            ignoreBtn.disabled = false;

            // Disable inputs
            if (input) {
                input.disabled = true;
                input.placeholder = 'Ignored';
            }
            if (logBtn) {
                logBtn.disabled = true;
                logBtn.style.opacity = '0.5';
            }
            if (resetBtn) {
                resetBtn.disabled = true;
                resetBtn.style.opacity = '0.5';
            }
            if (markBtn) {
                markBtn.disabled = true;
                markBtn.style.opacity = '0.5';
            }

        } else {
            // ACTIVE STATE
            if (input && !isDisabled) input.disabled = false;

            if (logBtn) {
                logBtn.disabled = true;
                logBtn.style.opacity = '0.5';
            }

            // ALLOW Ignore even if usage exists (User Request)
            ignoreBtn.textContent = 'Ignore Benefit';
            ignoreBtn.style.color = '#94A3B8';
            ignoreBtn.style.display = 'inline-block';
            ignoreBtn.disabled = false;
        }
    }
}

function navigatePeriod(direction) {
    const newIndex = currentPeriodIndex + direction;
    if (newIndex >= 0 && newIndex < currentBenefitPeriods.length) {
        currentPeriodIndex = newIndex;
        updateBenefitModalUI();
    }
}

function closeBenefitModal() {
    document.getElementById('benefit-modal').style.display = 'none';
    currentBenefitData = {};
    currentBenefitPeriods = [];
}

function updateProgress(used, total) {
    const percentage = Math.min(100, Math.max(0, (used / total) * 100));
    document.getElementById('benefit-circular-progress').style.setProperty('--progress', percentage + '%');
}

document.getElementById('benefit-amount-input')?.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    const logBtn = document.getElementById('btn-log-usage');
    if (logBtn) {
        if (!isNaN(val) && val >= 0) {
            logBtn.disabled = false;
            logBtn.style.opacity = '1';
        } else {
            logBtn.disabled = true;
            logBtn.style.opacity = '0.5';
        }
    }
});

function markAsFull() {
    const period = currentBenefitPeriods[currentPeriodIndex];
    // Fix: Allow 0 as valid value (don't falback to amount if 0)
    const maxVal = (period.max_value !== undefined && period.max_value !== null) ? period.max_value : currentBenefitData.amount;

    const btn = document.getElementById('mark-full-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="loader"></span> Marking...';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('amount', maxVal);
    formData.append('period_key', period.key);
    formData.append('is_full', 'true');
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch(`/wallet/update-benefit/${currentBenefitData.cardId}/${currentBenefitData.benefitId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // success - update local state
                period.status = 'full';
                period.is_full = true; // ensure consistency
                // Assume full means used all
                // Note: The backend logic should set 'used' to max. We simulate it here.
                // We don't have 'used' property on period object usually (it's in benefit_usage map), 
                // but updateBenefitModalUI uses a check: if status=='full' usedVal=maxVal.

                // Update ytdUsed to reflect that benefit has been used
                currentBenefitData.ytdUsed = (currentBenefitData.ytdUsed || 0) + maxVal;

                updateBenefitModalUI();

                // Persist update to DOM script tag
                if (currentBenefitData.scriptId) {
                    const script = document.getElementById(currentBenefitData.scriptId);
                    if (script) {
                        script.textContent = JSON.stringify(currentBenefitPeriods);
                    }
                }

                // Show success feedback
                if (typeof showToast === 'function') showToast('Marked as full!');

                // Refresh dashboard to update top stats
                refreshDashboardBenefits();

                // Update UI to show reset button
                updateBenefitModalUI();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error marking as full: ' + error.message);
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

function saveBenefitUsage() {
    const input = document.getElementById('benefit-amount-input');
    const amount = parseFloat(input.value);
    if (isNaN(amount) || amount < 0) return;

    const period = currentBenefitPeriods[currentPeriodIndex];
    const btn = document.getElementById('btn-log-usage');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="loader"></span>';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('amount', amount);
    formData.append('period_key', period.key);
    formData.append('increment', 'false'); // user requested overwrite logic
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch(`/wallet/update-benefit/${currentBenefitData.cardId}/${currentBenefitData.benefitId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // ... (previous code)

                // Update local state - OVERWRITE logic
                const newUsed = amount; // Was: (period.used || 0) + amount;
                period.used = newUsed;

                // Update ytdUsed to reflect that benefit has been used
                currentBenefitData.ytdUsed = (currentBenefitData.ytdUsed || 0) + amount;

                // Check if maxed out
                const maxVal = (period.max_value !== undefined && period.max_value !== null) ? period.max_value : currentBenefitData.amount;
                if (newUsed >= maxVal) {
                    period.status = 'full';
                    period.is_full = true;
                    if (typeof showToast === 'function') showToast('Benefit maxed out!');
                } else {
                    period.status = 'partial';
                    if (typeof showToast === 'function') showToast('Usage logged!');
                }

                // Persist update to DOM
                if (currentBenefitData.scriptId && document.getElementById(currentBenefitData.scriptId)) {
                    document.getElementById(currentBenefitData.scriptId).textContent = JSON.stringify(currentBenefitPeriods);
                }

                // Update UI (keep modal open)
                updateBenefitModalUI();

                // Refresh dashboard to update top stats
                refreshDashboardBenefits();

                // Clear input (if modal wasn't closed)
                input.value = '';

                // Enable button (but keep disabled until new input)
                btn.innerHTML = originalText;
                btn.disabled = true;
                btn.style.opacity = '0.5';

            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error logging usage: ' + error.message);
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

function toggleIgnoreBenefit() {
    const btn = document.getElementById('benefit-ignore-btn');
    const originalText = btn.innerHTML;
    const isIgnored = currentBenefitData.isIgnored;
    const newIgnoredState = !isIgnored;

    if (newIgnoredState) {
        // Attempting to Ignore
        // Double check usage
        let hasUsage = (currentBenefitData.ytdUsed > 0);
        // Also check current period used just in case
        if ((currentBenefitPeriods[currentPeriodIndex].used || 0) > 0) hasUsage = true;

        if (hasUsage) {
            alert("Cannot ignore a benefit that has logged usage.");
            return;
        }
    }

    btn.innerHTML = '<span class="loader"></span> processing...';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('is_ignored', newIgnoredState);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch(`/wallet/toggle-ignore-benefit/${currentBenefitData.cardId}/${currentBenefitData.benefitId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
        .then(async response => {
            let data;
            try {
                data = await response.json();
            } catch (e) {
                data = null;
            }

            if (!response.ok) {
                throw new Error((data && data.error) || 'Network response was not ok (' + response.status + ')');
            }
            return data;
        })
        .then(async data => {
            if (data.success) {
                // Wait for dashboard to refresh FIRST to ensure backend sync is visualized
                await refreshDashboardBenefits();

                if (newIgnoredState) {
                    // Being Ignored -> Close Modal
                    if (typeof showToast === 'function') showToast('Benefit ignored!');
                    closeBenefitModal();
                } else {
                    // Being Unignored -> Close Modal
                    if (typeof showToast === 'function') showToast('Benefit unignored!');
                    closeBenefitModal();
                }
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error updating benefit: ' + error.message);
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

function resetBenefit() {
    const period = currentBenefitPeriods[currentPeriodIndex];
    const btn = document.getElementById('reset-benefit-btn');
    const originalText = (btn) ? btn.innerHTML : 'Reset Usage';

    if (btn) {
        btn.innerHTML = '<span class="loader"></span> Resetting...';
        btn.disabled = true;
    }



    const formData = new FormData();
    formData.append('amount', 0);
    formData.append('period_key', period.key);
    formData.append('is_full', 'false');
    formData.append('increment', 'false'); // Explicit set to 0
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch(`/wallet/update-benefit/${currentBenefitData.cardId}/${currentBenefitData.benefitId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(async data => {
            if (data.success) {
                // Update local state
                period.status = 'empty';
                period.is_full = false;
                period.used = 0;

                // Persist update to DOM
                if (currentBenefitData.scriptId && document.getElementById(currentBenefitData.scriptId)) {
                    document.getElementById(currentBenefitData.scriptId).textContent = JSON.stringify(currentBenefitPeriods);
                }

                // Refresh dashboard
                refreshDashboardBenefits();

                if (typeof showToast === 'function') showToast('Benefit usage reset!');

                updateBenefitModalUI();

                if (btn) {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
                if (btn) {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error resetting benefit: ' + error.message);
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
}

// New function for bulk update
async function markFullToDate() {
    const btn = document.getElementById('mark-full-date-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="loader"></span> Marking...';
    btn.disabled = true;

    // Identify periods to update
    const realCurrentIndex = currentBenefitPeriods.findIndex(p => p.is_current);
    if (realCurrentIndex === -1) {
        btn.innerHTML = originalText;
        btn.disabled = false;
        return;
    }

    const periodsToUpdate = [];
    let totalAdded = 0;

    for (let i = 0; i <= realCurrentIndex; i++) {
        const p = currentBenefitPeriods[i];
        if (p.max_value > 0 && p.is_available !== false && p.status !== 'full') {
            const needed = p.max_value - (p.used || 0);
            if (needed > 0) {
                periodsToUpdate.push({
                    key: p.key,
                    amount: p.max_value // target max
                });
                totalAdded += needed;
            }
        }
    }

    if (periodsToUpdate.length === 0) {
        btn.innerHTML = originalText;
        btn.disabled = false;
        return;
    }

    // Process them sequentially
    let errorCount = 0;

    const updates = periodsToUpdate.map(p => {
        const formData = new FormData();
        formData.append('amount', p.amount);
        formData.append('period_key', p.key);
        formData.append('is_full', 'true');
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

        return fetch(`/wallet/update-benefit/${currentBenefitData.cardId}/${currentBenefitData.benefitId}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        }).then(res => {
            if (!res.ok) throw new Error('Update failed');
            return res.json();
        }).then(data => {
            if (data.success) {
                // Update local model
                const period = currentBenefitPeriods.find(per => per.key === p.key);
                if (period) {
                    period.status = 'full';
                    period.is_full = true;
                }
            } else {
                throw new Error(data.error);
            }
        }).catch(err => {
            console.error(err);
            errorCount++;
        });
    });

    try {
        await Promise.all(updates);

        if (errorCount === 0) {
            if (typeof showToast === 'function') showToast('All benefits marked full!');

            // Update ytdUsed
            currentBenefitData.ytdUsed = (currentBenefitData.ytdUsed || 0) + totalAdded;

            // Persist script
            if (currentBenefitData.scriptId && document.getElementById(currentBenefitData.scriptId)) {
                document.getElementById(currentBenefitData.scriptId).textContent = JSON.stringify(currentBenefitPeriods);
            }

            // Refresh dashboard
            refreshDashboardBenefits();

            // Update Modal UI
            updateBenefitModalUI();
        } else {
            alert(`Completed with ${errorCount} errors. Please check connection.`);
            // Still try update UI
            updateBenefitModalUI();
        }

    } catch (e) {
        alert("Critical error during update.");
    } finally {
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }
}
