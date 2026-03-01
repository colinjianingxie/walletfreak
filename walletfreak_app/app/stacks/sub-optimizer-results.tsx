import React, { useEffect } from 'react';
import { View, StyleSheet, ScrollView, Pressable } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { CardImage } from '../../src/components/ui/CardImage';
import { useCalculateSubOptimizer } from '../../src/hooks/useCalculators';
import { formatCurrency } from '../../src/utils/formatters';

export default function SubOptimizerResultsScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { spend, timeframe, sortBy } = useLocalSearchParams<{
    spend: string;
    timeframe: string;
    sortBy: string;
  }>();
  const mutation = useCalculateSubOptimizer();

  useEffect(() => {
    mutation.mutate({
      planned_spend: parseFloat(spend) || 4000,
      duration_months: parseInt(timeframe) || 3,
      sort_by: sortBy || 'recommended',
    });
  }, []);

  if (mutation.isPending) {
    return <LoadingState message="Scanning ROI leaderboard..." />;
  }

  if (mutation.isError) {
    return (
      <EmptyState
        icon="alert-circle-outline"
        title="Something went wrong"
        message="Could not calculate results. Please try again."
        actionLabel="Go Back"
        onAction={() => router.back()}
      />
    );
  }

  const results = mutation.data?.results ?? [];
  const topPick = results.find((r) => r.is_top_pick) ?? results[0];

  if (results.length === 0) {
    return (
      <EmptyState
        icon="magnify-close"
        title="No cards found"
        message="No cards match your criteria. Try adjusting your spend or timeframe."
        actionLabel="Go Back"
        onAction={() => router.back()}
      />
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={{ paddingBottom: 40 }}
    >
      {/* Summary */}
      <View style={styles.summarySection}>
        <Text style={styles.summaryTitle}>Recommendation Leaderboard</Text>
        <Text style={[styles.summarySubtitle, { color: theme.colors.onSurfaceVariant }]}>
          {formatCurrency(parseFloat(spend) || 4000)} spend · {timeframe} month{timeframe !== '1' ? 's' : ''}
        </Text>
      </View>

      {/* Freak's Insight */}
      {topPick && (
        <View style={styles.insightBox}>
          <View style={styles.insightHeader}>
            <MaterialCommunityIcons name="lightbulb-on" size={16} color="#FACC15" />
            <Text style={styles.insightHeaderText}>The Freak's Insight</Text>
          </View>
          <Text style={styles.insightText}>
            The <Text style={styles.insightBold}>{topPick.name}</Text> leads with{' '}
            {formatCurrency(topPick.net_value)} net value and {topPick.roi}% ROI on your{' '}
            {formatCurrency(parseFloat(spend) || 4000)} spend.
          </Text>
        </View>
      )}

      {/* Result Cards */}
      {results.map((item, idx) => (
        <Pressable
          key={item.slug}
          style={styles.resultCard}
          onPress={() => router.push(`/stacks/card-detail/${item.slug}` as any)}
        >
          {/* Rank + Card Info */}
          <View style={styles.resultHeader}>
            <View style={[styles.rankCircle, idx === 0 && styles.rankCircleTop]}>
              <Text style={[styles.rankText, idx === 0 && styles.rankTextTop]}>#{idx + 1}</Text>
            </View>
            <CardImage slug={item.slug} size="small" style={{ marginRight: 10 }} />
            <View style={{ flex: 1 }}>
              <Text style={styles.resultCardName} numberOfLines={1}>{item.name}</Text>
              <Text style={styles.resultCardIssuer}>{item.issuer}</Text>
            </View>
          </View>

          {/* Badges */}
          <View style={styles.badgeRow}>
            {item.is_top_pick && (
              <View style={styles.topPickBadge}>
                <MaterialCommunityIcons name="crown" size={10} color="#FACC15" />
                <Text style={styles.topPickBadgeText}>TOP PICK</Text>
              </View>
            )}
            {item.is_fee_neutral && (
              <View style={styles.feeNeutralBadge}>
                <Text style={styles.feeNeutralBadgeText}>FEE-NEUTRAL</Text>
              </View>
            )}
          </View>

          {/* Details */}
          <View style={styles.resultDetails}>
            <View style={styles.resultDetailRow}>
              <Text style={styles.resultDetailLabel}>Spend Requirement</Text>
              <Text style={styles.resultDetailValue}>{item.spend_requirement || 'None'}</Text>
            </View>
            <View style={styles.resultDetailRow}>
              <Text style={styles.resultDetailLabel}>Timeframe</Text>
              <Text style={styles.resultDetailValue}>
                {timeframe} month{timeframe !== '1' ? 's' : ''}
              </Text>
            </View>
            <View style={styles.resultDetailRow}>
              <Text style={styles.resultDetailLabel}>Ongoing Rate</Text>
              <Text style={styles.resultDetailValue}>{item.ongoing_rate}</Text>
            </View>
          </View>

          {/* ROI Badge */}
          <View style={styles.roiBadge}>
            <Text style={styles.roiBadgeText}>{item.roi}% ROI</Text>
          </View>

          {/* Net Value + CTA */}
          <View style={styles.resultFooter}>
            <View>
              <Text style={styles.netValueLabel}>Net Value</Text>
              <Text style={[styles.netValue, { color: item.net_value >= 0 ? '#16A34A' : '#DC2626' }]}>
                {item.net_value >= 0 ? '+' : ''}{formatCurrency(item.net_value)}
              </Text>
            </View>
            <View style={styles.viewApplyButton}>
              <Text style={styles.viewApplyText}>VIEW & APPLY</Text>
              <MaterialCommunityIcons name="arrow-right" size={14} color="#4F46E5" />
            </View>
          </View>
        </Pressable>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  // Summary
  summarySection: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 4,
  },
  summaryTitle: {
    fontSize: 22,
    fontFamily: 'Outfit-Bold',
    color: '#0F172A',
    marginBottom: 4,
  },
  summarySubtitle: {
    fontSize: 14,
    fontFamily: 'Outfit',
    marginBottom: 16,
  },
  // Insight Box
  insightBox: {
    backgroundColor: '#312E81',
    borderRadius: 14,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 20,
  },
  insightHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  insightHeaderText: {
    fontSize: 13,
    fontFamily: 'Outfit-Bold',
    color: '#C7D2FE',
    letterSpacing: 0.3,
  },
  insightText: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: '#E0E7FF',
    lineHeight: 20,
  },
  insightBold: {
    fontFamily: 'Outfit-SemiBold',
    color: '#FFFFFF',
  },
  // Result Card
  resultCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  rankCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F1F5F9',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  rankCircleTop: {
    backgroundColor: '#312E81',
  },
  rankText: {
    fontSize: 12,
    fontFamily: 'Outfit-Bold',
    color: '#64748B',
  },
  rankTextTop: {
    color: '#FFFFFF',
  },
  resultCardName: {
    fontSize: 15,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  resultCardIssuer: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#64748B',
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: 12,
    flexWrap: 'wrap',
  },
  topPickBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#312E81',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  topPickBadgeText: {
    fontSize: 9,
    fontFamily: 'Outfit-Bold',
    color: '#FACC15',
    letterSpacing: 0.5,
  },
  feeNeutralBadge: {
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  feeNeutralBadgeText: {
    fontSize: 9,
    fontFamily: 'Outfit-Bold',
    color: '#16A34A',
    letterSpacing: 0.5,
  },
  resultDetails: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 12,
    gap: 6,
    marginBottom: 12,
  },
  resultDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  resultDetailLabel: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#64748B',
  },
  resultDetailValue: {
    fontSize: 13,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  roiBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#312E81',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 8,
    marginBottom: 12,
  },
  roiBadgeText: {
    fontSize: 13,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
  },
  resultFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingTop: 12,
  },
  netValueLabel: {
    fontSize: 10,
    fontFamily: 'Outfit-Medium',
    color: '#94A3B8',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  netValue: {
    fontSize: 20,
    fontFamily: 'Outfit-Bold',
  },
  viewApplyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  viewApplyText: {
    fontSize: 12,
    fontFamily: 'Outfit-Bold',
    color: '#4F46E5',
    letterSpacing: 0.5,
  },
});
