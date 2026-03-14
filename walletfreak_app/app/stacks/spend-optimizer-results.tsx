import React, { useEffect } from 'react';
import { View, StyleSheet, ScrollView, Pressable } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { CardImage } from '../../src/components/ui/CardImage';
import { useCalculateSpendIt } from '../../src/hooks/useCalculators';
import { formatCurrency } from '../../src/utils/formatters';

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

  const { wallet_results, opportunity_results } = data;
  const topResult = wallet_results[0] || opportunity_results[0];

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.scrollContent}
    >
      {/* Hero Card */}
      {topResult && (
        <LinearGradient
          colors={['#0F172A', '#1E293B', '#1A2744']}
          style={styles.heroCard}
        >
          <Text style={styles.heroLabel}>YOU COULD EARN</Text>
          <Text style={styles.heroPoints}>
            {topResult.est_points?.toLocaleString() ?? '0'}
          </Text>
          <Text style={styles.heroPointsLabel}>Points</Text>
          <View style={styles.heroValuePill}>
            <MaterialCommunityIcons name="currency-usd" size={16} color="#94A3B8" />
            <Text style={styles.heroValueText}>
              ~{formatCurrency(topResult.est_value)} Value
            </Text>
          </View>
        </LinearGradient>
      )}

      {/* Recommended Card */}
      {topResult && (
        <Pressable
          style={[styles.recommendedCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}
          onPress={() => router.push(`/stacks/card-detail/${topResult.slug}` as any)}
        >
          <Text style={styles.recommendedLabel}>RECOMMENDED CARD</Text>
          <View style={styles.recommendedRow}>
            <CardImage slug={topResult.slug} size="small" />
            <View style={{ flex: 1 }}>
              <Text style={[styles.recommendedName, { color: theme.colors.onSurface }]}>
                {topResult.card_name}
              </Text>
              <Text style={styles.recommendedRate}>
                {topResult.earning_rate} Multiplier
              </Text>
            </View>
          </View>
        </Pressable>
      )}

      {/* Other wallet results */}
      {wallet_results.length > 1 && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>Also in Your Wallet</Text>
          {wallet_results.slice(1).map((item) => (
            <Pressable
              key={item.slug}
              style={[styles.altCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}
              onPress={() => router.push(`/stacks/card-detail/${item.slug}` as any)}
            >
              <CardImage slug={item.slug} size="small" />
              <View style={{ flex: 1 }}>
                <Text style={[styles.altName, { color: theme.colors.onSurface }]} numberOfLines={1}>{item.card_name}</Text>
                <Text style={styles.altDetail}>{item.earning_rate} · ~{formatCurrency(item.est_value)}</Text>
              </View>
              <MaterialCommunityIcons name="chevron-right" size={20} color={theme.colors.onSurfaceVariant} />
            </Pressable>
          ))}
        </View>
      )}

      {/* Opportunity results */}
      {opportunity_results.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>New Opportunities</Text>
          {opportunity_results.map((item) => (
            <Pressable
              key={item.slug}
              style={[styles.altCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}
              onPress={() => router.push(`/stacks/card-detail/${item.slug}` as any)}
            >
              <CardImage slug={item.slug} size="small" />
              <View style={{ flex: 1 }}>
                <Text style={[styles.altName, { color: theme.colors.onSurface }]} numberOfLines={1}>{item.card_name}</Text>
                <Text style={styles.altDetail}>{item.earning_rate} · ~{formatCurrency(item.est_value)}</Text>
              </View>
              <MaterialCommunityIcons name="chevron-right" size={20} color={theme.colors.onSurfaceVariant} />
            </Pressable>
          ))}
        </View>
      )}

      {!topResult && (
        <EmptyState
          icon="magnify-close"
          title="No results"
          message="No cards match this spend category."
        />
      )}

      {/* Optimize Another */}
      <Pressable
        style={[styles.anotherButton, { backgroundColor: theme.colors.surfaceVariant }]}
        onPress={() => router.replace('/stacks/spend-optimizer' as any)}
      >
        <Text style={[styles.anotherButtonText, { color: theme.colors.onSurface }]}>
          Optimize Another Purchase
        </Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  // Hero
  heroCard: {
    borderRadius: 18,
    padding: 28,
    alignItems: 'center',
    marginBottom: 16,
  },
  heroLabel: {
    fontSize: 12,
    fontFamily: 'Outfit-SemiBold',
    color: '#94A3B8',
    letterSpacing: 1,
    marginBottom: 8,
  },
  heroPoints: {
    fontSize: 52,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
    lineHeight: 58,
  },
  heroPointsLabel: {
    fontSize: 16,
    fontFamily: 'Outfit-Medium',
    color: '#16A34A',
    marginBottom: 14,
  },
  heroValuePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(255,255,255,0.1)',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
  },
  heroValueText: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    color: '#CBD5E1',
  },
  // Recommended
  recommendedCard: {
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    marginBottom: 16,
  },
  recommendedLabel: {
    fontSize: 11,
    fontFamily: 'Outfit-Bold',
    color: '#64748B',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  recommendedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  recommendedName: {
    fontSize: 17,
    fontFamily: 'Outfit-Bold',
  },
  recommendedRate: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    color: '#16A34A',
    marginTop: 2,
  },
  // Section
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontFamily: 'Outfit-Bold',
    marginBottom: 10,
  },
  // Alt cards
  altCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    marginBottom: 8,
  },
  altName: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
  },
  altDetail: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#64748B',
    marginTop: 2,
  },
  // Optimize Another
  anotherButton: {
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  anotherButtonText: {
    fontSize: 16,
    fontFamily: 'Outfit-SemiBold',
  },
});
