import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Text, Surface, Divider, Button, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { CardImage } from '../../src/components/ui/CardImage';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { useCardsStore } from '../../src/stores/cardsStore';
import { useCardDetail } from '../../src/hooks/useCards';
import { formatCurrency } from '../../src/utils/formatters';

function CompareColumn({ slug }: { slug: string }) {
  const { data: card, isLoading } = useCardDetail(slug);
  const theme = useTheme();

  if (isLoading || !card) {
    return (
      <View style={styles.column}>
        <Text variant="bodySmall">Loading...</Text>
      </View>
    );
  }

  return (
    <View style={styles.column}>
      <CardImage slug={slug} size="medium" style={{ alignSelf: 'center', marginBottom: 8 }} />
      <Text variant="labelLarge" numberOfLines={2} style={styles.cardName}>
        {card.name}
      </Text>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, textAlign: 'center' }}>
        {card.issuer}
      </Text>

      <Divider style={{ marginVertical: 8 }} />

      <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>Annual Fee</Text>
      <Text variant="titleSmall">{formatCurrency(card.annual_fee)}</Text>

      <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 8 }}>
        Welcome Bonus
      </Text>
      <Text variant="bodySmall" numberOfLines={3}>
        {card.welcome_bonus || 'None'}
      </Text>

      <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 8 }}>
        Benefits ({card.benefits?.length ?? 0})
      </Text>
      {card.benefits?.slice(0, 5).map((b: any, i: number) => (
        <Text key={i} variant="bodySmall" numberOfLines={1}>
          {b.dollar_value > 0 ? formatCurrency(b.dollar_value) + ' ' : ''}{b.description}
        </Text>
      ))}
      {(card.benefits?.length ?? 0) > 5 && (
        <Text variant="labelSmall" style={{ color: theme.colors.primary }}>
          +{card.benefits.length - 5} more
        </Text>
      )}

      <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 8 }}>
        Earning Rates
      </Text>
      {card.earning_rates?.slice(0, 4).map((r: any, i: number) => (
        <Text key={i} variant="bodySmall" numberOfLines={1}>
          {r.rate} — {r.category}
        </Text>
      ))}
    </View>
  );
}

export default function CompareCardsScreen() {
  const { selectedCards, clearCompare } = useCardsStore();
  const router = useRouter();
  const theme = useTheme();

  if (selectedCards.length === 0) {
    return (
      <EmptyState
        icon="compare-horizontal"
        title="No cards selected"
        message="Select cards from the Explore tab to compare them."
        actionLabel="Go to Explore"
        onAction={() => router.push('/(tabs)/explore' as any)}
      />
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={styles.compareRow}>
          {selectedCards.map((slug) => (
            <Surface
              key={slug}
              style={[styles.columnCard, { backgroundColor: theme.colors.elevation.level1 }]}
              elevation={1}
            >
              <CompareColumn slug={slug} />
            </Surface>
          ))}
        </View>
      </ScrollView>
      <Button
        mode="text"
        onPress={() => {
          clearCompare();
          router.back();
        }}
        style={{ marginTop: 16 }}
      >
        Clear Comparison
      </Button>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  compareRow: {
    flexDirection: 'row',
    gap: 12,
  },
  columnCard: {
    borderRadius: 12,
    width: 200,
  },
  column: {
    padding: 12,
  },
  cardName: {
    fontFamily: 'Outfit-Medium',
    textAlign: 'center',
  },
});
