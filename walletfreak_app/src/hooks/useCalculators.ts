import { useQuery, useMutation } from '@tanstack/react-query';
import {
  getWorthItCards,
  getWorthItQuestions,
  calculateWorthIt,
  getSpendCategories,
  calculateSpendIt,
  calculateSubOptimizer,
  WorthItResponse,
} from '../api/endpoints/calculators';

export const useWorthItCards = () => {
  return useQuery({
    queryKey: ['worthItCards'],
    queryFn: getWorthItCards,
  });
};

export const useWorthItQuestions = (slug: string) => {
  return useQuery({
    queryKey: ['worthItQuestions', slug],
    queryFn: () => getWorthItQuestions(slug),
    enabled: !!slug,
  });
};

export const useCalculateWorthIt = () => {
  return useMutation({
    mutationFn: ({ slug, responses }: { slug: string; responses: WorthItResponse[] }) =>
      calculateWorthIt(slug, responses),
  });
};

export const useSpendCategories = () => {
  return useQuery({
    queryKey: ['spendCategories'],
    queryFn: getSpendCategories,
  });
};

export const useCalculateSpendIt = () => {
  return useMutation({
    mutationFn: ({
      amount,
      category,
      subCategory,
    }: {
      amount: number;
      category: string;
      subCategory?: string;
    }) => calculateSpendIt(amount, category, subCategory),
  });
};

export const useCalculateSubOptimizer = () => {
  return useMutation({
    mutationFn: ({
      planned_spend,
      duration_months,
      sort_by,
    }: {
      planned_spend: number;
      duration_months: number;
      sort_by: string;
    }) => calculateSubOptimizer(planned_spend, duration_months, sort_by),
  });
};
