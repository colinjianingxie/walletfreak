import { create } from 'zustand';
import { UserCard, BenefitDisplay } from '../types/card';

interface WalletState {
  activeCards: UserCard[];
  inactiveCards: UserCard[];
  eyeingCards: UserCard[];
  actionNeededBenefits: BenefitDisplay[];
  maxedOutBenefits: BenefitDisplay[];
  ignoredBenefits: BenefitDisplay[];
  totalExtractedValue: number;
  totalPotentialValue: number;
  totalAnnualFee: number;
  netPerformance: number;
  chase524Count: number;
  isLoading: boolean;

  setWalletData: (data: Partial<WalletState>) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

export const useWalletStore = create<WalletState>((set) => ({
  activeCards: [],
  inactiveCards: [],
  eyeingCards: [],
  actionNeededBenefits: [],
  maxedOutBenefits: [],
  ignoredBenefits: [],
  totalExtractedValue: 0,
  totalPotentialValue: 0,
  totalAnnualFee: 0,
  netPerformance: 0,
  chase524Count: 0,
  isLoading: true,

  setWalletData: (data) => set(data),
  setLoading: (isLoading) => set({ isLoading }),
  reset: () =>
    set({
      activeCards: [],
      inactiveCards: [],
      eyeingCards: [],
      actionNeededBenefits: [],
      maxedOutBenefits: [],
      ignoredBenefits: [],
      totalExtractedValue: 0,
      totalPotentialValue: 0,
      totalAnnualFee: 0,
      netPerformance: 0,
      chase524Count: 0,
      isLoading: true,
    }),
}));
