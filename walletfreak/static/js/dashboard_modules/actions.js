/**
 * User Actions (API Calls & Forms)
 */

// --- Anniversary Modal Logic ---
let currentAnniversaryCardId = null;

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
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Failed to add card');
                }
            })
            .then(data => {
                if (data.success) {
                    closeAnniversaryModal();
                    showToast('Card added to wallet!');

                    // Update Personality if returned
                    if (data.personality) {
                        updatePersonalityUI(data.personality.id, data.personality.match_score);
                    }

                    // Re-render search results if search is active or just refresh list
                    const searchInput = document.getElementById('card-search-input');
                    if (searchInput && searchInput.value) {
                        searchInput.dispatchEvent(new Event('input'));
                    } else if (typeof availableCards !== 'undefined') {
                        renderCardResults(availableCards);
                    }

                    // Explicitly hide loader since we aren't reloading
                    hideLoader();

                    // Reset the preview state so it doesn't persist if user adds another card
                    if (typeof resetCardPreview === 'function') {
                        resetCardPreview();
                    }

                    // switch back to stack view to show the new card
                    if (window.innerWidth <= 768) {
                        showMobileMyStackScreen();
                    } else {
                        switchTab('stack');
                    }
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
        const formData = new FormData(form);
        formData.append('ajax', 'true'); // Explicitly signal AJAX in case headers fail

        const res = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (res.ok) {
            const data = await res.json();

            if (data.success) {
                showToast('Card removed successfully!');
                hideLoader();

                // Update Personality if returned
                if (data.personality) {
                    updatePersonalityUI(data.personality.id, data.personality.match_score);
                }

                // 2. Find the container row to remove
                const cardRow = form.closest('.card-item-container');
                if (cardRow) {
                    // Animate removal
                    cardRow.style.transition = 'all 0.3s ease';
                    cardRow.style.opacity = '0';
                    cardRow.style.transform = 'translateX(20px)';

                    // Optimistic UI: Update local state and re-render
                    setTimeout(() => {
                        // Extract ID from action "/wallet/remove-card/XYZ/"
                        const actionParts = form.action.split('/');
                        const cardId = actionParts[actionParts.length - 2] || actionParts[actionParts.length - 1];

                        if (cardId) {
                            walletCards = walletCards.filter(c => c.id !== cardId);
                            updateWalletUI();
                        } else {
                            // Fallback if ID parse fails
                            cardRow.remove();
                            // update count manually if needed, or just let listener handle it
                        }
                    }, 300);

                } else {
                    // Fallback
                    // The listener will catch up
                }
            } else {
                showToast('Error removing card: ' + (data.error || 'Unknown'), 'error');
                hideLoader();
            }
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
