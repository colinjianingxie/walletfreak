/**
 * UI Stats Logic (YTD, Credits, Fees, Net Perf)
 */

function updateNetPerformanceUI() {
    const display = document.getElementById('net-performance-val');
    const pill = document.getElementById('net-performance-badge');
    if (!display || !pill) return;

    // 1. Calculate Total Value (Credits Only) using shared helper
    const totalUsed = calculateCreditsUsed();

    // 2. Calculate Total Fees
    let totalFees = 0;
    if (typeof walletCards !== 'undefined' && Array.isArray(walletCards)) {
        walletCards.forEach(userCard => {
            if (typeof allCardsData !== 'undefined') {
                // Fix: Subcollection uses 'id' as slug, legacy uses 'card_id'
                const slug = userCard.card_id || userCard.id;
                const staticCard = allCardsData.find(c => c.id === slug);
                if (staticCard && staticCard.annual_fee) {
                    totalFees += parseFloat(staticCard.annual_fee);
                }
            }
        });
    }

    const net = totalUsed - totalFees;

    // Update Display
    display.textContent = `$${net.toFixed(2)}`;
    display.style.color = net < 0 ? '#F97316' : '#10B981';

    // Update Pill
    if (net < 0) {
        pill.textContent = "Underutilizing";
        pill.style.background = "rgba(249, 115, 22, 0.2)";
        pill.style.color = "#F97316";
    } else {
        pill.textContent = "Profit Mode";
        pill.style.background = "rgba(16, 185, 129, 0.2)";
        pill.style.color = "#10B981";
    }
}

function updateTotalAnnualFeeUI() {
    const displayElement = document.getElementById('total-annual-fee-display');
    if (!displayElement) return;

    let totalFees = 0;

    if (typeof walletCards !== 'undefined' && Array.isArray(walletCards)) {
        walletCards.forEach(userCard => {
            // Find static card data to get the fee
            if (typeof allCardsData !== 'undefined') {
                const slug = userCard.card_id || userCard.id;
                const staticCard = allCardsData.find(c => c.id === slug);
                if (staticCard && staticCard.annual_fee) {
                    totalFees += parseFloat(staticCard.annual_fee);
                }
            }
        });
    }

    // Format like Total Value: $<Int><span class="decimals">.00</span>
    const intPart = Math.floor(totalFees).toLocaleString();
    const decimalPart = (totalFees % 1).toFixed(2).substring(1); // .XX

    displayElement.innerHTML = `$${intPart}<span style="font-size: 1.25rem; font-weight: 500; opacity: 0.5;">${decimalPart}</span>`;
}

// Helper to calculate total credits used (shared logic)
function calculateCreditsUsed() {
    const currentYear = new Date().getFullYear().toString();
    let totalUsed = 0;

    if (typeof walletCards !== 'undefined' && Array.isArray(walletCards)) {
        walletCards.forEach(card => {
            if (card.benefit_usage) {
                Object.values(card.benefit_usage).forEach(benefit => {
                    if (benefit.periods) {
                        Object.entries(benefit.periods).forEach(([key, data]) => {
                            if (key.startsWith(currentYear)) {
                                // ALWAYS verify against static data (Source of Truth) to match Backend logic
                                // Ignore benefit.benefit_type on the user object as it may be stale or incorrect
                                if (typeof allCardsData !== 'undefined') {
                                    const slug = card.card_id || card.id;
                                    const staticCard = allCardsData.find(c => c.id === slug);
                                    if (staticCard && staticCard.benefits) {
                                        // Find benefit index from key "benefit_X"
                                        const benefitKey = Object.keys(card.benefit_usage).find(k => card.benefit_usage[k] === benefit);
                                        if (benefitKey) {
                                            // Fix: Handle both 'benefit_X' and 'X' keys
                                            let benefitIndex;
                                            if (benefitKey.startsWith('benefit_')) {
                                                benefitIndex = parseInt(benefitKey.split('_')[1]);
                                            } else {
                                                benefitIndex = parseInt(benefitKey);
                                            }
                                            const staticBenefit = staticCard.benefits[benefitIndex];

                                            // Strict check and LOGGING
                                            if (staticBenefit) {
                                                const type = staticBenefit.benefit_type;
                                                const val = parseFloat(staticBenefit.dollar_value);
                                                const name = staticBenefit.description || staticBenefit.name || 'Unnamed';

                                                // MATCH PY: benefit_type == 'Credit' OR 'Perk' AND dollar_value > 0
                                                if ((type === 'Credit' || type === 'Perk') && val > 0) {

                                                    totalUsed += (data.used || 0);
                                                }

                                            }
                                        }
                                    }
                                }
                            }
                        });
                    }
                });
            }
        });
    }
    return totalUsed;
}

function updateCreditsUsedUI() {
    const displayElement = document.getElementById('credits-used-display');
    if (!displayElement) return;

    const totalUsed = calculateCreditsUsed();

    // Format: CREDITS USED: $<Val>
    displayElement.textContent = `CREDITS USED: $${totalUsed.toFixed(2)}`;
}

function updateYtdRewardsUI() {
    const displayElement = document.getElementById('ytd-rewards-display');
    if (!displayElement) return;

    let totalPotential = 0;

    if (typeof walletCards !== 'undefined' && Array.isArray(walletCards)) {
        walletCards.forEach(userCard => {
            if (typeof allCardsData !== 'undefined') {
                const slug = userCard.card_id || userCard.id;
                const staticCard = allCardsData.find(c => c.id === slug);
                if (staticCard && staticCard.benefits) {
                    staticCard.benefits.forEach((b, index) => {
                        // Filter out Protection and Bonus benefits
                        if (b.dollar_value && b.benefit_type !== 'Protection' && b.benefit_type !== 'Bonus') {
                            // Fix: Support both legacy 'benefit_X' and new 'X' index keys
                            const simpleKey = index.toString();
                            const legacyKey = `benefit_${index}`;

                            let benefitData = null;
                            if (userCard.benefit_usage) {
                                if (userCard.benefit_usage[simpleKey]) benefitData = userCard.benefit_usage[simpleKey];
                                else if (userCard.benefit_usage[legacyKey]) benefitData = userCard.benefit_usage[legacyKey];
                            }

                            let isIgnored = benefitData ? benefitData.is_ignored : false;

                            if (!isIgnored) {
                                // Calculate available potential
                                totalPotential += calculateAvailablePotential(b, userCard.anniversary_date);
                            }
                        }
                    });
                }
            }
        });
    }

    // Format using strict locale
    const formattedTotal = totalPotential.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const parts = formattedTotal.split('.');

    displayElement.innerHTML = `$${parts[0]}<span style="font-size: 1.25rem; font-weight: 500; opacity: 0.5;">${parts[1]}</span>`;
}

/**
 * Helper to calculate available potential value for a benefit based on anniversary date
 * Replicates dashboard/views.py logic
 */
function calculateAvailablePotential(benefit, anniversaryDateStr) {
    if (!benefit.dollar_value) return 0;
    const val = parseFloat(benefit.dollar_value);
    if (isNaN(val) || val <= 0) return 0;

    const frequency = benefit.time_category || 'Annually';

    // Date Logic
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1; // 1-12

    let annMonth = 1;
    let annYear = currentYear;

    if (anniversaryDateStr) {
        // Parse YYYY-MM-DD manually to avoid timezone issues
        const parts = anniversaryDateStr.split('-');
        if (parts.length === 3) {
            annYear = parseInt(parts[0]);
            annMonth = parseInt(parts[1]);
        }
    }

    let available = 0;
    const lowerFreq = frequency.toLowerCase();
    const periodValues = benefit.period_values || {};

    if (lowerFreq.includes('monthly')) {
        const defaultMonthlyVal = val / 12;
        // Check each month 1-12
        for (let m = 1; m <= 12; m++) {
            // User Request: Sum all possible credits for the whole year
            const pKey = `${currentYear}_${m.toString().padStart(2, '0')}`;
            const pVal = (periodValues[pKey] !== undefined) ? parseFloat(periodValues[pKey]) : defaultMonthlyVal;
            available += pVal;
        }

    } else if (lowerFreq.includes('quarterly')) {
        const defaultQVal = val / 4;
        for (let q = 1; q <= 4; q++) {
            const pKey = `${currentYear}_Q${q}`;
            const pVal = (periodValues[pKey] !== undefined) ? parseFloat(periodValues[pKey]) : defaultQVal;
            available += pVal;
        }

    } else if (lowerFreq.includes('semi-annually')) {
        const defaultHVal = val / 2;

        // H1
        const pKeyH1 = `${currentYear}_H1`;
        const pValH1 = (periodValues[pKeyH1] !== undefined) ? parseFloat(periodValues[pKeyH1]) : defaultHVal;
        available += pValH1;

        // H2
        const pKeyH2 = `${currentYear}_H2`;
        const pValH2 = (periodValues[pKeyH2] !== undefined) ? parseFloat(periodValues[pKeyH2]) : defaultHVal;
        available += pValH2;

    } else {
        // Annual / Ongoing - assume full value available if card is active
        const pKey = `${currentYear}`;
        const pVal = (periodValues[pKey] !== undefined) ? parseFloat(periodValues[pKey]) : val;
        available = pVal;
    }

    return available;
}
