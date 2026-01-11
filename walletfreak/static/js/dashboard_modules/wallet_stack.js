/**
 * Wallet Stack View Logic
 */

function renderWalletStack() {
    // Helper to get master card details
    // User cards from Firestore only contain status/anniversary. We need to join with master data (allCardsData) for name/image.
    const getMasterCard = (c) => {
        let master = null;
        if (typeof allCardsData !== 'undefined') {
            // Check both id and card_id to handle both Firestore and static data formats
            master = allCardsData.find(ac => ac.id === c.id || ac.id === c.card_id);
        }
        // Merge user card data (c) over master data to preserve user-specifics like anniversary
        // We explicitly take name/image from master if available
        return master ? { ...master, ...c, name: master.name, image_url: master.image_url } : c;
    };

    const generateMobileHtml = (rawCard) => {
        const card = getMasterCard(rawCard);
        return `
        <div class="card-item-container" style="display: flex; align-items: center; gap: 1rem; padding: 1rem; background: white; border: 1px solid #E5E7EB; border-radius: 12px; margin-bottom: 0.75rem;">
            <img src="${card.image_url || '/static/images/card_placeholder.png'}" style="width: 60px; height: auto; object-fit: contain; border-radius: 4px;" alt="${card.name}">
            <div style="flex: 1;">
                <div style="font-weight: 700; color: #1F2937; font-size: 1rem; margin-bottom: 0.25rem;">${card.name || 'Unknown Card'}</div>
                <div style="color: #64748B; font-size: 0.875rem;">•••• ****</div>
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem; font-size: 0.8rem; color: #64748B;">
                    <span class="material-icons" style="font-size: 14px; opacity: 0.7;">event</span>
                    <span>Anniversary: <strong>${card.anniversary_date || "Not set"}</strong></span>
                    <button type="button" class="btn-edit-date" onclick="openEditAnniversaryModal(event, '${card.id}', '${card.anniversary_date || ''}')" style="background: none; border: none; cursor: pointer; color: #6366F1; padding: 0.125rem; display: flex; align-items: center;" title="Edit Anniversary Date">
                        <span class="material-icons" style="font-size: 14px;">edit</span>
                    </button>
                </div>
            </div>
            <form method="POST" action="/wallet/remove-card/${card.id}/" style="margin: 0;" onsubmit="return openRemoveCardModal(event, this, '${(card.name || '').replace(/'/g, "\\'")}', '${card.id}');">
                <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
                <button type="submit" style="background: none; border: none; color: #CBD5E1; cursor: pointer; padding: 0.5rem;" title="Remove Card">
                    <span class="material-icons" style="font-size: 1.5rem;">delete_outline</span>
                </button>
            </form>
        </div>
    `;
    };

    const generateDesktopHtml = (rawCard) => {
        const card = getMasterCard(rawCard);
        return `
        <div class="card-item-container" style="display: flex; align-items: center; padding: 1.25rem; border: 1px solid #F3F4F6; border-radius: 16px; margin-bottom: 1rem; background: white; transition: all 0.2s;">
            <img src="${card.image_url || '/static/images/card_placeholder.png'}" style="width: 60px; height: auto; object-fit: contain; border-radius: 4px; margin-right: 1.25rem;" alt="${card.name}">
            
            <div>
                <div style="font-weight: 700; color: #1F2937; font-size: 1rem;">${card.name || 'Unknown Card'}</div>
                <div style="font-size: 0.85rem; color: #94A3B8; font-family: monospace;">•••• ****</div>
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem; font-size: 0.8rem; color: #64748B;">
                    <span class="material-icons" style="font-size: 14px; opacity: 0.7;">event</span>
                    <span>Anniversary: <strong>${card.anniversary_date || "Not set"}</strong></span>
                    <button type="button" class="btn-edit-date" onclick="openEditAnniversaryModal(event, '${card.id}', '${card.anniversary_date || ''}')" style="background: none; border: none; cursor: pointer; color: #6366F1; padding: 0.125rem; display: flex; align-items: center;" title="Edit Anniversary Date">
                        <span class="material-icons" style="font-size: 14px;">edit</span>
                    </button>
                </div>
            </div>
            
            <div style="margin-left: auto; display: flex; align-items: center; gap: 1rem;">
                <span style="background: #DCFCE7; color: #16A34A; font-size: 0.75rem; font-weight: 700; padding: 0.25rem 0.75rem; border-radius: 99px;">Active</span>
                
                <form method="POST" action="/wallet/remove-card/${card.id}/" style="margin: 0;" onsubmit="return openRemoveCardModal(event, this, '${(card.name || '').replace(/'/g, "\\'")}', '${card.id}');">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
                    <button type="submit" class="btn-delete-card" style="background: none; border: none; cursor: pointer; color: #E2E8F0; padding: 0.5rem; transition: color 0.2s;" onmouseover="this.style.color='#EF4444'" onmouseout="this.style.color='#E2E8F0'" title="Remove Card">
                        <span class="material-icons" style="font-size: 20px;">delete_outline</span>
                    </button>
                </form>
            </div>
        </div>
    `;
    };

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
            // Apply current filter if any
            if (typeof filterCards === 'function' && typeof currentDesktopFilter !== 'undefined') {
                filterCards(currentDesktopFilter, false);
            }
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
