import cardImageMap from '../assets/cardImageMap';
import personalityImageMap from '../assets/personalityImageMap';

export function getCardImage(slug: string): any | null {
  return cardImageMap[slug] ?? null;
}

export function getPersonalityImage(slug: string): any | null {
  return personalityImageMap[slug] ?? null;
}
