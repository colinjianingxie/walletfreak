export interface LoyaltyProgram {
  program_id: string;
  name: string;
  type: 'miles' | 'points' | 'cash' | 'other';
  balance: number;
  valuation: number;
  est_value: number;
  logo_url: string;
  category: string;
}
