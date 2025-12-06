// Initialize selected cards map
const selectedCards = {};

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
        delete selectedCards[cardId];
    } else {
        element.classList.add('selected');
        statusIcon.textContent = 'check';
        selectionIndicator.style.background = '#3b82f6';
        selectionIndicator.style.borderColor = '#3b82f6';
        cardVisual.style.boxShadow = '0 0 0 4px rgba(59, 130, 246, 0.4), 0 10px 25px rgba(0,0,0,0.2)';
        cardVisual.style.transform = 'translateY(-4px)';

        selectedCards[cardId] = {
            fee: parseFloat(element.dataset.fee),
            bonusValue: parseFloat(element.dataset.bonusValue),
            bonusCurrency: element.dataset.bonusCurrency
        };
    }

    calculateMetrics();
}

function calculateMetrics() {
    let totalFees = 0;
    let creditValue = 0;
    let pointsValue = 0;

    Object.values(selectedCards).forEach(card => {
        totalFees += card.fee;

        if (card.bonusCurrency.toLowerCase() === 'cash') {
            creditValue += card.bonusValue;
        } else {
            // Assume points/miles are 1 cent per point
            pointsValue += (card.bonusValue * 0.01);
        }
    });

    const netValue = creditValue + pointsValue - totalFees;

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
