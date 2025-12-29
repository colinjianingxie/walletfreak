// Anniversary Date Logic
let currentEditCardId = null;

function openEditAnniversaryModal(event, userCardId, currentDate = null) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }

    currentEditCardId = userCardId;

    // If currentDate argument is missing, try to find it from the DOM element (button) that triggered event
    // or look up by ID if we can guess the button ID
    let initialDate = currentDate;

    if (!initialDate && event && event.currentTarget) {
        initialDate = event.currentTarget.dataset.anniversaryDate;
    }

    if (!initialDate) {
        // Fallback: try to find button by ID
        const btn = document.getElementById(`anniversary-edit-btn-${userCardId}`);
        if (btn) {
            initialDate = btn.dataset.anniversaryDate;
        }
    }

    // Populate the date input
    const dateInput = document.getElementById('edit-anniversary-date-input');
    const defaultDisplay = document.getElementById('edit-anniversary-default-display');
    const unknownBtn = document.getElementById('btn-unknown-anniversary');

    if (dateInput) {
        // If initialDate is 'default'
        if (initialDate === 'default') {
            setAnniversaryDefault();
        } else {
            // Check if initialDate is empty or 'None'
            if (!initialDate || initialDate === 'None' || initialDate === '') {
                // If no date, user can set one, or click I don't know
                // Ideally default to today if they are setting a specific date
                dateInput.value = new Date().toISOString().split('T')[0];
            } else {
                dateInput.value = initialDate;
            }
            clearAnniversaryDefault(); // Ensure default mode is off
        }
    }

    // Show the modal
    const modal = document.getElementById('edit-anniversary-modal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function setAnniversaryDefault() {
    const dateInput = document.getElementById('edit-anniversary-date-input');
    const defaultDisplay = document.getElementById('edit-anniversary-default-display');
    const unknownBtn = document.getElementById('btn-unknown-anniversary');
    const dateText = document.getElementById('edit-anniversary-default-date-display-text');

    if (dateInput) {
        dateInput.value = ''; // Clear value
        dateInput.style.display = 'none';
        dateInput.required = false;
    }
    if (defaultDisplay) defaultDisplay.style.display = 'flex';
    if (unknownBtn) unknownBtn.style.display = 'none';

    // Set dynamic date text
    if (dateText) {
        const prevYear = new Date().getFullYear() - 1;
        dateText.innerText = `1/1/${prevYear}`;
    }
}

function clearAnniversaryDefault() {
    const dateInput = document.getElementById('edit-anniversary-date-input');
    const defaultDisplay = document.getElementById('edit-anniversary-default-display');
    const unknownBtn = document.getElementById('btn-unknown-anniversary');

    if (dateInput) {
        dateInput.style.display = 'block';
        // Set to today if empty
        if (!dateInput.value) {
            dateInput.value = new Date().toISOString().split('T')[0];
        }
    }
    if (defaultDisplay) defaultDisplay.style.display = 'none';
    if (unknownBtn) unknownBtn.style.display = 'flex';
}

function closeEditAnniversaryModal() {
    const modal = document.getElementById('edit-anniversary-modal');
    if (modal) {
        modal.style.display = 'none';
        currentEditCardId = null;
    }
}

function confirmAnniversaryUpdate() {
    if (!currentEditCardId) return;

    const dateInput = document.getElementById('edit-anniversary-date-input');
    const defaultDisplay = document.getElementById('edit-anniversary-default-display');

    let newDate = null;

    // Check if in "default" mode
    if (defaultDisplay && defaultDisplay.style.display !== 'none') {
        newDate = 'default';
    } else {
        newDate = dateInput.value;
        if (!newDate) {
            alert("Please select a date.");
            return;
        }
        // Validate date format
        if (!/^\d{4}-\d{2}-\d{2}$/.test(newDate)) {
            alert("Invalid date format. Please use YYYY-MM-DD.");
            return;
        }
    }

    updateAnniversaryDate(currentEditCardId, newDate);
}

function updateAnniversaryDate(userCardId, newDate) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Show global loader
    if (typeof showLoader === 'function') {
        showLoader();
    }

    // Show loading state on button (keep as backup)
    const confirmBtn = document.querySelector('#edit-anniversary-modal button[onclick="confirmAnniversaryUpdate()"]');
    const originalText = confirmBtn.innerText;
    confirmBtn.innerText = 'Updating...';
    confirmBtn.disabled = true;

    fetch(`/wallet/update-anniversary/${userCardId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: `anniversary_date=${newDate}`
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                closeEditAnniversaryModal();

                if (typeof showToast === 'function') {
                    showToast('Anniversary date updated', 'success');
                }

                // Reload the page to refresh benefit calculations
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            } else {
                alert('Failed to update anniversary date: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while updating the anniversary date.');
        })
        .finally(() => {
            // Hide global loader
            if (typeof hideLoader === 'function') {
                hideLoader();
            }

            // Restore button state
            if (confirmBtn) {
                confirmBtn.innerText = originalText;
                confirmBtn.disabled = false;
            }
        });
}

// Close modal when clicking outside
window.addEventListener('click', function (event) {
    const modal = document.getElementById('edit-anniversary-modal');
    if (event.target === modal) {
        closeEditAnniversaryModal();
    }
});
