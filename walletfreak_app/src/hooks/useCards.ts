import { useQuery } from '@tanstack/react-query';
import { getCards, getCardDetail, CardListParams } from '../api/endpoints/cards';

export const useCardList = (params?: CardListParams) => {
  return useQuery({
    queryKey: ['cards', params],
    queryFn: () => getCards(params),
  });
};

export const useCardDetail = (slug: string) => {
  return useQuery({
    queryKey: ['card', slug],
    queryFn: () => getCardDetail(slug),
    enabled: !!slug,
  });
};
