export interface Personality {
  id: string;
  name: string;
  description: string;
  avatar_url: string;
  tagline?: string;
  rules?: { title: string; description: string }[];
  categories?: string[];
  slots: PersonalitySlot[];
  match_score?: number;
}

export interface PersonalitySlot {
  name: string;
  description: string;
  cards: string[];
  hydrated_cards?: HydratedCard[];
}

export interface HydratedCard {
  id: string;
  name: string;
  issuer: string;
  annual_fee: number;
  image_url: string;
  slug?: string;
}
