/**
 * Benefits Filtering Logic
 */

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
