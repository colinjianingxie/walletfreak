import React, { useState, useCallback, useRef, useMemo } from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import {
  Text,
  Searchbar,
  useTheme,
  Button,
  Checkbox,
  RadioButton,
  Divider,
} from 'react-native-paper';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  useAnimatedScrollHandler,
  interpolate,
  Extrapolation,
  FadeIn,
  FadeOut,
  SlideInDown,
  SlideOutDown,
} from 'react-native-reanimated';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import BottomSheet, { BottomSheetBackdrop, BottomSheetScrollView } from '@gorhom/bottom-sheet';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { CardImage } from '../../src/components/ui/CardImage';
import { useCardList } from '../../src/hooks/useCards';
import { useCardsStore } from '../../src/stores/cardsStore';
import { formatCurrency } from '../../src/utils/formatters';

const COLLAPSE_DISTANCE = 80;

const SORT_OPTIONS = [
  { value: 'match', label: 'Match Score' },
  { value: 'name', label: 'Name A-Z' },
  { value: 'fee_low', label: 'Lowest Fee' },
  { value: 'fee_high', label: 'Highest Fee' },
];

const CATEGORY_OPTIONS = [
  'All',
  'Travel',
  'Hotel',
  'Flights',
  'Dining',
  'Groceries',
  'Cash Back',
  'Luxury',
  'No Annual Fee',
];

export default function ExploreScreen() {
  const [search, setSearch] = useState('');
  const [selectedIssuers, setSelectedIssuers] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [sortBy, setSortBy] = useState('match');
  const [noFeeOnly, setNoFeeOnly] = useState(false);
  const router = useRouter();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { selectedCards, toggleCompareCard, clearCompare } = useCardsStore();
  const filterSheetRef = useRef<BottomSheet>(null);
  const filterSnapPoints = useMemo(() => ['75%'], []);

  const scrollY = useSharedValue(0);
  const scrollHandler = useAnimatedScrollHandler({
    onScroll: (event) => {
      scrollY.value = event.contentOffset.y;
    },
  });

  const { data, isLoading } = useCardList({
    search: search || undefined,
    page_size: 500,
  });

  const allCards = data?.cards ?? [];
  const issuers = data?.issuers ?? [];

  const filteredCards = useMemo(() => {
    let cards = [...allCards];

    if (selectedIssuers.length > 0) {
      cards = cards.filter((c: any) => selectedIssuers.includes(c.issuer));
    }

    if (selectedCategory !== 'All') {
      if (selectedCategory === 'No Annual Fee') {
        cards = cards.filter((c: any) => !c.annual_fee || c.annual_fee === 0);
      } else {
        cards = cards.filter((c: any) => {
          const cats = c.categories || c.category || '';
          if (Array.isArray(cats)) return cats.some((cat: string) => cat.toLowerCase().includes(selectedCategory.toLowerCase()));
          return String(cats).toLowerCase().includes(selectedCategory.toLowerCase());
        });
      }
    }

    if (noFeeOnly) {
      cards = cards.filter((c: any) => !c.annual_fee || c.annual_fee === 0);
    }

    if (sortBy === 'name') {
      cards.sort((a: any, b: any) => (a.name || '').localeCompare(b.name || ''));
    } else if (sortBy === 'fee_low') {
      cards.sort((a: any, b: any) => (a.annual_fee || 0) - (b.annual_fee || 0));
    } else if (sortBy === 'fee_high') {
      cards.sort((a: any, b: any) => (b.annual_fee || 0) - (a.annual_fee || 0));
    } else {
      cards.sort((a: any, b: any) => (b.match_score ?? 0) - (a.match_score ?? 0));
    }

    return cards;
  }, [allCards, selectedIssuers, selectedCategory, sortBy, noFeeOnly]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (selectedIssuers.length > 0) count++;
    if (selectedCategory !== 'All') count++;
    if (sortBy !== 'match') count++;
    if (noFeeOnly) count++;
    return count;
  }, [selectedIssuers, selectedCategory, sortBy, noFeeOnly]);

  const handleResetFilters = () => {
    setSelectedIssuers([]);
    setSelectedCategory('All');
    setSortBy('match');
    setNoFeeOnly(false);
  };

  const toggleIssuer = (issuer: string) => {
    setSelectedIssuers((prev) =>
      prev.includes(issuer) ? prev.filter((i) => i !== issuer) : [...prev, issuer]
    );
  };

  const getBenefitTags = (card: any): string[] => {
    const tags: string[] = [];
    if (card.benefits && Array.isArray(card.benefits)) {
      card.benefits.slice(0, 2).forEach((b: any) => {
        if (b.description) tags.push(b.description.length > 20 ? b.description.slice(0, 20) + '...' : b.description);
        else if (b.benefit_type) tags.push(b.benefit_type);
      });
    }
    if (tags.length === 0 && card.welcome_bonus) {
      tags.push(card.welcome_bonus.length > 25 ? card.welcome_bonus.slice(0, 25) + '...' : card.welcome_bonus);
    }
    return tags;
  };

  // Build a map of slug->card for compare bar previews
  const cardsMap = useMemo(() => {
    const map = new Map<string, any>();
    allCards.forEach((c: any) => {
      map.set(c.slug || c.id, c);
      map.set(c.id, c);
    });
    return map;
  }, [allCards]);

  // --- Animated Styles ---
  const animatedTitle = useAnimatedStyle(() => ({
    fontSize: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [28, 20], Extrapolation.CLAMP),
  }));

  const animatedSubtitle = useAnimatedStyle(() => ({
    height: interpolate(scrollY.value, [0, 50], [20, 0], Extrapolation.CLAMP),
    opacity: interpolate(scrollY.value, [0, 50], [1, 0], Extrapolation.CLAMP),
    overflow: 'hidden' as const,
  }));

  const animatedSearchBar = useAnimatedStyle(() => ({
    height: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [52, 0], Extrapolation.CLAMP),
    opacity: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [1, 0], Extrapolation.CLAMP),
    overflow: 'hidden' as const,
  }));

  const renderCardItem = useCallback(
    ({ item }: { item: any }) => {
      const rating = item.match_score ? (item.match_score / 20).toFixed(1) : null;
      const benefitTags = getBenefitTags(item);
      const extraCount = (item.benefits?.length ?? 0) - benefitTags.length;
      const cardSlug = item.slug || item.id;
      const isCompareSelected = selectedCards.includes(cardSlug);

      return (
        <Pressable
          style={[styles.cardItem, { borderColor: theme.colors.outlineVariant }]}
          onPress={() => router.push(`/stacks/card-detail/${cardSlug}` as any)}
        >
          <CardImage slug={cardSlug} size="medium" style={styles.cardImage} />
          <View style={styles.cardContent}>
            <View style={styles.cardNameRow}>
              <View style={{ flex: 1 }}>
                <Text variant="titleSmall" numberOfLines={1} style={{ fontFamily: 'Outfit-SemiBold' }}>
                  {item.name}
                </Text>
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                  {item.issuer}
                </Text>
              </View>
              {rating && (
                <View style={styles.ratingBadge}>
                  <MaterialCommunityIcons name="star" size={14} color="#EAB308" />
                  <Text style={styles.ratingText}>{rating}</Text>
                </View>
              )}
            </View>
            {benefitTags.length > 0 && (
              <View style={styles.tagRow}>
                {benefitTags.map((tag, i) => (
                  <View key={i} style={[styles.benefitTag, { borderColor: theme.colors.outlineVariant }]}>
                    <Text style={[styles.benefitTagText, { color: theme.colors.onSurfaceVariant }]}>
                      {tag}
                    </Text>
                  </View>
                ))}
                {extraCount > 0 && (
                  <View style={[styles.benefitTag, { borderColor: theme.colors.outlineVariant }]}>
                    <Text style={[styles.benefitTagText, { color: theme.colors.onSurfaceVariant }]}>
                      +{extraCount}
                    </Text>
                  </View>
                )}
              </View>
            )}
          </View>
          {/* Compare toggle button */}
          <Pressable
            style={styles.compareToggle}
            onPress={() => toggleCompareCard(cardSlug)}
            hitSlop={8}
          >
            <MaterialCommunityIcons
              name={isCompareSelected ? 'checkbox-marked' : 'checkbox-blank-outline'}
              size={22}
              color={isCompareSelected ? '#4F46E5' : theme.colors.onSurfaceVariant}
            />
          </Pressable>
        </Pressable>
      );
    },
    [router, theme, selectedCards, toggleCompareCard]
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Collapsible Header */}
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <View style={styles.headerTitleRow}>
          <View style={{ flex: 1 }}>
            <Animated.Text style={[styles.headerTitleText, animatedTitle]}>Explore Cards</Animated.Text>
            <Animated.View style={animatedSubtitle}>
              <Text style={[styles.headerSubtitle, { color: theme.colors.onSurfaceVariant }]}>
                Find the perfect card for your wallet.
              </Text>
            </Animated.View>
          </View>
          <Pressable
            style={[styles.filterIconButton, { borderColor: theme.colors.outlineVariant }]}
            onPress={() => filterSheetRef.current?.snapToIndex(0)}
          >
            <MaterialCommunityIcons name="filter-variant" size={20} color={theme.colors.onSurfaceVariant} />
            {activeFilterCount > 0 && (
              <View style={[styles.filterBadge, { backgroundColor: theme.colors.primary }]}>
                <Text style={styles.filterBadgeText}>{activeFilterCount}</Text>
              </View>
            )}
          </Pressable>
        </View>
      </View>

      {/* Search Bar — collapses on scroll */}
      <Animated.View style={[styles.searchContainer, animatedSearchBar]}>
        <Searchbar
          placeholder="Search cards, benefits, issuers..."
          onChangeText={setSearch}
          value={search}
          style={styles.searchbar}
          inputStyle={{ fontFamily: 'Outfit' }}
        />
      </Animated.View>

      {/* Cards List */}
      {isLoading ? (
        <LoadingState message="Loading cards..." />
      ) : filteredCards.length === 0 ? (
        <EmptyState
          icon="credit-card-off-outline"
          title="No cards found"
          message="Try adjusting your search or filters."
        />
      ) : (
        <Animated.FlatList
          data={filteredCards}
          renderItem={renderCardItem}
          keyExtractor={(item) => item.id || item.slug}
          contentContainerStyle={[
            styles.listContent,
            selectedCards.length > 0 && { paddingBottom: 96 },
          ]}
          showsVerticalScrollIndicator={false}
          onScroll={scrollHandler}
          scrollEventThrottle={16}
        />
      )}

      {/* Floating Compare Bar */}
      {selectedCards.length > 0 && (
        <Animated.View
          entering={SlideInDown.duration(250)}
          exiting={SlideOutDown.duration(200)}
          style={[styles.compareBar, { bottom: insets.bottom + 2 }]}
        >
          <View style={styles.compareBarInner}>
            <View style={styles.compareCardPreviews}>
              {selectedCards.map((cardSlug) => {
                const card = cardsMap.get(cardSlug);
                return (
                  <View key={cardSlug} style={styles.comparePreviewItem}>
                    <CardImage slug={cardSlug} size="tiny" />
                  </View>
                );
              })}
            </View>
            <Text style={styles.compareBarText}>
              {selectedCards.length} selected
            </Text>
            <View style={styles.compareBarActions}>
              <Pressable onPress={clearCompare} style={styles.compareClearButton}>
                <MaterialCommunityIcons name="close" size={18} color="#64748B" />
              </Pressable>
              <Pressable
                style={styles.compareButton}
                onPress={() => router.push('/stacks/compare-cards' as any)}
              >
                <Text style={styles.compareButtonText}>Compare</Text>
                <MaterialCommunityIcons name="arrow-right" size={16} color="#FFFFFF" />
              </Pressable>
            </View>
          </View>
        </Animated.View>
      )}

      {/* Filter Bottom Sheet */}
      <BottomSheet
        ref={filterSheetRef}
        index={-1}
        snapPoints={filterSnapPoints}
        enablePanDownToClose
        backdropComponent={(props) => (
          <BottomSheetBackdrop {...props} disappearsOnIndex={-1} appearsOnIndex={0} />
        )}
        backgroundStyle={{ backgroundColor: theme.colors.surface }}
        handleIndicatorStyle={{ backgroundColor: theme.colors.onSurfaceVariant }}
      >
        <BottomSheetScrollView contentContainerStyle={styles.filterContent}>
          <View style={styles.filterHeader}>
            <Text variant="titleMedium" style={{ fontFamily: 'Outfit-SemiBold' }}>
              Filters
            </Text>
            <Button mode="text" onPress={handleResetFilters} compact>
              Reset
            </Button>
          </View>

          <Text variant="labelLarge" style={[styles.filterSectionTitle, { color: theme.colors.onSurface }]}>
            Sort By
          </Text>
          <RadioButton.Group onValueChange={setSortBy} value={sortBy}>
            {SORT_OPTIONS.map((opt) => (
              <RadioButton.Item
                key={opt.value}
                label={opt.label}
                value={opt.value}
                labelStyle={{ fontFamily: 'Outfit' }}
              />
            ))}
          </RadioButton.Group>

          <Divider style={{ marginVertical: 12 }} />

          <Text variant="labelLarge" style={[styles.filterSectionTitle, { color: theme.colors.onSurface }]}>
            Category
          </Text>
          <View style={styles.categoryPills}>
            {CATEGORY_OPTIONS.map((cat) => (
              <Pressable
                key={cat}
                style={[
                  styles.categoryChip,
                  { borderColor: theme.colors.outlineVariant },
                  selectedCategory === cat && { backgroundColor: theme.colors.primaryContainer, borderColor: theme.colors.primary },
                ]}
                onPress={() => setSelectedCategory(cat)}
              >
                <Text style={[
                  styles.categoryChipText,
                  { color: theme.colors.onSurfaceVariant },
                  selectedCategory === cat && { color: theme.colors.onPrimaryContainer },
                ]}>
                  {cat}
                </Text>
              </Pressable>
            ))}
          </View>

          <Divider style={{ marginVertical: 12 }} />

          <Text variant="labelLarge" style={[styles.filterSectionTitle, { color: theme.colors.onSurface }]}>
            Issuer
          </Text>
          {issuers.map((issuer: string) => (
            <Checkbox.Item
              key={issuer}
              label={issuer}
              status={selectedIssuers.includes(issuer) ? 'checked' : 'unchecked'}
              onPress={() => toggleIssuer(issuer)}
              labelStyle={{ fontFamily: 'Outfit' }}
            />
          ))}

          <Divider style={{ marginVertical: 12 }} />

          <Checkbox.Item
            label="No Annual Fee Only"
            status={noFeeOnly ? 'checked' : 'unchecked'}
            onPress={() => setNoFeeOnly(!noFeeOnly)}
            labelStyle={{ fontFamily: 'Outfit-Medium' }}
          />

          <Button
            mode="contained"
            onPress={() => filterSheetRef.current?.close()}
            style={styles.applyButton}
            labelStyle={{ fontFamily: 'Outfit-Medium' }}
          >
            Apply Filters
          </Button>
        </BottomSheetScrollView>
      </BottomSheet>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingBottom: 12,
  },
  headerTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  headerTitleText: {
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
  },
  headerSubtitle: {
    fontSize: 14,
    fontFamily: 'Outfit',
    marginTop: 2,
  },
  filterIconButton: {
    width: 40,
    height: 40,
    borderRadius: 10,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 4,
  },
  filterBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    width: 16,
    height: 16,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  filterBadgeText: {
    fontSize: 9,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
  },
  searchContainer: {
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  searchbar: {
    borderRadius: 12,
    elevation: 0,
    backgroundColor: '#F5F5F5',
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  cardItem: {
    flexDirection: 'row',
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    marginBottom: 10,
    backgroundColor: '#FFFFFF',
  },
  cardImage: {
    marginRight: 14,
  },
  cardContent: {
    flex: 1,
  },
  cardNameRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  ratingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#FFFBEB',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  ratingText: {
    fontSize: 13,
    fontFamily: 'Outfit-Bold',
    color: '#B45309',
  },
  tagRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  benefitTag: {
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  benefitTagText: {
    fontSize: 11,
    fontFamily: 'Outfit',
  },
  // Compare toggle on card row
  compareToggle: {
    justifyContent: 'center',
    alignItems: 'center',
    paddingLeft: 8,
  },
  // Floating compare bar
  compareBar: {
    position: 'absolute',
    left: 12,
    right: 12,
  },
  compareBarInner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1B1F',
    borderRadius: 16,
    paddingVertical: 10,
    paddingHorizontal: 14,
    gap: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
  },
  compareCardPreviews: {
    flexDirection: 'row',
    gap: -8,
  },
  comparePreviewItem: {
    width: 32,
    height: 22,
    borderRadius: 4,
    overflow: 'hidden',
    borderWidth: 1.5,
    borderColor: '#FFFFFF',
  },
  compareBarText: {
    flex: 1,
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    color: '#FFFFFF',
  },
  compareBarActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  compareClearButton: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  compareButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#4F46E5',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
  },
  compareButtonText: {
    fontSize: 13,
    fontFamily: 'Outfit-SemiBold',
    color: '#FFFFFF',
  },
  // Filter sheet styles
  filterContent: {
    padding: 16,
    paddingBottom: 40,
  },
  filterHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  filterSectionTitle: {
    fontFamily: 'Outfit-Medium',
    marginBottom: 8,
  },
  categoryPills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  categoryChip: {
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 6,
  },
  categoryChipText: {
    fontSize: 13,
    fontFamily: 'Outfit',
  },
  applyButton: {
    marginTop: 16,
    borderRadius: 12,
  },
});
