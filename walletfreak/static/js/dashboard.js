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

// Mobile screen management functions
function showMobileMyStackScreen() {
    document.getElementById('mobile-my-stack-screen').style.display = 'flex';
    document.getElementById('mobile-add-new-screen').style.display = 'none';
    document.getElementById('mobile-card-detail-screen').style.display = 'none';
}

function showMobileAddNewScreen() {
    document.getElementById('mobile-my-stack-screen').style.display = 'none';
    document.getElementById('mobile-add-new-screen').style.display = 'flex';
    document.getElementById('mobile-card-detail-screen').style.display = 'none';
    
    // Load cards when showing add new screen
    loadMobileCards();
}

function showMobileCardDetailScreen() {
    document.getElementById('mobile-my-stack-screen').style.display = 'none';
    document.getElementById('mobile-add-new-screen').style.display = 'none';
    document.getElementById('mobile-card-detail-screen').style.display = 'flex';
}

function backToMobileSearch() {
    showMobileAddNewScreen();
}

// Mobile card loading and filtering
function loadMobileCards() {
    // This would typically load cards from an API
    // For now, we'll create some sample cards
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
    
    cards.forEach(card => {
        const cardElement = document.createElement('div');
        cardElement.style.cssText = `
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.75rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
        `;
        
        cardElement.innerHTML = `
            <div>
                <div style="font-weight: 700; color: #1F2937; font-size: 1rem; margin-bottom: 0.25rem;">${card.name}</div>
                <div style="font-size: 0.875rem; color: #64748B;">${card.issuer}</div>
            </div>
            <span class="material-icons" style="color: #CBD5E1; font-size: 20px;">chevron_right</span>
        `;
        
        cardElement.onclick = () => showMobileCardDetail(card);
        container.appendChild(cardElement);
    });
}

function filterMobileCards(issuer) {
    // Filter logic would go here
    console.log('Filtering by:', issuer);
}

function showMobileCardDetail(card) {
    showMobileCardDetailScreen();
    
    const container = document.getElementById('mobile-card-detail-screen');
    container.innerHTML = `
        <div style="height: 100vh; overflow-y: auto; background: white;">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; background: white; position: relative;">
                <h1 style="font-size: 1.5rem; font-weight: 700; color: #1F2937; margin: 0;">Manage Wallet</h1>
                <button onclick="closeManageWalletModal()" style="background: none; border: none; color: #64748B; font-size: 1.5rem; cursor: pointer; padding: 0.5rem; position: absolute; top: 1rem; right: 1rem;">×</button>
            </div>
            
            <!-- Tab Navigation -->
            <div style="padding: 1.5rem; background: white;">
                <div style="display: flex; gap: 1rem;">
                    <button onclick="showMobileMyStackScreen()" style="flex: 1; background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 1rem; display: flex; align-items: center; gap: 0.75rem; cursor: pointer; color: #6366F1; font-weight: 600;">
                        <span class="material-icons" style="font-size: 24px;">account_balance_wallet</span>
                        <div>
                            <div style="font-size: 0.875rem; font-weight: 500;">My Stack</div>
                            <div style="font-size: 1.25rem; font-weight: 700;">3</div>
                        </div>
                    </button>
                    
                    <button style="flex: 1; background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 1rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem; color: #6366F1; font-weight: 600; cursor: pointer;">
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
                <div style="width: 100%; max-width: 100%; margin: 0; border-radius: 16px; background: linear-gradient(135deg, #6366F1, #8B5CF6); padding: 1.25rem; color: white; box-shadow: 0 8px 24px rgba(99, 102, 241, 0.25);">
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
                <button style="background: #6366F1; width: 100%; padding: 1rem; border-radius: 12px; color: white; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 0.5rem; cursor: pointer; border: none; font-size: 1rem;">
                    <span class="material-icons">add</span> Add to Wallet
                </button>
            </div>

            <!-- Earning Rates -->
            <div style="padding: 0 1.5rem; margin-bottom: 1.5rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                    <span class="material-icons" style="font-size: 16px; color: #94A3B8;">trending_up</span>
                    <div style="font-size: 0.75rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.1em; text-transform: uppercase;">EARNING RATES</div>
                </div>
                <div style="background: white; border-radius: 12px; overflow: hidden;">
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.875rem 0; border-bottom: 1px solid #F3F4F6;">
                        <div style="font-weight: 600; color: #1F2937; font-size: 1rem;">Travel</div>
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <div style="color: #2563EB; font-weight: 700; font-size: 1rem;">2x</div>
                            <span class="material-icons" style="font-size: 18px; color: #D1D5DB;">expand_more</span>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.875rem 0; border-bottom: 1px solid #F3F4F6;">
                        <div style="font-weight: 600; color: #1F2937; font-size: 1rem;">Dining</div>
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <div style="color: #2563EB; font-weight: 700; font-size: 1rem;">3x</div>
                            <span class="material-icons" style="font-size: 18px; color: #D1D5DB;">expand_more</span>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.875rem 0;">
                        <div style="font-weight: 600; color: #1F2937; font-size: 1rem;">Streaming</div>
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <div style="color: #2563EB; font-weight: 700; font-size: 1rem;">3x</div>
                            <span class="material-icons" style="font-size: 18px; color: #D1D5DB;">expand_more</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Initialize tooltips or other interactive elements if needed
document.addEventListener('DOMContentLoaded', function () {
    // Any initialization logic
});
