import { useQuery, useMutation } from '@tanstack/react-query';
import {
  createCheckoutSession,
  createPortalSession,
  getSubscriptionStatus,
} from '../api/endpoints/subscriptions';

export const useSubscriptionStatus = () => {
  return useQuery({
    queryKey: ['subscription-status'],
    queryFn: getSubscriptionStatus,
  });
};

export const useCreateCheckout = () => {
  return useMutation({
    mutationFn: (priceId: string) => createCheckoutSession(priceId),
  });
};

export const useCreatePortal = () => {
  return useMutation({
    mutationFn: () => createPortalSession(),
  });
};
