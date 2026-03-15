import apiClient from '../client';

export const getWallet = async () => {
  const { data } = await apiClient.get('/wallet/');
  return data;
};

export const addCard = async (cardId: string, status = 'active', anniversaryDate?: string) => {
  const { data } = await apiClient.post(`/wallet/add-card/${cardId}/`, {
    status,
    anniversary_date: anniversaryDate,
  });
  return data;
};

export const removeCard = async (userCardId: string, deleteLoyalty = false) => {
  const { data } = await apiClient.post(`/wallet/remove-card/${userCardId}/`, {
    delete_loyalty_program: deleteLoyalty,
  });
  return data;
};

export const updateCardStatus = async (userCardId: string, status: string) => {
  const { data } = await apiClient.post(`/wallet/update-status/${userCardId}/`, { status });
  return data;
};

export const updateAnniversary = async (userCardId: string, anniversaryDate: string) => {
  const { data } = await apiClient.post(`/wallet/update-anniversary/${userCardId}/`, {
    anniversary_date: anniversaryDate,
  });
  return data;
};

export const updateBenefitUsage = async (
  userCardId: string,
  benefitId: string,
  amount: number,
  periodKey: string,
  isFull = false,
  increment = false
) => {
  const { data } = await apiClient.post(
    `/wallet/update-benefit/${userCardId}/${benefitId}/`,
    { amount, period_key: periodKey, is_full: isFull, increment }
  );
  return data;
};

export const toggleIgnoreBenefit = async (
  userCardId: string,
  benefitId: string,
  isIgnored: boolean
) => {
  const { data } = await apiClient.post(
    `/wallet/toggle-ignore-benefit/${userCardId}/${benefitId}/`,
    { is_ignored: isIgnored }
  );
  return data;
};

export const checkDeleteConsequences = async (userCardId: string) => {
  const { data } = await apiClient.get(`/wallet/check-delete/${userCardId}/`);
  return data;
};

export const syncWallet = async () => {
  const { data } = await apiClient.post('/wallet/sync/');
  return data;
};

export const getWalletChangelogs = async () => {
  const { data } = await apiClient.get('/wallet/changelogs/');
  return data;
};
