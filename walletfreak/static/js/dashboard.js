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

// --- Extracted from dashboard.html ---

let selectedAddCard = null;

function openManageWalletModal(view = 'stack') {
    const modal = document.getElementById('manage-wallet-modal');
    modal.style.display = 'flex';

    // Disable body scrolling when modal is open
    document.body.style.overflow = 'hidden';

    // Check if mobile
    if (window.innerWidth <= 768) {
        // Hide desktop content (CSS will handle most of this)
        const contentStack = document.getElementById('content-stack');
        const contentAdd = document.getElementById('content-add');
        const modalSidebar = document.querySelector('.modal-sidebar');

        if (contentStack) contentStack.style.display = 'none';
        if (contentAdd) contentAdd.style.display = 'none';
        if (modalSidebar) modalSidebar.style.display = 'none';

        // Reset mobile screens
        const mobileScreens = ['mobile-my-stack-screen', 'mobile-add-new-screen', 'mobile-card-detail-screen'];
        mobileScreens.forEach(screenId => {
            const screen = document.getElementById(screenId);
            if (screen) {
                screen.classList.remove('active');
                screen.style.display = 'none';
            }
        });

        // Show the requested mobile view
        if (view === 'stack') {
            showMobileMyStackScreen();
        } else {
            showMobileAddNewScreen();
        }
    } else {
        // Desktop view
        switchTab(view);
    }
}

function closeManageWalletModal() {
    document.getElementById('manage-wallet-modal').style.display = 'none';

    // Re-enable body scrolling when modal is closed
    document.body.style.overflow = '';

    // Reset preview (desktop)
    if (document.getElementById('card-preview-empty')) {
        document.getElementById('card-preview-empty').style.display = 'block';
    }
    if (document.getElementById('card-preview-content')) {
        document.getElementById('card-preview-content').style.display = 'none';
    }
    selectedAddCard = null;

    // Reset mobile screens
    const mobileScreens = ['mobile-my-stack-screen', 'mobile-add-new-screen', 'mobile-card-detail-screen'];
    mobileScreens.forEach(screenId => {
        const screen = document.getElementById(screenId);
        if (screen) {
            screen.classList.remove('active');
            screen.style.display = 'none';
        }
    });

    // Reset desktop content visibility (let CSS handle the rest)
    const contentStack = document.getElementById('content-stack');
    const contentAdd = document.getElementById('content-add');
    const modalSidebar = document.querySelector('.modal-sidebar');

    if (contentStack) contentStack.style.display = '';
    if (contentAdd) contentAdd.style.display = '';
    if (modalSidebar) modalSidebar.style.display = '';
}

function switchTab(view) {
    // Check if mobile
    if (window.innerWidth <= 768) {
        if (view === 'stack') {
            showMobileMyStackScreen();
        } else {
            showMobileAddNewScreen();
        }
        return;
    }

    // Desktop behavior
    // Update Sidebar/Tabs
    document.querySelectorAll('.modal-sidebar-item').forEach(el => el.classList.remove('active'));
    document.getElementById('tab-' + view).classList.add('active');

    // Update Content
    document.getElementById('content-stack').style.display = 'none';
    document.getElementById('content-add').style.display = 'none';

    if (view === 'stack') {
        document.getElementById('content-stack').style.display = 'flex';
    } else {
        document.getElementById('content-add').style.display = 'block';
        renderCardResults(availableCards);
    }
}

function renderCardResults(cards) {
    const container = document.getElementById('card-results-list');
    container.innerHTML = '';

    if (cards.length === 0) {
        container.innerHTML = '<div style="padding: 1rem; color: #94A3B8; text-align: center;">No cards found</div>';
        return;
    }

    cards.forEach(card => {
        const div = document.createElement('div');
        div.className = 'card-result-item';
        div.onclick = () => selectCardForPreview(card, div);

        div.innerHTML = `
            <div style="font-weight: 700; color: #1F2937; margin-bottom: 0.25rem;">${card.name}</div>
            <div style="font-size: 0.85rem; color: #64748B;">${card.issuer}</div>
        `;
        container.appendChild(div);
    });
}

function selectCardForPreview(card, element) {
    // Highlight selection
    document.querySelectorAll('.card-result-item').forEach(el => el.classList.remove('selected'));
    if (element) {
        element.classList.add('selected');
    }

    selectedAddCard = card;

    // Update Preview
    document.getElementById('card-preview-empty').style.display = 'none';
    document.getElementById('card-preview-content').style.display = 'block';

    // Visual
    // Visual
    const visual = document.getElementById('preview-card-visual');
    visual.innerHTML = ''; // Clear previous content
    visual.style.background = 'transparent';
    visual.style.padding = '0';
    visual.style.boxShadow = 'none';

    // Create image
    const img = document.createElement('img');
    img.src = card.image_url || '/static/images/card_placeholder.png'; // Fallback
    img.style.width = '100%';
    img.style.height = 'auto';
    img.style.borderRadius = '12px';
    img.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
    img.alt = card.name;

    visual.appendChild(img);

    // document.getElementById('preview-issuer').innerText = card.issuer.toUpperCase();

    // Render Earning Rates
    const earningContainer = document.getElementById('preview-earning-rates');
    if (earningContainer) {
        try {
            earningContainer.innerHTML = '';

            let earning = card.earning_rates || card.earning || card.rewards_structure || [];
            if (!Array.isArray(earning)) earning = [];

            // Fallback to benefits
            if (earning.length === 0) {
                const benefits = card.benefits || [];
                if (Array.isArray(benefits)) {
                    earning = benefits.filter(b => b && (b.benefit_type === 'Multiplier' || b.benefit_type === 'Cashback')).map(b => ({
                        category: b.short_description || b.name || b.title || b.description,
                        rate: b.numeric_value || b.value || b.multiplier,
                        currency: b.benefit_type === 'Cashback' ? 'cash' : (b.currency || 'points'),
                        details: b.description || b.long_description || b.additional_details
                    }));
                }
            }

            // Filter invalid items
            earning = earning.filter(item => item);

            if (earning.length > 0) {
                earning.sort((a, b) => {
                    const rateA = parseFloat(a.rate || a.value || 0);
                    const rateB = parseFloat(b.rate || b.value || 0);
                    return rateB - rateA;
                });

                earning.forEach(item => {
                    const cat = item.category || item.cat || item.description || 'Category';
                    const rate = parseFloat(item.rate || item.value || 0);
                    const currency = item.currency || 'points';

                    let displayRate;
                    if ((currency && String(currency).toLowerCase().includes('cash')) || (item.benefit_type === 'Cashback')) {
                        displayRate = `${rate}%`;
                    } else {
                        displayRate = `${rate}x`;
                    }

                    const row = document.createElement('div');
                    row.style.cssText = 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; font-size: 0.875rem;';
                    row.innerHTML = `
                        <div style="color: #475569; font-weight: 500;">${cat}</div>
                        <div style="font-weight: 700; color: #0F172A; background: #E0E7FF; color: #4338CA; padding: 0.125rem 0.5rem; border-radius: 4px;">${displayRate}</div>
                    `;
                    earningContainer.appendChild(row);
                });
            } else {
                earningContainer.innerHTML = '<div style="color: #94A3B8; font-size: 0.875rem; font-style: italic;">No earning rates details available.</div>';
            }
        } catch (e) {
            console.error('Error rendering earning rates:', e);
            earningContainer.innerHTML = '<div style="color: #EF4444; font-size: 0.875rem;">Error displaying rates</div>';
        }
    }

    // Render Credits
    const creditsContainer = document.getElementById('preview-credits');
    if (creditsContainer) {
        try {
            creditsContainer.innerHTML = '';

            const benefits = card.benefits || [];
            let filteredBenefits = [];
            if (Array.isArray(benefits)) {
                filteredBenefits = benefits.filter(b => b && b.benefit_type !== 'Multiplier' && b.benefit_type !== 'Cashback');
            }

            // Prioritize explicit credits list if available
            let credits = card.credits;
            if (Array.isArray(credits) && credits.length > 0) {
                // Use credits if available
                filteredBenefits = credits;
            }

            if (filteredBenefits.length > 0) {
                filteredBenefits.forEach((benefit, index) => {
                    if (!benefit) return;

                    const name = benefit.short_description || benefit.name || benefit.title || 'Benefit';
                    const value = benefit.numeric_value || benefit.value || benefit.amount || benefit.dollar_value;
                    let description = benefit.long_description || benefit.description || '';
                    if (benefit.additional_details) {
                        description += (description ? '<br><br>' : '') + benefit.additional_details;
                    }

                    let valueDisplay = String(value);
                    let shouldShow = false;

                    if (value && (typeof value === 'number' || !isNaN(parseFloat(value)))) {
                        if (!valueDisplay.includes('$')) valueDisplay = '$' + valueDisplay;
                        shouldShow = true;
                    } else if (String(value).toLowerCase() === 'included') {
                        valueDisplay = 'Included';
                        shouldShow = true;
                    }

                    // Always show if it's explicitly in 'credits' list, otherwise check value
                    if (shouldShow) {
                        const uniqueId = `preview-credit-${card.id}-${index}`;

                        const row = document.createElement('div');
                        row.onclick = () => {
                            const descEl = document.getElementById(uniqueId);
                            if (descEl) descEl.style.display = descEl.style.display === 'none' ? 'block' : 'none';
                            const icon = document.getElementById(`icon-${uniqueId}`);
                            if (icon) icon.style.transform = icon.style.transform === 'rotate(90deg)' ? 'rotate(0deg)' : 'rotate(90deg)';
                        };
                        row.style.cursor = 'pointer';

                        row.innerHTML = `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.875rem 0; border-bottom: 1px solid #F3F4F6;">
                                <div style="font-weight: 500; color: #1F2937; font-size: 0.95rem; max-width: 65%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${name}</div>
                                <div style="display: flex; align-items: center; gap: 0.75rem;">
                                    <div style="color: #6366F1; font-weight: 700; font-size: 0.95rem;">${valueDisplay}</div>
                                    <span id="icon-${uniqueId}" class="material-icons" style="font-size: 18px; color: #D1D5DB; transition: transform 0.2s;">chevron_right</span>
                                </div>
                            </div>
                            <div id="${uniqueId}" style="display: none; padding: 0 0 1rem 0; color: #64748B; font-size: 0.9rem; line-height: 1.5; border-bottom: 1px solid #F3F4F6;">
                                ${description || 'No description available'}
                            </div>
                        `;
                        creditsContainer.appendChild(row);
                    }
                });
            }

            if (creditsContainer.children.length === 0) {
                creditsContainer.innerHTML = '<div style="color: #94A3B8; font-size: 0.875rem; font-style: italic;">No credits available</div>';
            }
        } catch (e) {
            console.error('Error rendering credits:', e);
            creditsContainer.innerHTML = '<div style="color: #EF4444; font-size: 0.875rem;">Error displaying credits</div>';
        }
    }
}

function filterCards(issuer) {
    let searchIssuer = issuer;
    if (issuer === 'Amex') {
        searchIssuer = 'American Express';
    }
    const filtered = availableCards.filter(c => c.issuer.includes(searchIssuer));
    renderCardResults(filtered);
}

document.getElementById('card-search-input')?.addEventListener('input', (e) => {
    let term = e.target.value.toLowerCase();

    // Alias mapping
    if (term === 'amex') {
        term = 'american express';
    }

    const filtered = availableCards.filter(c =>
        c.name.toLowerCase().includes(term) || c.issuer.toLowerCase().includes(term) ||
        (term === 'amex' && c.issuer.toLowerCase().includes('american express'))
    );
    renderCardResults(filtered);
});

function addSelectedCard() {
    if (!selectedAddCard) return;

    // Open anniversary modal in "add" mode
    // We pass null as cardId to indicate we are adding a new card
    // But we store the selectedAddCard.id in a separate variable or reuse currentAnniversaryCardId with a flag

    currentAnniversaryCardId = 'ADD_NEW_CARD'; // Special flag
    document.getElementById('anniversary-card-name').textContent = selectedAddCard.name;

    // Default to current month
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = String(now.getMonth() + 1).padStart(2, '0');
    const defaultDate = `${currentYear}-${currentMonth}-01`;

    document.getElementById('anniversary-date-input').value = defaultDate;
    document.getElementById('anniversary-modal').style.display = 'flex';
}

// --- Anniversary Modal Logic ---
let currentAnniversaryCardId = null;

function openAnniversaryModal(cardId, cardName, currentDate) {
    currentAnniversaryCardId = cardId;
    document.getElementById('anniversary-card-name').textContent = cardName;
    document.getElementById('anniversary-date-input').value = currentDate || '';
    document.getElementById('anniversary-modal').style.display = 'flex';
}

function closeAnniversaryModal() {
    document.getElementById('anniversary-modal').style.display = 'none';
    currentAnniversaryCardId = null;
}

// --- UI Helpers ---
function showLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) loader.style.display = 'flex';
}

function hideLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) loader.style.display = 'none';
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'error' ? 'error_outline' : 'check_circle';
    toast.innerHTML = `<span class="material-icons">${icon}</span><span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(100%)';
        toast.style.transition = 'all 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- Remove Card Modal Logic ---
let cardToRemoveForm = null;

function openRemoveCardModal(e, form, cardName) {
    if (e) e.preventDefault();
    cardToRemoveForm = form;

    const nameSpan = document.getElementById('remove-card-name');
    if (nameSpan) nameSpan.textContent = cardName;

    const modal = document.getElementById('remove-card-modal');
    if (modal) {
        modal.style.display = 'flex';
        // modal.classList.add('active'); 
    }
    return false;
}

function closeRemoveCardModal() {
    const modal = document.getElementById('remove-card-modal');
    if (modal) {
        modal.style.display = 'none';
        // modal.classList.remove('active');
    }
    cardToRemoveForm = null;
}

async function confirmRemoveCard() {
    if (!cardToRemoveForm) return;
    const form = cardToRemoveForm;
    closeRemoveCardModal();
    await executeRemoveCard(form);
}

async function executeRemoveCard(form) {
    showLoader();
    try {
        const res = await fetch(form.action, { method: 'POST', body: new FormData(form) });
        if (res.ok) {
            showToast('Card removed successfully!');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast('Error removing card', 'error');
            hideLoader();
        }
    } catch (err) {
        console.error(err);
        showToast('Error removing card', 'error');
        hideLoader();
    }
}
// kept for backward compatibility if any button still calls it, but redirects to modal if possible or just executes
async function handleRemoveCard(e, form) {
    // This function shouldn't be called directly anymore by UI, but if so, just execute?
    // Or warn user. Assuming HTML update covers all usages.
    if (e) e.preventDefault();
    return executeRemoveCard(form);
}

function saveAnniversaryDate() {
    const date = document.getElementById('anniversary-date-input').value;
    if (!date) {
        showToast('Please select a date', 'error');
        return;
    }

    // Check if we are adding a new card
    if (currentAnniversaryCardId === 'ADD_NEW_CARD') {
        if (!selectedAddCard) return;

        showLoader();
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        formData.append('anniversary_date', date);

        fetch(`/wallet/add-card/${selectedAddCard.id}/`, {
            method: 'POST',
            body: formData
        })
            .then(response => {
                if (response.ok) {
                    closeAnniversaryModal();
                    showToast('Card added to wallet!');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    throw new Error('Failed to add card');
                }
            })
            .catch(err => {
                console.error('Error:', err);
                showToast('Error adding card', 'error');
                hideLoader();
            });

        return;
    }

    // Otherwise, we are updating an existing card
    showLoader();
    const formData = new FormData();
    formData.append('anniversary_date', date);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch(`/wallet/update-anniversary/${currentAnniversaryCardId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showToast('Anniversary updated!');
                setTimeout(() => location.reload(), 1000);
            } else {
                showToast('Error saving date: ' + (data.error || 'Unknown error'), 'error');
                hideLoader();
            }
        })
        .catch(err => {
            console.error('Error:', err);
            showToast('Error saving date: ' + err.message, 'error');
            hideLoader();
        });
}

// --- Benefit Modal Logic ---
let currentBenefitData = {};
let currentBenefitPeriods = [];
let currentPeriodIndex = 0;

function openBenefitModal(cardId, benefitId, benefitName, amount, used, frequency, periodKey, scriptId) {
    // Parse periods from json_script
    const script = document.getElementById(scriptId);
    if (script) {
        currentBenefitPeriods = JSON.parse(script.textContent);
    } else {
        // Fallback
        currentBenefitPeriods = [{ key: periodKey, label: 'Current', max_value: amount, status: 'unknown' }];
    }

    // Find index
    currentPeriodIndex = currentBenefitPeriods.findIndex(p => p.key === periodKey);
    if (currentPeriodIndex === -1) currentPeriodIndex = 0;

    currentBenefitData = {
        cardId,
        benefitId,
        benefitName,
        amount, // Base amount
        frequency
    };

    updateBenefitModalUI();
    document.getElementById('benefit-modal').style.display = 'flex';
}

function updateBenefitModalUI() {
    const period = currentBenefitPeriods[currentPeriodIndex];
    const maxVal = period.max_value || currentBenefitData.amount;

    let usedVal = 0;
    if (period.status === 'full') {
        usedVal = maxVal;
    } else if (period.key === currentBenefitPeriods.find(p => p.is_current)?.key) {
        usedVal = 0;
    }

    // Update Header
    document.getElementById('benefit-modal-title').textContent = currentBenefitData.benefitName;
    document.getElementById('benefit-modal-subtitle').textContent = `${period.label} Usage`;

    // Update Period Label in Navigator
    document.getElementById('benefit-period-label').textContent = period.label;

    // Update Values
    document.getElementById('benefit-current-used-display').textContent = `$${usedVal}`;
    document.getElementById('benefit-total-value-display').textContent = `$${maxVal}`;

    updateProgress(usedVal, maxVal);

    // Update Input
    document.getElementById('benefit-amount-input').value = '';
    document.getElementById('benefit-amount-input').placeholder = `Remaining: $${maxVal - usedVal}`;

    // Update Mark as Full Button
    const markBtn = document.getElementById('mark-full-btn');
    if (markBtn) {
        markBtn.innerHTML = `Mark <span style="margin: 0 0.25rem;">${period.label}</span> as Full`;
        if (period.status === 'full') {
            markBtn.innerHTML = `<span class="material-icons" style="font-size: 18px; margin-right: 0.5rem;">check</span> ${period.label} is Full`;
            markBtn.disabled = true;
            markBtn.style.opacity = '0.7';
        } else {
            markBtn.disabled = false;
            markBtn.style.opacity = '1';
        }
    }
}

function navigatePeriod(direction) {
    const newIndex = currentPeriodIndex + direction;
    if (newIndex >= 0 && newIndex < currentBenefitPeriods.length) {
        currentPeriodIndex = newIndex;
        updateBenefitModalUI();
    }
}

function closeBenefitModal() {
    document.getElementById('benefit-modal').style.display = 'none';
    currentBenefitData = {};
    currentBenefitPeriods = [];
}

function updateProgress(used, total) {
    const percentage = Math.min(100, Math.max(0, (used / total) * 100));
    document.getElementById('benefit-circular-progress').style.setProperty('--progress', percentage + '%');
}

document.getElementById('benefit-amount-input')?.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value) || 0;
});

function markAsFull() {
    const period = currentBenefitPeriods[currentPeriodIndex];
    const maxVal = period.max_value || currentBenefitData.amount;

    const btn = document.getElementById('mark-full-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="loader"></span> Marking...';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('amount', maxVal);
    formData.append('period_key', period.key);
    formData.append('is_full', 'true');
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch(`/wallet/update-benefit/${currentBenefitData.cardId}/${currentBenefitData.benefitId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error marking as full: ' + error.message);
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

function saveBenefitUsage() {
    const amount = parseFloat(document.getElementById('benefit-amount-input').value);
    if (isNaN(amount) || amount <= 0) return;

    const period = currentBenefitPeriods[currentPeriodIndex];
    const btn = document.getElementById('btn-log-usage');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="loader"></span>';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('amount', amount);
    formData.append('period_key', period.key);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch(`/wallet/update-benefit/${currentBenefitData.cardId}/${currentBenefitData.benefitId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error logging usage: ' + error.message);
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

// Handle window resize to switch between mobile and desktop modal layouts
// Handle window resize to switch between mobile and desktop modal layouts and persist state
// Handle window resize to switch between mobile and desktop modal layouts and persist state
function handleModalResize() {
    const modal = document.getElementById('manage-wallet-modal');
    if (modal && modal.style.display === 'flex') {
        const isMobile = window.innerWidth <= 768;

        const modalSidebar = document.querySelector('.modal-sidebar');
        // Check if sidebar is currently visible to determine if we are coming from Desktop
        // We use offsetParent as a proxy for visibility (null if display:none)
        const wasDesktop = modalSidebar && modalSidebar.offsetParent !== null;

        if (isMobile) {
            // SWITCH TO MOBILE

            if (wasDesktop) {
                // We just crossed from Desktop to Mobile -> SYNC STATE
                const desktopStackTab = document.getElementById('tab-stack');
                const isDesktopStackActive = desktopStackTab && desktopStackTab.classList.contains('active');

                if (isDesktopStackActive) {
                    showMobileMyStackScreen();
                } else {
                    // Add Tab was active
                    if (typeof selectedAddCard !== 'undefined' && selectedAddCard) {
                        showMobileCardDetail(selectedAddCard);
                    } else {
                        showMobileAddNewScreen();
                    }
                }
            }

            // Apply Mobile Layout (Hide Desktop)
            const contentStack = document.getElementById('content-stack');
            const contentAdd = document.getElementById('content-add');

            if (contentStack) contentStack.style.display = 'none';
            if (contentAdd) contentAdd.style.display = 'none';
            if (modalSidebar) modalSidebar.style.display = 'none';

            // Ensure a mobile screen is shown if none (fallback)
            const mobileStack = document.getElementById('mobile-my-stack-screen');
            const mobileAdd = document.getElementById('mobile-add-new-screen');
            const mobileDetail = document.getElementById('mobile-card-detail-screen');

            const isAnyMobileVisible = (mobileStack && mobileStack.style.display !== 'none') ||
                (mobileAdd && mobileAdd.style.display !== 'none') ||
                (mobileDetail && mobileDetail.style.display !== 'none');

            if (!isAnyMobileVisible) {
                showMobileMyStackScreen(); // Default fallback
            }

        } else {
            // SWITCH TO DESKTOP

            if (!wasDesktop) {
                // We just crossed from Mobile to Desktop -> SYNC STATE
                const mobileAdd = document.getElementById('mobile-add-new-screen');
                const mobileDetail = document.getElementById('mobile-card-detail-screen');

                // Check if we were on any Add-related screen
                const isMobileAddActive = mobileAdd && mobileAdd.classList.contains('active');
                const isMobileDetailVisible = mobileDetail && mobileDetail.style.display !== 'none';

                if (isMobileAddActive || isMobileDetailVisible) {
                    switchTab('add');
                    if (typeof selectedAddCard !== 'undefined' && selectedAddCard) {
                        if (typeof selectCardForPreview === 'function') {
                            selectCardForPreview(selectedAddCard, null);
                        }
                    }
                } else {
                    // Default/Stack
                    switchTab('stack');
                }
            }

            // Apply Desktop Layout
            if (modalSidebar) modalSidebar.style.display = 'flex';

            // Hide Mobile Screens
            const mobileScreens = ['mobile-my-stack-screen', 'mobile-add-new-screen', 'mobile-card-detail-screen'];
            mobileScreens.forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    el.style.display = 'none';
                    el.classList.remove('active');
                }
            });
        }
    }
}

window.addEventListener('resize', handleModalResize);
