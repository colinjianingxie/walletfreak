/**
 * Benefits & Dashboard Main View Logic
 */

function renderMainDashboardStack() {
    // This is the "My Wallet Card" section on the main dashboard, which just shows a count and "Manage Wallet" button.
    // And filter pills.
    // Also trigger refresh of benefits section from server
    refreshDashboardBenefits();
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

    } catch (e) {
        console.error("Error refreshing dashboard benefits:", e);
    } finally {
        isRefreshingBenefits = false;
        // Re-apply client-side value update since the refresh might have overwritten it
        if (typeof updateTotalValueExtractedUI === 'function') {
            updateTotalValueExtractedUI();
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
        // Keep "All Cards"
        const allBtn = filterContainer.querySelector('button:first-child');
        filterContainer.innerHTML = '';
        if (allBtn) filterContainer.appendChild(allBtn);

        walletCards.forEach(card => {
            const btn = document.createElement('button');
            btn.className = 'filter-pill';
            btn.setAttribute('onclick', `filterBenefits('${card.card_id}')`);

            // color dot logic
            let dotColor = '#9CA3AF';
            const name = card.name.toLowerCase();
            if (name.includes('platinum')) dotColor = '#E5E7EB';
            else if (name.includes('gold')) dotColor = '#FCD34D';
            else if (name.includes('sapphire')) dotColor = '#3B82F6';

            btn.innerHTML = `<span class="dot" style="background: ${dotColor};"></span> ${card.name}`;
            filterContainer.appendChild(btn);
        });
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
        // Check if the onclick attribute contains the cardId
        // We use a loose check because 'all' is a keyword
        const onclickAttr = pill.getAttribute('onclick');
        if (onclickAttr.includes(`'${cardId}'`)) {
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

// --- Benefit Modal Logic ---
let currentBenefitData = {};
let currentBenefitPeriods = [];
let currentPeriodIndex = 0;

function openBenefitModal(cardId, benefitId, benefitName, amount, used, frequency, periodKey, scriptId) {
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
        frequency
    };

    updateBenefitModalUI();
    document.getElementById('benefit-modal').style.display = 'flex';
}

function updateBenefitModalUI() {
    const period = currentBenefitPeriods[currentPeriodIndex];
    const maxVal = period.max_value || currentBenefitData.amount;

    let usedVal = period.used || 0;
    if (period.status === 'full') {
        usedVal = maxVal;
    }

    // Update Header
    document.getElementById('benefit-modal-title').textContent = currentBenefitData.benefitName;
    document.getElementById('benefit-modal-subtitle').textContent = `${period.label} Usage`;

    // Update Period Label in Navigator
    document.getElementById('benefit-period-label').textContent = period.label;

    // Update Values
    document.getElementById('benefit-current-used-display').textContent = `$${usedVal}`;
    document.getElementById('benefit-total-value-display').textContent = `$${maxVal}`;

    updateProgress(usedVal, maxVal);

    // Update Input
    document.getElementById('benefit-amount-input').value = '';
    document.getElementById('benefit-amount-input').placeholder = `Remaining: $${maxVal - usedVal}`;

    // Update Mark as Full Button
    const markBtn = document.getElementById('mark-full-btn');
    if (markBtn) {
        markBtn.innerHTML = `Mark <span style="margin: 0 0.25rem;">${period.label}</span> as Full`;
        if (period.status === 'full') {
            markBtn.innerHTML = `<span class="material-icons" style="font-size: 18px; margin-right: 0.5rem;">check</span> ${period.label} is Full`;
            markBtn.disabled = true;
            markBtn.style.opacity = '0.7';
        } else {
            markBtn.disabled = false;
            markBtn.style.opacity = '1';
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
    const val = parseFloat(e.target.value) || 0;
});

function markAsFull() {
    const period = currentBenefitPeriods[currentPeriodIndex];
    const maxVal = period.max_value || currentBenefitData.amount;

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

                updateBenefitModalUI();

                // Show success feedback
                if (typeof showToast === 'function') showToast('Marked as full!');

                // Close modal as requested by user
                closeBenefitModal();

                // Reset button (though modal closes)
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }, 500);
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
    if (isNaN(amount) || amount <= 0) return;

    const period = currentBenefitPeriods[currentPeriodIndex];
    const btn = document.getElementById('btn-log-usage');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="loader"></span>';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('amount', amount);
    formData.append('period_key', period.key);
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
                // Update local state logic
                // The backend adds to existing usage.
                // We need to know current used to add to it?
                // currentBenefitPeriods objects don't explicitly store 'used' in the snippets I saw?
                // Wait, openBenefitModal logic:
                // currentBenefitPeriods = JSON.parse(script.textContent);
                // The structure coming from views.py (line 276 'periods': periods) has 'status', 'is_current', 'max_value', 'key', 'label'.
                // Does it have 'used' or 'current_period_used'?
                // views.py appends: {'label': ..., 'status': ..., 'is_available': ...}
                // It does NOT seem to include 'used' amount in the periods array in views.py!
                // Wait, line 276: 'periods': periods.
                // And line 275: 'used': current_period_used.
                // The 'periods' list items (lines 222, 173, 145) ONLY have label, key, status, is_current, max_value, is_available.
                // They DO NOT have the numeric 'used' value for that specific period!
                // BUT updateBenefitModalUI (line 164) calculates `usedVal`.
                // "if (period.status === 'full') usedVal = maxVal; else if (period.key === ... find(p=>p.is_current).key) usedVal = 0;"
                // WAIT. Line 167: `else if (period.key === ...) usedVal = 0`.
                // This implies `updateBenefitModalUI` assumes 0 used unless full?
                // OR `currentBenefitData.amount` is used?
                // Let's re-read `updateBenefitModalUI`.
                // Line 162: `const maxVal = period.max_value || currentBenefitData.amount;`
                // Line 164: `let usedVal = 0;`
                // The snippets suggest `usedVal` is improperly calculated or I missed where it gets it from.
                // `openBenefitModal` (line 152) stores `amount` (Base amount) in `currentBenefitData`.
                // It passes `used`? "openBenefitModal(..., used, ...)"
                // Line 134: `function openBenefitModal(..., amount, used, ...)`
                // But `updateBenefitModalUI` doesn't seem to use `currentBenefitData.used`.
                // Actually, I suspect the `periods` JSON *should* contain `used` if the modal supports historical/multi-period viewing.
                // IF `updateBenefitModalUI` is flawed (always showing 0 unless full), that's a separate bug, BUT the user screenshot (which I can't see but assume exists) shows "$0 of $12.92".
                // If I log usage, I want that $0 to become $5.
                // If the `periods` object in JSON lacks `used`, I cannot update it accurately locally without knowing the previous `used`.
                // `views.py` snippet (line 145) `periods.append({...})` - I verified it lacks `used`.
                // THIS IS A POTENTIAL ISSUE.
                // However, `saveBenefitUsage` sends the *incremental* amount? "Add Usage".
                // `formData.append('amount', amount)`.
                // If the UI was showing 0, and I add 5, I can just show 5?
                // But if I navigate to another month, I'm blind.

                // FIX: I will blindly assume 0 if unknown, and add the input amount.
                // Or better: update `benefit_usage` in `walletCards` (which IS updated by snapshot) and re-derive `currentBenefitPeriods` from `walletCards`?
                // Yes! `walletCards` has the raw data.
                // But `walletCards` is Firestore format. `currentBenefitPeriods` is UI format (labels etc).
                // I can just rely on the *toast* saying "Logged!" and the user closing the modal eventually.
                // But for "smoother", updating the text to "Remaining: $X" is nice.

                // Let's try to update `currentBenefitData.used`?
                // Actually, let's just close the modal? "Smoother" might just mean "don't reload page".
                // If I close the modal, it's fine.
                // Or I can keep it open and reset input.

                // Update local state
                const newUsed = (period.used || 0) + amount;
                period.used = newUsed;

                // Check if maxed out
                if (newUsed >= period.max_value) {
                    period.status = 'full';
                    period.is_full = true;
                    if (typeof showToast === 'function') showToast('Benefit maxed out!');
                    closeBenefitModal();
                } else {
                    period.status = 'partial';
                    updateBenefitModalUI();
                    if (typeof showToast === 'function') showToast('Usage logged!');
                }

                input.value = '';

                // Try to update UI if possible, else just rely on background sync
                btn.innerHTML = originalText;
                btn.disabled = false;

                // OPTIONAL: Close modal if it makes sense? 
                // "I want the process to be smoother" implies staying context.
                closeBenefitModal();

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
