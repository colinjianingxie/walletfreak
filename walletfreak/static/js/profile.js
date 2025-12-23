/* Profile Page Logic */

// --- Toast Notification ---
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? 'check' : 'error_outline';

    toast.innerHTML = `
        <div class="toast-icon">
            <span class="material-icons" style="font-size: 16px;">${icon}</span>
        </div>
        <div class="toast-content">${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s forwards';
        setTimeout(() => { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 300);
    }, 3000);
}

// --- Avatar Selection ---
let selectedAvatarSlug = null;

function openAvatarModal() {
    const avatarModal = document.getElementById('avatar-modal');
    avatarModal.style.display = 'flex';
    // Reset selection visual
    document.querySelectorAll('.avatar-option').forEach(el => {
        el.style.borderColor = 'transparent';
        el.style.backgroundColor = 'transparent';
    });
    document.getElementById('btn-save-avatar').disabled = true;
    selectedAvatarSlug = null;
}

function closeAvatarModal() {
    document.getElementById('avatar-modal').style.display = 'none';
}

function selectAvatar(slug) {
    selectedAvatarSlug = slug;

    // Update UI
    document.querySelectorAll('.avatar-option').forEach(el => {
        el.style.borderColor = 'transparent';
        el.style.backgroundColor = 'transparent';
    });

    // Highlight selection
    const selectedEl = document.getElementById(`avatar-option-${slug}`);
    if (selectedEl) {
        selectedEl.style.borderColor = 'var(--primary)';
        selectedEl.style.backgroundColor = 'rgba(16, 185, 129, 0.05)';
    }

    document.getElementById('btn-save-avatar').disabled = false;
}

async function saveAvatar() {
    if (!selectedAvatarSlug) return;

    const btn = document.getElementById('btn-save-avatar');
    const originalText = btn.innerText;
    btn.innerHTML = '<span class="loader"></span> Saving...';
    btn.disabled = true;

    try {
        const response = await fetch(window.PROFILE_CONFIG.urls.sync_profile, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.PROFILE_CONFIG.csrf_token
            },
            body: JSON.stringify({ avatar_slug: selectedAvatarSlug })
        });

        const data = await response.json();

        if (data.status === 'success') {
            showToast('Profile picture updated successfully!');

            // Update preview
            const currentImg = document.getElementById('profile-avatar-display');
            const placeholder = document.getElementById('profile-avatar-placeholder');
            const newSrc = `/static/images/personalities/${selectedAvatarSlug}.png`;

            if (currentImg) {
                currentImg.src = newSrc;
            } else if (placeholder) {
                // Replace placeholder with image
                const container = placeholder.parentElement;
                container.innerHTML = `<img src="${newSrc}" alt="Profile" class="avatar-img" id="profile-avatar-display">`;
            }

            closeAvatarModal();
        } else {
            throw new Error(data.message || 'Failed to update avatar');
        }

    } catch (error) {
        console.error('Error updating avatar:', error);
        showToast(error.message, 'error');
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}


// --- Name Editing ---

function openChangeNameModal() {
    document.getElementById('name-modal').style.display = 'flex';
    const fullName = document.getElementById('profile-name-display').innerText;
    const parts = fullName.split(' ');
    const first = parts[0] || '';
    const last = parts.slice(1).join(' ') || '';

    document.getElementById('new-first-name-input').value = first;
    document.getElementById('new-last-name-input').value = last;
    document.getElementById('new-first-name-input').focus();
}

function closeChangeNameModal() {
    document.getElementById('name-modal').style.display = 'none';
}

async function submitChangeName() {
    const firstName = document.getElementById('new-first-name-input').value.trim();
    const lastName = document.getElementById('new-last-name-input').value.trim();

    if (!firstName) {
        showToast('First name is required.', 'error');
        return;
    }

    const btn = document.getElementById('btn-save-name');
    const originalText = btn.innerText;
    btn.innerHTML = '<span class="loader"></span> Saving...';
    btn.disabled = true;

    try {
        const response = await fetch(window.PROFILE_CONFIG.urls.sync_profile, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.PROFILE_CONFIG.csrf_token },
            body: JSON.stringify({ first_name: firstName, last_name: lastName })
        });
        const data = await response.json();
        if (data.status === 'success') {
            showToast('Name updated successfully!');
            document.getElementById('profile-name-display').innerText = `${firstName} ${lastName}`;
            closeChangeNameModal();
        } else {
            throw new Error(data.message || 'Failed to update name');
        }
    } catch (error) {
        showToast(error.message.replace('Error: ', ''), 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// --- Username Editing ---

function openChangeUsernameModal() {
    document.getElementById('username-modal').style.display = 'flex';
    // Remove the @ if present
    let current = document.getElementById('profile-username-display').innerText.trim();
    if (current.startsWith('@')) current = current.substring(1);

    document.getElementById('new-username-input').value = current;
    document.getElementById('new-username-input').focus();
}

function closeChangeUsernameModal() {
    document.getElementById('username-modal').style.display = 'none';
}

async function submitChangeUsername() {
    const username = document.getElementById('new-username-input').value.trim();

    if (!username || username.length < 3) {
        showToast('Username must be at least 3 characters.', 'error');
        return;
    }

    const btn = document.getElementById('btn-save-username');
    const originalText = btn.innerText;
    btn.innerHTML = '<span class="loader"></span> Saving...';
    btn.disabled = true;

    try {
        const response = await fetch(window.PROFILE_CONFIG.urls.sync_profile, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.PROFILE_CONFIG.csrf_token },
            body: JSON.stringify({ username: username })
        });
        const data = await response.json();
        if (data.status === 'success') {
            showToast('Username updated successfully!');
            document.getElementById('profile-username-display').innerText = `@${username}`;
            closeChangeUsernameModal();
        } else {
            throw new Error(data.message || 'Failed to update username');
        }
    } catch (error) {
        showToast(error.message.replace('Error: ', ''), 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}
// --- Notification Settings Logic ---
let initialPreferences = {};

function initNotificationSettings() {
    // 1. Capture initial state
    captureInitialState();

    // 2. Add event listeners
    document.querySelectorAll('.notification-toggle, .pref-select, #exp-start-days, #exp-repeat-freq').forEach(input => {
        input.addEventListener('change', (e) => {
            handleSettingChange(e.target);
            checkDirtyState();
        });
    });

    // 3. Initialize UI state (disable/enable dependent fields)
    document.querySelectorAll('.notification-toggle').forEach(toggle => {
        updateDependentFields(toggle);
    });
}

function captureInitialState() {
    initialPreferences = {};

    // Toggles
    document.querySelectorAll('.notification-toggle').forEach(toggle => {
        initialPreferences[toggle.dataset.type] = toggle.checked;
    });

    // Selects
    document.querySelectorAll('.pref-select').forEach(select => {
        // Key is compounded for uniqueness if needed, but here simple ID or data-key works
        // Using a composite key: "type:key"
        if (select.dataset.type && select.dataset.key) {
            initialPreferences[`${select.dataset.type}:${select.dataset.key}`] = select.value;
        }
    });

    // Handle specific hardcoded IDs if they don't have data attributes (like benefit expiration)
    const benefitStart = document.getElementById('exp-start-days');
    if (benefitStart) initialPreferences['benefit_expiration:start_days_before'] = benefitStart.value;

    const benefitFreq = document.getElementById('exp-repeat-freq');
    if (benefitFreq) initialPreferences['benefit_expiration:repeat_frequency'] = benefitFreq.value;
}

function handleSettingChange(target) {
    if (target.type === 'checkbox') {
        updateDependentFields(target);
    }
}

function updateDependentFields(toggle) {
    // Logic to disable/enable inputs based on the toggle
    // Specifically for Benefit Expiration and Annual Fee
    const type = toggle.dataset.type;
    const isEnabled = toggle.checked;

    if (type === 'benefit_expiration') {
        const startSelect = document.getElementById('exp-start-days');
        const freqSelect = document.getElementById('exp-repeat-freq');

        if (startSelect) startSelect.disabled = !isEnabled;
        if (freqSelect) freqSelect.disabled = !isEnabled;

        // Add visual disabled state class if needed
        if (startSelect) isEnabled ? startSelect.classList.remove('pref-select-disabled') : startSelect.classList.add('pref-select-disabled');
        if (freqSelect) isEnabled ? freqSelect.classList.remove('pref-select-disabled') : freqSelect.classList.add('pref-select-disabled');

    } else if (type === 'annual_fee') {
        const selects = document.querySelectorAll(`.pref-select[data-type="${type}"]`);
        selects.forEach(s => s.disabled = !isEnabled);
    }
}

function checkDirtyState() {
    let isDirty = false;
    const saveBtn = document.getElementById('btn-save-notifications');

    // Check Toggles
    document.querySelectorAll('.notification-toggle').forEach(toggle => {
        if (initialPreferences[toggle.dataset.type] !== toggle.checked) {
            isDirty = true;
        }
    });

    // Check Selects
    document.querySelectorAll('.pref-select').forEach(select => {
        if (select.dataset.type && select.dataset.key) {
            if (initialPreferences[`${select.dataset.type}:${select.dataset.key}`] !== select.value) {
                isDirty = true;
            }
        }
    });

    // Check IDs
    const benefitStart = document.getElementById('exp-start-days');
    if (benefitStart && initialPreferences['benefit_expiration:start_days_before'] !== benefitStart.value) isDirty = true;

    const benefitFreq = document.getElementById('exp-repeat-freq');
    if (benefitFreq && initialPreferences['benefit_expiration:repeat_frequency'] !== benefitFreq.value) isDirty = true;

    // Update Button
    if (saveBtn) {
        saveBtn.disabled = !isDirty;
        saveBtn.style.opacity = isDirty ? '1' : '0.5';
        saveBtn.style.cursor = isDirty ? 'pointer' : 'not-allowed';
    }
}

async function saveAllPreferences() {
    const btn = document.getElementById('btn-save-notifications');
    const originalText = btn.innerText;
    btn.innerHTML = '<span class="loader"></span> Saving...';
    btn.disabled = true;

    // Build Payload
    const payload = {
        blog_updates: {
            enabled: document.querySelector('.notification-toggle[data-type="blog_updates"]').checked
        },
        benefit_expiration: {
            enabled: document.querySelector('.notification-toggle[data-type="benefit_expiration"]').checked,
            start_days_before: parseInt(document.getElementById('exp-start-days').value),
            repeat_frequency: document.getElementById('exp-repeat-freq').value // Keep as string or float handled by backend
        },
        annual_fee: {
            enabled: document.querySelector('.notification-toggle[data-type="annual_fee"]').checked,
            start_days_before: parseInt(document.querySelector('.pref-select[data-type="annual_fee"][data-key="start_days_before"]').value)
        }
    };

    try {
        const response = await fetch(window.PROFILE_CONFIG.urls.update_notifications, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.PROFILE_CONFIG.csrf_token
            },
            body: JSON.stringify({ preferences: payload })
        });

        const data = await response.json();

        if (data.status === 'success') {
            // Determine user feedback based on whether benefit email is pending
            let msg = 'Preferences saved successfully.';
            if (data.next_email_formatted && payload.benefit_expiration.enabled) {
                msg += ` Next benefit alert: ${data.next_email_formatted}`;
            }

            showToast(msg);

            // Reset state
            captureInitialState();
            checkDirtyState(); // Will disable button

        } else {
            throw new Error(data.message || 'Failed to save preferences');
        }

    } catch (error) {
        console.error('Error saving preferences:', error);
        showToast(error.message, 'error');
    } finally {
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false; // logic in checkDirtyState will re-disable if not dirty, but here we just saved so it should be not dirty
            checkDirtyState();
        }
    }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
    // --- Initialize Modals Close on Outside Click ---
    const modals = [
        document.getElementById('avatar-modal'),
        document.getElementById('name-modal'),
        document.getElementById('username-modal'),
        document.getElementById('email-modal'),
        document.getElementById('settings-saved-modal')
    ];

    modals.forEach(modal => {
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.style.display = 'none';
            });
        }
    });

    // Initialize Notification Settings
    initNotificationSettings();
});

// Modal Close Functions Global Export
function closeChangeEmailModal() {
    document.getElementById('email-modal').style.display = 'none';
}
function openChangeEmailModal() {
    document.getElementById('email-modal').style.display = 'flex';
}
function closeSettingsSavedModal() {
    document.getElementById('settings-saved-modal').style.display = 'none';
}
