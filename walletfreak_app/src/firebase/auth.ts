import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
  sendEmailVerification,
  signOut,
  onAuthStateChanged,
  User,
  GoogleAuthProvider,
  signInWithCredential,
} from 'firebase/auth';
import { firebaseAuth } from './config';

export const loginWithEmail = (email: string, password: string) =>
  signInWithEmailAndPassword(firebaseAuth, email, password);

export const registerWithEmail = async (email: string, password: string) => {
  const credential = await createUserWithEmailAndPassword(firebaseAuth, email, password);
  await sendEmailVerification(credential.user);
  return credential;
};

export const resetPassword = (email: string) =>
  sendPasswordResetEmail(firebaseAuth, email);

export const resendVerification = async () => {
  const user = firebaseAuth.currentUser;
  if (user) {
    await sendEmailVerification(user);
  }
};

export const logout = () => signOut(firebaseAuth);

export const getIdToken = async (): Promise<string | null> => {
  const user = firebaseAuth.currentUser;
  if (!user) return null;
  return user.getIdToken();
};

export const onAuthChanged = (callback: (user: User | null) => void) =>
  onAuthStateChanged(firebaseAuth, callback);

export const loginWithGoogleCredential = async (idToken: string) => {
  const credential = GoogleAuthProvider.credential(idToken);
  return signInWithCredential(firebaseAuth, credential);
};

// Google OAuth client IDs
export const GOOGLE_WEB_CLIENT_ID = '99478632058-t7t9qrbug3hm2k20mv7tu1gh3apb08d7.apps.googleusercontent.com';
export const GOOGLE_IOS_CLIENT_ID = '99478632058-htadqp97ehht9um8b5sp3r83jklitv9q.apps.googleusercontent.com';
