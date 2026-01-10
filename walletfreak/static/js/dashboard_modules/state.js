/**
 * Dashboard State & Listeners
 */

// Initialize Firestore
// Initialize Firestore
// Initialize Firestore
// Use a unique name to avoid conflict with base.html's const db
var firestoreDb = firebase.firestore();

// Ensure global variables for cleanup (HTMX re-runs this script)
if (window.walletListenerUnsubscribe) {
    window.walletListenerUnsubscribe();
    window.walletListenerUnsubscribe = null;
}
if (window.userListenerUnsubscribe) {
    window.userListenerUnsubscribe();
    window.userListenerUnsubscribe = null;
}

// Reset local reference
var walletCards = [];

// Initialize tooltips or other interactive elements if needed
document.addEventListener('DOMContentLoaded', function () {
    // any initialization logic
});

// MAIN ENTRY POINT
// Check if user is already known (synchronously/cached)
if (firebase.auth().currentUser) {
    // Immediate trigger for SPA navigation speed
    setupWalletListener(firebase.auth().currentUser.uid);
}

// Also set up observer for auth state changes (initial load / login / logout)
firebase.auth().onAuthStateChanged((user) => {
    if (user) {
        setupWalletListener(user.uid);
    } else {
        // Handle signed out state if needed
        if (window.walletListenerUnsubscribe) {
            window.walletListenerUnsubscribe();
            window.walletListenerUnsubscribe = null;
        }
    }
});

function setupWalletListener(uid) {
    if (!uid) return;

    // Clean up existing listener if any (e.g. from immediate check vs async check)
    if (window.walletListenerUnsubscribe) {
        window.walletListenerUnsubscribe();
    }

    console.log("Setting up Wallet Listener for:", uid);

    window.walletListenerUnsubscribe = firestoreDb.collection('users').doc(uid).collection('user_cards')
        .where('status', '==', 'active') // Only listen for active cards for the stack
        .onSnapshot((snapshot) => {

            const cards = [];
            snapshot.forEach((doc) => {
                cards.push({ id: doc.id, ...doc.data() });
            });

            walletCards = cards;

            // Make sure walletCards is available globally for other modules if they need it directly?
            // ui_core.js seems to rely on 'walletCards' variable being in scope. 
            // Since they are concatenated scripts, they share the same scope?
            // Actually, if modules are separate script tags, high-level vars in 'state.js' ARE global if not in a module/IIFE.
            // But 'let walletCards' at top level of a script is NOT global window property.
            // It is global scope for specific script block? 
            // Wait, independent script tags in HTML share the global 'window' scope, but 'let'/'const' are block scoped?
            // 'let' at top level of script tag is NOT attached to window, but IS available to subsequent scripts?
            // No. 'let' at top level of a module/script is global if type="text/javascript" (default) but strictly speaking:
            // "In non-module scripts, var declarations become properties of the global object. let and const do not."
            // BUT they are in the global scope chain.
            // HOWEVER, if 'ui_core.js' tries to access 'walletCards', it needs it to be defined.
            // 'state.js' defines `let walletCards`.
            // 'ui_core.js' runs AFTER 'state.js'.
            // They are separate script tags.
            // Variables declared with 'let' in one script tag are NOT visible in another script tag if they are sharing the same scope? 
            // actually they ARE visible if they are in the global scope. 
            // WAIT. "let" in the top level of a script is global scope, but not window property.
            // So `updateWalletUI` in `ui_core.js` SHOULD see `walletCards` from `state.js`.
            // UNLESS `state.js` is failing.

            // Just to be safe, let's attach to window as well or ensure updateWalletUI can access it.
            // But assuming it worked before, it should work now.

            // Call the UI updater (defined in ui_core.js)
            if (typeof updateWalletUI === 'function') {
                updateWalletUI();
            } else {
                console.warn("updateWalletUI function not found yet.");
            }
        }, (error) => {
            console.error("Error listening to wallet updates:", error);

        });

    // Also setup user listener for personality
    setupUserListener(uid);
}

function setupUserListener(uid) {
    if (!uid) return;

    if (window.userListenerUnsubscribe) {
        window.userListenerUnsubscribe();
    }

    window.userListenerUnsubscribe = firestoreDb.collection('users').doc(uid)
        .onSnapshot(async (doc) => {
            if (!doc.exists) return;


            const data = doc.data();
            const personalitySlug = data.assigned_personality;
            const score = data.personality_score || 0;

            if (typeof updatePersonalityUI === 'function') {
                updatePersonalityUI(personalitySlug, score);
            }
        }, (error) => {
            console.error("Error listening to user profile:", error);
        });
}
