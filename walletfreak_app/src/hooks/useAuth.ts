import { useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';
import { onAuthChanged, getIdToken } from '../firebase/auth';
import { apiLogin } from '../api/endpoints/auth';

export const useAuthListener = () => {
  const { setUser, setProfile, setLoading } = useAuthStore();

  useEffect(() => {
    const unsubscribe = onAuthChanged(async (user) => {
      setUser(user);

      if (user) {
        try {
          const token = await user.getIdToken();
          const response = await apiLogin(token);
          if (response.success) {
            setProfile(response.profile);
          }
        } catch (error) {
          console.error('Failed to sync profile:', error);
        }
      } else {
        setProfile(null);
      }

      setLoading(false);
    });

    return unsubscribe;
  }, [setUser, setProfile, setLoading]);
};
