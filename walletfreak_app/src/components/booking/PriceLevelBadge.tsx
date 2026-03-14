import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text } from 'react-native-paper';

interface PriceLevelBadgeProps {
  level: number; // 0-4
  size?: 'small' | 'medium';
}

const LEVEL_COLORS: Record<number, { bg: string; text: string }> = {
  0: { bg: '#F0FDF4', text: '#16A34A' },
  1: { bg: '#F0FDF4', text: '#16A34A' },
  2: { bg: '#FFFBEB', text: '#D97706' },
  3: { bg: '#FFF1F2', text: '#DC2626' },
  4: { bg: '#FDF2F8', text: '#BE185D' },
};

export const PriceLevelBadge: React.FC<PriceLevelBadgeProps> = ({ level, size = 'small' }) => {
  const displayLevel = Math.max(1, Math.min(level, 4));
  const dollars = '$'.repeat(displayLevel);
  const colors = LEVEL_COLORS[displayLevel] || LEVEL_COLORS[2];

  return (
    <View style={[styles.badge, { backgroundColor: colors.bg }, size === 'medium' && styles.badgeMedium]}>
      <Text style={[styles.text, { color: colors.text }, size === 'medium' && styles.textMedium]}>
        {dollars}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  badgeMedium: {
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  text: {
    fontSize: 11,
    fontFamily: 'Outfit-Bold',
    letterSpacing: 0.5,
  },
  textMedium: {
    fontSize: 13,
  },
});
