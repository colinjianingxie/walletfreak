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
        const walletCardIds = new Set(walletCards.map(c => c.card_id));
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
    const totalUsed = calculateCreditsUsed();
    console.log("Net Performance Calc - Total Used (Credits Only):", totalUsed);

    // 2. Calculate Total Fees
    let totalFees = 0;
    if (typeof walletCards !== 'undefined' && Array.isArray(walletCards)) {
        walletCards.forEach(userCard => {
            if (typeof allCardsData !== 'undefined') {
                const staticCard = allCardsData.find(c => c.id === userCard.card_id);
                if (staticCard && staticCard.annual_fee) {
                    totalFees += parseFloat(staticCard.annual_fee);
                }
            }
        });
    }

    const net = totalUsed - totalFees;
    console.log("Net Performance Calc - Net:", net);

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
                const staticCard = allCardsData.find(c => c.id === userCard.card_id);
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
                                    const staticCard = allCardsData.find(c => c.id === card.card_id);
                                    if (staticCard && staticCard.benefits) {
                                        // Find benefit index from key "benefit_X"
                                        const benefitKey = Object.keys(card.benefit_usage).find(k => card.benefit_usage[k] === benefit);
                                        if (benefitKey) {
                                            const benefitIndex = parseInt(benefitKey.split('_')[1]);
                                            const staticBenefit = staticCard.benefits[benefitIndex];

                                            // Strict check and LOGGING
                                            if (staticBenefit) {
                                                const type = staticBenefit.benefit_type;
                                                const val = parseFloat(staticBenefit.dollar_value);
                                                const name = staticBenefit.description || staticBenefit.name || 'Unnamed';

                                                // MATCH PY: benefit_type == 'Credit' AND dollar_value > 0
                                                if (type === 'Credit' && val > 0) {
                                                    console.log(`[+] Adding Credit: ${name} (Type: ${type}, Val: ${val}) - Amount: ${data.used}`);
                                                    totalUsed += (data.used || 0);
                                                } else {
                                                    console.log(`[-] Skipping ${name} (Type: ${type}, Val: ${val})`);
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
    // YTD Rewards is essentially static potential from the server for now,
    // but if we were to calculate it client side it would be sum of all benefit potentials.
    // For now, let's just leave the server value or strictly implement if needed.
    // Since this value shouldn't change based on usage (it's potential), we arguably don't need to update it client-side.
    // However if the user *Adds* a card, we should.

    const displayElement = document.getElementById('ytd-rewards-display');
    if (!displayElement) return;

    let totalPotential = 0;

    if (typeof walletCards !== 'undefined' && Array.isArray(walletCards)) {
        walletCards.forEach(userCard => {
            if (typeof allCardsData !== 'undefined') {
                const staticCard = allCardsData.find(c => c.id === userCard.card_id);
                if (staticCard && staticCard.benefits) {
                    staticCard.benefits.forEach(b => {
                        // Sum ALL benefits potential (as per user request)
                        // logic mirrors views.py: total_potential_value sums all valid benefits
                        if (b.dollar_value && b.benefit_type !== 'Protection' && b.benefit_type !== 'Bonus') {
                            totalPotential += parseFloat(b.dollar_value);
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

function updateChase524UI() {
    const badge = document.getElementById('chase-524-badge');
    if (!badge) return;

    // Calculate count based on walletCards
    // Rule: Count cards opened in last 24 months
    const now = new Date();
    const cutoffDate = new Date();
    cutoffDate.setFullYear(now.getFullYear() - 2);

    let count = 0;

    if (typeof walletCards !== 'undefined' && Array.isArray(walletCards)) {
        walletCards.forEach(card => {
            if (card.anniversary_date) {
                const annDate = new Date(card.anniversary_date);
                if (!isNaN(annDate) && annDate >= cutoffDate) {
                    count++;
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

    if (modalCount) {
        modalCount.textContent = `${count}/24`;
        modalCount.style.color = eligible ? '#16A34A' : '#DC2626';
    }

    if (modalStatus) {
        modalStatus.textContent = eligible ? 'You are eligible for Chase cards!' : 'You are likely ineligible for new Chase cards.';
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
