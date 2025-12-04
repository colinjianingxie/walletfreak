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

// Mobile screen management functions
function showMobileMyStackScreen() {
    // Hide ALL screens first
    const mobileScreens = ['mobile-my-stack-screen', 'mobile-add-new-screen', 'mobile-card-detail-screen'];
    mobileScreens.forEach(screenId => {
        const screen = document.getElementById(screenId);
        if (screen) {
            screen.classList.remove('active');
            screen.style.display = 'none';
        }
    });

    // Show only my stack screen
    const myStackScreen = document.getElementById('mobile-my-stack-screen');
    if (myStackScreen) {
        myStackScreen.classList.add('active');
        myStackScreen.style.display = 'flex';
    }
}

function showMobileAddNewScreen() {
    // Hide ALL screens first
    const mobileScreens = ['mobile-my-stack-screen', 'mobile-add-new-screen', 'mobile-card-detail-screen'];
    mobileScreens.forEach(screenId => {
        const screen = document.getElementById(screenId);
        if (screen) {
            screen.classList.remove('active');
            screen.style.display = 'none';
        }
    });

    // Show only add new screen
    const addNewScreen = document.getElementById('mobile-add-new-screen');
    if (addNewScreen) {
        addNewScreen.classList.add('active');
        addNewScreen.style.display = 'flex';
    }

    // Load cards when showing add new screen - use actual availableCards data
    if (typeof availableCards !== 'undefined') {
        renderMobileCards(availableCards);
    } else {
        loadMobileCards(); // fallback to sample data
    }
}

function showMobileCardDetailScreen() {
    // Hide ALL screens first
    const mobileScreens = ['mobile-my-stack-screen', 'mobile-add-new-screen', 'mobile-card-detail-screen'];
    mobileScreens.forEach(screenId => {
        const screen = document.getElementById(screenId);
        if (screen) {
            screen.classList.remove('active');
            screen.style.display = 'none';
        }
    });

    // Show only card detail screen
    const cardDetailScreen = document.getElementById('mobile-card-detail-screen');
    if (cardDetailScreen) {
        cardDetailScreen.classList.add('active');
        cardDetailScreen.style.display = 'flex';
    }
}

function backToMobileSearch() {
    showMobileAddNewScreen();
}

// Mobile card loading and filtering
function loadMobileCards() {
    // Fallback sample cards if availableCards is not defined
    const sampleCards = [
        { id: 1, name: 'Sapphire Preferred', issuer: 'Chase' },
        { id: 2, name: 'Sapphire Reserve', issuer: 'Chase' },
        { id: 3, name: 'Platinum Card', issuer: 'American Express' },
        { id: 4, name: 'Gold Card', issuer: 'American Express' },
        { id: 5, name: 'Venture X', issuer: 'Capital One' }
    ];

    renderMobileCards(sampleCards);
}

function renderMobileCards(cards) {
    const container = document.getElementById('mobile-card-results-list');
    container.innerHTML = '';

    if (cards.length === 0) {
        container.innerHTML = '<div style="padding: 2rem; text-align: center; color: #94A3B8;">No cards found</div>';
        return;
    }

    cards.forEach(card => {
        const cardElement = document.createElement('div');
        cardElement.className = 'mobile-card-item';

        cardElement.innerHTML = `
            <div>
                <div class="card-name">${card.name}</div>
                <div class="card-issuer">${card.issuer}</div>
            </div>
            <span class="material-icons" style="color: #CBD5E1; font-size: 20px;">chevron_right</span>
        `;

        cardElement.onclick = () => showMobileCardDetail(card);
        container.appendChild(cardElement);
    });
}

// Track selected filters for mobile
let selectedMobileFilters = new Set();

function toggleMobileFilter(issuer) {
    const btn = document.getElementById(`filter-${issuer}`);

    if (selectedMobileFilters.has(issuer)) {
        // Deselect
        selectedMobileFilters.delete(issuer);
        btn.style.background = 'white';
        btn.style.color = '#64748B';
        btn.style.borderColor = '#E2E8F0';
    } else {
        // Select
        selectedMobileFilters.add(issuer);
        btn.style.background = '#6366F1';
        btn.style.color = 'white';
        btn.style.borderColor = '#6366F1';
    }

    // Apply filter
    applyMobileFilters();
}

function applyMobileFilters() {
    if (typeof availableCards === 'undefined') {
        console.log('availableCards not available');
        return;
    }

    if (selectedMobileFilters.size === 0) {
        // No filters selected, show all cards
        renderMobileCards(availableCards);
    } else {
        // Filter cards based on selected issuers (OR logic)
        const filtered = availableCards.filter(card => {
            return Array.from(selectedMobileFilters).some(issuer => {
                return card.issuer.includes(issuer);
            });
        });
        renderMobileCards(filtered);
    }
}

function filterMobileCards(issuer) {
    if (typeof availableCards === 'undefined') {
        console.log('availableCards not available, filtering by:', issuer);
        return;
    }

    let searchIssuer = issuer;
    if (issuer === 'American Express') {
        searchIssuer = 'American Express';
    }

    const filtered = availableCards.filter(c =>
        c.issuer.toLowerCase().includes(searchIssuer.toLowerCase())
    );
    renderMobileCards(filtered);
}

function showMobileCardDetail(card) {
    showMobileCardDetailScreen();

    // Set the selected card for adding
    if (typeof selectedAddCard !== 'undefined') {
        selectedAddCard = card;
    }

    // Determine card background color based on issuer
    let cardBackground = 'linear-gradient(135deg, #6366F1, #8B5CF6)';
    if (card.name.toLowerCase().includes('chase')) {
        cardBackground = 'linear-gradient(135deg, #117ACA 0%, #005EB8 100%)';
    } else if (card.name.toLowerCase().includes('amex') || card.name.toLowerCase().includes('american express')) {
        cardBackground = 'linear-gradient(135deg, #2563EB 0%, #1E40AF 100%)';
    } else if (card.name.toLowerCase().includes('capital')) {
        cardBackground = 'linear-gradient(135deg, #0F172A 0%, #1E293B 100%)';
    }

    const container = document.getElementById('mobile-card-detail-screen');
    container.innerHTML = `
        <!-- Header -->
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; background: white; position: relative;">
            <h1 style="font-size: 1.5rem; font-weight: 700; color: #1F2937; margin: 0;">Manage Wallet</h1>
            <button class="modal-close-btn" onclick="closeManageWalletModal()" style="background: none; border: none; color: #64748B; font-size: 1.5rem; cursor: pointer; padding: 0.5rem; position: absolute; top: 1rem; right: 1rem;">×</button>
        </div>
        
        <div style="height: calc(100vh - 80px); overflow-y: auto; background: white;">
            <!-- Tab Navigation -->
            <div style="padding: 1.5rem; background: white;">
                <div style="display: flex; gap: 1rem;">
                    <button onclick="showMobileMyStackScreen()" class="mobile-tab-button">
                        <span class="material-icons" style="font-size: 24px;">account_balance_wallet</span>
                        <div>
                            <div style="font-size: 0.875rem; font-weight: 500;">My Stack</div>
                            <div style="font-size: 1.25rem; font-weight: 700;">${getActiveCardsCount()}</div>
                        </div>
                    </button>
                    
                    <button onclick="showMobileAddNewScreen()" class="mobile-tab-button active">
                        <span class="material-icons">add</span>
                        Add New
                    </button>
                </div>
            </div>
            
            <!-- Back to Search -->
            <div style="padding: 0 1.5rem;">
                <button onclick="backToMobileSearch()" style="background: none; border: none; display: flex; align-items: center; gap: 0.5rem; color: #1F2937; font-weight: 600; font-size: 1rem; margin-bottom: 1.5rem; cursor: pointer; padding: 0;">
                    <span class="material-icons">arrow_back</span>
                    Back to Search
                </button>
            </div>

            <!-- Card Visual -->
            <div style="padding: 0 1.5rem; margin-bottom: 2rem;">
                <div style="width: 100%; max-width: 100%; margin: 0; border-radius: 16px; background: ${cardBackground}; padding: 1.25rem; color: white; box-shadow: 0 8px 24px rgba(99, 102, 241, 0.25);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                        <div style="font-size: 0.75rem; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; opacity: 0.9;">${card.issuer.toUpperCase()}</div>
                        <span class="material-icons" style="font-size: 28px; opacity: 0.8;">contactless</span>
                    </div>
                    <div style="width: 50px; height: 35px; background: linear-gradient(135deg, #F4D03F, #C9A02C); border-radius: 6px; margin-bottom: 1rem;"></div>
                    <div style="font-size: 1.25rem; letter-spacing: 0.1em; margin-bottom: 1rem; font-weight: 500;">•••• •••• •••• 4242</div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                        <div style="font-size: 0.9rem; letter-spacing: 0.05em; text-transform: uppercase;">YOUR NAME</div>
                        <div style="display: flex; gap: 2px;">
                            <div style="width: 20px; height: 20px; background: #EB001B; border-radius: 50%; opacity: 0.9;"></div>
                            <div style="width: 20px; height: 20px; background: #F79E1B; border-radius: 50%; margin-left: -8px; opacity: 0.9;"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Add Button -->
            <div style="padding: 0 1.5rem; margin-bottom: 2rem;">
                <button onclick="addMobileSelectedCard()" style="background: #6366F1; width: 100%; padding: 1rem; border-radius: 12px; color: white; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 0.5rem; cursor: pointer; border: none; font-size: 1rem;">
                    <span class="material-icons">add</span> Add to Wallet
                </button>
            </div>

            <!-- Earning Rates -->
            <div style="padding: 0 1.5rem; margin-bottom: 1.5rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                    <span class="material-icons" style="font-size: 16px; color: #94A3B8;">trending_up</span>
                    <div style="font-size: 0.75rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.1em; text-transform: uppercase;">EARNING RATES</div>
                </div>
                ${generateMobileEarningRates(card)}
            </div>

            <!-- Credits -->
            <div style="padding: 0 1.5rem; margin-bottom: 2rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                    <span class="material-icons" style="font-size: 16px; color: #F59E0B;">bolt</span>
                    <div style="font-size: 0.75rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.1em; text-transform: uppercase;">CREDITS</div>
                </div>
                ${generateMobileBenefits(card)}
            </div>
        </div>
    `;
}

// Helper function to generate benefits for mobile view
function generateMobileBenefits(card) {
    const benefits = card.benefits || [];
    // Filter out benefits with benefit_type "Multiplier" or "Cashback" as they are in earning rates
    const filteredBenefits = benefits.filter(b => b.benefit_type !== 'Multiplier' && b.benefit_type !== 'Cashback');

    if (!Array.isArray(filteredBenefits) || filteredBenefits.length === 0) {
        return '<div style="color: #9CA3AF; font-size: 0.9rem; text-align: center; padding: 1rem;">No benefits available</div>';
    }

    let html = '<div style="background: white; border-radius: 12px; overflow: hidden;">';
    filteredBenefits.forEach((benefit, index) => {
        const name = benefit.short_description || benefit.name || benefit.title || 'Benefit';
        const value = benefit.numeric_value || benefit.value || benefit.amount || 'Included';
        const description = benefit.long_description || benefit.description || 'No additional details available.';
        const uniqueId = `mobile-benefit-${card.id}-${index}`;

        // Format value
        let valueDisplay = String(value);
        let valueColor = '#1F2937';

        if (valueDisplay.includes('$') || !isNaN(parseFloat(value))) {
            if (!valueDisplay.includes('$')) {
                valueDisplay = '$' + valueDisplay;
            }
            valueColor = '#10B981';
        } else if (valueDisplay.toLowerCase() === 'included') {
            valueColor = '#2563EB';
        }

        const borderBottom = index < filteredBenefits.length - 1 ? 'border-bottom: 1px solid #F3F4F6;' : '';

        html += `
            <div onclick="toggleMobileDetail('${uniqueId}')" style="cursor: pointer;">
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.875rem 1rem; ${borderBottom}">
                    <div style="font-weight: 600; color: #1F2937; font-size: 1rem; max-width: 70%;">${name}</div>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div style="color: ${valueColor}; font-weight: 700; font-size: 1rem;">${valueDisplay}</div>
                        <span id="icon-${uniqueId}" class="material-icons" style="font-size: 18px; color: #D1D5DB; transition: transform 0.2s;">expand_more</span>
                    </div>
                </div>
                <div id="${uniqueId}" style="display: none; padding: 0 1rem 1rem 1rem; color: #64748B; font-size: 0.9rem; line-height: 1.5; border-bottom: 1px solid #F3F4F6;">
                    ${description}
                </div>
            </div>
        `;
    });
    html += '</div>';

    return html;
}

// Helper function to generate earning rates for mobile view
function generateMobileEarningRates(card) {
    let earning = card.earning_rates || card.earning || card.rewards_structure || [];

    // If no earning rates found, extract from benefits with benefit_type "Multiplier" or "Cashback"
    if (!earning || earning.length === 0) {
        const benefits = card.benefits || [];
        earning = benefits.filter(b => b.benefit_type === 'Multiplier' || b.benefit_type === 'Cashback').map(b => ({
            category: b.short_description || b.name || b.title || b.description,
            rate: b.numeric_value || b.value || b.multiplier,
            currency: b.benefit_type === 'Cashback' ? 'cash' : (b.currency || 'points')
        }));
    }

    if (!Array.isArray(earning) || earning.length === 0) {
        return '<div style="color: #9CA3AF; font-size: 0.9rem; text-align: center; padding: 1rem;">No earning rates available</div>';
    }

    let html = '<div style="background: white; border-radius: 12px; overflow: hidden;">';
    earning.forEach((item, index) => {
        const cat = item.category || item.cat || item.description || 'Category';
        const rate = item.rate || item.mult || item.multiplier || item.value || 0;
        const currency = item.currency || 'points';

        let mult;
        if (currency.toLowerCase().includes('cash') || currency.toLowerCase().includes('%')) {
            mult = `${rate}%`;
        } else {
            mult = `${rate}x`;
        }

        const borderBottom = index < earning.length - 1 ? 'border-bottom: 1px solid #F3F4F6;' : '';

        html += `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.875rem 1rem; ${borderBottom}">
                <div style="font-weight: 600; color: #1F2937; font-size: 1rem; max-width: 70%;">${cat}</div>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="color: #2563EB; font-weight: 700; font-size: 1rem;">${mult}</div>
                    <span class="material-icons" style="font-size: 18px; color: #D1D5DB;">expand_more</span>
                </div>
            </div>
        `;
    });
    html += '</div>';

    return html;
}

// Function to handle adding card from mobile detail view
function addMobileSelectedCard() {
    if (typeof selectedAddCard !== 'undefined' && selectedAddCard) {
        // Use the same logic as desktop version
        if (typeof addSelectedCard === 'function') {
            addSelectedCard();
        } else {
            // Fallback - directly trigger anniversary modal
            if (typeof currentAnniversaryCardId !== 'undefined') {
                currentAnniversaryCardId = 'ADD_NEW_CARD';
                document.getElementById('anniversary-card-name').textContent = selectedAddCard.name;

                const now = new Date();
                const currentYear = now.getFullYear();
                const currentMonth = String(now.getMonth() + 1).padStart(2, '0');
                const defaultDate = `${currentYear}-${currentMonth}-01`;

                document.getElementById('anniversary-date-input').value = defaultDate;
                document.getElementById('anniversary-modal').style.display = 'flex';
            }
        }
    }
}

// Handle mobile search input
function handleMobileSearch(searchTerm) {
    if (typeof availableCards === 'undefined') {
        console.log('availableCards not available for search:', searchTerm);
        return;
    }

    let term = searchTerm.toLowerCase();

    // Alias mapping
    if (term === 'amex') {
        term = 'american express';
    }

    const filtered = availableCards.filter(c =>
        c.name.toLowerCase().includes(term) ||
        c.issuer.toLowerCase().includes(term) ||
        (term === 'amex' && c.issuer.toLowerCase().includes('american express'))
    );

    renderMobileCards(filtered);
}

// Toggle function for mobile detail expansion
function toggleMobileDetail(id) {
    const el = document.getElementById(id);
    const icon = document.getElementById(`icon-${id}`);
    if (el) {
        if (el.style.display === 'none' || el.style.display === '') {
            el.style.display = 'block';
            if (icon) icon.style.transform = 'rotate(180deg)';
        } else {
            el.style.display = 'none';
            if (icon) icon.style.transform = 'rotate(0deg)';
        }
    }
}

// Initialize tooltips or other interactive elements if needed
document.addEventListener('DOMContentLoaded', function () {
    // Any initialization logic
});
