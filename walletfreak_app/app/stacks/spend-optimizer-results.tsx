import React, { useEffect } from 'react';
import { View, StyleSheet, ScrollView, Pressable } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { CardImage } from '../../src/components/ui/CardImage';
import { useCalculateSpendIt } from '../../src/hooks/useCalculators';
import { formatCurrency } from '../../src/utils/formatters';
import type { SpendItResultItem } from '../../src/api/endpoints/calculators';

export default function SpendOptimizerResultsScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { amount, category, subCategory } = useLocalSearchParams<{
    amount: string;
    category: string;
    subCategory: string;
  }>();
  const mutation = useCalculateSpendIt();

  useEffect(() => {
    const amt = parseFloat(amount) || 500;
    mutation.mutate({ amount: amt, category: category || '', subCategory: subCategory || '' });
  }, []); // Run once on mount

  if (mutation.isPending) {
    return <LoadingState message="Finding your best cards..." />;
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

  const data = mutation.data;
  if (!data) return null;

  const { wallet_results, opportunity_results, lost_value, net_gain } = data;

  const renderCardResult = (item: SpendItResultItem, idx: number) => (
    <Pressable
      key={item.slug}
      style={styles.resultCard}
      onPress={() => router.push(`/stacks/card-detail/${item.slug}` as any)}
    >
      <View style={styles.resultHeader}>
        <View style={[styles.rankBadge, idx === 0 && styles.rankBadgeTop]}>
          <Text style={[styles.rankText, idx === 0 && styles.rankTextTop]}>#{idx + 1}</Text>
        </View>
        <CardImage slug={item.slug} size="small" style={{ marginRight: 10 }} />
        <View style={{ flex: 1 }}>
          <Text style={styles.resultName} numberOfLines={1}>{item.card_name}</Text>
          <Text style={styles.resultIssuer}>{item.issuer}</Text>
        </View>
        {item.is_winner && (
          <View style={styles.winnerBadge}>
            <MaterialCommunityIcons name="crown" size={10} color="#FACC15" />
            <Text style={styles.winnerBadgeText}>BEST</Text>
          </View>
        )}
      </View>

      <View style={styles.resultDetails}>
        <View style={styles.resultDetailRow}>
          <Text style={styles.detailLabel}>Earning Rate</Text>
          <Text style={styles.detailValue}>{item.earning_rate}</Text>
        </View>
        <View style={styles.resultDetailRow}>
          <Text style={styles.detailLabel}>Est. Points</Text>
          <Text style={styles.detailValue}>
            {item.est_points?.toLocaleString()} {item.currency_display}
          </Text>
        </View>
        <View style={styles.resultDetailRow}>
          <Text style={styles.detailLabel}>Est. Value</Text>
          <Text style={[styles.detailValue, { color: '#16A34A', fontFamily: 'Outfit-Bold' }]}>
            {formatCurrency(item.est_value)}
          </Text>
        </View>
      </View>

      <View style={styles.resultFooter}>
        <Text style={styles.categoryMatch}>{item.category_matched}</Text>
        <MaterialCommunityIcons name="chevron-right" size={18} color="#94A3B8" />
      </View>
    </Pressable>
  );

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={{ paddingBottom: 40 }}
    >
      {/* Summary Header */}
      <View style={styles.summarySection}>
        <Text style={styles.summaryTitle}>
          ${amount} on {category}
          {subCategory ? ` · ${subCategory}` : ''}
        </Text>

        {/* Stats row */}
        <View style={styles.statsRow}>
          <View style={styles.statBox}>
            <Text style={styles.statLabel}>Net Gain</Text>
            <Text style={[styles.statValue, { color: net_gain >= 0 ? '#16A34A' : '#DC2626' }]}>
              {net_gain >= 0 ? '+' : ''}{formatCurrency(net_gain)}
            </Text>
          </View>
          {lost_value > 0 && (
            <View style={styles.statBox}>
              <Text style={styles.statLabel}>Lost Value</Text>
              <Text style={[styles.statValue, { color: '#DC2626' }]}>
                {formatCurrency(lost_value)}
              </Text>
            </View>
          )}
        </View>
      </View>

      {/* Your Best Moves */}
      {wallet_results.length > 0 && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <MaterialCommunityIcons name="wallet" size={20} color="#4F46E5" />
            <Text style={styles.sectionTitle}>Your Best Moves</Text>
          </View>
          <Text style={[styles.sectionSubtitle, { color: theme.colors.onSurfaceVariant }]}>
            Cards already in your wallet
          </Text>
          {wallet_results.map((item, idx) => renderCardResult(item, idx))}
        </View>
      )}

      {/* New Opportunities */}
      {opportunity_results.length > 0 && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <MaterialCommunityIcons name="lightbulb-on-outline" size={20} color="#F59E0B" />
            <Text style={styles.sectionTitle}>New Opportunities</Text>
          </View>
          <Text style={[styles.sectionSubtitle, { color: theme.colors.onSurfaceVariant }]}>
            Cards you could add to your wallet
          </Text>
          {opportunity_results.map((item, idx) => renderCardResult(item, idx))}
        </View>
      )}

      {wallet_results.length === 0 && opportunity_results.length === 0 && (
        <EmptyState
          icon="magnify-close"
          title="No results"
          message="No cards match this spend category. Try a different category or amount."
        />
      )}
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
    paddingBottom: 8,
  },
  summaryTitle: {
    fontSize: 22,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
    marginBottom: 12,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 8,
  },
  statBox: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  statLabel: {
    fontSize: 11,
    fontFamily: 'Outfit-Medium',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 22,
    fontFamily: 'Outfit-Bold',
  },
  // Section
  section: {
    paddingHorizontal: 16,
    marginTop: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
  },
  sectionSubtitle: {
    fontSize: 13,
    fontFamily: 'Outfit',
    marginBottom: 12,
  },
  // Result Card
  resultCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  rankBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#F1F5F9',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  rankBadgeTop: {
    backgroundColor: '#4F46E5',
  },
  rankText: {
    fontSize: 11,
    fontFamily: 'Outfit-Bold',
    color: '#64748B',
  },
  rankTextTop: {
    color: '#FFFFFF',
  },
  resultName: {
    fontSize: 15,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  resultIssuer: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#64748B',
  },
  winnerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#312E81',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  winnerBadgeText: {
    fontSize: 9,
    fontFamily: 'Outfit-Bold',
    color: '#FACC15',
    letterSpacing: 0.5,
  },
  resultDetails: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 12,
    gap: 6,
    marginBottom: 8,
  },
  resultDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#64748B',
  },
  detailValue: {
    fontSize: 13,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  resultFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  categoryMatch: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#94A3B8',
  },
});
