import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getLoyaltyPrograms,
  addLoyaltyProgram,
  updateLoyaltyBalance,
  removeLoyaltyProgram,
} from '../api/endpoints/loyalty';

export const useLoyaltyPrograms = () => {
  return useQuery({
    queryKey: ['loyalty'],
    queryFn: getLoyaltyPrograms,
  });
};

export const useAddLoyaltyProgram = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (programId: string) => addLoyaltyProgram(programId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loyalty'] });
    },
  });
};

export const useUpdateLoyaltyBalance = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ programId, balance }: { programId: string; balance: number }) =>
      updateLoyaltyBalance(programId, balance),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loyalty'] });
    },
  });
};

export const useRemoveLoyaltyProgram = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (programId: string) => removeLoyaltyProgram(programId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loyalty'] });
    },
  });
};
