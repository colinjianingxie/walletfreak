// Elements
const searchInput = document.getElementById('search-input');
const minFeeSlider = document.getElementById('min-fee-slider');
const maxFeeSlider = document.getElementById('max-fee-slider');
const feeRangeDisplay = document.getElementById('fee-range-display');
const sliderTrack = document.getElementById('slider-track');
const sortSelect = document.getElementById('sort-select');
const issuerFilters = document.querySelectorAll('.issuer-filter');
const categoryPills = document.querySelectorAll('.category-pill');
const cardsGrid = document.getElementById('cards-grid');
const exploreCards = document.querySelectorAll('.explore-card');
const noResults = document.getElementById('no-results');
const loadMoreBtn = document.getElementById('load-more-btn');
const loadMoreContainer = document.getElementById('load-more-container');
const remainingCount = document.getElementById('remaining-count');
const totalCardsCount = document.getElementById('total-cards-count');
const compareBar = document.getElementById('compare-bar');
const comparePreviewCircles = document.getElementById('compare-preview-circles');
const compareCountText = document.getElementById('compare-count-text');

// Compare State
let selectedCards = new Map(); // id -> {name, issuer, color}

// State
let cardsPerPage = 100; // Show all cards by default as requested
let currentlyShowing = cardsPerPage;
let activeCategory = '';

// Helper to normalize strings for comparison (remove spaces, special chars, lowercase)
function normalize(str) {
    return str ? str.toLowerCase().replace(/[^a-z0-9]/g, '') : '';
}

// Initialize Sliders
function updateSlider() {
    const min = parseInt(minFeeSlider.value);
    const max = parseInt(maxFeeSlider.value);

    // Prevent crossover
    if (min > max - 10) {
        if (this === minFeeSlider) minFeeSlider.value = max - 10;
        else maxFeeSlider.value = min + 10;
    }

    const minVal = parseInt(minFeeSlider.value);
    const maxVal = parseInt(maxFeeSlider.value);

    feeRangeDisplay.textContent = `$${minVal} - $${maxVal}`;

    // Calculate track position using percentages for better responsiveness
    const percent1 = (minVal / 1000) * 100;
    const percent2 = (maxVal / 1000) * 100;

    // Adjust for thumb width (approximate)
    // We want the track to start at the center of the first thumb and end at the center of the second thumb
    // Since we can't easily get pixel widths in percentage logic without resize listeners, 
    // we'll use a hybrid approach or just stick to percentages which is usually fine for this UI.

    sliderTrack.style.left = percent1 + '%';
    sliderTrack.style.width = (percent2 - percent1) + '%';

    // Z-index management for overlapping thumbs
    if (minVal > 900) {
        minFeeSlider.style.zIndex = 5;
    } else {
        minFeeSlider.style.zIndex = 3;
    }

    filterCards();
}

if (minFeeSlider && maxFeeSlider) {
    minFeeSlider.addEventListener('input', updateSlider);
    maxFeeSlider.addEventListener('input', updateSlider);
    minFeeSlider.addEventListener('change', updateSlider);
    maxFeeSlider.addEventListener('change', updateSlider);
    // Ensure slider updates on resize
    window.addEventListener('resize', updateSlider);
}

// Category Selection
function selectCategory(btn) {
    // Update UI
    categoryPills.forEach(p => {
        p.classList.remove('active');
        p.style.background = 'white';
        p.style.color = '#64748B';
        p.style.border = '1px solid #E2E8F0';
    });

    btn.classList.add('active');
    btn.style.background = '#1E293B';
    btn.style.color = 'white';
    btn.style.border = '1px solid #1E293B';

    activeCategory = btn.dataset.category.toLowerCase();
    filterCards();
}

// Checkbox styling logic
issuerFilters.forEach(checkbox => {
    checkbox.addEventListener('change', function () {
        filterCards();
    });
});

// Reset Filters
function resetFilters() {
    if (minFeeSlider) minFeeSlider.value = 0;
    if (maxFeeSlider) maxFeeSlider.value = 1000;
    if (minFeeSlider && maxFeeSlider) updateSlider();

    issuerFilters.forEach(cb => {
        cb.checked = false;
    });

    if (searchInput) searchInput.value = '';
    activeCategory = '';
    // Reset category pills UI
    categoryPills.forEach(p => {
        p.classList.remove('active');
        p.style.background = 'white';
        p.style.color = '#64748B';
        p.style.border = '1px solid #E2E8F0';
        if (p.dataset.category === '') {
            p.classList.add('active');
            p.style.background = '#1E293B';
            p.style.color = 'white';
            p.style.border = '1px solid #1E293B';
        }
    });

    filterCards();
}

// Search & Sort
if (searchInput) searchInput.addEventListener('input', filterCards);
if (sortSelect) {
    sortSelect.addEventListener('change', () => {
        const url = new URL(window.location);
        url.searchParams.set('sort', sortSelect.value);
        window.location.href = url.toString();
    });
}

function filterCards() {
    const query = searchInput ? searchInput.value.toLowerCase() : '';
    const minFee = minFeeSlider ? parseInt(minFeeSlider.value) : 0;
    const maxFee = maxFeeSlider ? parseInt(maxFeeSlider.value) : 1000;

    const selectedIssuers = Array.from(issuerFilters)
        .filter(f => f.checked)
        .map(f => normalize(f.value));

    let matchingCards = [];

    exploreCards.forEach(card => {
        const name = card.dataset.name;
        const issuerRaw = card.dataset.issuer || '';
        const issuerNorm = normalize(issuerRaw);
        const categories = card.dataset.categories; // already lower
        const fee = parseInt(card.dataset.fee);

        const matchesSearch = query === '' || name.includes(query) || issuerRaw.toLowerCase().includes(query) || categories.includes(query);
        const matchesFee = fee >= minFee && fee <= maxFee;

        // Robust issuer matching
        const matchesIssuer = selectedIssuers.length === 0 || selectedIssuers.some(si => issuerNorm.includes(si) || si.includes(issuerNorm));

        const matchesCategory = activeCategory === '' || categories.includes(activeCategory);

        if (matchesSearch && matchesFee && matchesIssuer && matchesCategory) {
            matchingCards.push(card);
        }
    });

    // Update Count
    if (totalCardsCount) {
        totalCardsCount.textContent = matchingCards.length;
    }

    // Reset pagination
    currentlyShowing = cardsPerPage;

    // Show cards
    exploreCards.forEach(card => card.style.display = 'none'); // Hide all first

    matchingCards.forEach((card, index) => {
        if (index < currentlyShowing) {
            card.style.display = 'flex';
        }
    });

    // Update Load More
    if (loadMoreContainer) {
        if (matchingCards.length > currentlyShowing) {
            loadMoreContainer.style.display = 'flex';
            const remaining = matchingCards.length - currentlyShowing;
            if (remainingCount) remainingCount.textContent = `${remaining} more`;
        } else {
            loadMoreContainer.style.display = 'none';
        }
    }

    // No Results
    if (noResults) {
        if (matchingCards.length === 0) {
            if (cardsGrid) cardsGrid.style.display = 'none';
            noResults.style.display = 'block';
        } else {
            if (cardsGrid) cardsGrid.style.display = 'grid';
            noResults.style.display = 'none';
        }
    }
}

function loadMoreCards() {
    // Re-run filter logic to get matching cards list (inefficient but safe)
    // In a real app we'd cache the matching list
    const query = searchInput ? searchInput.value.toLowerCase() : '';
    const minFee = minFeeSlider ? parseInt(minFeeSlider.value) : 0;
    const maxFee = maxFeeSlider ? parseInt(maxFeeSlider.value) : 1000;

    const selectedIssuers = Array.from(issuerFilters)
        .filter(f => f.checked)
        .map(f => normalize(f.value));

    let matchingCards = [];
    exploreCards.forEach(card => {
        const name = card.dataset.name;
        const issuerRaw = card.dataset.issuer || '';
        const issuerNorm = normalize(issuerRaw);
        const categories = card.dataset.categories;
        const fee = parseInt(card.dataset.fee);

        const matchesSearch = query === '' || name.includes(query) || issuerRaw.toLowerCase().includes(query) || categories.includes(query);
        const matchesFee = fee >= minFee && fee <= maxFee;
        const matchesIssuer = selectedIssuers.length === 0 || selectedIssuers.some(si => issuerNorm.includes(si) || si.includes(issuerNorm));
        const matchesCategory = activeCategory === '' || categories.includes(activeCategory);

        if (matchesSearch && matchesFee && matchesIssuer && matchesCategory) {
            matchingCards.push(card);
        }
    });

    currentlyShowing += cardsPerPage;

    matchingCards.forEach((card, index) => {
        if (index < currentlyShowing) {
            card.style.display = 'flex';
        }
    });

    if (loadMoreContainer) {
        if (currentlyShowing >= matchingCards.length) {
            loadMoreContainer.style.display = 'none';
        } else {
            const remaining = matchingCards.length - currentlyShowing;
            if (remainingCount) remainingCount.textContent = `${remaining} more`;
        }
    }
}

// Initialize
window.addEventListener('DOMContentLoaded', () => {
    // Set initial active category style
    const allCatBtn = document.querySelector('.category-pill[data-category=""]');
    if (allCatBtn) {
        allCatBtn.style.background = '#1E293B';
        allCatBtn.style.color = 'white';
        allCatBtn.style.border = '1px solid #1E293B';
    }

    // Explicitly set initial slider values to ensure they're at extremes
    if (minFeeSlider) minFeeSlider.value = 0;
    if (maxFeeSlider) maxFeeSlider.value = 1000;

    // Force update to position track and ensure rendering
    if (minFeeSlider && maxFeeSlider) updateSlider();

    // Move sort to mobile container if needed
    handleResize();
    window.addEventListener('resize', handleResize);
});

function openFilters() {
    const sidebar = document.getElementById('filters-sidebar');
    const overlay = document.getElementById('filter-overlay');
    if (sidebar) sidebar.classList.add('active');
    if (overlay) overlay.style.display = 'block';
    document.body.style.overflow = 'hidden';

    // Hide compare bar on mobile when filters are open
    if (compareBar && window.innerWidth <= 768) {
        compareBar.style.display = 'none';
    }
}

function closeFilters() {
    const sidebar = document.getElementById('filters-sidebar');
    const overlay = document.getElementById('filter-overlay');
    if (sidebar) sidebar.classList.remove('active');
    if (overlay) overlay.style.display = 'none';
    document.body.style.overflow = '';

    // Show compare bar again if needed
    if (compareBar) {
        compareBar.style.display = 'flex';
        updateCompareBar(); // Re-apply transform logic
    }
}

function handleResize() {
    const sortContainer = document.querySelector('.desktop-sort');
    const mobileSortContainer = document.querySelector('.mobile-sort-container');
    const sortContent = document.getElementById('sort-content-wrapper');

    // We need to wrap the sort content first if not already
    if (!sortContent && sortContainer) {
        const wrapper = document.createElement('div');
        wrapper.id = 'sort-content-wrapper';
        wrapper.style.display = 'flex';
        wrapper.style.alignItems = 'center';
        wrapper.style.gap = '0.75rem';
        while (sortContainer.firstChild) {
            wrapper.appendChild(sortContainer.firstChild);
        }
        sortContainer.appendChild(wrapper);
    }

    const wrapper = document.getElementById('sort-content-wrapper');
    if (window.innerWidth <= 1024) {
        if (mobileSortContainer && wrapper && !mobileSortContainer.contains(wrapper)) {
            mobileSortContainer.appendChild(wrapper);
        }
    } else {
        if (sortContainer && wrapper && !sortContainer.contains(wrapper)) {
            sortContainer.appendChild(wrapper);
        }
    }
}

// Compare Functions
function toggleCardSelection(cardId, btn) {
    const cardData = {
        id: cardId,
        name: btn.dataset.cardName,
        issuer: btn.dataset.cardIssuer,
        color: btn.dataset.cardColor
    };

    if (selectedCards.has(cardId)) {
        selectedCards.delete(cardId);
        updateCompareUI(cardId, false);
    } else {
        if (selectedCards.size >= 3) {
            alert("You can compare up to 3 cards at a time.");
            return;
        }
        selectedCards.set(cardId, cardData);
        updateCompareUI(cardId, true);
    }

    updateCompareBar();
}

function updateCompareUI(cardId, isSelected) {
    // Find the button for this card (could be multiple if we had list/grid view, but here just one per card)
    const btn = document.querySelector(`.compare-select-btn[data-card-id="${cardId}"]`);
    if (!btn) return;

    if (isSelected) {
        btn.style.background = '#3B82F6';
        btn.style.color = 'white';
        btn.innerHTML = '<span class="material-icons" style="font-size: 18px; color: white;">check</span>';
    } else {
        btn.style.background = 'white';
        btn.style.color = '#64748B';
        btn.innerHTML = '<span class="material-icons" style="font-size: 18px; color: #64748B;">balance</span>';
    }
}

function updateCompareBar() {
    if (!compareBar) return;

    if (selectedCards.size > 0) {
        compareBar.style.transform = 'translateX(-50%) translateY(0)';
    } else {
        compareBar.style.transform = 'translateX(-50%) translateY(150%)';
    }

    if (compareCountText) compareCountText.textContent = `${selectedCards.size} selected`;

    // Update circles
    if (comparePreviewCircles) {
        comparePreviewCircles.innerHTML = '';
        let offset = 0;

        selectedCards.forEach((card) => {
            const circle = document.createElement('div');
            circle.style.width = '32px';
            circle.style.height = '32px';
            circle.style.borderRadius = '50%';
            circle.style.background = card.color;
            circle.style.border = '2px solid #0F172A';
            circle.style.marginLeft = offset === 0 ? '0' : '-10px';
            circle.style.position = 'relative';
            circle.style.zIndex = offset + 1;

            // Optional: Tooltip
            circle.title = card.name;

            comparePreviewCircles.appendChild(circle);
            offset++;
        });
    }
}

function goToCompare() {
    // Deprecated in favor of modal
    if (typeof openCompareModal === 'function') {
        openCompareModal();
    }
}
