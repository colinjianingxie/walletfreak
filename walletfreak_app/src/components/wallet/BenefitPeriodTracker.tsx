import React from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text, Button, Chip, useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colors } from '../../theme';
import { formatCurrency } from '../../utils/formatters';
import type { BenefitDisplay, PeriodDisplay } from '../../types/card';

interface BenefitPeriodTrackerProps {
  benefit: BenefitDisplay;
  onMarkUsed: (benefit: BenefitDisplay) => void;
  onToggleIgnore: (benefit: BenefitDisplay) => void;
}

const PERIOD_DOT_COLORS = {
  empty: colors.benefitEmpty,
  partial: colors.benefitPartial,
  full: colors.benefitFull,
};

export const BenefitPeriodTracker: React.FC<BenefitPeriodTrackerProps> = ({
  benefit,
  onMarkUsed,
  onToggleIgnore,
}) => {
  const theme = useTheme();

  const currentPeriod = benefit.periods.find((p) => p.is_current);
  const progressPct = currentPeriod
    ? Math.min((currentPeriod.used / currentPeriod.max_value) * 100, 100)
    : 0;

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.elevation.level1 }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Text variant="titleSmall" numberOfLines={2}>
            {benefit.benefit_name}
          </Text>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {benefit.card_name}
          </Text>
        </View>
        <View style={{ alignItems: 'flex-end' }}>
          <Text variant="titleSmall" style={{ color: theme.colors.primary }}>
            {formatCurrency(benefit.amount)}
          </Text>
          <Chip compact style={styles.frequencyChip} textStyle={{ fontSize: 10 }}>
            {benefit.frequency}
          </Chip>
        </View>
      </View>

      {/* Period Pills */}
      <View style={styles.periodsRow}>
        {benefit.periods.map((period) => (
          <View key={period.key} style={styles.periodItem}>
            <View
              style={[
                styles.periodDot,
                {
                  backgroundColor: PERIOD_DOT_COLORS[period.status],
                  borderWidth: period.is_current ? 2 : 0,
                  borderColor: theme.colors.primary,
                },
              ]}
            />
            <Text
              variant="labelSmall"
              style={{
                color: period.is_current ? theme.colors.primary : theme.colors.onSurfaceVariant,
                fontSize: 9,
              }}
            >
              {period.label}
            </Text>
          </View>
        ))}
      </View>

      {/* Current Period Progress */}
      {currentPeriod && (
        <View style={styles.progressSection}>
          <View style={styles.progressHeader}>
            <Text variant="bodySmall">
              {formatCurrency(currentPeriod.used)} / {formatCurrency(currentPeriod.max_value)}
            </Text>
            {benefit.days_until_expiration != null && (
              <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                {benefit.days_until_expiration}d left
              </Text>
            )}
          </View>
          <View style={[styles.progressBar, { backgroundColor: theme.colors.surfaceVariant }]}>
            <View
              style={[
                styles.progressFill,
                {
                  width: `${progressPct}%`,
                  backgroundColor:
                    currentPeriod.status === 'full'
                      ? colors.success
                      : currentPeriod.status === 'partial'
                        ? colors.warning
                        : theme.colors.primary,
                },
              ]}
            />
          </View>
        </View>
      )}

      {/* Actions */}
      <View style={styles.actions}>
        <Button
          mode="contained-tonal"
          compact
          onPress={() => onMarkUsed(benefit)}
          icon="plus-circle-outline"
        >
          Mark Used
        </Button>
        <Pressable onPress={() => onToggleIgnore(benefit)} style={styles.ignoreButton}>
          <MaterialCommunityIcons
            name={benefit.is_ignored ? 'eye-outline' : 'eye-off-outline'}
            size={18}
            color={theme.colors.onSurfaceVariant}
          />
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant, marginLeft: 4 }}>
            {benefit.is_ignored ? 'Unignore' : 'Ignore'}
          </Text>
        </Pressable>
      </View>

      {benefit.additional_details ? (
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 8 }}>
          {benefit.additional_details}
        </Text>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  frequencyChip: {
    height: 22,
    marginTop: 4,
  },
  periodsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 6,
    marginBottom: 12,
    flexWrap: 'wrap',
  },
  periodItem: {
    alignItems: 'center',
    minWidth: 24,
  },
  periodDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    marginBottom: 2,
  },
  progressSection: {
    marginBottom: 12,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ignoreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
  },
});
