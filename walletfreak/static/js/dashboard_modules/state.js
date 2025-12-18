/**
 * Dashboard State & Listeners
 */

// Initialize Firestore
const db = firebase.firestore();
let walletCards = [];
let walletListenerUnsubscribe = null;
let userListenerUnsubscribe = null;

// Initialize tooltips or other interactive elements if needed
document.addEventListener('DOMContentLoaded', function () {
    // any initialization logic
});

// Wait for Firebase Auth to be ready before setting up listener
// This prevents "insufficient permissions" errors on page load
firebase.auth().onAuthStateChanged((user) => {
    if (user) {
        // user.uid matches currentUserUid ideally
        setupWalletListener();
    } else {
        // Handle signed out state if needed
        if (walletListenerUnsubscribe) {
            walletListenerUnsubscribe();
            walletListenerUnsubscribe = null;
        }
    }
});

function setupWalletListener() {
    if (!currentUserUid) return;

    if (walletListenerUnsubscribe) {
        walletListenerUnsubscribe();
    }

    walletListenerUnsubscribe = db.collection('users').doc(currentUserUid).collection('user_cards')
        .where('status', '==', 'active') // Only listen for active cards for the stack
        .onSnapshot((snapshot) => {
            console.log("Wallet update received:", snapshot.size, "docs");
            const cards = [];
            snapshot.forEach((doc) => {
                cards.push({ id: doc.id, ...doc.data() });
            });

            walletCards = cards;
            updateWalletUI();
        }, (error) => {
            console.error("Error listening to wallet updates:", error);
            console.log("Current User UID (Django):", currentUserUid);
            console.log("Current User UID (Auth):", firebase.auth().currentUser ? firebase.auth().currentUser.uid : 'null');
        });

    // Also setup user listener for personality
    setupUserListener();
}

function setupUserListener() {
    if (!currentUserUid) return;

    if (userListenerUnsubscribe) {
        userListenerUnsubscribe();
    }

    userListenerUnsubscribe = db.collection('users').doc(currentUserUid)
        .onSnapshot(async (doc) => {
            if (!doc.exists) return;
            console.log("User listener updated:", doc.data()); // Debug log

            const data = doc.data();
            const personalitySlug = data.assigned_personality;
            const score = data.personality_score || 0;

            updatePersonalityUI(personalitySlug, score);
        }, (error) => {
            console.error("Error listening to user profile:", error);
        });
}
