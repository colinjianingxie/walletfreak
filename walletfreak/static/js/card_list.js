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

// Auth & Realtime State
let walletListenerUnsubscribe = null;
if (typeof firebase !== 'undefined' && typeof firebase.auth === 'function') {
    firebase.auth().onAuthStateChanged((user) => {
        if (user) {
            setupExploreWalletListener(user.uid);
        } else {
            if (walletListenerUnsubscribe) {
                walletListenerUnsubscribe();
            }
        }
    });
}

// State
let cardsPerPage = 9; // Updated to 9 as requested
let currentlyShowing = cardsPerPage;
let activeCategory = '';
let currentView = localStorage.getItem('exploreView') || 'grid';
let currentMatchingCards = []; // Store filtered results for pagination

// Helper to normalize strings for comparison (remove spaces, special chars, lowercase)
function normalize(str) {
    return str ? str.toLowerCase().replace(/[^a-z0-9]/g, '') : '';
}

// View Toggle
function toggleView(view) {
    currentView = view;
    localStorage.setItem('exploreView', view);

    // Update Grid Class
    if (cardsGrid) {
        if (view === 'list') {
            cardsGrid.classList.add('list-view');
        } else {
            cardsGrid.classList.remove('list-view');
        }
    }

    // Update Scroll Container Class
    const scrollContainer = document.getElementById('cards-scroll-container');
    if (scrollContainer) {
        if (view === 'list') {
            scrollContainer.classList.add('list-view-active');
        } else {
            scrollContainer.classList.remove('list-view-active');
        }
    }

    // Update Header Visibility
    const listHeader = document.getElementById('list-header');
    if (listHeader) {
        // Only show list header if in list view AND not on mobile (mobile check done via CSS usually, but here we can be explicit or rely on CSS)
        // We rely on CSS media query to hide it on mobile, so just toggle display here based on view
        listHeader.style.display = view === 'list' ? 'flex' : 'none';

        // Extra check: if window is mobile width, force hide? CSS handles it with !important or media query
    }

    // Update Buttons
    const gridBtn = document.getElementById('view-grid-btn');
    const listBtn = document.getElementById('view-list-btn');

    if (gridBtn && listBtn) {
        if (view === 'grid') {
            gridBtn.classList.add('active');
            gridBtn.style.background = '#F1F5F9';
            gridBtn.style.color = '#0F172A';

            listBtn.classList.remove('active');
            listBtn.style.background = 'transparent';
            listBtn.style.color = '#94A3B8';
        } else {
            listBtn.classList.add('active');
            listBtn.style.background = '#F1F5F9';
            listBtn.style.color = '#0F172A';

            gridBtn.classList.remove('active');
            gridBtn.style.background = 'transparent';
            gridBtn.style.color = '#94A3B8';
        }
    }
}

// Initialize Sliders
// Initialize Sliders
function updateSlider() {
    if (!minFeeSlider || !maxFeeSlider) return;

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

    sliderTrack.style.left = percent1 + '%';
    sliderTrack.style.width = (percent2 - percent1) + '%';

    // Z-index management for overlapping thumbs
    if (minVal > 900) {
        minFeeSlider.style.zIndex = 5;
    } else {
        minFeeSlider.style.zIndex = 3;
    }
}

function handleSliderInput(e) {
    updateSlider.call(this, e);
    filterCards();
}

if (minFeeSlider && maxFeeSlider) {
    minFeeSlider.addEventListener('input', handleSliderInput);
    maxFeeSlider.addEventListener('input', handleSliderInput);
    minFeeSlider.addEventListener('change', handleSliderInput);
    maxFeeSlider.addEventListener('change', handleSliderInput);
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

    // Store for pagination
    currentMatchingCards = matchingCards;

    // Update Count
    if (totalCardsCount) {
        totalCardsCount.textContent = matchingCards.length;
    }

    // Reset pagination
    currentlyShowing = cardsPerPage;

    // Show cards
    exploreCards.forEach(card => card.style.display = 'none'); // Hide all first

    currentMatchingCards.forEach((card, index) => {
        if (index < currentlyShowing) {
            card.style.display = '';
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
    // Use stored results
    currentlyShowing += cardsPerPage;

    currentMatchingCards.forEach((card, index) => {
        if (index < currentlyShowing) {
            card.style.display = '';
        }
    });

    if (loadMoreContainer) {
        if (currentlyShowing >= currentMatchingCards.length) {
            loadMoreContainer.style.display = 'none';
        } else {
            const remaining = currentMatchingCards.length - currentlyShowing;
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

    // Initialize View
    toggleView(currentView);
    filterCards();
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
        // Force Grid View on Mobile
        if (currentView === 'list') {
            toggleView('grid');
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
    // 1. Update Compare Button (Grid View / General)
    const btn = document.querySelector(`.compare-select-btn[data-card-id="${cardId}"]`);
    if (btn) {
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

    // 2. Update Checkbox (List View)
    // Find the data source div for this card, then finding the sibling checkbox
    const dataDiv = document.querySelector(`.compare-data-source[data-card-id="${cardId}"]`);
    if (dataDiv) {
        const checkbox = dataDiv.parentElement.querySelector('.list-checkbox');
        if (checkbox) {
            if (isSelected) {
                checkbox.classList.add('checked');
            } else {
                checkbox.classList.remove('checked');
            }
        }
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

// Deprecated goToCompare function body was here, removing orphan code block
function goToCompare() {
    if (typeof openCompareModal === 'function') {
        openCompareModal();
    }
}


// --- Realtime Wallet Updates (Explore Page) ---
function setupExploreWalletListener(uid) {
    if (typeof firebase === 'undefined' || !firebase.firestore) return;
    const db = firebase.firestore();

    if (walletListenerUnsubscribe) {
        walletListenerUnsubscribe();
    }

    walletListenerUnsubscribe = db.collection('users').doc(uid).collection('user_cards')
        .where('status', '==', 'active')
        .onSnapshot((snapshot) => {
            const currentWalletIds = new Set();
            snapshot.forEach(doc => {
                // We use document ID or card_id field? Ideally 'card_id' if that's what we store.
                // Looking at other files, we normally map doc.data().card_id
                const data = doc.data();
                if (data.card_id) {
                    currentWalletIds.add(data.card_id);
                }
            });

            updateWalletState(currentWalletIds);
        }, (error) => {
            console.error("Explore: Error listening to wallet updates:", error);
        });
}

function updateWalletState(newWalletIds) {
    // 1. Update Global Set
    walletCardIds.clear();
    newWalletIds.forEach(id => walletCardIds.add(id));

    // 2. Recalculate Scores & Update DOM
    exploreCards.forEach(cardEl => {
        const cardId = cardEl.getAttribute('onclick').match(/'([^']+)'/)[1];
        if (!cardId) return;

        const cardData = allCardsData[cardId]; // Use the global dictionary from template
        if (!cardData) return; // Should exist

        // Recalculate Match Score
        // Python Logic:
        // Base: 50
        // + Category Overlap (up to 30)
        // + No Fee (10) OR Fee > 500 (-10)
        // - In Wallet (-30)

        let score = 50;

        // Categories
        if (userPersonality && userPersonality.focus_categories) {
            const userCats = new Set(userPersonality.focus_categories);
            const cardCats = new Set(cardData.categories || []);
            let overlap = 0;
            cardCats.forEach(c => {
                if (userCats.has(c)) overlap++;
            });
            score += Math.min(30, overlap * 10);
        }

        // Fee
        const annualFee = cardData.annual_fee || 0;
        if (annualFee === 0) score += 10;
        else if (annualFee > 500) score -= 10;

        // Wallet Penalty
        const inWallet = walletCardIds.has(cardId);
        if (inWallet) score -= 30;

        // Clamp
        score = Math.max(0, Math.min(100, score));

        // Update DOM Elements
        // Find match badge inside this card element
        const matchBadge = cardEl.querySelector('.match-score');
        if (matchBadge) {
            matchBadge.textContent = score + '%';
            // Optional: color coding could be updated here if needed
        }

        // Store score in userMatchScores map for sorting
        userMatchScores[cardId] = score;

        // Update data-attributes for filtering/sorting if we used them in JS sort logic
        // Current JS sort logic uses userMatchScores map in `filterCards`?
        // Wait, `filterCards` doesn't sort. `sortSelect` triggers reload.
        // But `card_list.js` line 417 (Python) does sort.
        // The JS `filterCards` only hides/shows. It does NOT re-sort DOM elements.
        // So the order won't change until refresh, BUT the badges will update.
        // The user said "benefits... need to update". This likely refers to the visual indicators.
        // If sorting is critical, we'd need to re-sort the DOM in JS, which is a bigger change.
        // For now, updating the values is the priority.

        // Mark in-wallet status on card (if we have a visual style for it)
        // Perhaps add a class?
        if (inWallet) {
            cardEl.classList.add('in-wallet');
        } else {
            cardEl.classList.remove('in-wallet');
        }
    });

    // 3. Re-run filters to ensure consistency (though usually filters don't depend on wallet status unless we have that filter)
    // There is a 'wallet_filter' in Python, but JS filterCards doesn't seem to implement it fully?
    // Let's check filterCards... no, it doesn't filter by wallet status in JS.
    // So just updating visual badges is enough for now.
}

// Handling Card Click based on view
function handleCardClick(cardId) {
    // If in LIST view, row click toggles selection (checkbox)
    if (currentView === 'list') {
        // Find the data source element to get card details
        const dataDiv = document.querySelector(`.compare-data-source[data-card-id="${cardId}"]`);
        if (dataDiv) {
            toggleCardSelection(cardId, dataDiv);
        }
        return;
    }

    // In GRID view, the whole card is clickable.
    openCardModal(cardId);
}
