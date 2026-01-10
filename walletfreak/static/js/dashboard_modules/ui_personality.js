/**
 * UI Personality Badge Logic
 */

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
        const pDoc = await firestoreDb.collection('personalities').doc(slug).get();
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
