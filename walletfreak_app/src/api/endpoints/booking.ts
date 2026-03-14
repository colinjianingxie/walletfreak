import apiClient from '../client';
import type {
  HotelSearchResult,
  BookingStrategy,
  BookingStrategyListItem,
} from '../../types/booking';

export interface LocationSuggestion {
  text: string;
  place_id: string;
}

export const autocompleteLocation = async (
  query: string
): Promise<{ suggestions: LocationSuggestion[] }> => {
  const { data } = await apiClient.get('/booking/autocomplete/', {
    params: { query },
  });
  return data;
};

export const searchHotels = async (
  location: string,
  checkIn?: string,
  checkOut?: string,
  guests?: string
): Promise<{ hotels: HotelSearchResult[] }> => {
  const params: Record<string, string> = { location };
  if (checkIn) params.check_in = checkIn;
  if (checkOut) params.check_out = checkOut;
  if (guests) params.guests = guests;

  const { data } = await apiClient.get('/booking/search/', { params });
  return data;
};

export const analyzeBooking = async (
  selectedHotels: Record<string, any>[],
  location: string,
  checkIn: string,
  checkOut: string,
  guests: string
): Promise<{ strategy_id: string; status: string }> => {
  const { data } = await apiClient.post('/booking/analyze/', {
    selected_hotels: selectedHotels,
    location,
    check_in: checkIn,
    check_out: checkOut,
    guests,
  });
  return data;
};

export const getStrategies = async (): Promise<{ strategies: BookingStrategyListItem[] }> => {
  const { data } = await apiClient.get('/booking/strategies/');
  return data;
};

export const getStrategy = async (id: string): Promise<BookingStrategy> => {
  const { data } = await apiClient.get(`/booking/strategies/${id}/`);
  return data;
};

export const getStrategyStatus = async (id: string): Promise<{ status: string }> => {
  const { data } = await apiClient.get(`/booking/strategies/${id}/status/`);
  return data;
};

export const deleteStrategy = async (id: string): Promise<{ success: boolean }> => {
  const { data } = await apiClient.delete(`/booking/strategies/${id}/`);
  return data;
};
