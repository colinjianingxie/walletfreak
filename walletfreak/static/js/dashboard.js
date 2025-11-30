/**
 * Dashboard JavaScript
 * Handles card filtering and interactions
 */

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

    // Handle empty states if needed
    // You might want to show a "No benefits found" message if visibleCount === 0
}

// Initialize tooltips or other interactive elements if needed
document.addEventListener('DOMContentLoaded', function () {
    // Any initialization logic
});
