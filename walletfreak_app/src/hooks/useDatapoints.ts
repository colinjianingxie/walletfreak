import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDatapoints,
  submitDatapoint,
  voteDatapoint,
  DatapointListParams,
} from '../api/endpoints/datapoints';

export const useDatapoints = (params?: DatapointListParams) => {
  return useQuery({
    queryKey: ['datapoints', params],
    queryFn: () => getDatapoints(params),
  });
};

export const useSubmitDatapoint = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: submitDatapoint,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datapoints'] });
    },
  });
};

export const useVoteDatapoint = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => voteDatapoint(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datapoints'] });
    },
  });
};
