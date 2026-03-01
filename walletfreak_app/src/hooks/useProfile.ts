import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProfile, syncProfile, updateNotifications } from '../api/endpoints/profile';

export const useProfile = () => {
  return useQuery({
    queryKey: ['profile'],
    queryFn: getProfile,
  });
};

export const useSyncProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: syncProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
  });
};

export const useUpdateNotifications = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateNotifications,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
  });
};
