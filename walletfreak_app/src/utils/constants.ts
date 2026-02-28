export const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const CARD_IMAGE_BASE_URL = 'https://walletfreak.com/static/images/cards/';

export const PERSONALITY_IMAGE_BASE_URL =
  'https://walletfreak.com/static/images/personalities/';

export const TAB_ICONS = {
  wallet: 'wallet-outline',
  explore: 'credit-card-search-outline',
  community: 'account-group-outline',
  tools: 'calculator-variant-outline',
  profile: 'account-circle-outline',
} as const;

export const CARD_STATUSES = ['active', 'inactive', 'eyeing'] as const;

export const BENEFIT_TYPES = [
  'Credit',
  'Perk',
  'Protection',
  'Bonus',
  'Lounge',
  'Status',
  'Insurance',
] as const;
