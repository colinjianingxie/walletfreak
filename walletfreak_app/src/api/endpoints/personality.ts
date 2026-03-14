import apiClient from '../client';

export const getPersonalities = async () => {
  const { data } = await apiClient.get('/personalities/');
  return data;
};

export const getPersonalityDetail = async (slug: string) => {
  const { data } = await apiClient.get(`/personalities/${slug}/`);
  return data;
};

export const submitQuiz = async (personalityId: string, score: number) => {
  const { data } = await apiClient.post('/personalities/submit/', {
    personality_id: personalityId,
    score,
  });
  return data;
};
