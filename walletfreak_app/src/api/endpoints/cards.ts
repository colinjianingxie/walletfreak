import apiClient from '../client';

export interface CardListParams {
  page?: number;
  issuer?: string;
  category?: string;
  min_fee?: number;
  max_fee?: number;
  search?: string;
  sort?: string;
  wallet?: string;
}

export const getCards = async (params?: CardListParams) => {
  const { data } = await apiClient.get('/cards/', { params });
  return data;
};

export const getCardDetail = async (slug: string) => {
  const { data } = await apiClient.get(`/cards/${slug}/`);
  return data;
};
