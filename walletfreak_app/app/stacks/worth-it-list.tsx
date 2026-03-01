import React from 'react';
import { View, StyleSheet, FlatList } from 'react-native';
import { Text, Surface, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { CardImage } from '../../src/components/ui/CardImage';
import { useWallet } from '../../src/hooks/useWallet';
import { formatCurrency } from '../../src/utils/formatters';
import { colors } from '../../src/theme';

export default function WorthItListScreen() {
  const { data: walletData, isLoading } = useWallet();
  const router = useRouter();
  const theme = useTheme();

  if (isLoading) {
    return <LoadingState message="Calculating..." />;
  }

  const allCards = [
    ...(walletData?.active_cards ?? []),
    ...(walletData?.inactive_cards ?? []),
  ];

  // Calculate net value per card (extracted value - annual fee)
  const cardValues = allCards.map((card: any) => {
    const cardBenefits = [
      ...(walletData?.action_needed_benefits ?? []),
      ...(walletData?.maxed_out_benefits ?? []),
      ...(walletData?.ignored_benefits ?? []),
    ].filter((b: any) => b.user_card_id === card.user_card_id);

    const totalBenefitValue = cardBenefits.reduce((sum: number, b: any) => sum + (b.amount || 0), 0);
    const extractedValue = cardBenefits.reduce((sum: number, b: any) => sum + (b.ytd_used || 0), 0);
    const netValue = totalBenefitValue - (card.annual_fee || 0);

    return {
      ...card,
      totalBenefitValue,
      extractedValue,
      netValue,
      worthIt: netValue >= 0,
    };
  }).sort((a: any, b: any) => b.netValue - a.netValue);

  if (cardValues.length === 0) {
    return (
      <EmptyState
        icon="scale-balance"
        title="No cards to analyze"
        message="Add cards to your wallet to see if they're worth keeping."
        actionLabel="Go to Explore"
        onAction={() => router.push('/(tabs)/explore' as any)}
      />
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <FlatList
        data={cardValues}
        renderItem={({ item }) => (
          <Surface style={[styles.card, { backgroundColor: theme.colors.elevation.level1 }]} elevation={1}>
            <View style={styles.cardRow}>
              <CardImage slug={item.card_id} size="small" style={{ marginRight: 12 }} />
              <View style={{ flex: 1 }}>
                <Text variant="titleSmall" numberOfLines={1}>{item.name}</Text>
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                  Fee: {formatCurrency(item.annual_fee)} · Benefits: {formatCurrency(item.totalBenefitValue)}
                </Text>
              </View>
              <View style={{ alignItems: 'flex-end' }}>
                <Text
                  variant="titleSmall"
                  style={{ color: item.worthIt ? colors.success : theme.colors.error }}
                >
                  {item.netValue >= 0 ? '+' : ''}{formatCurrency(item.netValue)}
                </Text>
                <MaterialCommunityIcons
                  name={item.worthIt ? 'thumb-up-outline' : 'thumb-down-outline'}
                  size={16}
                  color={item.worthIt ? colors.success : theme.colors.error}
                />
              </View>
            </View>
          </Surface>
        )}
        keyExtractor={(item) => item.user_card_id || item.id}
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
    paddingTop: 16,
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
