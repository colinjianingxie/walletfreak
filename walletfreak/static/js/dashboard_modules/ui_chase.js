/**
 * UI Chase 5/24 Status Logic
 */

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
