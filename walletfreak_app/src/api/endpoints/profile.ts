import apiClient from '../client';

export const getProfile = async () => {
  const { data } = await apiClient.get('/profile/');
  return data;
};

export const syncProfile = async (updates: {
  email?: string;
  first_name?: string;
  last_name?: string;
  username?: string;
  avatar_slug?: string;
}) => {
  const { data } = await apiClient.post('/profile/sync/', updates);
  return data;
};

export const updateNotifications = async (preferences: Record<string, any>) => {
  const { data } = await apiClient.post('/profile/notifications/', { preferences });
  return data;
};
