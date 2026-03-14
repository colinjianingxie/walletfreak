import React, { useState } from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { formatCurrency } from '../../utils/formatters';
import type { HotelAnalysis, StrategyOption } from '../../types/booking';

interface StrategyCardProps {
  analysis: HotelAnalysis;
}

const OPTION_ICONS: Record<string, React.ComponentProps<typeof MaterialCommunityIcons>['name']> = {
  'star': 'star',
  'credit-card': 'credit-card',
  'transfer': 'swap-horizontal',
  'cash': 'cash',
  'portal': 'earth',
  'gem': 'diamond-stone',
};

const isPremium = (option: StrategyOption) => !!option.premium_program;

const OptionRow: React.FC<{ option: StrategyOption; isRecommended?: boolean }> = ({ option, isRecommended }) => {
  const iconName = OPTION_ICONS[option.icon] || 'circle-outline';
  const premium = isPremium(option);

  return (
    <View style={[
      styles.optionRow,
      isRecommended && styles.optionRowRecommended,
      premium && styles.optionRowPremium,
    ]}>
      <View style={styles.optionLeft}>
        <MaterialCommunityIcons
          name={iconName}
          size={16}
          color={isRecommended ? '#16A34A' : premium ? '#C9B037' : '#64748B'}
        />
        <View style={{ flex: 1 }}>
          <Text style={styles.optionLabel}>{option.label}</Text>
          <Text style={styles.optionSubLabel}>{option.sub_label}</Text>
          {option.premium_benefits && option.premium_benefits.length > 0 && (
            <Text style={styles.premiumBenefitsText}>
              {option.premium_benefits.join(' · ')}
            </Text>
          )}
        </View>
      </View>
      <View style={styles.optionRight}>
        <Text style={styles.optionUpfront}>
          {option.upfront != null
            ? `${option.upfront_currency === 'pts' ? option.upfront.toLocaleString() + ' pts' : formatCurrency(option.upfront)}`
            : 'N/A'}
        </Text>
        <Text style={[styles.optionEffective, isRecommended && styles.optionEffectiveGreen]}>
          {option.effective != null ? `Eff. ${formatCurrency(option.effective)}` : ''}
        </Text>
      </View>
    </View>
  );
};

export const StrategyCard: React.FC<StrategyCardProps> = ({ analysis }) => {
  const [expanded, setExpanded] = useState(false);
  const rec = analysis.recommended_strategy;
  const savings = rec?.savings_vs_cash;

  return (
    <View style={styles.card}>
      {/* Hotel Header */}
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Text style={styles.hotelName}>{analysis.hotel_name}</Text>
          <Text style={styles.starRating}>{analysis.star_rating}</Text>
        </View>
        <View style={styles.cashPriceBox}>
          <Text style={styles.cashLabel}>Cash Price</Text>
          <Text style={styles.cashPrice}>{formatCurrency(analysis.cash_price)}</Text>
        </View>
      </View>

      {/* Recommended Strategy */}
      {rec && (
        <View style={styles.recommendedBox}>
          <View style={styles.recommendedHeader}>
            <MaterialCommunityIcons name="trophy" size={14} color="#16A34A" />
            <Text style={styles.recommendedTitle}>Best Strategy</Text>
          </View>
          <Text style={styles.recommendedStrategy}>{rec.title}</Text>
          <Text style={styles.recommendedDesc}>{rec.description}</Text>
          <View style={styles.recommendedMetrics}>
            <View>
              <Text style={styles.metricLabel}>Upfront</Text>
              <Text style={styles.metricValue}>
                {rec.upfront != null
                  ? rec.upfront_currency === 'pts'
                    ? `${rec.upfront.toLocaleString()} pts`
                    : formatCurrency(rec.upfront)
                  : 'N/A'}
              </Text>
            </View>
            <View>
              <Text style={styles.metricLabel}>Effective Cost</Text>
              <Text style={styles.metricValue}>
                {rec.effective != null ? formatCurrency(rec.effective) : 'N/A'}
              </Text>
            </View>
            {savings != null && savings > 0 && (
              <View>
                <Text style={styles.metricLabel}>Savings</Text>
                <Text style={[styles.metricValue, { color: '#16A34A' }]}>
                  {formatCurrency(savings)}
                </Text>
              </View>
            )}
          </View>
        </View>
      )}

      {/* All Options Toggle */}
      {analysis.all_options?.length > 0 && (
        <>
          <Pressable
            onPress={() => setExpanded(!expanded)}
            style={styles.expandToggle}
          >
            <Text style={styles.expandText}>
              {expanded ? 'Hide' : 'Show'} all {analysis.all_options.length} options
            </Text>
            <MaterialCommunityIcons
              name={expanded ? 'chevron-up' : 'chevron-down'}
              size={18}
              color="#6366F1"
            />
          </Pressable>

          {expanded && (
            <View style={styles.optionsList}>
              {analysis.all_options.map((opt, idx) => (
                <OptionRow
                  key={`${opt.type}-${opt.label}-${idx}`}
                  option={opt}
                  isRecommended={opt.label === rec?.title && opt.sub_label === rec?.description}
                />
              ))}
            </View>
          )}
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    marginHorizontal: 16,
    marginBottom: 16,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    padding: 16,
    paddingBottom: 12,
  },
  hotelName: {
    fontSize: 16,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  starRating: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#94A3B8',
    marginTop: 2,
  },
  cashPriceBox: {
    alignItems: 'flex-end',
  },
  cashLabel: {
    fontSize: 10,
    fontFamily: 'Outfit',
    color: '#94A3B8',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  cashPrice: {
    fontSize: 18,
    fontFamily: 'Outfit-Bold',
    color: '#0F172A',
  },
  // Recommended
  recommendedBox: {
    backgroundColor: '#F0FDF4',
    borderTopWidth: 1,
    borderTopColor: '#BBF7D0',
    padding: 14,
    marginHorizontal: 12,
    marginBottom: 12,
    borderRadius: 10,
  },
  recommendedHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  recommendedTitle: {
    fontSize: 11,
    fontFamily: 'Outfit-Bold',
    color: '#16A34A',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  recommendedStrategy: {
    fontSize: 15,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  recommendedDesc: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#64748B',
    marginTop: 2,
  },
  recommendedMetrics: {
    flexDirection: 'row',
    gap: 20,
    marginTop: 10,
  },
  metricLabel: {
    fontSize: 10,
    fontFamily: 'Outfit',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  metricValue: {
    fontSize: 14,
    fontFamily: 'Outfit-Bold',
    color: '#0F172A',
    marginTop: 2,
  },
  // Expand
  expandToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    marginHorizontal: 16,
  },
  expandText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    color: '#6366F1',
  },
  // Options
  optionsList: {
    paddingHorizontal: 12,
    paddingBottom: 12,
    gap: 6,
  },
  optionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    padding: 10,
  },
  optionRowRecommended: {
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: '#BBF7D0',
  },
  optionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  optionLabel: {
    fontSize: 13,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  optionSubLabel: {
    fontSize: 11,
    fontFamily: 'Outfit',
    color: '#94A3B8',
  },
  optionRight: {
    alignItems: 'flex-end',
  },
  optionUpfront: {
    fontSize: 12,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  optionEffective: {
    fontSize: 10,
    fontFamily: 'Outfit',
    color: '#64748B',
  },
  optionEffectiveGreen: {
    color: '#16A34A',
  },
  optionRowPremium: {
    backgroundColor: '#FFFBEB',
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  premiumBenefitsText: {
    fontSize: 10,
    fontFamily: 'Outfit',
    color: '#92400E',
    marginTop: 2,
  },
});
