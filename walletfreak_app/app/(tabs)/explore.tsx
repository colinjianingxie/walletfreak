import React, { useState, useCallback } from 'react';
import { View, StyleSheet, FlatList, Pressable } from 'react-native';
import {
  Text,
  Searchbar,
  useTheme,
  Surface,
  Chip,
  IconButton,
} from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { useCardList } from '../../src/hooks/useCards';
import { useCardsStore } from '../../src/stores/cardsStore';
import { formatCurrency } from '../../src/utils/formatters';

export default function ExploreScreen() {
  const [search, setSearch] = useState('');
  const [selectedIssuer, setSelectedIssuer] = useState('');
  const router = useRouter();
  const theme = useTheme();
  const { viewMode, setViewMode, selectedCards, toggleCompareCard } = useCardsStore();

  const { data, isLoading, refetch } = useCardList({
    search: search || undefined,
    issuer: selectedIssuer || undefined,
  });

  const cards = data?.cards ?? [];
  const issuers = data?.issuers ?? [];

  const renderCardItem = useCallback(
    ({ item }: { item: any }) => (
      <Surface
        style={[styles.cardItem, { backgroundColor: theme.colors.elevation.level1 }]}
        elevation={1}
      >
        <Pressable
          onPress={() => router.push(`/stacks/card-detail/${item.slug || item.id}` as any)}
          style={styles.cardPressable}
        >
          <View style={styles.cardContent}>
            <Text variant="titleSmall" numberOfLines={1}>
              {item.name}
            </Text>
            <Text
              variant="bodySmall"
              style={{ color: theme.colors.onSurfaceVariant }}
            >
              {item.issuer}
            </Text>
            <View style={styles.cardMeta}>
              <Text variant="labelSmall" style={{ color: theme.colors.primary }}>
                {formatCurrency(item.annual_fee)}/yr
              </Text>
              {item.match_score !== undefined && (
                <Chip
                  compact
                  style={[styles.matchChip, { backgroundColor: theme.colors.primaryContainer }]}
                  textStyle={{ fontSize: 10, color: theme.colors.onPrimaryContainer }}
                >
                  {item.match_score}% match
                </Chip>
              )}
            </View>
          </View>
          <MaterialCommunityIcons
            name="chevron-right"
            size={20}
            color={theme.colors.onSurfaceVariant}
          />
        </Pressable>
      </Surface>
    ),
    [router, theme]
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Search Bar */}
      <Searchbar
        placeholder="Search cards..."
        onChangeText={setSearch}
        value={search}
        style={styles.searchbar}
        inputStyle={{ fontFamily: 'Outfit' }}
      />

      {/* Filter Chips */}
      <FlatList
        data={['All', ...issuers]}
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filterRow}
        renderItem={({ item }) => (
          <Chip
            selected={item === 'All' ? !selectedIssuer : selectedIssuer === item}
            onPress={() => setSelectedIssuer(item === 'All' ? '' : item)}
            style={styles.filterChip}
            compact
          >
            {item}
          </Chip>
        )}
        keyExtractor={(item) => item}
      />

      {/* View Mode Toggle & Compare */}
      <View style={styles.toolbar}>
        <View style={styles.viewToggle}>
          <IconButton
            icon="view-list"
            size={20}
            selected={viewMode === 'list'}
            onPress={() => setViewMode('list')}
          />
          <IconButton
            icon="view-grid"
            size={20}
            selected={viewMode === 'grid'}
            onPress={() => setViewMode('grid')}
          />
        </View>
        {selectedCards.length > 0 && (
          <Chip
            icon="compare-horizontal"
            onPress={() => router.push('/stacks/compare-cards' as any)}
          >
            Compare ({selectedCards.length})
          </Chip>
        )}
      </View>

      {/* Cards List */}
      {isLoading ? (
        <LoadingState message="Loading cards..." />
      ) : cards.length === 0 ? (
        <EmptyState
          icon="credit-card-off-outline"
          title="No cards found"
          message="Try adjusting your search or filters."
        />
      ) : (
        <FlatList
          data={cards}
          renderItem={renderCardItem}
          keyExtractor={(item) => item.id || item.slug}
          numColumns={viewMode === 'grid' ? 2 : 1}
          key={viewMode}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
  },
  searchbar: {
    marginTop: 8,
    marginBottom: 8,
    borderRadius: 12,
  },
  filterRow: {
    paddingVertical: 4,
    gap: 8,
  },
  filterChip: {
    marginRight: 4,
  },
  toolbar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 4,
  },
  viewToggle: {
    flexDirection: 'row',
  },
  listContent: {
    paddingBottom: 16,
  },
  cardItem: {
    borderRadius: 12,
    marginBottom: 8,
    flex: 1,
  },
  cardPressable: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  cardContent: {
    flex: 1,
  },
  cardMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    gap: 8,
  },
  matchChip: {
    height: 24,
  },
});
