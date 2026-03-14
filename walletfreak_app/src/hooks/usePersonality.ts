import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getPersonalities,
  getPersonalityDetail,
  submitQuiz,
} from '../api/endpoints/personality';

export const usePersonalities = () => {
  return useQuery({
    queryKey: ['personalities'],
    queryFn: getPersonalities,
  });
};

export const usePersonalityDetail = (slug: string) => {
  return useQuery({
    queryKey: ['personality', slug],
    queryFn: () => getPersonalityDetail(slug),
    enabled: !!slug,
  });
};

export const useSubmitQuiz = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ personalityId, score }: { personalityId: string; score: number }) =>
      submitQuiz(personalityId, score),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['personalities'] });
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
    },
  });
};
