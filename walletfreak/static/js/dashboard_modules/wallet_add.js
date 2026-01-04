/**
 * Wallet Filter & Search (Add Card View) Logic
 */

// State for desktop persistence
let currentDesktopFilter = 'All';
let currentDesktopSearch = '';

function renderCardResults(cards) {
    const container = document.getElementById('card-results-list');
    container.innerHTML = '';

    if (cards.length === 0) {
        container.innerHTML = '<div style="padding: 1rem; color: #94A3B8; text-align: center;">No cards found</div>';
        return;
    }

    cards.forEach(card => {
        // Check if card is already in wallet
        // walletCards is a global array maintained by listener
        const inWallet = typeof walletCards !== 'undefined' && walletCards.some(wc => wc.id === card.id || wc.card_id === card.id);

        const div = document.createElement('div');
        div.className = 'card-result-item';

        // Helper to find image URL (same as renderWalletStack)
        const getCardImage = (c) => {
            if (c.image_url && c.image_url.startsWith('http')) return c.image_url;
            // Try to find in allCardsData (source of truth) if available, though 'card' here should be from availableCards
            if (c.image_url) return c.image_url;
            return '/static/images/card_placeholder.png';
        };

        if (inWallet) {
            div.style.opacity = '0.6';
            div.style.cursor = 'default';
            div.style.background = '#F9FAFB';
            div.onclick = null; // Disable clicking

            div.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                         <img src="${getCardImage(card)}" style="width: 40px; height: auto; object-fit: contain; border-radius: 4px;" alt="${card.name}">
                        <div>
                            <div style="font-weight: 700; color: #64748B; margin-bottom: 0.125rem;">${card.name}</div>
                            <div style="font-size: 0.85rem; color: #94A3B8;">${card.issuer}</div>
                        </div>
                    </div>
                     <span style="font-size: 0.75rem; font-weight: 700; color: #64748B; background: #E2E8F0; padding: 0.25rem 0.5rem; border-radius: 4px;">In Wallet</span>
                </div>
            `;
        } else {
            div.onclick = () => selectCardForPreview(card, div);
            div.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <img src="${getCardImage(card)}" style="width: 40px; height: auto; object-fit: contain; border-radius: 4px;" alt="${card.name}">
                    <div>
                        <div style="font-weight: 700; color: #1F2937; margin-bottom: 0.125rem;">${card.name}</div>
                        <div style="font-size: 0.85rem; color: #64748B;">${card.issuer}</div>
                    </div>
                </div>
            `;
        }

        container.appendChild(div);
    });
}

function filterCards(issuer, resetSearch = true) {
    currentDesktopFilter = issuer;

    // Update active state
    document.querySelectorAll('.quick-add-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.id === `desktop-filter-${issuer}`) {
            btn.classList.add('active');
        }
    });

    // Clear search if requested
    const searchInput = document.getElementById('card-search-input');
    if (resetSearch && searchInput) {
        searchInput.value = '';
        currentDesktopSearch = '';
    }

    // Apply combined filter: Search + Category
    let filtered = availableCards;

    // 1. Text Search (if any)
    if (currentDesktopSearch) {
        let term = currentDesktopSearch.toLowerCase();
        if (term === 'amex') term = 'american express';

        filtered = filtered.filter(c =>
            c.name.toLowerCase().includes(term) || c.issuer.toLowerCase().includes(term) ||
            (term === 'amex' && c.issuer.toLowerCase().includes('american express'))
        );
    }

    // 2. Issuer Filter
    if (issuer !== 'All') {
        let searchIssuer = issuer;
        if (issuer === 'Amex') {
            searchIssuer = 'American Express';
        }
        filtered = filtered.filter(c => c.issuer.includes(searchIssuer));
    }

    renderCardResults(filtered);
}

// Global search listener setup
document.addEventListener('DOMContentLoaded', () => {
    // We attach listener this way or assume inline, but inline ? checks are safer.
    const searchInput = document.getElementById('card-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            let term = e.target.value.toLowerCase();
            currentDesktopSearch = term;

            // We can rely on filterCards to do the combination logic, but we need to trigger it with current filter
            // Pass false to not reset the search we just typed
            filterCards(currentDesktopFilter, false);
        });
    }
});
