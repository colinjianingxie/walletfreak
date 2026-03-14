export interface PremiumProgramMatch {
  matched: boolean;
  name: string;
  credit?: string;
  early_checkin?: string;
  free_breakfast?: string;
  late_checkout?: string;
  room_upgrade?: string;
  brand?: string;
  chase_2026_credit?: boolean;
  michelin_keys?: string;
}

export interface PremiumPrograms {
  amex_fhr: PremiumProgramMatch | null;
  amex_thc: PremiumProgramMatch | null;
  chase_edit: PremiumProgramMatch | null;
}

export interface PriceHistory {
  prior_avg: number;
  prior_count: number;
  last_rate: number;
  last_observed_at: string;
}

export interface HotelSearchResult {
  place_id: string;
  name: string;
  rating: number;
  user_rating_count: number;
  price_level: number; // 0-4
  photo_url: string | null;
  address: string;
  brand: string;
  brand_class: string;
  program_id: string;
  program_name: string;
  rate_per_night: number | null;
  rate_display: string;
  total_rate: number | null;
  premium_programs: PremiumPrograms;
  json_data: string; // JSON string of hotel data for strategy submission
  price_history?: PriceHistory;
  is_cached?: boolean;
  cached_at?: string;
}

export interface StrategyOption {
  type: string;
  label: string;
  sub_label: string;
  strategy_summary: string;
  upfront: number | null;
  upfront_currency: string;
  effective: number | null;
  effective_currency: string;
  earning_nominal: number | null;
  earning_nominal_currency: string;
  earning_value: number | null;
  icon: string;
  card_slug: string | null;
  hotel_loyalty: string | null;
  earning_rate: number;
  earning_description: string | null;
  premium_program?: string; // 'amex_fhr' | 'amex_thc' | 'chase_edit'
  premium_benefits?: string[];
}

export interface HotelAnalysis {
  hotel_id: string;
  hotel_name: string;
  star_rating: string;
  cash_price: number;
  recommended_strategy: StrategyOption;
  all_options: StrategyOption[];
}

export interface BookingStrategy {
  id: string;
  location_text: string;
  check_in: string;
  check_out: string;
  guests: string;
  hotel_count: number;
  status: 'processing' | 'ready' | 'failed';
  analysis_results: HotelAnalysis[];
  created_at?: string;
}

export interface BookingStrategyListItem {
  id: string;
  location_text: string;
  check_in: string;
  check_out: string;
  guests: string;
  hotel_count: number;
  status: 'processing' | 'ready' | 'failed';
  created_at?: string;
}
