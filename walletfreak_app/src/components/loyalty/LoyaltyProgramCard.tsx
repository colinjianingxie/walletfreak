import React from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text, Surface, useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { formatCurrency, formatNumber } from '../../utils/formatters';
import type { LoyaltyProgram } from '../../types/loyalty';

interface LoyaltyProgramCardProps {
  program: LoyaltyProgram;
  onPress: (program: LoyaltyProgram) => void;
}

const TYPE_ICONS: Record<string, string> = {
  miles: 'airplane',
  points: 'star-circle-outline',
  cash: 'cash',
  other: 'gift-outline',
};

export const LoyaltyProgramCard: React.FC<LoyaltyProgramCardProps> = ({ program, onPress }) => {
  const theme = useTheme();

  return (
    <Surface style={[styles.container, { backgroundColor: theme.colors.elevation.level1 }]} elevation={1}>
      <Pressable onPress={() => onPress(program)} style={styles.pressable}>
        <View style={[styles.iconCircle, { backgroundColor: theme.colors.primaryContainer }]}>
          <MaterialCommunityIcons
            name={(TYPE_ICONS[program.type] || 'gift-outline') as any}
            size={24}
            color={theme.colors.onPrimaryContainer}
          />
        </View>
        <View style={styles.info}>
          <Text variant="titleSmall" numberOfLines={1}>
            {program.name}
          </Text>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {formatNumber(program.balance)} {program.type}
          </Text>
        </View>
        <View style={{ alignItems: 'flex-end' }}>
          <Text variant="titleSmall" style={{ color: theme.colors.primary }}>
            {formatCurrency(program.est_value)}
          </Text>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {program.valuation}¢ each
          </Text>
        </View>
      </Pressable>
    </Surface>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    marginBottom: 8,
  },
  pressable: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  info: {
    flex: 1,
  },
});
