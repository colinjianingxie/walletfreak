import React from 'react';
import { View, StyleSheet, FlatList, Pressable } from 'react-native';
import { Text, Surface, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { CardImage } from '../../src/components/ui/CardImage';
import { useWorthItCards } from '../../src/hooks/useCalculators';
import { formatCurrency } from '../../src/utils/formatters';
import type { WorthItCardItem } from '../../src/api/endpoints/calculators';

export default function WorthItListScreen() {
  const { data, isLoading } = useWorthItCards();
  const router = useRouter();
  const theme = useTheme();

  if (isLoading) {
    return <LoadingState message="Loading cards..." />;
  }

  const cards = data?.cards ?? [];

  if (cards.length === 0) {
    return (
      <EmptyState
        icon="scale-balance"
        title="No cards to analyze"
        message="No cards with annual fees found."
      />
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <Text
        variant="bodyMedium"
        style={{ color: theme.colors.onSurfaceVariant, paddingHorizontal: 4, paddingTop: 16, paddingBottom: 8 }}
      >
        Which annual fee are we auditing today?
      </Text>
      <FlatList
        data={cards}
        renderItem={({ item }: { item: WorthItCardItem }) => (
          <Surface style={[styles.card, { backgroundColor: theme.colors.elevation.level1 }]} elevation={1}>
            <Pressable
              onPress={() => router.push(`/stacks/worth-it-audit?slug=${item.card_id}` as any)}
              style={styles.cardRow}
            >
              <CardImage slug={item.card_id} size="small" style={{ marginRight: 12 }} />
              <View style={{ flex: 1 }}>
                <Text variant="titleSmall" numberOfLines={1}>{item.name}</Text>
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                  {formatCurrency(item.annual_fee)} / YEAR
                </Text>
              </View>
              <MaterialCommunityIcons
                name="chevron-right"
                size={20}
                color={theme.colors.onSurfaceVariant}
              />
            </Pressable>
          </Surface>
        )}
        keyExtractor={(item) => item.card_id}
        contentContainerStyle={styles.list}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
  },
  list: {
    paddingBottom: 16,
  },
  card: {
    borderRadius: 12,
    marginBottom: 8,
  },
  cardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
});
