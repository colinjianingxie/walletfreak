import React, { useMemo, useState, useCallback } from 'react';
import { View, StyleSheet, Pressable, ActivityIndicator } from 'react-native';
import { Text, Searchbar, Button, useTheme } from 'react-native-paper';
import BottomSheet, { BottomSheetBackdrop, BottomSheetView, BottomSheetFlatList, BottomSheetScrollView } from '@gorhom/bottom-sheet';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { CardImage } from '../ui/CardImage';
import { useCardList, useCardDetail } from '../../hooks/useCards';
import { useAddCard } from '../../hooks/useWallet';
import { formatCurrency } from '../../utils/formatters';

interface AddCardSheetProps {
  sheetRef: React.RefObject<BottomSheet | null>;
  existingCardIds: string[];
  onDismiss: () => void;
}

const MONTHS = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

const currentYear = new Date().getFullYear();
const YEARS = Array.from({ length: 15 }, (_, i) => currentYear - i);

export const AddCardSheet: React.FC<AddCardSheetProps> = ({
  sheetRef,
  existingCardIds,
  onDismiss,
}) => {
  const theme = useTheme();
  const snapPoints = useMemo(() => ['85%'], []);
  const [search, setSearch] = useState('');
  const [selectedCard, setSelectedCard] = useState<any>(null);
  const [selectedMonth, setSelectedMonth] = useState<number | null>(null);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [useDefault, setUseDefault] = useState(false);
  const addCard = useAddCard();

  const { data } = useCardList({ page_size: 500 });
  const allCards = data?.cards ?? [];

  const { data: cardDetail, isLoading: detailLoading } = useCardDetail(selectedCard?.slug || selectedCard?.id || '');

  const availableCards = useMemo(() => {
    const existing = new Set(existingCardIds);
    let filtered = allCards.filter((c: any) => !existing.has(c.id) && !existing.has(c.slug));
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter((c: any) =>
        (c.name || '').toLowerCase().includes(q) ||
        (c.issuer || '').toLowerCase().includes(q)
      );
    }
    return filtered;
  }, [allCards, existingCardIds, search]);

  const resetPreview = useCallback(() => {
    setSelectedCard(null);
    setSelectedMonth(null);
    setSelectedYear(null);
    setUseDefault(false);
  }, []);

  const handleSelectCard = (card: any) => {
    setSelectedCard(card);
  };

  const handleBack = () => {
    resetPreview();
  };

  const handleAdd = () => {
    const cardId = selectedCard?.id || selectedCard?.slug;
    let anniversaryDate: string | undefined;
    if (useDefault) {
      anniversaryDate = 'default';
    } else if (selectedMonth !== null && selectedYear !== null) {
      const mm = String(selectedMonth + 1).padStart(2, '0');
      anniversaryDate = `${selectedYear}-${mm}-01`;
    }

    addCard.mutate({ cardId, anniversaryDate }, {
      onSuccess: () => {
        resetPreview();
        onDismiss();
      },
    });
  };

  const handleClose = () => {
    resetPreview();
    setSearch('');
    onDismiss();
  };

  const detail = cardDetail;
  const benefits = detail?.benefits?.slice(0, 4) ?? [];

  return (
    <BottomSheet
      ref={sheetRef}
      index={-1}
      snapPoints={snapPoints}
      enablePanDownToClose
      onClose={handleClose}
      backdropComponent={(props) => (
        <BottomSheetBackdrop {...props} disappearsOnIndex={-1} appearsOnIndex={0} />
      )}
      backgroundStyle={{ backgroundColor: theme.colors.surface }}
      handleIndicatorStyle={{ backgroundColor: 'transparent' }}
    >
      {selectedCard ? (
        /* Step 2: Card Preview + Anniversary Picker */
        <BottomSheetScrollView contentContainerStyle={styles.previewContainer}>
          {/* Header */}
          <View style={styles.header}>
            <Pressable onPress={handleBack} style={styles.backButton}>
              <MaterialCommunityIcons name="arrow-left" size={20} color={theme.colors.onSurface} />
              <Text style={[styles.backText, { color: theme.colors.onSurface }]}>Back</Text>
            </Pressable>
            <Pressable onPress={handleClose} style={styles.closeButton}>
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
              {/* Card Info */}
              <View style={styles.cardPreviewRow}>
                <CardImage slug={selectedCard.slug || selectedCard.id} size="medium" style={{ marginRight: 16 }} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.previewCardName}>{selectedCard.name}</Text>
                  <Text style={[styles.previewIssuer, { color: theme.colors.onSurfaceVariant }]}>
                    {selectedCard.issuer}
                  </Text>
                  {detail?.annual_fee !== undefined && (
                    <Text style={[styles.previewFee, { color: theme.colors.primary }]}>
                      {formatCurrency(detail.annual_fee)}/yr
                    </Text>
                  )}
                </View>
              </View>

              {/* Key Benefits */}
              {benefits.length > 0 && (
                <View style={styles.benefitsSection}>
                  <Text style={[styles.sectionLabel, { color: theme.colors.onSurfaceVariant }]}>
                    KEY BENEFITS
                  </Text>
                  {benefits.map((b: any, i: number) => (
                    <View key={i} style={styles.benefitRow}>
                      <MaterialCommunityIcons
                        name="check-circle"
                        size={18}
                        color={theme.colors.primary}
                        style={{ marginRight: 8, marginTop: 2 }}
                      />
                      <View style={{ flex: 1 }}>
                        <Text style={styles.benefitName}>{b.name}</Text>
                        {b.value != null && (
                          <Text style={[styles.benefitValue, { color: theme.colors.onSurfaceVariant }]}>
                            {formatCurrency(b.value)} value
                          </Text>
                        )}
                      </View>
                    </View>
                  ))}
                </View>
              )}

              {/* Anniversary Picker */}
              <View style={styles.anniversarySection}>
                <Text style={[styles.sectionLabel, { color: theme.colors.onSurfaceVariant }]}>
                  CARD ANNIVERSARY DATE
                </Text>
                <Text style={[styles.anniversaryHint, { color: theme.colors.onSurfaceVariant }]}>
                  When did you open this card? This helps track your annual benefits.
                </Text>

                {!useDefault && (
                  <>
                    {/* Month Picker */}
                    <Text style={[styles.pickerLabel, { color: theme.colors.onSurface }]}>Month</Text>
                    <View style={styles.monthGrid}>
                      {MONTHS.map((m, i) => (
                        <Pressable
                          key={m}
                          style={[
                            styles.monthChip,
                            {
                              backgroundColor: selectedMonth === i ? theme.colors.primary : theme.colors.surfaceVariant,
                              borderColor: selectedMonth === i ? theme.colors.primary : theme.colors.outlineVariant,
                            },
                          ]}
                          onPress={() => setSelectedMonth(i)}
                        >
                          <Text
                            style={[
                              styles.monthChipText,
                              { color: selectedMonth === i ? '#FFFFFF' : theme.colors.onSurface },
                            ]}
                          >
                            {m}
                          </Text>
                        </Pressable>
                      ))}
                    </View>

                    {/* Year Picker */}
                    <Text style={[styles.pickerLabel, { color: theme.colors.onSurface }]}>Year</Text>
                    <View style={styles.yearGrid}>
                      {YEARS.map((y) => (
                        <Pressable
                          key={y}
                          style={[
                            styles.yearChip,
                            {
                              backgroundColor: selectedYear === y ? theme.colors.primary : theme.colors.surfaceVariant,
                              borderColor: selectedYear === y ? theme.colors.primary : theme.colors.outlineVariant,
                            },
                          ]}
                          onPress={() => setSelectedYear(y)}
                        >
                          <Text
                            style={[
                              styles.yearChipText,
                              { color: selectedYear === y ? '#FFFFFF' : theme.colors.onSurface },
                            ]}
                          >
                            {y}
                          </Text>
                        </Pressable>
                      ))}
                    </View>
                  </>
                )}

                {/* Default Option */}
                <Pressable
                  style={[
                    styles.defaultOption,
                    {
                      backgroundColor: useDefault ? theme.colors.primaryContainer : theme.colors.surfaceVariant,
                      borderColor: useDefault ? theme.colors.primary : theme.colors.outlineVariant,
                    },
                  ]}
                  onPress={() => {
                    setUseDefault(!useDefault);
                    if (!useDefault) {
                      setSelectedMonth(null);
                      setSelectedYear(null);
                    }
                  }}
                >
                  <MaterialCommunityIcons
                    name={useDefault ? 'checkbox-marked-circle' : 'checkbox-blank-circle-outline'}
                    size={20}
                    color={useDefault ? theme.colors.primary : theme.colors.onSurfaceVariant}
                    style={{ marginRight: 8 }}
                  />
                  <Text style={[styles.defaultOptionText, { color: theme.colors.onSurface }]}>
                    I don't know my anniversary date
                  </Text>
                </Pressable>
              </View>

              {/* Add Button */}
              <Button
                mode="contained"
                onPress={handleAdd}
                loading={addCard.isPending}
                disabled={addCard.isPending || (!useDefault && (selectedMonth === null || selectedYear === null))}
                style={styles.addButton}
                contentStyle={styles.addButtonContent}
                icon="plus"
              >
                Add to Wallet
              </Button>
            </>
          )}
        </BottomSheetScrollView>
      ) : (
        /* Step 1: Search + Card List */
        <BottomSheetView style={styles.container}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.headerTitle}>Add Credit Card</Text>
            <Pressable onPress={handleClose} style={styles.closeButton}>
              <MaterialCommunityIcons name="close" size={22} color={theme.colors.onSurfaceVariant} />
            </Pressable>
          </View>

          <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />

          {/* Search */}
          <Searchbar
            placeholder="Search cards (e.g. Gold, Sapphire)..."
            onChangeText={setSearch}
            value={search}
            style={[styles.searchbar, { borderColor: theme.colors.primary }]}
            inputStyle={{ fontFamily: 'Outfit', fontSize: 14 }}
          />

          {/* Suggested Label */}
          <Text style={[styles.suggestedLabel, { color: theme.colors.onSurfaceVariant }]}>
            SUGGESTED
          </Text>

          {/* Card List */}
          <BottomSheetFlatList
            data={availableCards}
            keyExtractor={(item: any) => item.id || item.slug}
            renderItem={({ item }: { item: any }) => (
              <Pressable
                style={styles.cardRow}
                onPress={() => handleSelectCard(item)}
              >
                <CardImage slug={item.slug || item.id} size="small" style={{ marginRight: 12 }} />
                <View style={{ flex: 1 }}>
                  <Text variant="titleSmall" numberOfLines={1} style={{ fontFamily: 'Outfit-SemiBold' }}>
                    {item.name}
                  </Text>
                  <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                    {item.issuer}
                  </Text>
                </View>
                <MaterialCommunityIcons name="chevron-right" size={20} color={theme.colors.onSurfaceVariant} />
              </Pressable>
            )}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: 20 }}
            ListEmptyComponent={
              <Text
                variant="bodyMedium"
                style={{ color: theme.colors.onSurfaceVariant, textAlign: 'center', marginTop: 24 }}
              >
                {search ? 'No cards found' : 'All cards already added'}
              </Text>
            }
          />
        </BottomSheetView>
      )}
    </BottomSheet>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
  },
  previewContainer: {
    paddingHorizontal: 20,
    paddingBottom: 40,
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
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    padding: 4,
  },
  backText: {
    fontSize: 16,
    fontFamily: 'Outfit-Medium',
  },
  closeButton: {
    padding: 4,
  },
  divider: {
    height: 1,
    marginVertical: 12,
  },
  searchbar: {
    borderRadius: 12,
    elevation: 0,
    backgroundColor: '#F5F5F5',
    borderWidth: 1,
    marginBottom: 16,
  },
  suggestedLabel: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    letterSpacing: 1,
    marginBottom: 12,
  },
  cardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
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
  cardPreviewRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  previewCardName: {
    fontSize: 20,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
  },
  previewIssuer: {
    fontSize: 14,
    fontFamily: 'Outfit',
    marginTop: 2,
  },
  previewFee: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    marginTop: 4,
  },
  benefitsSection: {
    marginBottom: 24,
  },
  sectionLabel: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    letterSpacing: 1,
    marginBottom: 12,
  },
  benefitRow: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  benefitName: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    color: '#1C1B1F',
  },
  benefitValue: {
    fontSize: 12,
    fontFamily: 'Outfit',
    marginTop: 2,
  },
  anniversarySection: {
    marginBottom: 24,
  },
  anniversaryHint: {
    fontSize: 13,
    fontFamily: 'Outfit',
    marginBottom: 16,
    lineHeight: 18,
  },
  pickerLabel: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    marginBottom: 8,
  },
  monthGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  monthChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
  },
  monthChipText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
  },
  yearGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  yearChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
  },
  yearChipText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
  },
  defaultOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    marginTop: 4,
  },
  defaultOptionText: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
  },
  addButton: {
    borderRadius: 12,
    marginTop: 8,
  },
  addButtonContent: {
    paddingVertical: 6,
  },
});
