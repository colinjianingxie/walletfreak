import React, { useMemo, useState, useCallback } from 'react';
import { View, StyleSheet, Pressable, ActivityIndicator, Alert, Platform } from 'react-native';
import { Text, Button, useTheme } from 'react-native-paper';
import BottomSheet, { BottomSheetBackdrop, BottomSheetSectionList, BottomSheetScrollView, BottomSheetTextInput } from '@gorhom/bottom-sheet';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import DateTimePicker, { DateTimePickerEvent } from '@react-native-community/datetimepicker';
import { CardImage } from '../ui/CardImage';
import { useCardList, useCardDetail } from '../../hooks/useCards';
import { useAddCard } from '../../hooks/useWallet';
import { formatCurrency } from '../../utils/formatters';

interface AddCardSheetProps {
  sheetRef: React.RefObject<BottomSheet | null>;
  existingCardIds: string[];
  onDismiss: () => void;
}

const ISSUER_FILTERS = ['All', 'Chase', 'Amex', 'Capital One', 'Citi', 'Discover'];

export const AddCardSheet: React.FC<AddCardSheetProps> = ({
  sheetRef,
  existingCardIds,
  onDismiss,
}) => {
  const theme = useTheme();
  const snapPoints = useMemo(() => ['92%'], []);
  const [search, setSearch] = useState('');
  const [issuerFilter, setIssuerFilter] = useState('All');
  const [selectedCard, setSelectedCard] = useState<any>(null);
  const [anniversaryDate, setAnniversaryDate] = useState<Date>(new Date());
  const [hasPickedDate, setHasPickedDate] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [useDefault, setUseDefault] = useState(false);
  const addCard = useAddCard();

  const { data } = useCardList({ page_size: 500 });
  const allCards = data?.cards ?? [];

  const { data: cardDetail, isLoading: detailLoading } = useCardDetail(selectedCard?.slug || selectedCard?.id || '');

  // Group available cards by issuer into sections
  const sections = useMemo(() => {
    const existing = new Set(existingCardIds);
    let filtered = allCards.filter((c: any) => !existing.has(c.id) && !existing.has(c.slug));

    if (issuerFilter !== 'All') {
      const filterLower = issuerFilter.toLowerCase();
      filtered = filtered.filter((c: any) => {
        const issuer = (c.issuer || '').toLowerCase();
        if (filterLower === 'amex') return issuer.includes('american express') || issuer.includes('amex');
        return issuer.includes(filterLower);
      });
    }

    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter((c: any) =>
        (c.name || '').toLowerCase().includes(q) ||
        (c.issuer || '').toLowerCase().includes(q)
      );
    }

    const groups: Record<string, any[]> = {};
    filtered.forEach((c: any) => {
      const issuer = c.issuer || 'Other';
      if (!groups[issuer]) groups[issuer] = [];
      groups[issuer].push(c);
    });

    return Object.keys(groups)
      .sort()
      .map((issuer) => ({
        title: issuer,
        data: groups[issuer].sort((a: any, b: any) => (a.name || '').localeCompare(b.name || '')),
      }));
  }, [allCards, existingCardIds, search, issuerFilter]);

  const totalCards = useMemo(() => sections.reduce((sum, s) => sum + s.data.length, 0), [sections]);

  const resetPreview = useCallback(() => {
    setSelectedCard(null);
    setAnniversaryDate(new Date());
    setHasPickedDate(false);
    setShowDatePicker(false);
    setUseDefault(false);
  }, []);

  const handleBack = () => resetPreview();

  const handleClose = () => {
    resetPreview();
    setSearch('');
    setIssuerFilter('All');
    onDismiss();
  };

  const handleDateChange = (_event: DateTimePickerEvent, date?: Date) => {
    if (Platform.OS === 'android') setShowDatePicker(false);
    if (date) {
      setAnniversaryDate(date);
      setHasPickedDate(true);
      setUseDefault(false);
    }
  };

  const formatDate = (d: Date) => {
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const yyyy = d.getFullYear();
    return `${mm}/${dd}/${yyyy}`;
  };

  const handleAdd = () => {
    const cardId = selectedCard?.id || selectedCard?.slug;
    let anniversaryStr: string | undefined;
    if (useDefault) {
      const prevYear = new Date().getFullYear() - 1;
      anniversaryStr = `${prevYear}-01-01`;
    } else if (hasPickedDate) {
      const mm = String(anniversaryDate.getMonth() + 1).padStart(2, '0');
      const dd = String(anniversaryDate.getDate()).padStart(2, '0');
      anniversaryStr = `${anniversaryDate.getFullYear()}-${mm}-${dd}`;
    }

    const cardName = selectedCard?.name || 'Card';
    addCard.mutate({ cardId, anniversaryDate: anniversaryStr }, {
      onSuccess: () => {
        resetPreview();
        onDismiss();
        Alert.alert('Card Added', `${cardName} has been added to your wallet.`, [{ text: 'OK' }]);
      },
    });
  };

  const detail = cardDetail;
  const benefits = detail?.benefits?.slice(0, 5) ?? [];

  // --- Renderers ---

  const renderSectionHeader = useCallback(({ section }: { section: { title: string; data: any[] } }) => (
    <View style={styles.sectionHeaderRow}>
      <Text style={styles.sectionHeaderText}>{section.title}</Text>
      <View style={styles.sectionHeaderCount}>
        <Text style={styles.sectionHeaderCountText}>{section.data.length}</Text>
      </View>
    </View>
  ), []);

  const renderCardRow = useCallback(({ item }: { item: any }) => (
    <Pressable style={styles.cardRow} onPress={() => setSelectedCard(item)}>
      <CardImage slug={item.slug || item.id} size="small" style={{ marginRight: 12 }} />
      <View style={{ flex: 1 }}>
        <Text variant="titleSmall" numberOfLines={1} style={{ fontFamily: 'Outfit-SemiBold' }}>
          {item.name}
        </Text>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {item.issuer}{item.annual_fee ? ` · ${formatCurrency(item.annual_fee)}/yr` : ''}
        </Text>
      </View>
      <MaterialCommunityIcons name="chevron-right" size={20} color={theme.colors.onSurfaceVariant} />
    </Pressable>
  ), [theme]);

  return (
    <BottomSheet
      ref={sheetRef}
      index={-1}
      snapPoints={snapPoints}
      enablePanDownToClose
      onClose={handleClose}
      keyboardBehavior="interactive"
      keyboardBlurBehavior="restore"
      android_keyboardInputMode="adjustResize"
      backdropComponent={(props) => (
        <BottomSheetBackdrop {...props} disappearsOnIndex={-1} appearsOnIndex={0} />
      )}
      backgroundStyle={{ backgroundColor: theme.colors.surface }}
      handleIndicatorStyle={{ backgroundColor: 'transparent' }}
    >
      {selectedCard ? (
        /* Step 2: Setup — Card preview + Anniversary date picker */
        <View style={{ flex: 1 }}>
          <BottomSheetScrollView contentContainerStyle={styles.setupContainer}>
            {/* Header */}
            <View style={styles.setupHeader}>
              <Pressable onPress={handleBack} hitSlop={8} style={styles.headerIconBtn}>
                <MaterialCommunityIcons name="arrow-left" size={22} color={theme.colors.onSurface} />
              </Pressable>
              <Text style={styles.setupTitle}>Setup</Text>
              <Pressable onPress={handleClose} hitSlop={8} style={styles.headerIconBtn}>
                <MaterialCommunityIcons name="close" size={22} color={theme.colors.onSurfaceVariant} />
              </Pressable>
            </View>

            <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />

            {detailLoading ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color={theme.colors.primary} />
                <Text style={[styles.loadingText, { color: theme.colors.onSurfaceVariant }]}>
                  Loading card details...
                </Text>
              </View>
            ) : (
              <>
                {/* Card Info Row */}
                <View style={styles.cardInfoRow}>
                  <CardImage slug={selectedCard.slug || selectedCard.id} size="medium" style={{ marginRight: 16 }} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.cardName}>{selectedCard.name}</Text>
                    <Text style={[styles.cardIssuer, { color: theme.colors.onSurfaceVariant }]}>
                      {selectedCard.issuer}
                    </Text>
                    {detail?.annual_fee !== undefined && (
                      <Text style={[styles.cardFee, { color: theme.colors.primary }]}>
                        {formatCurrency(detail.annual_fee)}/yr
                      </Text>
                    )}
                  </View>
                </View>

                {/* Benefits Card */}
                {benefits.length > 0 && (
                  <View style={styles.benefitsCard}>
                    <View style={styles.benefitsHeader}>
                      <MaterialCommunityIcons name="check-decagram" size={20} color="#16A34A" />
                      <Text style={styles.benefitsTitle}>Benefits Included</Text>
                    </View>
                    {benefits.map((b: any, i: number) => (
                      <View key={i} style={styles.benefitItem}>
                        <Text style={styles.bulletDot}>{'\u2022'}</Text>
                        <Text style={styles.benefitText}>
                          {b.description || b.name || `${formatCurrency(b.dollar_value || b.value)} value`}
                        </Text>
                      </View>
                    ))}
                  </View>
                )}

                {/* Anniversary Date Section */}
                <View style={styles.anniversarySection}>
                  <Text style={styles.anniversaryTitle}>Anniversary Date</Text>
                  <Text style={styles.anniversarySubtitle}>
                    Best estimate if cannot find. The more accurate the anniversary, the better the tracking.
                  </Text>

                  {/* Date display — shows picked date, default, or placeholder */}
                  {useDefault ? (
                    <View style={styles.defaultDateBox}>
                      <MaterialCommunityIcons name="calendar-check-outline" size={20} color="#6B7280" />
                      <Text style={styles.defaultDateText}>
                        Default (1/1/{new Date().getFullYear() - 1})
                      </Text>
                      <Pressable
                        hitSlop={8}
                        onPress={() => setUseDefault(false)}
                      >
                        <MaterialCommunityIcons name="close" size={18} color="#9CA3AF" />
                      </Pressable>
                    </View>
                  ) : (
                    <Pressable
                      style={styles.dateInput}
                      onPress={() => setShowDatePicker(true)}
                    >
                      <Text style={[
                        styles.dateInputText,
                        !hasPickedDate && { color: '#9CA3AF' },
                      ]}>
                        {hasPickedDate ? formatDate(anniversaryDate) : 'Select date'}
                      </Text>
                      <MaterialCommunityIcons name="calendar-blank-outline" size={22} color="#6B7280" />
                    </Pressable>
                  )}

                  {/* Native Date Picker */}
                  {showDatePicker && (
                    <View style={styles.datePickerWrapper}>
                      <DateTimePicker
                        value={anniversaryDate}
                        mode="date"
                        display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                        onChange={handleDateChange}
                        maximumDate={new Date()}
                        minimumDate={new Date(2005, 0, 1)}
                      />
                      {Platform.OS === 'ios' && (
                        <Pressable
                          style={styles.datePickerDone}
                          onPress={() => {
                            setShowDatePicker(false);
                            if (!hasPickedDate) {
                              setHasPickedDate(true);
                              setUseDefault(false);
                            }
                          }}
                        >
                          <Text style={styles.datePickerDoneText}>Done</Text>
                        </Pressable>
                      )}
                    </View>
                  )}

                  <Text style={styles.anniversaryHelp}>
                    This helps track which months/quarters are available for benefit tracking.
                  </Text>

                  {/* Skip Option */}
                  {!useDefault && (
                    <Pressable
                      style={styles.skipButton}
                      onPress={() => {
                        setUseDefault(true);
                        setHasPickedDate(false);
                        setShowDatePicker(false);
                      }}
                    >
                      <Text style={styles.skipButtonText}>
                        I don't know my anniversary date
                      </Text>
                    </Pressable>
                  )}
                </View>

                {/* Info Callout */}
                <View style={styles.infoCallout}>
                  <MaterialCommunityIcons name="information-outline" size={18} color="#3B82F6" style={{ marginTop: 1 }} />
                  <Text style={styles.infoCalloutText}>
                    We'll automatically set up your benefit trackers based on this date. You can adjust them later in the card settings.
                  </Text>
                </View>
              </>
            )}
          </BottomSheetScrollView>

          {/* Sticky Add Button */}
          {!detailLoading && (
            <View style={styles.stickyButtonContainer}>
              <Pressable
                style={[
                  styles.addButton,
                  (!useDefault && !hasPickedDate) && styles.addButtonDisabled,
                  addCard.isPending && styles.addButtonDisabled,
                ]}
                onPress={handleAdd}
                disabled={addCard.isPending || (!useDefault && !hasPickedDate)}
              >
                {addCard.isPending ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <>
                    <MaterialCommunityIcons name="check" size={20} color="#FFFFFF" />
                    <Text style={styles.addButtonText}>Add to Wallet</Text>
                  </>
                )}
              </Pressable>
            </View>
          )}
        </View>
      ) : (
        /* Step 1: Search + Card List */
        <BottomSheetSectionList
          sections={sections}
          keyExtractor={(item: any) => item.id || item.slug}
          renderItem={renderCardRow}
          renderSectionHeader={renderSectionHeader}
          stickySectionHeadersEnabled={false}
          showsVerticalScrollIndicator={true}
          contentContainerStyle={styles.listContentContainer}
          ListHeaderComponent={
            <View style={styles.listHeader}>
              <View style={styles.header}>
                <Text style={styles.headerTitle}>Add Credit Card</Text>
                <Pressable onPress={handleClose} style={styles.headerIconBtn}>
                  <MaterialCommunityIcons name="close" size={22} color={theme.colors.onSurfaceVariant} />
                </Pressable>
              </View>

              <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />

              <View style={[styles.searchContainer, { borderColor: theme.colors.primary }]}>
                <MaterialCommunityIcons name="magnify" size={20} color={theme.colors.primary} style={{ marginRight: 8 }} />
                <BottomSheetTextInput
                  placeholder="Search cards (e.g. Gold, Sapphire)..."
                  placeholderTextColor={theme.colors.onSurfaceVariant}
                  onChangeText={setSearch}
                  value={search}
                  style={[styles.searchInput, { color: theme.colors.onSurface }]}
                  autoCorrect={false}
                />
                {search.length > 0 && (
                  <Pressable onPress={() => setSearch('')} hitSlop={8}>
                    <MaterialCommunityIcons name="close-circle" size={18} color={theme.colors.onSurfaceVariant} />
                  </Pressable>
                )}
              </View>

              <View style={styles.filterRow}>
                {ISSUER_FILTERS.map((f) => (
                  <Pressable
                    key={f}
                    style={[
                      styles.filterChip,
                      issuerFilter === f && { backgroundColor: theme.colors.primary },
                    ]}
                    onPress={() => setIssuerFilter(f)}
                  >
                    <Text style={[
                      styles.filterChipText,
                      issuerFilter === f && { color: '#FFFFFF' },
                    ]}>
                      {f}
                    </Text>
                  </Pressable>
                ))}
              </View>

              <Text style={[styles.resultsLabel, { color: theme.colors.onSurfaceVariant }]}>
                {totalCards} {totalCards === 1 ? 'card' : 'cards'} available
              </Text>
            </View>
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <MaterialCommunityIcons name="credit-card-search-outline" size={48} color={theme.colors.onSurfaceVariant} style={{ opacity: 0.4, marginBottom: 12 }} />
              <Text
                variant="bodyMedium"
                style={{ color: theme.colors.onSurfaceVariant, textAlign: 'center' }}
              >
                {search || issuerFilter !== 'All' ? 'No cards match your search' : 'All cards already added'}
              </Text>
            </View>
          }
        />
      )}
    </BottomSheet>
  );
};

const styles = StyleSheet.create({
  /* Step 1: Card List */
  listContentContainer: {
    paddingBottom: 40,
  },
  listHeader: {
    paddingHorizontal: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  headerTitle: {
    fontSize: 20,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
  },
  headerIconBtn: {
    padding: 4,
  },
  divider: {
    height: 1,
    marginVertical: 12,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 12,
    borderWidth: 1,
    backgroundColor: '#F5F5F5',
    paddingHorizontal: 12,
    height: 48,
    marginBottom: 12,
  },
  searchInput: {
    flex: 1,
    fontFamily: 'Outfit',
    fontSize: 14,
    paddingVertical: 0,
  },
  filterRow: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: 12,
    flexWrap: 'wrap',
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F1F5F9',
  },
  filterChipText: {
    fontSize: 12,
    fontFamily: 'Outfit-Medium',
    color: '#64748B',
  },
  resultsLabel: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 20,
    gap: 8,
  },
  sectionHeaderText: {
    fontSize: 13,
    fontFamily: 'Outfit-SemiBold',
    color: '#6366F1',
  },
  sectionHeaderCount: {
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 8,
  },
  sectionHeaderCountText: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    color: '#6366F1',
  },
  cardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 20,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingTop: 40,
  },

  /* Step 2: Setup */
  setupContainer: {
    paddingHorizontal: 20,
    paddingBottom: 100,
  },
  setupHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  setupTitle: {
    fontSize: 18,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  loadingText: {
    marginTop: 12,
    fontFamily: 'Outfit',
    fontSize: 14,
  },
  cardInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  cardName: {
    fontSize: 18,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
  },
  cardIssuer: {
    fontSize: 14,
    fontFamily: 'Outfit',
    marginTop: 2,
  },
  cardFee: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    marginTop: 4,
  },

  /* Benefits Card */
  benefitsCard: {
    backgroundColor: '#F8FAF9',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 16,
    marginBottom: 24,
  },
  benefitsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  benefitsTitle: {
    fontSize: 15,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
  },
  benefitItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingLeft: 4,
    marginBottom: 6,
    gap: 8,
  },
  bulletDot: {
    fontSize: 16,
    color: '#374151',
    lineHeight: 22,
  },
  benefitText: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: '#374151',
    flex: 1,
    lineHeight: 22,
  },

  /* Anniversary Section */
  anniversarySection: {
    marginBottom: 16,
  },
  anniversaryTitle: {
    fontSize: 16,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
    marginBottom: 4,
  },
  anniversarySubtitle: {
    fontSize: 13,
    fontFamily: 'Outfit',
    color: '#6B7280',
    marginBottom: 14,
  },
  dateInput: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    paddingHorizontal: 16,
    height: 52,
    marginBottom: 12,
  },
  defaultDateBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderStyle: 'dashed',
    paddingHorizontal: 16,
    height: 52,
    marginBottom: 12,
  },
  defaultDateText: {
    flex: 1,
    fontSize: 15,
    fontFamily: 'Outfit-Medium',
    color: '#374151',
  },
  dateInputText: {
    fontSize: 15,
    fontFamily: 'Outfit-Medium',
    color: '#1C1B1F',
  },
  datePickerWrapper: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    marginBottom: 12,
    overflow: 'hidden',
  },
  datePickerDone: {
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  datePickerDoneText: {
    fontSize: 16,
    fontFamily: 'Outfit-SemiBold',
    color: '#6366F1',
  },
  anniversaryHelp: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#9CA3AF',
    marginBottom: 12,
  },
  skipButton: {
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  skipButtonText: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    color: '#374151',
  },

  /* Info Callout */
  infoCallout: {
    flexDirection: 'row',
    backgroundColor: '#EFF6FF',
    borderRadius: 12,
    padding: 14,
    gap: 10,
    marginTop: 8,
  },
  infoCalloutText: {
    fontSize: 13,
    fontFamily: 'Outfit',
    color: '#3B82F6',
    flex: 1,
    lineHeight: 19,
  },

  /* Sticky Add Button */
  stickyButtonContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 20,
    paddingBottom: Platform.OS === 'ios' ? 34 : 20,
    paddingTop: 12,
    backgroundColor: 'rgba(255,255,255,0.97)',
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  addButton: {
    backgroundColor: '#16A34A',
    borderRadius: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    height: 54,
  },
  addButtonDisabled: {
    opacity: 0.5,
  },
  addButtonText: {
    fontSize: 16,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
  },
});
