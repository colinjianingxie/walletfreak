export interface CreditCard {
  id: string;
  name: string;
  slug: string;
  issuer: string;
  annual_fee: number;
  image_url: string;
  benefits: Benefit[];
  earning_rates: EarningRate[];
  rewards_structure: any[];
  credits: any[];
  welcome_bonus: string;
  welcome_offer: string;
  signup_bonus: string;
  welcome_requirement: string;
  is_524: boolean;
  loyalty_program: string | null;
  category: string;
  in_wallet?: boolean;
  match_score?: number;
}

export interface Benefit {
  id: string;
  description: string;
  dollar_value: number;
  benefit_type: string;
  time_category: string;
  period_values: Record<string, number>;
  additional_details?: string;
}

export interface EarningRate {
  category: string;
  rate: string;
  description: string;
}

export interface UserCard {
  id: string;
  user_card_id: string;
  card_id: string;
  status: 'active' | 'inactive' | 'eyeing';
  anniversary_date: string;
  benefit_usage: Record<string, BenefitUsage>;
  // Hydrated fields
  name: string;
  issuer: string;
  annual_fee: number;
  image_url: string;
  benefits: Benefit[];
  loyalty_program: string | null;
}

export interface BenefitUsage {
  periods: Record<string, PeriodUsage>;
  is_ignored: boolean;
  last_updated?: any;
}

export interface PeriodUsage {
  used: number;
  is_full: boolean;
}

export interface BenefitDisplay {
  user_card_id: string;
  card_id: string;
  card_name: string;
  benefit_id: string;
  benefit_name: string;
  amount: number;
  used: number;
  periods: PeriodDisplay[];
  frequency: string;
  current_period_status: 'empty' | 'partial' | 'full';
  days_until_expiration: number | null;
  is_ignored: boolean;
  ytd_used: number;
  additional_details?: string;
  benefit_type?: string;
}

export interface PeriodDisplay {
  label: string;
  key: string;
  status: 'empty' | 'partial' | 'full';
  is_current: boolean;
  max_value: number;
  is_available: boolean;
  used: number;
  reset_date?: string;
}
