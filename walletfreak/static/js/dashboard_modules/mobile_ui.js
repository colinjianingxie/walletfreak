/**
 * Mobile UI Logic
 */

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

    // Load cards when showing add new screen - use actual globalAvailableCards data
    if (typeof globalAvailableCards !== 'undefined') {
        renderMobileCards(globalAvailableCards);
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
    // Hide details screen
    const detailScreen = document.getElementById('mobile-card-detail-screen');
    if (detailScreen) {
        detailScreen.classList.remove('active');
        detailScreen.style.display = 'none';
    }

    // Show add new screen (without resetting filters)
    const addNewScreen = document.getElementById('mobile-add-new-screen');
    if (addNewScreen) {
        addNewScreen.classList.add('active');
        addNewScreen.style.display = 'flex';
    }
}

// Mobile card loading and filtering
function loadMobileCards() {
    // Fallback sample cards if globalAvailableCards is not defined
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
            <div style="display: flex; align-items: center; gap: 1rem;">
                <img src="${card.image_url || '/static/images/card_placeholder.png'}" style="width: 48px; height: auto; border-radius: 4px; object-fit: contain;" alt="${card.name}">
                <div>
                    <div class="card-name">${card.name}</div>
                    <div class="card-issuer">${card.issuer}</div>
                </div>
            </div>
            <span class="material-icons" style="color: #CBD5E1; font-size: 20px;">chevron_right</span>
        `;

        cardElement.onclick = () => showMobileCardDetail(card);
        container.appendChild(cardElement);
    });
}

// Track selected filters// Basic Mobile UI Handling
var selectedMobileFilter = 'all'; // Changed from Set to single value for Radio behavior

function toggleMobileFilter(issuer) {
    const btn = document.getElementById(`filter-${issuer}`);

    // If clicking same filter (and it's not All), do nothing or ensure it remains active ? 
    // User requested "radio button" behavior. Usually radio buttons can't be deselected by clicking the active one, 
    // you have to click another one. 'All' is the default 'none' state.

    if (selectedMobileFilter === issuer) {
        return; // Already selected
    }

    selectedMobileFilter = issuer;

    // Update UI active state for ALL buttons
    // Since we don't have a list of all possible issuers easily accessible without querySelectorAll, 
    // let's just reset all '.mobile-quick-add-btn'
    document.querySelectorAll('.mobile-quick-add-btn').forEach(b => {
        b.classList.remove('active');
        b.style.background = 'white';
        b.style.color = '#64748B';
        b.style.borderColor = '#E2E8F0';
    });

    // Activate current
    if (btn) {
        btn.classList.add('active');
        btn.style.background = '#6366F1';
        btn.style.color = 'white';
        btn.style.borderColor = '#6366F1';
    }

    // Apply filter
    applyMobileFilters();
}

function applyMobileFilters() {
    if (typeof globalAvailableCards === 'undefined') {
        console.log('globalAvailableCards not available');
        return;
    }

    const searchInput = document.getElementById('mobile-card-search');
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';

    let filtered = globalAvailableCards;

    // 1. Filter by Search Term
    if (searchTerm) {
        let term = searchTerm;
        if (term === 'amex') term = 'american express';

        filtered = filtered.filter(c =>
            c.name.toLowerCase().includes(term) ||
            c.issuer.toLowerCase().includes(term) ||
            (term === 'amex' && c.issuer.toLowerCase().includes('american express'))
        );
    }

    // 2. Filter by Issuer (if not All)
    if (selectedMobileFilter !== 'All') {
        let issuer = selectedMobileFilter;
        if (issuer === 'American Express') {
            // Mapping check - HTML has "American Express" ID but simple text "Amex"
            // The argument passed is 'American Express' from HTML for Amex button
        }
        // Handle Discover? The arg passed is 'Discover'

        filtered = filtered.filter(c => c.issuer.includes(issuer));
    }

    renderMobileCards(filtered);
}

function filterMobileCards(issuer) {
    if (typeof globalAvailableCards === 'undefined') {
        console.log('globalAvailableCards not available, filtering by:', issuer);
        return;
    }

    let searchIssuer = issuer;
    if (issuer === 'American Express') {
        searchIssuer = 'American Express';
    }

    const filtered = globalAvailableCards.filter(c =>
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
    // Use Flexbox for robust full-height layout
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.height = '100vh';
    container.style.overflow = 'hidden';

    container.innerHTML = `
        <!-- Header (Fixed) -->
        <div style="flex-shrink: 0; display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; background: white; border-bottom: 1px solid #F3F4F6;">
            <h1 style="font-size: 1.5rem; font-weight: 700; color: #1F2937; margin: 0;">Manage Wallet</h1>
            <button class="modal-close-btn" onclick="closeManageWalletModal()" style="background: none; border: none; color: #64748B; font-size: 1.5rem; cursor: pointer; padding: 0.5rem;">×</button>
        </div>
        
        <!-- Scrollable Content Body -->
        <div style="flex: 1; overflow-y: auto; background: white; padding-bottom: 2rem;">
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
                <div style="width: 100%; max-width: 100%; margin: 0; padding: 1rem 0; text-align: center;">
                   <img src="${card.image_url || '/static/images/card_placeholder.png'}" style="width: 100%; max-width: 320px; height: auto; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.15);" alt="${card.name}">
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
        let description = benefit.long_description || benefit.description || '';
        if (benefit.additional_details) {
            description += (description ? '<br><br>' : '') + benefit.additional_details;
        }
        if (!description) description = 'No additional details available.';

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
            currency: b.benefit_type === 'Cashback' ? 'cash' : (b.currency || 'points'),
            details: b.description || b.long_description || b.additional_details
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

        // Build details text similar to card modal logic
        let details = item.details || item.description_long || item.additional_details || '';
        if (!details) {
            if (currency.toLowerCase().includes('cash')) {
                details = `Earn ${rate}% cash back on ${cat.toLowerCase()}.`;
            } else {
                details = `Earn ${rate}x ${currency} on ${cat.toLowerCase()}.`;
            }
        }

        const uniqueId = `mobile-earning-${card.id}-${index}`;
        const borderBottom = index < earning.length - 1 ? 'border-bottom: 1px solid #F3F4F6;' : '';

        // Add onclick interaction and hidden details content
        html += `
            <div onclick="toggleMobileDetail('${uniqueId}')" style="cursor: pointer;">
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.875rem 1rem; ${borderBottom}">
                    <div style="font-weight: 600; color: #1F2937; font-size: 1rem; max-width: 70%;">${cat}</div>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div style="color: #2563EB; font-weight: 700; font-size: 1rem;">${mult}</div>
                         <span id="icon-${uniqueId}" class="material-icons" style="font-size: 18px; color: #D1D5DB; transition: transform 0.2s;">expand_more</span>
                    </div>
                </div>
                <div id="${uniqueId}" style="display: none; padding: 0 1rem 1rem 1rem; color: #64748B; font-size: 0.9rem; line-height: 1.5; border-bottom: 1px solid #F3F4F6;">
                    ${details}
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
            if (typeof globalAnniversaryCardId !== 'undefined') {
                globalAnniversaryCardId = 'ADD_NEW_CARD';
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
    // Just trigger the unified filter function
    applyMobileFilters();
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
