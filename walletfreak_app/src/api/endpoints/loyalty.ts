import apiClient from '../client';

export const getLoyaltyPrograms = async () => {
  const { data } = await apiClient.get('/loyalty/');
  return data;
};

export const addLoyaltyProgram = async (programId: string) => {
  const { data } = await apiClient.post('/loyalty/add/', { program_id: programId });
  return data;
};

export const updateLoyaltyBalance = async (programId: string, balance: number) => {
  const { data } = await apiClient.post('/loyalty/update/', { program_id: programId, balance });
  return data;
};

export const removeLoyaltyProgram = async (programId: string) => {
  const { data } = await apiClient.post('/loyalty/remove/', { program_id: programId });
  return data;
};
