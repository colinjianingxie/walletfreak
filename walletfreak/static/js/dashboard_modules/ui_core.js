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
    updateChase524UI();

    // 6. Update Total Value Extracted & YTD Rewards
    updateYtdRewardsUI();
    updateCreditsUsedUI();

    // 7. Update Total Annual Fees
    updateTotalAnnualFeeUI();

    // 8. Update Net Performance
    updateNetPerformanceUI();
}

function updateNetPerformanceUI() {
    const display = document.getElementById('net-performance-val');
    const pill = document.getElementById('net-performance-badge');
    if (!display || !pill) return;

    // 1. Calculate Total Value (Credits Only) using shared helper
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

    displayElement.innerHTML = `$${parts[0]}<span style="font-size: 1.25rem; font-weight: 500; opacity: 0.5;">.${parts[1]}</span>`;
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
            let isAvailable = false;
            // Available if: anniversary year < current year (all months up to current)
            // OR (same year AND month >= anniversary_month AND month <= current_month)
            if (annYear < currentYear) {
                isAvailable = m <= currentMonth;
            } else if (annYear === currentYear) {
                isAvailable = (m >= annMonth && m <= currentMonth);
            }

            if (isAvailable) {
                const pKey = `${currentYear}_${m.toString().padStart(2, '0')}`;
                // Use override if exists and not null/undefined
                const pVal = (periodValues[pKey] !== undefined) ? parseFloat(periodValues[pKey]) : defaultMonthlyVal;
                available += pVal;
            }
        }

    } else if (lowerFreq.includes('quarterly')) {
        const defaultQVal = val / 4;
        const currentQ = Math.floor((currentMonth - 1) / 3) + 1;
        const annQ = Math.floor((annMonth - 1) / 3) + 1;

        for (let q = 1; q <= 4; q++) {
            let isAvailable = false;
            if (annYear < currentYear) {
                isAvailable = q <= currentQ;
            } else if (annYear === currentYear) {
                isAvailable = (q >= annQ && q <= currentQ);
            }

            if (isAvailable) {
                const pKey = `${currentYear}_Q${q}`;
                const pVal = (periodValues[pKey] !== undefined) ? parseFloat(periodValues[pKey]) : defaultQVal;
                available += pVal;
            }
        }

    } else if (lowerFreq.includes('semi-annually')) {
        const defaultHVal = val / 2;

        // H1 check
        let h1Available = false;
        if (annYear < currentYear) {
            h1Available = currentMonth >= 1; // Always available if year passed? logic says m <= current
        } else if (annYear === currentYear) {
            // Available if ann in H1 and we are past start
            h1Available = (annMonth <= 6 && currentMonth >= 1);
        }
        // Only count if H1 is current or passed
        if (h1Available && currentMonth >= 1) {
            const pKey = `${currentYear}_H1`;
            const pVal = (periodValues[pKey] !== undefined) ? parseFloat(periodValues[pKey]) : defaultHVal;
            available += pVal;
        }

        // H2 check
        let h2Available = false;
        if (annYear < currentYear) {
            h2Available = currentMonth >= 7;
        } else if (annYear === currentYear) {
            // (ann<=6 and curr>=7) OR (ann>=7 and curr >= ann)
            h2Available = (annMonth <= 6 && currentMonth >= 7) || (annMonth >= 7 && currentMonth >= annMonth);
        }
        if (h2Available) {
            const pKey = `${currentYear}_H2`;
            const pVal = (periodValues[pKey] !== undefined) ? parseFloat(periodValues[pKey]) : defaultHVal;
            available += pVal;
        }

    } else {
        // Annual / Ongoing - assume full value available if card is active
        // Check for yearly override?
        const pKey = `${currentYear}`;
        const pVal = (periodValues[pKey] !== undefined) ? parseFloat(periodValues[pKey]) : val;
        available = pVal;
    }

    return available;
}

function updateChase524UI() {
    const badge = document.getElementById('chase-524-badge');
    if (!badge) return;

    // Calculate count based on walletCards
    // Rule: Count cards opened in last 24 months
    const now = new Date();
    const cutoffDate = new Date();
    cutoffDate.setFullYear(now.getFullYear() - 2);

    let count = 0;
    // Collect all valid dates for eligibility calculation
    let cardDates = [];

    if (typeof walletCards !== 'undefined' && Array.isArray(walletCards)) {
        walletCards.forEach(card => {
            if (card.anniversary_date) {
                const annDate = new Date(card.anniversary_date);
                // Adjust to local time if needed, but date string usually implies UTC or local 
                // Given "YYYY-MM-DD", new Date("YYYY-MM-DD") is usually UTC. 
                // But let's stick to existing logic for consistency first.
                // However, to be precise on "Date", usage of timezone might matter.
                // For simplified logic, we treat it as is.

                // Existing logic check
                if (!isNaN(annDate)) {
                    // Fix timezone offset issue for pure dates if necessary, 
                    // but assuming existing logic is acceptable for count:
                    if (annDate >= cutoffDate) {
                        count++;
                    }
                    cardDates.push(annDate);
                }
            }
        });
    }

    const eligible = count < 5;

    // Update Badge
    badge.title = `Chase 5/24 Status: ${count} cards in 24 months`;
    if (eligible) {
        badge.style.background = '#DCFCE7';
        badge.style.color = '#16A34A';
        badge.innerHTML = '<span class="material-icons" style="font-size: 10px; vertical-align: middle;">check_circle</span> CHASE ELIGIBLE (' + count + '/24)';
    } else {
        badge.style.background = '#FEE2E2';
        badge.style.color = '#DC2626';
        badge.innerHTML = '<span class="material-icons" style="font-size: 10px; vertical-align: middle;">error</span> CHASE INELIGIBLE (' + count + '/24)';
    }

    // Update Modal Content (if open or for next open)
    const modalCount = document.getElementById('chase-524-modal-count');
    const modalStatus = document.getElementById('chase-524-modal-status');
    const modalEligibilityDate = document.getElementById('chase-524-eligibility-date');

    if (modalCount) {
        modalCount.textContent = `${count}/24`;
        modalCount.style.color = eligible ? '#16A34A' : '#DC2626';
    }

    if (modalStatus) {
        modalStatus.textContent = eligible ? 'You are eligible for Chase cards!' : 'You are likely ineligible for new Chase cards.';
    }

    // Calculate and display eligibility date if ineligible
    if (modalEligibilityDate) {
        if (!eligible && cardDates.length >= 5) {
            // Sort dates descending (newest first)
            cardDates.sort((a, b) => b - a);

            // The card that needs to "fall off" is the 5th newest card (index 4)
            const fifthNewestDate = cardDates[4];

            // Eligibility date is 24 months after that date
            const eligibilityDate = new Date(fifthNewestDate);
            eligibilityDate.setFullYear(eligibilityDate.getFullYear() + 2);
            // Add 1 day to be safely "after" 24 months
            eligibilityDate.setDate(eligibilityDate.getDate() + 1);

            const options = { year: 'numeric', month: 'short', day: 'numeric' };
            const dateStr = eligibilityDate.toLocaleDateString('en-US', options);

            modalEligibilityDate.textContent = `(You will be eligible on ${dateStr})`;
            modalEligibilityDate.style.display = 'block';
        } else {
            modalEligibilityDate.textContent = '';
            modalEligibilityDate.style.display = 'none';
        }
    }
}

async function updatePersonalityUI(slug, score) {
    const badgeSection = document.getElementById('personality-badge-section');
    if (!badgeSection) return;

    if (!slug) {
        // Fallback or "Add more cards" state
        badgeSection.innerHTML = `
            <span style="color: #94A3B8; font-size: 0.875rem; font-style: italic;">
                <span class="material-icons" style="font-size: 14px; vertical-align: middle; margin-right: 4px;">info</span>
                Add at least 2 cards to discover your freak
            </span>
        `;
        return;
    }

    try {
        // Fetch personality details for the name
        // We could cache this, but it changes rarely
        const pDoc = await db.collection('personalities').doc(slug).get();
        let name = slug;
        if (pDoc.exists) {
            name = pDoc.data().name;
        } else if (slug === 'student-starter') {
            name = "Student Starter"; // Fallback if doc missing
        }

        const html = `
            <a href="/personalities/${slug}/" style="text-decoration: none;">
                <span
                    style="background: #E0F2FE; color: #0284C7; font-size: 0.7rem; font-weight: 700; padding: 0.25rem 0.75rem; border-radius: 4px; letter-spacing: 0.05em; text-transform: uppercase; cursor: pointer; transition: all 0.2s;"
                    onmouseover="this.style.background='#BAE6FD'"
                    onmouseout="this.style.background='#E0F2FE'">
                    <span class="material-icons" style="font-size: 10px; vertical-align: middle;">psychology</span>
                    ${name}
                </span>
            </a>
        `;

        badgeSection.innerHTML = html;

        // Also update dropdown if present
        const dropdownTagline = document.querySelector('.user-dropdown-tagline');
        if (dropdownTagline) {
            let icon = 'auto_awesome'; // default
            if (pDoc.exists && pDoc.data().icon) {
                icon = pDoc.data().icon;
            }

            dropdownTagline.innerHTML = `
                <span class="material-icons" style="font-size: 14px;">${icon}</span>
                ${name}
            `;
        }

    } catch (e) {
        console.error("Error updating personality UI:", e);
    }
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
