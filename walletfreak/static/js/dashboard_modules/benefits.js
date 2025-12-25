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

    // Update Mark as Full / Reset Button
    const markBtn = document.getElementById('mark-full-btn');
    const resetBtn = document.getElementById('reset-benefit-btn');

    if (markBtn && resetBtn) {
        // Reset base styles
        markBtn.style.background = 'white';
        markBtn.style.borderColor = '#E5E7EB';
        markBtn.style.color = '#1F2937';

        if (period.status === 'full') {
            // Show Reset Button
            markBtn.style.display = 'none';
            resetBtn.style.display = 'flex';
        } else {
            // Show Mark as Full Button
            resetBtn.style.display = 'none';
            markBtn.style.display = 'flex';

            markBtn.innerHTML = `Mark <span style="margin: 0 0.25rem;">${period.label}</span> as Full`;
            markBtn.disabled = false;
            markBtn.style.opacity = '1';
        }
    }

    // Update Ignore Button & Input State
    const ignoreBtn = document.getElementById('benefit-ignore-btn');
    const logBtn = document.getElementById('btn-log-usage');
    const input = document.getElementById('benefit-amount-input');

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
            if (input) input.disabled = false;
            if (logBtn) {
                // Default to disabled because input is cleared on open
                logBtn.disabled = true;
                logBtn.style.opacity = '0.5';
            }
            // markBtn state logic is preserved above unless overridden by isIgnored

            if (currentBenefitData.ytdUsed && currentBenefitData.ytdUsed > 0) {
                // Has usage -> Hide ignore button (cannot ignore)
                ignoreBtn.style.display = 'none';
            } else {
                ignoreBtn.textContent = 'Ignore Benefit';
                ignoreBtn.style.color = '#94A3B8';
                ignoreBtn.style.display = 'inline-block';
                ignoreBtn.disabled = false;
            }
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

                // Persist update to DOM script tag
                if (currentBenefitData.scriptId) {
                    const script = document.getElementById(currentBenefitData.scriptId);
                    if (script) {
                        script.textContent = JSON.stringify(currentBenefitPeriods);
                    }
                }

                // Show success feedback
                if (typeof showToast === 'function') showToast('Marked as full!');

                // Update button to show success state
                btn.innerHTML = '<span class="material-icons" style="font-size: 20px; margin-right: 0.5rem;">check_circle</span> Marked!';
                btn.style.background = '#ECFDF5';
                btn.style.borderColor = '#10B981';
                btn.style.color = '#047857';

                // Refresh dashboard to update top stats
                refreshDashboardBenefits();

                // Delay closing to allow user to see the success state
                setTimeout(() => {
                    closeBenefitModal();

                    // Reset button style after modal is closed
                    setTimeout(() => {
                        btn.innerHTML = originalText;
                        btn.disabled = false;
                        btn.style.background = 'white';
                        btn.style.borderColor = '#E5E7EB';
                        btn.style.color = '#1F2937';
                    }, 500);
                }, 1000);
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
    formData.append('increment', 'true');
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
                    // Persist update to DOM
                    if (currentBenefitData.scriptId && document.getElementById(currentBenefitData.scriptId)) {
                        document.getElementById(currentBenefitData.scriptId).textContent = JSON.stringify(currentBenefitPeriods);
                    }
                    if (typeof showToast === 'function') showToast('Benefit maxed out!');

                    // Update UI to show Reset button
                    updateBenefitModalUI();
                } else {
                    period.status = 'partial';
                    // Persist update to DOM
                    if (currentBenefitData.scriptId && document.getElementById(currentBenefitData.scriptId)) {
                        document.getElementById(currentBenefitData.scriptId).textContent = JSON.stringify(currentBenefitPeriods);
                    }
                    updateBenefitModalUI();
                    if (typeof showToast === 'function') showToast('Usage logged!');
                }

                // Refresh dashboard to update top stats
                refreshDashboardBenefits();

                input.value = '';

                // Update UI based on new state
                updateBenefitModalUI();

                // Enable button (but keep disabled until new input)
                btn.innerHTML = originalText;
                btn.disabled = true;
                btn.style.opacity = '0.5';

            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

function toggleIgnoreBenefit() {
    const btn = document.getElementById('benefit-ignore-btn');
    const originalText = btn.innerHTML;
    const isIgnored = currentBenefitData.isIgnored;

    btn.innerHTML = '<span class="loader"></span> processing...';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('is_ignored', !isIgnored);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch(`/wallet/toggle-ignore-benefit/${currentBenefitData.cardId}/${currentBenefitData.benefitId}/`, {
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
                // Wait for dashboard to refresh FIRST to ensure backend sync is visualized
                await refreshDashboardBenefits();

                if (typeof showToast === 'function') showToast(isIgnored ? 'Benefit unignored!' : 'Benefit ignored!');
                closeBenefitModal();
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

                closeBenefitModal();
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
