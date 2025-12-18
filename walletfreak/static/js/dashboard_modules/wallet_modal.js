/**
 * Manage Wallet Modal & Desktop Logic
 */

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

function renderWalletStack() {
    // Helper to find image URL
    const getCardImage = (c) => {
        if (c.image_url && c.image_url.startsWith('http')) return c.image_url;
        // Try to find in allCardsData (source of truth)
        if (typeof allCardsData !== 'undefined') {
            // Check both id and card_id to handle both Firestore and static data formats
            const found = allCardsData.find(ac => ac.id === c.id || ac.id === c.card_id);
            if (found && found.image_url) return found.image_url;
        }
        return '/static/images/card_placeholder.png';
    };

    const generateMobileHtml = (card) => `
        <div class="card-item-container" style="display: flex; align-items: center; gap: 1rem; padding: 1rem; background: white; border: 1px solid #E5E7EB; border-radius: 12px; margin-bottom: 0.75rem;">
            <img src="${getCardImage(card)}" style="width: 60px; height: auto; object-fit: contain; border-radius: 4px;" alt="${card.name}">
            <div style="flex: 1;">
                <div style="font-weight: 700; color: #1F2937; font-size: 1rem; margin-bottom: 0.25rem;">${card.name}</div>
                <div style="color: #64748B; font-size: 0.875rem;">•••• ****</div>
            </div>
            <form method="POST" action="/wallet/remove-card/${card.id}/" style="margin: 0;" onsubmit="return openRemoveCardModal(event, this, '${card.name.replace(/'/g, "\\'")}');">
                <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
                <button type="submit" style="background: none; border: none; color: #CBD5E1; cursor: pointer; padding: 0.5rem;" title="Remove Card">
                    <span class="material-icons" style="font-size: 1.5rem;">delete_outline</span>
                </button>
            </form>
        </div>
    `;

    const generateDesktopHtml = (card) => `
        <div class="card-item-container" style="display: flex; align-items: center; padding: 1.25rem; border: 1px solid #F3F4F6; border-radius: 16px; margin-bottom: 1rem; background: white; transition: all 0.2s;">
            <img src="${getCardImage(card)}" style="width: 60px; height: auto; object-fit: contain; border-radius: 4px; margin-right: 1.25rem;" alt="${card.name}">
            
            <div>
                <div style="font-weight: 700; color: #1F2937; font-size: 1rem;">${card.name}</div>
                <div style="font-size: 0.85rem; color: #94A3B8; font-family: monospace;">•••• ****</div>
            </div>
            
            <div style="margin-left: auto; display: flex; align-items: center; gap: 1rem;">
                <span style="background: #DCFCE7; color: #16A34A; font-size: 0.75rem; font-weight: 700; padding: 0.25rem 0.75rem; border-radius: 99px;">Active</span>
                
                <form method="POST" action="/wallet/remove-card/${card.id}/" style="margin: 0;" onsubmit="return openRemoveCardModal(event, this, '${card.name.replace(/'/g, "\\'")}');">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
                    <button type="submit" class="btn-delete-card" style="background: none; border: none; cursor: pointer; color: #E2E8F0; padding: 0.5rem; transition: color 0.2s;" onmouseover="this.style.color='#EF4444'" onmouseout="this.style.color='#E2E8F0'" title="Remove Card">
                        <span class="material-icons" style="font-size: 20px;">delete_outline</span>
                    </button>
                </form>
            </div>
        </div>
    `;

    // Mobile
    const mobileStackList = document.querySelector('#mobile-my-stack-screen div[style*="overflow-y: auto"]');
    if (mobileStackList) {
        // Clear existing card items (keep the header)
        const header = mobileStackList.querySelector('div[style*="margin-bottom: 1rem"]');
        mobileStackList.innerHTML = '';
        if (header) mobileStackList.appendChild(header);

        if (walletCards.length === 0) {
            mobileStackList.insertAdjacentHTML('beforeend', getEmptyStateHtml());
        } else {
            walletCards.forEach(card => {
                mobileStackList.insertAdjacentHTML('beforeend', generateMobileHtml(card));
            });
        }
    }

    // Desktop
    const desktopStackList = document.querySelector('#content-stack div[style*="overflow-y: auto"]');
    if (desktopStackList) {
        desktopStackList.innerHTML = '';
        if (walletCards.length === 0) {
            desktopStackList.innerHTML = getEmptyStateHtml();
        } else {
            walletCards.forEach(card => {
                desktopStackList.insertAdjacentHTML('beforeend', generateDesktopHtml(card));
            });
        }
    }

    // Refresh Add Card list to update "In Wallet" status if visible
    const searchInput = document.getElementById('card-search-input');
    const contentAdd = document.getElementById('content-add');
    if (contentAdd && contentAdd.style.display !== 'none') {
        const query = searchInput ? searchInput.value : '';
        if (query) {
            searchInput.dispatchEvent(new Event('input'));
        } else {
            renderCardResults(availableCards);
        }
    }
}

function getEmptyStateHtml() {
    return `
        <div style="text-align: center; padding: 4rem 2rem; color: #94A3B8;">
            <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.3;"><span class="material-icons" style="font-size: 48px;">wallet</span></div>
            <p>Your wallet is empty.</p>
            <button onclick="window.innerWidth <= 768 ? showMobileAddNewScreen() : switchTab('add')" style="margin-top: 1rem; padding: 0.75rem 1.5rem; background: #6366F1; color: white; border: none; border-radius: 12px; font-weight: 600; cursor: pointer;">
                Add Your First Card
            </button>
        </div>
    `;
}

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

        if (inWallet) {
            div.style.opacity = '0.6';
            div.style.cursor = 'default';
            div.style.background = '#F9FAFB';
            div.onclick = null; // Disable clicking

            div.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 700; color: #64748B; margin-bottom: 0.25rem;">${card.name}</div>
                        <div style="font-size: 0.85rem; color: #94A3B8;">${card.issuer}</div>
                    </div>
                     <span style="font-size: 0.75rem; font-weight: 700; color: #64748B; background: #E2E8F0; padding: 0.25rem 0.5rem; border-radius: 4px;">In Wallet</span>
                </div>
            `;
        } else {
            div.onclick = () => selectCardForPreview(card, div);
            div.innerHTML = `
                <div style="font-weight: 700; color: #1F2937; margin-bottom: 0.25rem;">${card.name}</div>
                <div style="font-size: 0.85rem; color: #64748B;">${card.issuer}</div>
            `;
        }

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
