const selectedCards = new Set();

function toggleCardSelection(element, slotIndex) {
    const cardId = element.dataset.id;
    const selectionIndicator = element.querySelector('.selection-indicator');
    const statusIcon = element.querySelector('.status-icon');
    const cardVisual = element.querySelector('.credit-card');

    if (element.classList.contains('selected')) {
        element.classList.remove('selected');
        statusIcon.textContent = 'add';
        selectionIndicator.style.background = 'rgba(255,255,255,0.2)';
        selectionIndicator.style.borderColor = 'rgba(255,255,255,0.4)';
        cardVisual.style.boxShadow = '';
        cardVisual.style.transform = '';
        selectedCards.delete(cardId);
    } else {
        element.classList.add('selected');
        statusIcon.textContent = 'check';
        selectionIndicator.style.background = '#3b82f6';
        selectionIndicator.style.borderColor = '#3b82f6';
        cardVisual.style.boxShadow = '0 0 0 4px rgba(59, 130, 246, 0.4), 0 10px 25px rgba(0,0,0,0.2)';
        cardVisual.style.transform = 'translateY(-4px)';
        selectedCards.add(cardId);
    }

    calculateMetrics();
}

function calculateMetrics() {
    let totalFees = 0;
    let creditValue = 0;
    let pointsValue = 0;

    selectedCards.forEach(cardId => {
        const card = allCardsData[cardId];
        if (!card) return;

        // 1. Annual Fee
        totalFees += (card.annual_fee || 0);

        // 2. Credit Value & Points Value
        if (card.benefits && Array.isArray(card.benefits)) {
            card.benefits.forEach(benefit => {
                const numericVal = parseFloat(benefit.numeric_value) || 0;
                const numericType = (benefit.numeric_type || '').toLowerCase();

                if (numericType === 'cash') {
                    creditValue += numericVal;
                } else if (numericType === 'points' || numericType === 'miles') {
                    pointsValue += numericVal;
                }
            });
        }

        // 3. Points Value: Calculated above
    });

    // Net Value excludes Points Value
    const netValue = creditValue - totalFees;

    // Update DOM with animation
    animateValue('metric-annual-fees', -totalFees);
    animateValue('metric-credit-value', creditValue);
    animateValue('metric-points-value', pointsValue);
    animateValue('metric-net-value', netValue);
}

function animateValue(id, end) {
    const obj = document.getElementById(id);
    const start = parseFloat(obj.textContent.replace(/[^0-9.-]+/g, "")) || 0;
    const duration = 500;
    let startTimestamp = null;

    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const current = Math.floor(progress * (end - start) + start);

        const formatted = Math.abs(current).toLocaleString();
        const sign = current < 0 ? '-' : (current > 0 ? '+' : '');

        if (id === 'metric-points-value') {
            obj.textContent = `${sign}${formatted}`;
        } else {
            obj.textContent = `${sign}$${formatted}`;
        }

        // Color logic for Net Value
        if (id === 'metric-net-value') {
            obj.style.color = current >= 0 ? '#10b981' : '#ef4444';
        } else if (id === 'metric-annual-fees') {
            obj.style.color = current < 0 ? '#ef4444' : '#1e293b';
        } else {
            obj.style.color = current > 0 ? '#10b981' : '#1e293b';
        }

        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };

    window.requestAnimationFrame(step);
}

// Auto-select cards that are in the user's wallet
window.addEventListener('load', () => {
    setTimeout(() => {
        // Clear any previous selection just in case, though it should be empty
        selectedCards.clear();

        // Iterate through all card options
        document.querySelectorAll('.card-option').forEach(cardEl => {
            const cardId = cardEl.dataset.id;

            // Check if this card is in the user's wallet
            // walletCardIds is a Set defined in the template
            if (walletCardIds.has(parseInt(cardId)) || walletCardIds.has(cardId)) {
                // If the card is not already selected (visual check), select it
                if (!cardEl.classList.contains('selected')) {
                    toggleCardSelection(cardEl, cardEl.dataset.slot);
                }

                // If the card is hidden in the carousel, we should probably rotate to it?
                // For now, let's just ensure it's selected. The metrics will update.
                // Optionally, we could find the slot and rotate the carousel to show this card.
                // Let's do a simple check: if it's hidden, try to show it.
                if (cardEl.classList.contains('slot-card-hidden')) {
                    // Find the slot index
                    const slotIndex = cardEl.dataset.slot;
                    const cardIndex = parseInt(cardEl.dataset.index);

                    // We need to set the current index for this slot to this card's index
                    // But changeCard functions relatively. 
                    // We can manually manipulate the DOM to show this card for a better UX.

                    // Use the helper if available or manual override
                    // Actually, simply selecting it is the core requirement. 
                    // Enhancing visibility is a "nice to have". 
                    // Let's stick to the core requirement first to avoid carousel sync bugs.
                }
            }
        });

        // If no cards were selected (e.g. anonymous user or no matches), 
        // calculateMetrics will run with empty selection, resulting in 0s, which is correct.
        calculateMetrics();

    }, 100);
});

// --- CAROUSEL LOGIC ---

// Track current index for each slot
const currentSlotIndices = {};

function changeCard(slotIndex, direction) {
    // Try to find cards using the slot-card class first
    const slotClass = `slot-card-${slotIndex}`;
    let cards = document.querySelectorAll(`.${slotClass}`);

    // If no cards found with slot-card class, use data-slot attribute
    if (cards.length === 0) {
        cards = document.querySelectorAll(`.card-option[data-slot="${slotIndex}"]`);
    }

    if (cards.length <= 1) {
        return;
    }

    // Get current index
    let currentIndex = currentSlotIndices[slotIndex] || 0;

    // Hide current card
    cards[currentIndex].classList.add('slot-card-hidden');
    cards[currentIndex].style.display = 'none'; // Fallback

    // Calculate new index
    currentIndex += direction;
    if (currentIndex < 0) currentIndex = cards.length - 1;
    if (currentIndex >= cards.length) currentIndex = 0;

    // Show new card and update tracker
    cards[currentIndex].classList.remove('slot-card-hidden');
    cards[currentIndex].style.display = 'block'; // Fallback
    currentSlotIndices[slotIndex] = currentIndex;

    // Update pagination dots
    const dotsContainer = document.getElementById(`dots-slot-${slotIndex}`);
    if (dotsContainer) {
        const dots = dotsContainer.querySelectorAll('.pagination-dot');
        dots.forEach((dot, index) => {
            if (index === currentIndex) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }
}

// Initialize carousel logic
window.addEventListener('load', function () {
    // Initialize current indices for all slots
    const slots = document.querySelectorAll('.slot-carousel');
    slots.forEach((slot, index) => {
        const slotIndex = index + 1;
        // Use the same selector strategy as changeCard
        const slotClass = `slot-card-${slotIndex}`;
        let cards = document.querySelectorAll(`.${slotClass}`);
        if (cards.length === 0) {
            cards = slot.querySelectorAll(`.card-option[data-slot="${slotIndex}"]`);
        }

        if (cards.length > 1) {
            // Initialize the current index
            currentSlotIndices[slotIndex] = 0;

            // Ensure only the first one is visible
            cards.forEach((card, cardIndex) => {
                if (cardIndex === 0) {
                    card.classList.remove('slot-card-hidden');
                    card.style.display = 'block';
                } else {
                    card.classList.add('slot-card-hidden');
                    card.style.display = 'none';
                }
            });

            // Set first dot as active
            const dotsContainer = document.getElementById(`dots-slot-${slotIndex}`);
            if (dotsContainer) {
                const dots = dotsContainer.querySelectorAll('.pagination-dot');
                dots.forEach((dot, dotIndex) => {
                    if (dotIndex === 0) {
                        dot.classList.add('active');
                    } else {
                        dot.classList.remove('active');
                    }
                });
            }
        }
    });
});
