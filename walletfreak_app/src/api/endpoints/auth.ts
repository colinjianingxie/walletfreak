import apiClient from '../client';

export interface UserProfile {
  uid: string;
  email: string;
  first_name: string;
  last_name: string;
  username: string;
  is_premium: boolean;
  assigned_personality: string | null;
  photo_url: string | null;
}

export interface LoginResponse {
  success: boolean;
  profile: UserProfile;
}

export const apiLogin = async (idToken: string): Promise<LoginResponse> => {
  const { data } = await apiClient.post('/auth/login/', { id_token: idToken });
  return data;
};
