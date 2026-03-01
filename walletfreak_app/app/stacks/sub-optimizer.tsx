import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, TextInput as RNTextInput, Pressable } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { CardImage } from '../../src/components/ui/CardImage';
import { useCalculateSubOptimizer } from '../../src/hooks/useCalculators';
import { formatCurrency } from '../../src/utils/formatters';
import type { SubOptimizerResult } from '../../src/api/endpoints/calculators';

const TIMEFRAME_OPTIONS = [
  { value: '1', label: '1 mo' },
  { value: '2', label: '2 mo' },
  { value: '3', label: '3 mo' },
  { value: '6', label: '6 mo' },
];

export default function SubOptimizerScreen() {
  const theme = useTheme();
  const router = useRouter();
  const [spend, setSpend] = useState('4000');
  const [timeframe, setTimeframe] = useState('3');
  const [sortBy, setSortBy] = useState('recommended');
  const calculateMutation = useCalculateSubOptimizer();

  const handleCalculate = () => {
    const amt = parseFloat(spend) || 4000;
    calculateMutation.mutate({
      planned_spend: amt,
      duration_months: parseInt(timeframe) || 3,
      sort_by: sortBy,
    });
  };

  const results = calculateMutation.data?.results ?? [];
  const topPick = results.find((r) => r.is_top_pick) ?? results[0];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ paddingBottom: 40 }}
    >
      {/* Dark Hero Section */}
      <LinearGradient
        colors={['#0F0F1A', '#1A1A2E', '#16213E']}
        style={styles.heroSection}
      >
        {/* Background orbs */}
        <View style={styles.orbContainer} pointerEvents="none">
          <View style={styles.yellowOrb} />
          <View style={styles.blueOrb} />
        </View>

        {/* Badge */}
        <View style={styles.heroBadge}>
          <MaterialCommunityIcons name="lightning-bolt" size={14} color="#FACC15" />
          <Text style={styles.heroBadgeText}>SIGN-UP BONUS INTEL</Text>
        </View>

        {/* Headline */}
        <Text style={styles.heroHeadline}>Target your next{'\n'}big haul.</Text>
        <Text style={styles.heroSubheadline}>
          Analyze sign-up bonus ROI across all cards and find the best value for your spend.
        </Text>

        {/* Glass Form */}
        <View style={styles.glassForm}>
          {/* Planned Spend */}
          <Text style={styles.formLabel}>Planned Spend</Text>
          <View style={styles.darkInput}>
            <Text style={styles.dollarPrefix}>$</Text>
            <RNTextInput
              style={styles.darkInputText}
              value={spend}
              onChangeText={setSpend}
              keyboardType="numeric"
              placeholder="4000"
              placeholderTextColor="rgba(255,255,255,0.3)"
            />
          </View>

          {/* Timeframe */}
          <Text style={[styles.formLabel, { marginTop: 16 }]}>Timeframe</Text>
          <View style={styles.timeframeRow}>
            {TIMEFRAME_OPTIONS.map((opt) => (
              <Pressable
                key={opt.value}
                style={[
                  styles.timeframeButton,
                  timeframe === opt.value && styles.timeframeButtonActive,
                ]}
                onPress={() => setTimeframe(opt.value)}
              >
                <Text
                  style={[
                    styles.timeframeButtonText,
                    timeframe === opt.value && styles.timeframeButtonTextActive,
                  ]}
                >
                  {opt.label}
                </Text>
              </Pressable>
            ))}
          </View>

          {/* Strategy */}
          <Text style={[styles.formLabel, { marginTop: 16 }]}>Strategy</Text>
          <View style={styles.strategyRow}>
            <Pressable
              style={[
                styles.strategyCard,
                sortBy === 'recommended' && styles.strategyCardActive,
              ]}
              onPress={() => setSortBy('recommended')}
            >
              <MaterialCommunityIcons
                name="lightning-bolt"
                size={20}
                color={sortBy === 'recommended' ? '#0F0F1A' : 'rgba(255,255,255,0.6)'}
              />
              <Text
                style={[
                  styles.strategyCardText,
                  sortBy === 'recommended' && styles.strategyCardTextActive,
                ]}
              >
                Freak Score
              </Text>
            </Pressable>
            <Pressable
              style={[
                styles.strategyCard,
                sortBy === 'value' && styles.strategyCardActive,
              ]}
              onPress={() => setSortBy('value')}
            >
              <MaterialCommunityIcons
                name="diamond-stone"
                size={20}
                color={sortBy === 'value' ? '#0F0F1A' : 'rgba(255,255,255,0.6)'}
              />
              <Text
                style={[
                  styles.strategyCardText,
                  sortBy === 'value' && styles.strategyCardTextActive,
                ]}
              >
                Pure Value
              </Text>
            </Pressable>
          </View>

          {/* CTA Button */}
          <Pressable
            style={[styles.ctaButton, calculateMutation.isPending && { opacity: 0.7 }]}
            onPress={handleCalculate}
            disabled={calculateMutation.isPending}
          >
            <MaterialCommunityIcons name="target" size={18} color="#0F0F1A" />
            <Text style={styles.ctaButtonText}>
              {calculateMutation.isPending ? 'Scanning...' : 'Scan ROI Leaderboard'}
            </Text>
          </Pressable>
        </View>
      </LinearGradient>

      {/* Results Section (light themed) */}
      {results.length > 0 && (
        <View style={[styles.resultsSection, { backgroundColor: theme.colors.background }]}>
          <Text style={styles.resultsTitle}>Recommendation Leaderboard</Text>

          {/* Freak's Insight */}
          {topPick && (
            <View style={styles.insightBox}>
              <View style={styles.insightHeader}>
                <MaterialCommunityIcons name="lightbulb-on" size={16} color="#FACC15" />
                <Text style={styles.insightHeaderText}>The Freak's Insight</Text>
              </View>
              <Text style={styles.insightText}>
                The <Text style={styles.insightBold}>{topPick.name}</Text> leads with{' '}
                {formatCurrency(topPick.net_value)} net value and {topPick.roi}% ROI on your {formatCurrency(parseFloat(spend) || 4000)} spend.
              </Text>
            </View>
          )}

          {/* Result Cards */}
          {results.map((item, idx) => (
            <View key={item.slug} style={styles.resultCard}>
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
                  <Text style={styles.resultDetailValue}>{timeframe} month{timeframe !== '1' ? 's' : ''}</Text>
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
                <Pressable
                  style={styles.viewApplyButton}
                  onPress={() => router.push(`/stacks/card-detail/${item.slug}` as any)}
                >
                  <Text style={styles.viewApplyText}>VIEW AND APPLY</Text>
                  <MaterialCommunityIcons name="arrow-right" size={14} color="#4F46E5" />
                </Pressable>
              </View>
            </View>
          ))}
        </View>
      )}

      {calculateMutation.data && results.length === 0 && (
        <View style={styles.emptyResults}>
          <MaterialCommunityIcons name="magnify-close" size={48} color="#94A3B8" />
          <Text style={styles.emptyResultsText}>
            No cards match your criteria. Try adjusting your spend or timeframe.
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  // Hero Section
  heroSection: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 28,
    position: 'relative',
    overflow: 'hidden',
  },
  orbContainer: {
    ...StyleSheet.absoluteFillObject,
  },
  yellowOrb: {
    position: 'absolute',
    top: -40,
    right: -30,
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: 'rgba(250, 204, 21, 0.08)',
  },
  blueOrb: {
    position: 'absolute',
    bottom: -60,
    left: -40,
    width: 180,
    height: 180,
    borderRadius: 90,
    backgroundColor: 'rgba(79, 70, 229, 0.1)',
  },
  heroBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 6,
    backgroundColor: 'rgba(250, 204, 21, 0.12)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginBottom: 16,
  },
  heroBadgeText: {
    fontSize: 11,
    fontFamily: 'Outfit-Bold',
    color: '#FACC15',
    letterSpacing: 1,
  },
  heroHeadline: {
    fontSize: 32,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
    lineHeight: 38,
    marginBottom: 8,
  },
  heroSubheadline: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: 'rgba(255,255,255,0.5)',
    lineHeight: 20,
    marginBottom: 24,
  },
  // Glass Form
  glassForm: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  formLabel: {
    fontSize: 12,
    fontFamily: 'Outfit-SemiBold',
    color: 'rgba(255,255,255,0.6)',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  darkInput: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  dollarPrefix: {
    fontSize: 24,
    fontFamily: 'Outfit-Bold',
    color: 'rgba(255,255,255,0.5)',
    marginRight: 4,
  },
  darkInputText: {
    flex: 1,
    fontSize: 24,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
  },
  // Timeframe
  timeframeRow: {
    flexDirection: 'row',
    gap: 8,
  },
  timeframeButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    alignItems: 'center',
  },
  timeframeButtonActive: {
    backgroundColor: 'rgba(250, 204, 21, 0.15)',
    borderColor: '#FACC15',
  },
  timeframeButtonText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    color: 'rgba(255,255,255,0.5)',
  },
  timeframeButtonTextActive: {
    color: '#FACC15',
  },
  // Strategy
  strategyRow: {
    flexDirection: 'row',
    gap: 10,
  },
  strategyCard: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  strategyCardActive: {
    backgroundColor: '#FACC15',
    borderColor: '#FACC15',
  },
  strategyCardText: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    color: 'rgba(255,255,255,0.6)',
  },
  strategyCardTextActive: {
    color: '#0F0F1A',
  },
  // CTA Button
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#FACC15',
    borderRadius: 12,
    paddingVertical: 16,
    marginTop: 20,
  },
  ctaButtonText: {
    fontSize: 16,
    fontFamily: 'Outfit-Bold',
    color: '#0F0F1A',
  },
  // Results Section
  resultsSection: {
    paddingHorizontal: 16,
    paddingTop: 24,
  },
  resultsTitle: {
    fontSize: 22,
    fontFamily: 'Outfit-Bold',
    color: '#0F172A',
    marginBottom: 16,
  },
  // Insight Box
  insightBox: {
    backgroundColor: '#312E81',
    borderRadius: 14,
    padding: 16,
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
  // Result Details
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
  // ROI Badge
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
  // Result Footer
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
  // Empty Results
  emptyResults: {
    alignItems: 'center',
    paddingVertical: 48,
    paddingHorizontal: 32,
  },
  emptyResultsText: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: '#94A3B8',
    textAlign: 'center',
    marginTop: 12,
    lineHeight: 20,
  },
});
