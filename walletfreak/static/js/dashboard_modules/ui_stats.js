/**
 * UI Stats Logic (YTD, Credits, Fees, Net Perf)
 */

/**
 * Check if an is_ignored flag is stale (set in a previous benefit period).
 * Matches the Python logic in dashboard/views/main.py and api/routers/wallet.py.
 * Returns true if the benefit should be treated as ignored, false if stale (reset).
 */
function isEffectivelyIgnored(benefitData, frequency, anniversaryDateStr) {
    if (!benefitData || !benefitData.is_ignored) return false;

    const lastUpdated = benefitData.last_updated;
    if (!lastUpdated) return false; // No timestamp → treat as not ignored

    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1;

    let annMonth = 1;
    let annYear = currentYear;
    let annDay = 1;
    if (anniversaryDateStr && anniversaryDateStr !== 'default') {
        const parts = anniversaryDateStr.split('-');
        if (parts.length >= 3) {
            annYear = parseInt(parts[0]);
            annMonth = parseInt(parts[1]);
            annDay = parseInt(parts[2]);
        }
    }

    let periodStart = null;
    const lowerFreq = (frequency || '').toLowerCase();

    if (lowerFreq.includes('monthly')) {
        periodStart = new Date(currentYear, currentMonth - 1, 1);
    } else if (lowerFreq.includes('quarterly')) {
        const currQ = Math.ceil(currentMonth / 3);
        const qStartMonth = (currQ - 1) * 3 + 1;
        periodStart = new Date(currentYear, qStartMonth - 1, 1);
    } else if (lowerFreq.includes('semi-annually')) {
        const hStartMonth = currentMonth <= 6 ? 1 : 7;
        periodStart = new Date(currentYear, hStartMonth - 1, 1);
    } else if (lowerFreq.includes('every 4 years')) {
        let annualStartYear = currentYear;
        if (annMonth) {
            const thisYearAnniv = new Date(currentYear, annMonth - 1, annDay);
            if (now < thisYearAnniv) annualStartYear = currentYear - 1;
        }
        const baseYear = annYear || 2020;
        const blockIdx = Math.floor((annualStartYear - baseYear) / 4);
        const blockStartYear = baseYear + (blockIdx * 4);
        periodStart = annMonth ? new Date(blockStartYear, annMonth - 1, annDay) : new Date(blockStartYear, 0, 1);
    } else if (lowerFreq.includes('anniversary')) {
        if (annMonth) {
            const thisYearAnniv = new Date(currentYear, annMonth - 1, annDay);
            const pStartYear = now < thisYearAnniv ? currentYear - 1 : currentYear;
            periodStart = new Date(pStartYear, annMonth - 1, annDay);
        } else {
            periodStart = new Date(currentYear, 0, 1);
        }
    } else {
        // Annual / calendar year
        periodStart = new Date(currentYear, 0, 1);
    }

    if (!periodStart) return true;

    // Convert Firestore timestamp to Date
    let lastUpdatedDate;
    if (lastUpdated.toDate) {
        lastUpdatedDate = lastUpdated.toDate(); // Firestore Timestamp
    } else if (lastUpdated instanceof Date) {
        lastUpdatedDate = lastUpdated;
    } else if (typeof lastUpdated === 'string') {
        lastUpdatedDate = new Date(lastUpdated);
    } else if (lastUpdated.seconds) {
        lastUpdatedDate = new Date(lastUpdated.seconds * 1000); // Firestore-like
    } else {
        return true; // Can't parse, keep ignored
    }

    // If last_updated is before the current period started, the ignore is stale
    return lastUpdatedDate >= periodStart;
}

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

// Helper to resolve a benefit key to its static benefit data
function resolveStaticBenefit(benefitKey, staticCard) {
    if (!staticCard || !staticCard.benefits) return null;
    // Try new system: match by benefit ID
    let staticBenefit = staticCard.benefits.find(b => b.id === benefitKey || b.benefit_id === benefitKey);
    if (staticBenefit) return staticBenefit;
    // Fallback to legacy system: match by array index
    let benefitIndex;
    if (benefitKey.startsWith('benefit_')) {
        benefitIndex = parseInt(benefitKey.split('_')[1]);
    } else {
        benefitIndex = parseInt(benefitKey);
    }
    if (!isNaN(benefitIndex) && benefitIndex >= 0 && benefitIndex < staticCard.benefits.length) {
        return staticCard.benefits[benefitIndex];
    }
    return null;
}

// Helper to calculate total credits used (shared logic)
function calculateCreditsUsed() {
    const currentYear = new Date().getFullYear().toString();
    let totalUsed = 0;

    if (typeof walletCards !== 'undefined' && Array.isArray(walletCards)) {
        walletCards.forEach(card => {
            if (!card.benefit_usage || typeof allCardsData === 'undefined') return;
            const slug = card.card_id || card.id;
            const staticCard = allCardsData.find(c => c.id === slug);
            if (!staticCard) return;

            Object.entries(card.benefit_usage).forEach(([benefitKey, benefit]) => {
                const staticBenefit = resolveStaticBenefit(benefitKey, staticCard);
                if (!staticBenefit) return;

                const type = staticBenefit.benefit_type;
                const val = parseFloat(staticBenefit.dollar_value);
                if (!((type === 'Credit' || type === 'Perk') && val > 0)) return;

                // Check is_ignored with stale-period reset
                const frequency = staticBenefit.time_category || 'Annually';
                if (isEffectivelyIgnored(benefit, frequency, card.anniversary_date)) return;

                if (benefit.periods) {
                    Object.entries(benefit.periods).forEach(([key, data]) => {
                        if (key.startsWith(currentYear)) {
                            totalUsed += (data.used || 0);
                        }
                    });
                }
            });
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
                    const EXCLUDED_TYPES = ['Protection', 'Bonus', 'Perk', 'Lounge', 'Status', 'Insurance'];
                    staticCard.benefits.forEach((b, index) => {
                        // Filter out non-trackable benefit types (must match Python backend)
                        if (b.dollar_value && !EXCLUDED_TYPES.includes(b.benefit_type)) {
                            // Match by benefit ID (new system) or index (legacy system)
                            let benefitData = null;
                            if (userCard.benefit_usage) {
                                const benefitId = b.id || b.benefit_id;

                                // Try new system: match by benefit ID
                                if (benefitId && userCard.benefit_usage[benefitId]) {
                                    benefitData = userCard.benefit_usage[benefitId];
                                } else {
                                    // Fallback to legacy system: match by index
                                    const simpleKey = index.toString();
                                    const legacyKey = `benefit_${index}`;
                                    if (userCard.benefit_usage[simpleKey]) benefitData = userCard.benefit_usage[simpleKey];
                                    else if (userCard.benefit_usage[legacyKey]) benefitData = userCard.benefit_usage[legacyKey];
                                }
                            }

                            // Check is_ignored with stale-period reset
                            const frequency = b.time_category || 'Annually';
                            if (isEffectivelyIgnored(benefitData, frequency, userCard.anniversary_date)) return;

                            // Calculate available potential
                            totalPotential += calculateAvailablePotential(b, userCard.anniversary_date);
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
