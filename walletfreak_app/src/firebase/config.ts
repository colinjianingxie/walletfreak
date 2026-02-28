import { initializeApp, getApps } from 'firebase/app';
import { initializeAuth, getAuth } from 'firebase/auth';
// @ts-expect-error - getReactNativePersistence is exported at runtime
import { getReactNativePersistence } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import AsyncStorage from '@react-native-async-storage/async-storage';

const firebaseConfig = {
  apiKey: 'AIzaSyDZ4JTnyOBlkXoRlR7FbiQs6nPrwRlixEM',
  authDomain: 'walletfreak-cc.firebaseapp.com',
  projectId: 'walletfreak-cc',
  storageBucket: 'walletfreak-cc.firebasestorage.app',
  messagingSenderId: '99478632058',
  appId: '1:99478632058:web:410490ffab3e4011426dc3',
  measurementId: 'G-DJSZXRZH6V',
};

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

let firebaseAuth: ReturnType<typeof getAuth>;
try {
  firebaseAuth = initializeAuth(app, {
    persistence: getReactNativePersistence(AsyncStorage),
  });
} catch {
  // Already initialized
  firebaseAuth = getAuth(app);
}

export { firebaseAuth };
export const firebaseDb = getFirestore(app);
export default app;
