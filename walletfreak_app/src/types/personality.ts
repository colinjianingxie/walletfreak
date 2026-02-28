export interface Personality {
  id: string;
  name: string;
  description: string;
  avatar_url: string;
  slots: PersonalitySlot[];
  match_score?: number;
}

export interface PersonalitySlot {
  name: string;
  description: string;
  cards: string[];
}
