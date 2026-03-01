import apiClient from '../client';

export interface WorthItQuestion {
  short_description: string;
  dollar_value: number;
  time_category: string;
  question: string;
  input_type: 'toggle' | 'multiple_choice';
  max_val: number;
  choices: string[];
  weights: number[];
}

export interface WorthItQuestionsResponse {
  card: {
    id: string;
    slug: string;
    name: string;
    issuer: string;
    annual_fee: number;
    image_url?: string;
  };
  benefits: WorthItQuestion[];
}

export interface WorthItResponse {
  index: number;
  value: number;
}

export interface WorthItResult {
  annual_fee: number;
  total_value: number;
  net_profit: number;
  optimization_score: number;
  is_worth_it: boolean;
  verdict: string;
}

export interface SpendCategory {
  name: string;
  icon: string;
  sub_categories: string[];
}

export interface SpendItResultItem {
  slug: string;
  card_name: string;
  issuer: string;
  annual_fee: number;
  est_points: number;
  est_value: number;
  earning_rate: string;
  category_matched: string;
  currency_display: string;
  match_type: string;
  is_winner: boolean;
}

export interface SpendItResult {
  wallet_results: SpendItResultItem[];
  opportunity_results: SpendItResultItem[];
  lost_value: number;
  net_gain: number;
}

export interface WorthItCardItem {
  card_id: string;
  name: string;
  issuer: string;
  annual_fee: number;
}

export const getWorthItCards = async (): Promise<{ cards: WorthItCardItem[] }> => {
  const { data } = await apiClient.get('/calculators/worth-it/cards/');
  return data;
};

export const getWorthItQuestions = async (slug: string): Promise<WorthItQuestionsResponse> => {
  const { data } = await apiClient.get(`/calculators/worth-it/${slug}/questions/`);
  return data;
};

export const calculateWorthIt = async (
  slug: string,
  responses: WorthItResponse[]
): Promise<WorthItResult> => {
  const { data } = await apiClient.post(`/calculators/worth-it/${slug}/calculate/`, {
    responses,
  });
  return data;
};

export const getSpendCategories = async (): Promise<{ categories: SpendCategory[] }> => {
  const { data } = await apiClient.get('/calculators/spend-it/categories/');
  return data;
};

export interface SubOptimizerResult {
  slug: string;
  name: string;
  issuer: string;
  annual_fee: number;
  bonus_display: string;
  bonus_value: number;
  spend_requirement: string;
  ongoing_rate: string;
  total_value: number;
  net_value: number;
  roi: number;
  match_score: number;
  is_top_pick: boolean;
  is_fee_neutral: boolean;
}

export const calculateSubOptimizer = async (
  planned_spend: number,
  duration_months: number,
  sort_by: string
): Promise<{ results: SubOptimizerResult[] }> => {
  const { data } = await apiClient.post('/calculators/sub-optimizer/calculate/', {
    planned_spend,
    duration_months,
    sort_by,
  });
  return data;
};

export const calculateSpendIt = async (
  amount: number,
  category: string,
  subCategory?: string
): Promise<SpendItResult> => {
  const { data } = await apiClient.post('/calculators/spend-it/calculate/', {
    amount,
    category,
    sub_category: subCategory || '',
  });
  return data;
};
