import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  autocompleteLocation,
  searchHotels,
  analyzeBooking,
  getStrategies,
  getStrategy,
  getStrategyStatus,
  deleteStrategy,
} from '../api/endpoints/booking';

export const useLocationAutocomplete = (query: string) => {
  return useQuery({
    queryKey: ['locationAutocomplete', query],
    queryFn: () => autocompleteLocation(query),
    enabled: query.length >= 2,
    staleTime: 60000,
  });
};

export const useHotelSearch = (
  location: string,
  checkIn?: string,
  checkOut?: string,
  guests?: string
) => {
  return useQuery({
    queryKey: ['hotelSearch', location, checkIn, checkOut, guests],
    queryFn: () => searchHotels(location, checkIn, checkOut, guests),
    enabled: !!location,
  });
};

export const useAnalyzeBooking = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      selectedHotels,
      location,
      checkIn,
      checkOut,
      guests,
    }: {
      selectedHotels: Record<string, any>[];
      location: string;
      checkIn: string;
      checkOut: string;
      guests: string;
    }) => analyzeBooking(selectedHotels, location, checkIn, checkOut, guests),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookingStrategies'] });
    },
  });
};

export const useStrategies = (pollWhileProcessing = false) => {
  return useQuery({
    queryKey: ['bookingStrategies'],
    queryFn: getStrategies,
    refetchInterval: (query) => {
      if (!pollWhileProcessing) return false;
      const hasProcessing = query.state.data?.strategies?.some(
        (s) => s.status === 'processing'
      );
      return hasProcessing ? 5000 : false;
    },
  });
};

export const useStrategy = (id: string, pollWhileProcessing = true) => {
  return useQuery({
    queryKey: ['bookingStrategy', id],
    queryFn: () => getStrategy(id),
    enabled: !!id,
    refetchInterval: (query) => {
      if (!pollWhileProcessing) return false;
      const status = query.state.data?.status;
      return status === 'processing' ? 3000 : false;
    },
  });
};

export const useDeleteStrategy = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteStrategy(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookingStrategies'] });
    },
  });
};

export const useStrategyStatus = (id: string) => {
  return useQuery({
    queryKey: ['strategyStatus', id],
    queryFn: () => getStrategyStatus(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'processing' ? 3000 : false;
    },
  });
};
