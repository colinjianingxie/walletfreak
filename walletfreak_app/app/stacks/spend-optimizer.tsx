import React from 'react';
import { Text, useTheme } from 'react-native-paper';
import { ScreenContainer } from '../../src/components/layout/ScreenContainer';
import { PremiumGate } from '../../src/components/layout/PremiumGate';

export default function SpendOptimizerScreen() {
  const theme = useTheme();
  return (
    <PremiumGate feature="Spend Optimizer">
      <ScreenContainer>
        <Text variant="headlineSmall">Spend Optimizer</Text>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant, marginTop: 8 }}>
          This screen is coming soon.
        </Text>
      </ScreenContainer>
    </PremiumGate>
  );
}
