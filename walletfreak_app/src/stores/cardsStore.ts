import { create } from 'zustand';
import { CreditCard } from '../types/card';

interface CardsState {
  cards: CreditCard[];
  issuers: string[];
  categories: string[];
  selectedCards: string[]; // for compare

  setCards: (cards: CreditCard[]) => void;
  setIssuers: (issuers: string[]) => void;
  setCategories: (categories: string[]) => void;
  toggleCompareCard: (cardId: string) => void;
  clearCompare: () => void;
}

export const useCardsStore = create<CardsState>((set) => ({
  cards: [],
  issuers: [],
  categories: [],
  selectedCards: [],

  setCards: (cards) => set({ cards }),
  setIssuers: (issuers) => set({ issuers }),
  setCategories: (categories) => set({ categories }),
  toggleCompareCard: (cardId) =>
    set((state) => {
      if (state.selectedCards.includes(cardId)) {
        return { selectedCards: state.selectedCards.filter((id) => id !== cardId) };
      }
      if (state.selectedCards.length >= 4) return state;
      return { selectedCards: [...state.selectedCards, cardId] };
    }),
  clearCompare: () => set({ selectedCards: [] }),
}));
