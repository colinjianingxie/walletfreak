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

        // 2. Credit Value: sum of numeric_values only if benefit_type is credit or bonus
        if (card.benefits && Array.isArray(card.benefits)) {
            card.benefits.forEach(benefit => {
                const bType = (benefit.benefit_type || '').toLowerCase();
                const numericVal = parseFloat(benefit.numeric_value) || 0;

                if (bType === 'credit' || bType === 'bonus') {
                    creditValue += numericVal;
                }
            });
        }

        // 3. Points Value: Set to 0 for now as requested
        pointsValue += 0;
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

        obj.textContent = `${sign}$${formatted}`;

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

// Auto-select first card in each slot on load - delay to allow carousel initialization
window.addEventListener('load', () => {
    setTimeout(() => {
        const slots = new Set();
        document.querySelectorAll('.card-option').forEach(el => slots.add(el.dataset.slot));

        slots.forEach(slot => {
            const firstCard = document.querySelector(`.card-option[data-slot="${slot}"][style*="display: block"], .card-option[data-slot="${slot}"]:not([style*="display: none"])`);
            if (firstCard) {
                toggleCardSelection(firstCard, slot);
            }
        });
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
window.addEventListener('load', function() {
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
