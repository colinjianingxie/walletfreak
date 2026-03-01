import React, { useState, useRef } from 'react';
import { View, StyleSheet, Pressable, TextInput, ActivityIndicator, Animated, ScrollView } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { formatCurrency } from '../../utils/formatters';
import { useUpdateBenefit } from '../../hooks/useWallet';
import type { BenefitDisplay, PeriodDisplay } from '../../types/card';

interface BenefitPeriodTrackerProps {
  benefit: BenefitDisplay;
  onToggleIgnore: (benefit: BenefitDisplay) => void;
  isIgnoring?: boolean;
}

export const BenefitPeriodTracker: React.FC<BenefitPeriodTrackerProps> = ({
  benefit,
  onToggleIgnore,
  isIgnoring = false,
}) => {
  const theme = useTheme();
  const updateBenefit = useUpdateBenefit();
  const [editMode, setEditMode] = useState(false);
  const [editAmount, setEditAmount] = useState('');
  const [selectedPeriodKey, setSelectedPeriodKey] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const successOpacity = useRef(new Animated.Value(0)).current;

  const flashSuccess = () => {
    setShowSuccess(true);
    successOpacity.setValue(1);
    Animated.timing(successOpacity, {
      toValue: 0,
      duration: 1200,
      useNativeDriver: true,
    }).start(() => setShowSuccess(false));
  };

  const currentPeriod = benefit.periods.find((p) => p.is_current);
  const activePeriod = selectedPeriodKey
    ? benefit.periods.find((p) => p.key === selectedPeriodKey) || currentPeriod
    : currentPeriod;

  const totalAmount = benefit.amount ?? 0;
  const isMonthly = benefit.frequency?.toLowerCase() === 'monthly';
  const isSemiAnnual = benefit.frequency?.toLowerCase().includes('semi');
  const isQuarterly = benefit.frequency?.toLowerCase().includes('quarter');
  const hasMultiplePeriods = isMonthly || isSemiAnnual || isQuarterly;

  // For multi-period benefits, use the active period's max_value for display
  const periodAmount = hasMultiplePeriods && activePeriod ? activePeriod.max_value : totalAmount;
  const usedAmount = activePeriod?.used ?? 0;
  const remainingAmount = Math.max(0, periodAmount - usedAmount);
  const progressPct = periodAmount > 0 ? Math.min((usedAmount / periodAmount) * 100, 100) : 0;

  const isExpiring = benefit.days_until_expiration != null && benefit.days_until_expiration <= 30;

  // Determine progress bar color
  const getProgressColor = () => {
    if (activePeriod?.status === 'full') return '#4A90D9';
    if (usedAmount > 0) return '#E67E22';
    return '#4A90D9';
  };

  const handleUpdateAmount = () => {
    setEditAmount(String(activePeriod?.used ?? 0));
    setEditMode(true);
  };

  const handleSave = () => {
    if (!activePeriod) return;
    const newAmount = parseFloat(editAmount) || 0;
    updateBenefit.mutate(
      {
        userCardId: benefit.user_card_id,
        benefitId: benefit.benefit_id,
        amount: newAmount,
        periodKey: activePeriod.key,
        isFull: false,
        increment: false,
      },
      {
        onSuccess: () => {
          setEditMode(false);
          setEditAmount('');
          flashSuccess();
        },
      }
    );
  };

  const handleCancel = () => {
    setEditMode(false);
    setEditAmount('');
  };

  const handleMarkFull = () => {
    if (!activePeriod) return;
    updateBenefit.mutate(
      {
        userCardId: benefit.user_card_id,
        benefitId: benefit.benefit_id,
        amount: activePeriod.max_value,
        periodKey: activePeriod.key,
        isFull: true,
        increment: false,
      },
      {
        onSuccess: () => flashSuccess(),
      }
    );
  };

  const handlePeriodPress = (period: PeriodDisplay) => {
    if (!period.is_available && !period.is_current) return;
    setSelectedPeriodKey(period.key === selectedPeriodKey ? null : period.key);
  };

  return (
    <View style={[
      styles.container,
      { borderColor: isExpiring ? '#F59E0B' : '#E5E7EB' },
      benefit.is_ignored && { opacity: 0.5 },
    ]}>
      {/* Header Row */}
      <View style={styles.headerRow}>
        <View style={{ flex: 1, marginRight: 12 }}>
          <View style={styles.titleRow}>
            <Text style={styles.benefitName}>
              {formatCurrency(totalAmount)} {benefit.benefit_name.replace(/^\$[\d,.]+\s*/, '')}
            </Text>
            {isExpiring && (
              <View style={styles.expiringBadge}>
                <MaterialCommunityIcons name="clock-alert-outline" size={12} color="#DC2626" />
                <Text style={styles.expiringText}>EXPIRING</Text>
              </View>
            )}
          </View>
          {benefit.additional_details && (
            <Text style={[styles.description, { color: theme.colors.onSurfaceVariant }]} numberOfLines={2}>
              {benefit.additional_details}
            </Text>
          )}
        </View>
        <View style={styles.amountCol}>
          <Text style={styles.amountValue}>{formatCurrency(periodAmount)}</Text>
          <Text style={styles.frequencyLabel}>
            {benefit.frequency?.toUpperCase() || 'ANNUAL'}
          </Text>
        </View>
      </View>

      {/* Usage Progress */}
      <View style={styles.usageRow}>
        <Text style={styles.usedText}>{formatCurrency(usedAmount)} used</Text>
        <Text style={[styles.remainingText, { color: theme.colors.onSurfaceVariant }]}>
          {formatCurrency(remainingAmount)} remaining
        </Text>
      </View>
      <View style={styles.progressBarBg}>
        <View
          style={[
            styles.progressBarFill,
            { width: `${progressPct}%`, backgroundColor: getProgressColor() },
          ]}
        />
      </View>

      {/* Period Blocks (for monthly/quarterly/semi-annual) */}
      {hasMultiplePeriods && benefit.periods.length > 0 && (
        <ScrollView
          horizontal={isMonthly}
          showsHorizontalScrollIndicator={false}
          style={styles.periodsScroll}
          contentContainerStyle={[
            styles.periodsRow,
            !isMonthly && { justifyContent: 'center' },
          ]}
        >
          {benefit.periods.map((period) => {
            const isSelected = period.key === selectedPeriodKey;
            const isFull = period.status === 'full';
            const isPartial = period.status === 'partial';
            const isCurrent = period.is_current;
            const isPast = !isCurrent && period.is_available;

            return (
              <Pressable
                key={period.key}
                style={[
                  styles.periodBlock,
                  isMonthly && styles.periodBlockMonthly,
                  !isMonthly && styles.periodBlockWide,
                  isFull && styles.periodBlockFull,
                  (isSelected || isCurrent) && !isFull && styles.periodBlockSelected,
                  !isPast && !isCurrent && !isFull && !isPartial && styles.periodBlockFuture,
                ]}
                onPress={() => handlePeriodPress(period)}
              >
                <Text
                  style={[
                    styles.periodLabel,
                    (isPast || isCurrent) && styles.periodLabelActive,
                    isFull && { color: '#FFFFFF' },
                  ]}
                >
                  {period.label}
                </Text>
                <Text
                  style={[
                    styles.periodValue,
                    (isPast || isCurrent) && styles.periodValueActive,
                    isFull && { color: '#FFFFFF' },
                  ]}
                >
                  {formatCurrency(period.max_value)}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>
      )}

      {/* Edit Mode: Inline Amount Input */}
      {editMode ? (
        <View style={styles.editRow}>
          <TextInput
            style={[styles.editInput, { borderColor: theme.colors.outlineVariant }]}
            value={editAmount}
            onChangeText={setEditAmount}
            keyboardType="decimal-pad"
            placeholder="0"
            autoFocus
          />
          <Pressable
            style={[styles.saveButton, { backgroundColor: '#4F46E5', opacity: updateBenefit.isPending ? 0.7 : 1 }]}
            onPress={handleSave}
            disabled={updateBenefit.isPending}
          >
            {updateBenefit.isPending ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.saveButtonText}>Save</Text>
            )}
          </Pressable>
          <Pressable
            style={[styles.cancelButton, { borderColor: theme.colors.outlineVariant }]}
            onPress={handleCancel}
          >
            <Text style={[styles.cancelButtonText, { color: theme.colors.onSurface }]}>Cancel</Text>
          </Pressable>
        </View>
      ) : (
        /* Action Buttons + Ignore */
        <View style={styles.actionsRow}>
          <Pressable
            style={[styles.actionButton, styles.updateButton, { backgroundColor: '#F1F5F9' }]}
            onPress={handleUpdateAmount}
          >
            <Text style={styles.updateButtonText}>Update Amount</Text>
          </Pressable>
          <Pressable
            style={[styles.actionButton, styles.markFullButton, { backgroundColor: showSuccess ? '#DCFCE7' : '#EEF2FF', opacity: updateBenefit.isPending ? 0.7 : 1 }]}
            onPress={handleMarkFull}
            disabled={updateBenefit.isPending}
          >
            {updateBenefit.isPending ? (
              <ActivityIndicator size="small" color="#4F46E5" />
            ) : showSuccess ? (
              <>
                <Animated.View style={{ opacity: successOpacity }}>
                  <MaterialCommunityIcons name="check-circle" size={18} color="#16A34A" />
                </Animated.View>
                <Text style={[styles.markFullButtonText, { color: '#16A34A' }]}>Done!</Text>
              </>
            ) : (
              <>
                <MaterialCommunityIcons name="check-circle-outline" size={18} color="#4F46E5" />
                <Text style={styles.markFullButtonText}>Mark Full</Text>
              </>
            )}
          </Pressable>
          <Pressable
            style={styles.ignoreInlineButton}
            onPress={() => onToggleIgnore(benefit)}
            hitSlop={4}
          >
            {isIgnoring ? (
              <ActivityIndicator size={16} color="#94A3B8" />
            ) : (
              <MaterialCommunityIcons
                name={benefit.is_ignored ? 'eye-outline' : 'eye-off-outline'}
                size={20}
                color="#94A3B8"
              />
            )}
          </Pressable>
        </View>
      )}

    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderWidth: 1.5,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    backgroundColor: '#FFFFFF',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 2,
  },
  benefitName: {
    fontSize: 16,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
  },
  expiringBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    gap: 4,
  },
  expiringText: {
    fontSize: 10,
    fontFamily: 'Outfit-Bold',
    color: '#DC2626',
    letterSpacing: 0.5,
  },
  description: {
    fontSize: 13,
    fontFamily: 'Outfit',
    lineHeight: 18,
  },
  amountCol: {
    alignItems: 'flex-end',
  },
  amountValue: {
    fontSize: 22,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
  },
  frequencyLabel: {
    fontSize: 10,
    fontFamily: 'Outfit-Medium',
    color: '#6366F1',
    letterSpacing: 0.5,
    marginTop: 2,
  },
  // Usage progress
  usageRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  usedText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    color: '#1C1B1F',
  },
  remainingText: {
    fontSize: 13,
    fontFamily: 'Outfit',
  },
  progressBarBg: {
    height: 6,
    backgroundColor: '#E5E7EB',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 14,
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  // Period blocks
  periodsScroll: {
    marginBottom: 14,
  },
  periodsRow: {
    flexDirection: 'row',
    gap: 6,
  },
  periodBlock: {
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 6,
    alignItems: 'center',
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  periodBlockMonthly: {
    minWidth: 48,
  },
  periodBlockWide: {
    flex: 1,
  },
  periodBlockFull: {
    backgroundColor: '#4F46E5',
    borderColor: '#4F46E5',
  },
  periodBlockSelected: {
    borderColor: '#4F46E5',
    backgroundColor: '#EEF2FF',
  },
  periodBlockFuture: {
    opacity: 0.5,
  },
  periodLabel: {
    fontSize: 11,
    fontFamily: 'Outfit-Medium',
    color: '#94A3B8',
  },
  periodLabelActive: {
    color: '#334155',
  },
  periodValue: {
    fontSize: 12,
    fontFamily: 'Outfit-SemiBold',
    color: '#94A3B8',
    marginTop: 2,
  },
  periodValueActive: {
    color: '#1C1B1F',
  },
  // Actions
  actionsRow: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 12,
    borderRadius: 10,
    gap: 6,
  },
  updateButton: {},
  updateButtonText: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
  },
  markFullButton: {},
  markFullButtonText: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    color: '#4F46E5',
  },
  // Ignore inline button (end of actions row)
  ignoreInlineButton: {
    width: 40,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F1F5F9',
  },
  // Edit mode
  editRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  editInput: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 16,
    fontFamily: 'Outfit',
    backgroundColor: '#F8FAFC',
  },
  saveButton: {
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 10,
  },
  saveButtonText: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    color: '#FFFFFF',
  },
  cancelButton: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
  },
  cancelButtonText: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
  },
});
