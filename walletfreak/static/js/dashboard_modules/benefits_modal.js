/**
 * Benefits Modal Logic & State
 */

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
    document.body.classList.add('modal-open');
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
    document.body.classList.remove('modal-open');
    currentBenefitData = {};
    currentBenefitPeriods = [];
}

function updateProgress(used, total) {
    const percentage = Math.min(100, Math.max(0, (used / total) * 100));
    document.getElementById('benefit-circular-progress').style.setProperty('--progress', percentage + '%');
}

// Global listener for dynamic input, needs to check if element exists (as modal is static usually, but good practice)
document.addEventListener('input', (e) => {
    if (e.target && e.target.id === 'benefit-amount-input') {
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
    }
});
