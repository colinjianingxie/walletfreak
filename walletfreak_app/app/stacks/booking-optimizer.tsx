import React, { useState, useCallback } from 'react';
import { View, StyleSheet, FlatList, Pressable, Platform, Modal } from 'react-native';
import { Text, TextInput, Button, useTheme, FAB } from 'react-native-paper';
import { useRouter } from 'expo-router';
import DateTimePicker from '@react-native-community/datetimepicker';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { PremiumGate } from '../../src/components/layout/PremiumGate';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { HotelCard } from '../../src/components/booking/HotelCard';
import { useHotelSearch, useAnalyzeBooking, useLocationAutocomplete } from '../../src/hooks/useBooking';
import type { HotelSearchResult } from '../../src/types/booking';

export default function BookingOptimizerScreen() {
  const theme = useTheme();
  const router = useRouter();

  const [location, setLocation] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [guests, setGuests] = useState('1');
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Dates
  const today = new Date();
  const defaultCheckIn = new Date(today);
  defaultCheckIn.setDate(today.getDate() + 1);
  const defaultCheckOut = new Date(today);
  defaultCheckOut.setDate(today.getDate() + 3);

  const [checkIn, setCheckIn] = useState(defaultCheckIn);
  const [checkOut, setCheckOut] = useState(defaultCheckOut);
  const [showCheckIn, setShowCheckIn] = useState(false);
  const [showCheckOut, setShowCheckOut] = useState(false);

  // Selection
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const formatDateStr = (d: Date) => d.toISOString().split('T')[0];
  const formatDisplayDate = (d: Date) =>
    d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

  // Autocomplete
  const { data: autocompleteData } = useLocationAutocomplete(
    showSuggestions ? location : ''
  );
  const suggestions = autocompleteData?.suggestions ?? [];

  // Search query
  const { data, isLoading, isError } = useHotelSearch(
    searchQuery,
    formatDateStr(checkIn),
    formatDateStr(checkOut),
    guests
  );
  const hotels = data?.hotels ?? [];

  // Analyze mutation
  const analyzeMutation = useAnalyzeBooking();

  const handleLocationChange = (text: string) => {
    setLocation(text);
    setShowSuggestions(text.length >= 2);
  };

  const handleSelectSuggestion = (text: string) => {
    setLocation(text);
    setShowSuggestions(false);
  };

  const handleSearch = () => {
    if (location.trim()) {
      setShowSuggestions(false);
      setSelectedIds(new Set());
      setSearchQuery(location.trim());
    }
  };

  const toggleSelect = useCallback((placeId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(placeId)) {
        next.delete(placeId);
      } else {
        next.add(placeId);
      }
      return next;
    });
  }, []);

  const handleAnalyze = async () => {
    const selectedHotels = hotels
      .filter((h) => selectedIds.has(h.place_id))
      .map((h) => JSON.parse(h.json_data));

    try {
      await analyzeMutation.mutateAsync({
        selectedHotels,
        location: searchQuery,
        checkIn: formatDateStr(checkIn),
        checkOut: formatDateStr(checkOut),
        guests,
      });
      router.push('/stacks/booking-history' as any);
    } catch {
      // Error handled by mutation state
    }
  };

  const renderHotel = useCallback(
    ({ item }: { item: HotelSearchResult }) => (
      <HotelCard
        hotel={item}
        selected={selectedIds.has(item.place_id)}
        onToggle={() => toggleSelect(item.place_id)}
      />
    ),
    [selectedIds, toggleSelect]
  );

  return (
    <PremiumGate feature="Booking Optimizer">
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        {/* Search Form */}
        <View style={styles.searchForm}>
          <View style={{ zIndex: 10 }}>
            <TextInput
              mode="outlined"
              label="Destination"
              placeholder="e.g. Miami, NYC, Paris"
              value={location}
              onChangeText={handleLocationChange}
              onSubmitEditing={handleSearch}
              onFocus={() => location.length >= 2 && setShowSuggestions(true)}
              left={<TextInput.Icon icon="map-marker" />}
              style={styles.input}
            />

            {/* Autocomplete Dropdown */}
            {showSuggestions && suggestions.length > 0 && (
              <View style={[styles.suggestionsDropdown, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outline }]}>
                {suggestions.map((s, idx) => (
                  <Pressable
                    key={s.place_id || idx}
                    onPress={() => handleSelectSuggestion(s.text)}
                    style={[styles.suggestionItem, idx < suggestions.length - 1 && styles.suggestionBorder]}
                  >
                    <MaterialCommunityIcons name="map-marker-outline" size={16} color={theme.colors.onSurfaceVariant} />
                    <Text style={[styles.suggestionText, { color: theme.colors.onSurface }]} numberOfLines={1}>
                      {s.text}
                    </Text>
                  </Pressable>
                ))}
              </View>
            )}
          </View>

          {/* Dates Row */}
          <View style={styles.dateRow}>
            <Pressable
              style={[styles.dateButton, { borderColor: theme.colors.outline }]}
              onPress={() => setShowCheckIn(true)}
            >
              <MaterialCommunityIcons name="calendar" size={16} color={theme.colors.onSurfaceVariant} />
              <Text style={styles.dateText}>{formatDisplayDate(checkIn)}</Text>
            </Pressable>
            <MaterialCommunityIcons name="arrow-right" size={16} color={theme.colors.onSurfaceVariant} />
            <Pressable
              style={[styles.dateButton, { borderColor: theme.colors.outline }]}
              onPress={() => setShowCheckOut(true)}
            >
              <MaterialCommunityIcons name="calendar" size={16} color={theme.colors.onSurfaceVariant} />
              <Text style={styles.dateText}>{formatDisplayDate(checkOut)}</Text>
            </Pressable>
            <View style={[styles.guestButton, { borderColor: theme.colors.outline }]}>
              <MaterialCommunityIcons name="account" size={16} color={theme.colors.onSurfaceVariant} />
              <TextInput
                mode="flat"
                value={guests}
                onChangeText={setGuests}
                keyboardType="number-pad"
                style={styles.guestInput}
                underlineColor="transparent"
                activeUnderlineColor="transparent"
                dense
              />
            </View>
          </View>

          <Button
            mode="contained"
            onPress={handleSearch}
            loading={isLoading}
            disabled={!location.trim() || isLoading}
            style={styles.searchButton}
          >
            Search Hotels
          </Button>
        </View>

        {/* Date Pickers - iOS needs modal, Android uses native dialog */}
        {Platform.OS === 'ios' ? (
          <>
            <Modal visible={showCheckIn} transparent animationType="slide">
              <View style={styles.dateModalOverlay}>
                <View style={styles.dateModalContent}>
                  <View style={styles.dateModalHeader}>
                    <Text style={styles.dateModalTitle}>Check-in Date</Text>
                    <Pressable onPress={() => setShowCheckIn(false)}>
                      <Text style={styles.dateModalDone}>Done</Text>
                    </Pressable>
                  </View>
                  <DateTimePicker
                    value={checkIn}
                    mode="date"
                    display="spinner"
                    minimumDate={today}
                    onChange={(_, date) => {
                      if (date) {
                        setCheckIn(date);
                        if (date >= checkOut) {
                          const next = new Date(date);
                          next.setDate(date.getDate() + 1);
                          setCheckOut(next);
                        }
                      }
                    }}
                  />
                </View>
              </View>
            </Modal>
            <Modal visible={showCheckOut} transparent animationType="slide">
              <View style={styles.dateModalOverlay}>
                <View style={styles.dateModalContent}>
                  <View style={styles.dateModalHeader}>
                    <Text style={styles.dateModalTitle}>Check-out Date</Text>
                    <Pressable onPress={() => setShowCheckOut(false)}>
                      <Text style={styles.dateModalDone}>Done</Text>
                    </Pressable>
                  </View>
                  <DateTimePicker
                    value={checkOut}
                    mode="date"
                    display="spinner"
                    minimumDate={new Date(checkIn.getTime() + 86400000)}
                    onChange={(_, date) => {
                      if (date) setCheckOut(date);
                    }}
                  />
                </View>
              </View>
            </Modal>
          </>
        ) : (
          <>
            {showCheckIn && (
              <DateTimePicker
                value={checkIn}
                mode="date"
                minimumDate={today}
                onChange={(_, date) => {
                  setShowCheckIn(false);
                  if (date) {
                    setCheckIn(date);
                    if (date >= checkOut) {
                      const next = new Date(date);
                      next.setDate(date.getDate() + 1);
                      setCheckOut(next);
                    }
                  }
                }}
              />
            )}
            {showCheckOut && (
              <DateTimePicker
                value={checkOut}
                mode="date"
                minimumDate={new Date(checkIn.getTime() + 86400000)}
                onChange={(_, date) => {
                  setShowCheckOut(false);
                  if (date) setCheckOut(date);
                }}
              />
            )}
          </>
        )}

        {/* Results */}
        {isLoading ? (
          <LoadingState message="Searching hotels..." />
        ) : isError ? (
          <EmptyState
            icon="alert-circle-outline"
            title="Search failed"
            message="Could not search hotels. Please try again."
          />
        ) : searchQuery && hotels.length === 0 ? (
          <EmptyState
            icon="bed-empty"
            title="No hotels found"
            message={`No hotels found in "${searchQuery}". Try a different location.`}
          />
        ) : (
          <FlatList
            data={hotels}
            renderItem={renderHotel}
            keyExtractor={(item) => item.place_id}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            ListHeaderComponent={
              hotels.length > 0 ? (
                <View style={styles.resultsHeader}>
                  <Text style={styles.resultsCount}>
                    {hotels.length} hotels found
                  </Text>
                  <Text style={styles.selectionCount}>
                    {selectedIds.size} selected
                  </Text>
                </View>
              ) : null
            }
          />
        )}

        {/* Analyze FAB */}
        {selectedIds.size > 0 && (
          <FAB
            icon="lightning-bolt"
            label={`Analyze ${selectedIds.size} Hotel${selectedIds.size > 1 ? 's' : ''}`}
            onPress={handleAnalyze}
            loading={analyzeMutation.isPending}
            disabled={analyzeMutation.isPending}
            style={[styles.fab, { backgroundColor: '#312E81' }]}
            color="#FFFFFF"
          />
        )}
      </View>
    </PremiumGate>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  searchForm: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
  },
  input: {
    marginBottom: 0,
  },
  suggestionsDropdown: {
    position: 'absolute',
    top: 58,
    left: 0,
    right: 0,
    borderWidth: 1,
    borderRadius: 8,
    overflow: 'hidden',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    zIndex: 20,
  },
  suggestionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  suggestionBorder: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E7EB',
  },
  suggestionText: {
    fontSize: 14,
    fontFamily: 'Outfit',
    flex: 1,
  },
  dateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 10,
    marginBottom: 10,
  },
  dateButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderWidth: 1,
    borderRadius: 8,
  },
  dateText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    color: '#0F172A',
  },
  guestButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
    paddingLeft: 8,
    borderWidth: 1,
    borderRadius: 8,
    width: 60,
  },
  guestInput: {
    height: 36,
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    backgroundColor: 'transparent',
    width: 30,
    paddingHorizontal: 0,
  },
  searchButton: {
    borderRadius: 10,
  },
  // Results
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 100,
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  resultsCount: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    color: '#64748B',
  },
  selectionCount: {
    fontSize: 13,
    fontFamily: 'Outfit-SemiBold',
    color: '#6366F1',
  },
  fab: {
    position: 'absolute',
    bottom: 24,
    left: 16,
    right: 16,
    borderRadius: 16,
  },
  dateModalOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0,0,0,0.4)',
  },
  dateModalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: 30,
  },
  dateModalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E7EB',
  },
  dateModalTitle: {
    fontSize: 16,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  dateModalDone: {
    fontSize: 16,
    fontFamily: 'Outfit-SemiBold',
    color: '#6366F1',
  },
});
