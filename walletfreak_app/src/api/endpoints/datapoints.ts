import apiClient from '../client';

export interface DatapointListParams {
  page?: number;
  page_size?: number;
  sort?: string;
  card?: string;
  benefit?: string;
}

export const getDatapoints = async (params?: DatapointListParams) => {
  const { data } = await apiClient.get('/datapoints/', { params });
  return data;
};

export const submitDatapoint = async (payload: {
  card_id: string;
  benefit: string;
  data: string;
}) => {
  const { data } = await apiClient.post('/datapoints/', payload);
  return data;
};

export const voteDatapoint = async (id: string) => {
  const { data } = await apiClient.post(`/datapoints/${id}/vote/`);
  return data;
};
