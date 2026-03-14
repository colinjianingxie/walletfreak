import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../../src/components/layout/LoadingState';
import { EmptyState } from '../../../src/components/layout/EmptyState';
import { StrategyCard } from '../../../src/components/booking/StrategyCard';
import { useStrategy } from '../../../src/hooks/useBooking';

export default function BookingStrategyScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();

  const { data: strategy, isLoading, isError } = useStrategy(id);

  if (isLoading || !strategy) {
    return <LoadingState message="Loading strategy..." />;
  }

  if (isError) {
    return (
      <EmptyState
        icon="alert-circle-outline"
        title="Something went wrong"
        message="Could not load the strategy report."
        actionLabel="Go Back"
        onAction={() => router.back()}
      />
    );
  }

  if (strategy.status === 'processing') {
    return (
      <View style={[styles.processingContainer, { backgroundColor: theme.colors.background }]}>
        <View style={styles.processingBox}>
          <MaterialCommunityIcons name="robot-outline" size={48} color="#6366F1" />
          <Text style={styles.processingTitle}>Analyzing Hotels</Text>
          <Text style={styles.processingSubtitle}>
            Our AI is searching real-time prices, award availability, and calculating the best strategies
            for your {strategy.hotel_count} hotel{strategy.hotel_count !== 1 ? 's' : ''}...
          </Text>
          <View style={styles.processingMeta}>
            <Text style={styles.processingMetaText}>
              {strategy.location_text} · {strategy.check_in} → {strategy.check_out}
            </Text>
          </View>
          <LoadingState message="This usually takes 30-60 seconds..." />
        </View>
      </View>
    );
  }

  if (strategy.status === 'failed') {
    return (
      <EmptyState
        icon="alert-circle-outline"
        title="Analysis Failed"
        message="The strategy analysis could not be completed. Please try again."
        actionLabel="Go Back"
        onAction={() => router.back()}
      />
    );
  }

  const results = strategy.analysis_results ?? [];

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={{ paddingBottom: 40 }}
    >
      {/* Summary Header */}
      <View style={styles.summarySection}>
        <Text style={styles.summaryTitle}>Strategy Report</Text>
        <Text style={[styles.summarySubtitle, { color: theme.colors.onSurfaceVariant }]}>
          {strategy.location_text} · {strategy.check_in} → {strategy.check_out} · {strategy.guests} guest{strategy.guests !== '1' ? 's' : ''}
        </Text>
      </View>

      {/* Insight Box */}
      {results.length > 0 && (
        <View style={styles.insightBox}>
          <View style={styles.insightHeader}>
            <MaterialCommunityIcons name="lightbulb-on" size={16} color="#FACC15" />
            <Text style={styles.insightHeaderText}>The Freak's Analysis</Text>
          </View>
          <Text style={styles.insightText}>
            Analyzed {results.length} hotel{results.length !== 1 ? 's' : ''} with real-time pricing,
            award availability, and your card portfolio to find the best booking strategies.
          </Text>
        </View>
      )}

      {/* Strategy Cards */}
      {results.length === 0 ? (
        <EmptyState
          icon="magnify-close"
          title="No results"
          message="No analysis results were returned."
        />
      ) : (
        results.map((analysis, idx) => (
          <StrategyCard key={`${analysis.hotel_id}-${idx}`} analysis={analysis} />
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  processingContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
  },
  processingBox: {
    alignItems: 'center',
    gap: 12,
  },
  processingTitle: {
    fontSize: 20,
    fontFamily: 'Outfit-Bold',
    color: '#0F172A',
  },
  processingSubtitle: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 20,
    paddingHorizontal: 16,
  },
  processingMeta: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  processingMetaText: {
    fontSize: 12,
    fontFamily: 'Outfit-Medium',
    color: '#64748B',
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
  // Insight
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
});
