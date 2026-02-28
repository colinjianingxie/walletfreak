import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button, Surface, useTheme, Divider } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ScreenContainer } from '../../src/components/layout/ScreenContainer';
import { useAuthStore } from '../../src/stores/authStore';

const features = [
  { icon: 'chart-donut', label: 'Spend Optimizer', free: false, premium: true },
  { icon: 'bed-outline', label: 'Booking Optimizer', free: false, premium: true },
  { icon: 'magnify', label: 'Award Scout', free: false, premium: true },
  { icon: 'scale-balance', label: 'Worth It? Calculator', free: true, premium: true },
  { icon: 'wallet-outline', label: 'Wallet Management', free: true, premium: true },
  { icon: 'account-group', label: 'Community', free: true, premium: true },
];

export default function SubscriptionScreen() {
  const { profile } = useAuthStore();
  const theme = useTheme();

  return (
    <ScreenContainer>
      <View style={styles.header}>
        <MaterialCommunityIcons
          name="crown"
          size={48}
          color={theme.colors.primary}
        />
        <Text variant="headlineMedium" style={styles.title}>
          WalletFreak Premium
        </Text>
        <Text
          variant="bodyMedium"
          style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}
        >
          Unlock all tools and maximize your credit card rewards.
        </Text>
      </View>

      {/* Feature Comparison */}
      <Surface style={[styles.featureTable, { backgroundColor: theme.colors.elevation.level1 }]} elevation={1}>
        <View style={styles.featureHeader}>
          <Text variant="labelLarge" style={{ flex: 1 }}>Feature</Text>
          <Text variant="labelLarge" style={styles.colHeader}>Free</Text>
          <Text variant="labelLarge" style={[styles.colHeader, { color: theme.colors.primary }]}>
            Premium
          </Text>
        </View>
        <Divider />
        {features.map((feat, idx) => (
          <View key={idx} style={styles.featureRow}>
            <Text variant="bodyMedium" style={{ flex: 1 }}>{feat.label}</Text>
            <MaterialCommunityIcons
              name={feat.free ? 'check-circle' : 'close-circle-outline'}
              size={20}
              color={feat.free ? theme.colors.primary : theme.colors.outlineVariant}
              style={styles.colIcon}
            />
            <MaterialCommunityIcons
              name="check-circle"
              size={20}
              color={theme.colors.primary}
              style={styles.colIcon}
            />
          </View>
        ))}
      </Surface>

      {/* Pricing */}
      <View style={styles.pricing}>
        <Button
          mode="contained"
          onPress={() => {
            // Stripe checkout via WebBrowser
          }}
          style={styles.priceButton}
          contentStyle={styles.priceButtonContent}
        >
          $4.99/month
        </Button>
        <Button
          mode="outlined"
          onPress={() => {
            // Stripe checkout via WebBrowser
          }}
          style={styles.priceButton}
          contentStyle={styles.priceButtonContent}
        >
          $39.99/year (Save 33%)
        </Button>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  title: {
    fontFamily: 'Outfit-Bold',
    marginTop: 12,
  },
  subtitle: {
    marginTop: 8,
    textAlign: 'center',
  },
  featureTable: {
    borderRadius: 16,
    padding: 16,
    marginTop: 16,
  },
  featureHeader: {
    flexDirection: 'row',
    paddingBottom: 8,
  },
  colHeader: {
    width: 60,
    textAlign: 'center',
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  colIcon: {
    width: 60,
    textAlign: 'center',
  },
  pricing: {
    marginTop: 24,
    gap: 12,
  },
  priceButton: {
    borderRadius: 12,
  },
  priceButtonContent: {
    paddingVertical: 8,
  },
});
