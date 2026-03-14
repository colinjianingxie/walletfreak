import React, { useMemo } from 'react';
import { View, StyleSheet, ScrollView, Pressable } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { CardImage } from '../../src/components/ui/CardImage';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { useCardsStore } from '../../src/stores/cardsStore';
import { useCardDetail } from '../../src/hooks/useCards';
import { formatCurrency } from '../../src/utils/formatters';

function useCardData(slug: string) {
  const { data, isLoading } = useCardDetail(slug);
  return { card: data, isLoading };
}

// Row component for a single comparison field
function CompareRow({
  label,
  icon,
  values,
  highlight,
}: {
  label: string;
  icon: string;
  values: (string | React.ReactNode)[];
  highlight?: 'lowest' | 'highest' | null;
}) {
  const theme = useTheme();

  return (
    <View style={[styles.compareRow, { borderBottomColor: theme.colors.outlineVariant }]}>
      <View style={styles.rowLabel}>
        <MaterialCommunityIcons name={icon as any} size={14} color="#64748B" />
        <Text style={styles.rowLabelText}>{label}</Text>
      </View>
      <View style={styles.rowValues}>
        {values.map((val, i) => (
          <View key={i} style={styles.rowValueCell}>
            {typeof val === 'string' ? (
              <Text style={styles.rowValueText} numberOfLines={3}>{val}</Text>
            ) : (
              val
            )}
          </View>
        ))}
      </View>
    </View>
  );
}

function CompareContent({ slugs }: { slugs: string[] }) {
  const theme = useTheme();
  const router = useRouter();

  // Fetch all cards
  const card0 = useCardData(slugs[0] || '');
  const card1 = useCardData(slugs[1] || '');
  const card2 = useCardData(slugs[2] || '');
  const card3 = useCardData(slugs[3] || '');

  const allCardData = [card0, card1, card2, card3].slice(0, slugs.length);
  const cards = allCardData.map((d) => d.card);
  const isAnyLoading = allCardData.some((d) => d.isLoading);

  // Build comparison data
  const comparisonRows = useMemo(() => {
    if (cards.some((c) => !c)) return [];

    const rows: { label: string; icon: string; values: string[] }[] = [];

    // Annual Fee
    rows.push({
      label: 'Annual Fee',
      icon: 'credit-card-outline',
      values: cards.map((c) => c!.annual_fee > 0 ? formatCurrency(c!.annual_fee) : 'No Fee'),
    });

    // Welcome Bonus
    rows.push({
      label: 'Welcome Bonus',
      icon: 'gift-outline',
      values: cards.map((c) => c!.welcome_bonus || 'None'),
    });

    // Total Credits Value
    rows.push({
      label: 'Credits Value',
      icon: 'currency-usd',
      values: cards.map((c) => {
        const total = (c!.benefits || []).reduce(
          (sum: number, b: any) => sum + (b.dollar_value || 0),
          0
        );
        return total > 0 ? formatCurrency(total) : '$0';
      }),
    });

    // Number of Benefits
    rows.push({
      label: 'Benefits',
      icon: 'star-outline',
      values: cards.map((c) => `${c!.benefits?.length ?? 0} perks`),
    });

    // Top Earning Rate
    rows.push({
      label: 'Top Earning',
      icon: 'chart-line',
      values: cards.map((c) => {
        const rates = c!.earning_rates || [];
        if (rates.length === 0) return 'N/A';
        return `${rates[0].rate} on ${rates[0].category}`;
      }),
    });

    // Issuer
    rows.push({
      label: 'Issuer',
      icon: 'domain',
      values: cards.map((c) => c!.issuer || 'Unknown'),
    });

    return rows;
  }, [cards]);

  if (isAnyLoading || cards.some((c) => !c)) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={{ color: theme.colors.onSurfaceVariant }}>Loading card details...</Text>
      </View>
    );
  }

  // Find best values for highlighting
  const fees = cards.map((c) => c!.annual_fee || 0);
  const lowestFeeIdx = fees.indexOf(Math.min(...fees));

  const creditsValues = cards.map((c) =>
    (c!.benefits || []).reduce((sum: number, b: any) => sum + (b.dollar_value || 0), 0)
  );
  const highestCreditsIdx = creditsValues.indexOf(Math.max(...creditsValues));

  return (
    <ScrollView
      style={{ backgroundColor: theme.colors.background }}
      contentContainerStyle={styles.content}
    >
      {/* Card Headers - horizontal scroll for overflow */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={styles.cardHeaders}>
          {cards.map((card, i) => (
            <Pressable
              key={slugs[i]}
              style={styles.cardHeaderItem}
              onPress={() => router.push(`/stacks/card-detail/${slugs[i]}` as any)}
            >
              <CardImage slug={slugs[i]} size="medium" style={{ marginBottom: 8 }} />
              <Text style={styles.cardHeaderName} numberOfLines={2}>{card!.name}</Text>
              <Text style={[styles.cardHeaderIssuer, { color: theme.colors.onSurfaceVariant }]}>
                {card!.issuer}
              </Text>
            </Pressable>
          ))}
        </View>
      </ScrollView>

      {/* Comparison Table */}
      <View style={styles.tableContainer}>
        {comparisonRows.map((row, rowIdx) => (
          <CompareRow
            key={row.label}
            label={row.label}
            icon={row.icon}
            values={row.values.map((val, colIdx) => {
              // Highlight best value
              const isBest =
                (rowIdx === 0 && colIdx === lowestFeeIdx && slugs.length > 1) ||
                (rowIdx === 2 && colIdx === highestCreditsIdx && creditsValues[highestCreditsIdx] > 0 && slugs.length > 1);
              return (
                <Text
                  key={colIdx}
                  style={[
                    styles.rowValueText,
                    isBest && styles.rowValueHighlight,
                  ]}
                  numberOfLines={3}
                >
                  {val}
                </Text>
              );
            })}
          />
        ))}
      </View>

      {/* Top Benefits Detail */}
      <View style={styles.benefitsSection}>
        <Text style={styles.benefitsSectionTitle}>Top Benefits</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.benefitsColumns}>
            {cards.map((card, i) => (
              <View key={slugs[i]} style={styles.benefitsColumn}>
                <Text style={styles.benefitsColumnHeader} numberOfLines={1}>{card!.name}</Text>
                {(card!.benefits || []).slice(0, 5).map((b: any, bIdx: number) => (
                  <View key={bIdx} style={[styles.benefitItem, { borderColor: theme.colors.outlineVariant }]}>
                    {b.dollar_value > 0 && (
                      <Text style={styles.benefitValue}>{formatCurrency(b.dollar_value)}</Text>
                    )}
                    <Text style={styles.benefitDesc} numberOfLines={2}>{b.description}</Text>
                  </View>
                ))}
                {(card!.benefits?.length ?? 0) > 5 && (
                  <Text style={[styles.moreText, { color: theme.colors.primary }]}>
                    +{card!.benefits!.length - 5} more
                  </Text>
                )}
              </View>
            ))}
          </View>
        </ScrollView>
      </View>
    </ScrollView>
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
      <CompareContent slugs={selectedCards} />
      <View style={[styles.bottomBar, { borderTopColor: theme.colors.outlineVariant }]}>
        <Pressable style={styles.clearButton} onPress={() => { clearCompare(); router.back(); }}>
          <MaterialCommunityIcons name="close" size={18} color="#64748B" />
          <Text style={styles.clearButtonText}>Clear All</Text>
        </Pressable>
        <Text style={styles.cardCount}>{selectedCards.length} cards</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    paddingBottom: 80,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  // Card Headers
  cardHeaders: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 20,
    gap: 12,
  },
  cardHeaderItem: {
    width: 120,
    alignItems: 'center',
  },
  cardHeaderName: {
    fontSize: 13,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
    textAlign: 'center',
  },
  cardHeaderIssuer: {
    fontSize: 11,
    fontFamily: 'Outfit',
    textAlign: 'center',
    marginTop: 2,
  },
  // Table
  tableContainer: {
    marginHorizontal: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  compareRow: {
    borderBottomWidth: 1,
    paddingVertical: 12,
    paddingHorizontal: 14,
  },
  rowLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  rowLabelText: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  rowValues: {
    flexDirection: 'row',
    gap: 8,
  },
  rowValueCell: {
    flex: 1,
  },
  rowValueText: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    color: '#1C1B1F',
  },
  rowValueHighlight: {
    color: '#16A34A',
    fontFamily: 'Outfit-Bold',
  },
  // Benefits Section
  benefitsSection: {
    marginTop: 20,
    paddingHorizontal: 16,
  },
  benefitsSectionTitle: {
    fontSize: 18,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
    marginBottom: 12,
  },
  benefitsColumns: {
    flexDirection: 'row',
    gap: 12,
  },
  benefitsColumn: {
    width: 180,
  },
  benefitsColumnHeader: {
    fontSize: 13,
    fontFamily: 'Outfit-SemiBold',
    color: '#4361EE',
    marginBottom: 8,
  },
  benefitItem: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    marginBottom: 6,
    backgroundColor: '#FFFFFF',
  },
  benefitValue: {
    fontSize: 14,
    fontFamily: 'Outfit-Bold',
    color: '#16A34A',
    marginBottom: 2,
  },
  benefitDesc: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#475569',
    lineHeight: 16,
  },
  moreText: {
    fontSize: 12,
    fontFamily: 'Outfit-Medium',
    marginTop: 4,
  },
  // Bottom Bar
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
  },
  clearButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  clearButtonText: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    color: '#64748B',
  },
  cardCount: {
    fontSize: 13,
    fontFamily: 'Outfit',
    color: '#94A3B8',
  },
});
