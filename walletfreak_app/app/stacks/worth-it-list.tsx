import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { ScreenContainer } from '../../src/components/layout/ScreenContainer';

export default function WorthItListScreen() {
  const theme = useTheme();
  return (
    <ScreenContainer>
      <Text variant="headlineSmall">Worth It? Cards</Text>
      <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant, marginTop: 8 }}>
        This screen is coming soon.
      </Text>
    </ScreenContainer>
  );
}
