import {
  collection,
  doc,
  getDoc,
  getDocs,
  query,
  where,
  onSnapshot,
  Unsubscribe,
} from 'firebase/firestore';
import { firebaseDb } from './config';

export const getUserProfile = async (uid: string) => {
  const docRef = doc(firebaseDb, 'users', uid);
  const docSnap = await getDoc(docRef);
  if (docSnap.exists()) {
    return { id: docSnap.id, ...docSnap.data() };
  }
  return null;
};

export const subscribeToUserCards = (
  uid: string,
  callback: (cards: any[]) => void
): Unsubscribe => {
  const cardsRef = collection(firebaseDb, 'users', uid, 'user_cards');
  return onSnapshot(cardsRef, (snapshot) => {
    const cards = snapshot.docs.map((doc) => ({
      id: doc.id,
      ...doc.data(),
    }));
    callback(cards);
  });
};

export const subscribeToUserProfile = (
  uid: string,
  callback: (profile: any) => void
): Unsubscribe => {
  const docRef = doc(firebaseDb, 'users', uid);
  return onSnapshot(docRef, (snapshot) => {
    if (snapshot.exists()) {
      callback({ id: snapshot.id, ...snapshot.data() });
    }
  });
};
