import apiClient from '../client';

export const createCheckoutSession = async (priceId: string) => {
  const { data } = await apiClient.post('/subscriptions/checkout/', {
    price_id: priceId,
    success_url: 'walletfreak://subscription/success?session_id={CHECKOUT_SESSION_ID}',
    cancel_url: 'walletfreak://subscription/cancel',
  });
  return data;
};

export const createPortalSession = async () => {
  const { data } = await apiClient.post('/subscriptions/portal/');
  return data;
};

export const getSubscriptionStatus = async () => {
  const { data } = await apiClient.get('/subscriptions/status/');
  return data;
};
