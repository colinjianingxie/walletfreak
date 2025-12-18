/**
 * Dashboard Core UI Logic
 */

function updateWalletUI() {
    // 1. Render My Stack in Modal (Mobile & Desktop)
    if (typeof renderWalletStack === 'function') {
        renderWalletStack();
    }

    // 2. Update Counts
    const count = walletCards.length;
    document.querySelectorAll('.modal-sidebar .modal-sidebar-item span[style*="background: #E2E8F0"]').forEach(el => el.textContent = count);
    document.querySelectorAll('#mobile-my-stack-tab div div:last-child').forEach(el => el.textContent = count);

    // Update Dropdown Count
    document.querySelectorAll('.user-dropdown-badge').forEach(el => el.textContent = count);

    // 3. Update Available Cards (Global) for Search
    // Filter allCardsData to exclude cards currently in wallet
    if (typeof allCardsData !== 'undefined') {
        const walletCardIds = new Set(walletCards.map(c => c.card_id));
        availableCards = allCardsData.filter(card => !walletCardIds.has(card.id));

        // Refresh the search list if it's visible
        // We use applyMobileFilters() as it handles the rendering and existing filters
        if (typeof applyMobileFilters === 'function') {
            applyMobileFilters();
        }
    }

    // 4. Update Main Dashboard (Partial DOM update)
    if (typeof renderMainDashboardStack === 'function') {
        renderMainDashboardStack();
    }
}

async function updatePersonalityUI(slug, score) {
    const badgeSection = document.getElementById('personality-badge-section');
    if (!badgeSection) return;

    if (!slug) {
        // Fallback or "Add more cards" state
        badgeSection.innerHTML = `
            <span style="color: #94A3B8; font-size: 0.875rem; font-style: italic;">
                <span class="material-icons" style="font-size: 14px; vertical-align: middle; margin-right: 4px;">info</span>
                Add at least 2 cards to discover your freak
            </span>
        `;
        return;
    }

    try {
        // Fetch personality details for the name
        // We could cache this, but it changes rarely
        const pDoc = await db.collection('personalities').doc(slug).get();
        let name = slug;
        if (pDoc.exists) {
            name = pDoc.data().name;
        } else if (slug === 'student-starter') {
            name = "Student Starter"; // Fallback if doc missing
        }

        const html = `
            <a href="/personalities/${slug}/" style="text-decoration: none;">
                <span
                    style="background: #E0F2FE; color: #0284C7; font-size: 0.7rem; font-weight: 700; padding: 0.25rem 0.75rem; border-radius: 4px; letter-spacing: 0.05em; text-transform: uppercase; cursor: pointer; transition: all 0.2s;"
                    onmouseover="this.style.background='#BAE6FD'"
                    onmouseout="this.style.background='#E0F2FE'">
                    <span class="material-icons" style="font-size: 10px; vertical-align: middle;">psychology</span>
                    ${name}
                </span>
            </a>
            ${score ? `<span style="color: #64748B; font-size: 0.9rem;">${score} card${score !== 1 ? 's' : ''} match</span>` : ''}
        `;

        badgeSection.innerHTML = html;

        // Also update dropdown if present
        const dropdownTagline = document.querySelector('.user-dropdown-tagline');
        if (dropdownTagline) {
            let icon = 'auto_awesome'; // default
            if (pDoc.exists && pDoc.data().icon) {
                icon = pDoc.data().icon;
            }

            dropdownTagline.innerHTML = `
                <span class="material-icons" style="font-size: 14px;">${icon}</span>
                ${name}
            `;
        }

    } catch (e) {
        console.error("Error updating personality UI:", e);
    }
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
