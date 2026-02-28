import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getWallet,
  addCard,
  removeCard,
  updateCardStatus,
  updateAnniversary,
  updateBenefitUsage,
  toggleIgnoreBenefit,
  checkDeleteConsequences,
} from '../api/endpoints/wallet';

export const useWallet = () => {
  return useQuery({
    queryKey: ['wallet'],
    queryFn: getWallet,
  });
};

export const useAddCard = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      cardId,
      status,
      anniversaryDate,
    }: {
      cardId: string;
      status?: string;
      anniversaryDate?: string;
    }) => addCard(cardId, status, anniversaryDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
    },
  });
};

export const useRemoveCard = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      userCardId,
      deleteLoyalty,
    }: {
      userCardId: string;
      deleteLoyalty?: boolean;
    }) => removeCard(userCardId, deleteLoyalty),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
    },
  });
};

export const useUpdateCardStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userCardId, status }: { userCardId: string; status: string }) =>
      updateCardStatus(userCardId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
    },
  });
};

export const useUpdateAnniversary = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      userCardId,
      anniversaryDate,
    }: {
      userCardId: string;
      anniversaryDate: string;
    }) => updateAnniversary(userCardId, anniversaryDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
    },
  });
};

export const useUpdateBenefit = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      userCardId,
      benefitId,
      amount,
      periodKey,
      isFull,
      increment,
    }: {
      userCardId: string;
      benefitId: string;
      amount: number;
      periodKey: string;
      isFull?: boolean;
      increment?: boolean;
    }) => updateBenefitUsage(userCardId, benefitId, amount, periodKey, isFull, increment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
    },
  });
};

export const useToggleIgnoreBenefit = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      userCardId,
      benefitId,
      isIgnored,
    }: {
      userCardId: string;
      benefitId: string;
      isIgnored: boolean;
    }) => toggleIgnoreBenefit(userCardId, benefitId, isIgnored),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
    },
  });
};

export const useCheckDelete = (userCardId: string) => {
  return useQuery({
    queryKey: ['check-delete', userCardId],
    queryFn: () => checkDeleteConsequences(userCardId),
    enabled: !!userCardId,
  });
};
