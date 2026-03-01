import React from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { Text, Button, Surface, useTheme, Divider } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import * as WebBrowser from 'expo-web-browser';
import { ScreenContainer } from '../../src/components/layout/ScreenContainer';
import { useAuthStore } from '../../src/stores/authStore';
import { useSubscriptionStatus, useCreateCheckout, useCreatePortal } from '../../src/hooks/useSubscription';

const features = [
  { icon: 'chart-donut', label: 'Spend Optimizer', free: false, premium: true },
  { icon: 'bed-outline', label: 'Booking Optimizer', free: false, premium: true },
  { icon: 'magnify', label: 'Award Scout', free: false, premium: true },
  { icon: 'scale-balance', label: 'Worth It? Calculator', free: true, premium: true },
  { icon: 'wallet-outline', label: 'Wallet Management', free: true, premium: true },
  { icon: 'account-group', label: 'Community', free: true, premium: true },
];

// Replace with actual Stripe price IDs
const MONTHLY_PRICE_ID = 'price_monthly';
const YEARLY_PRICE_ID = 'price_yearly';

export default function SubscriptionScreen() {
  const { profile } = useAuthStore();
  const theme = useTheme();
  const { data: subStatus } = useSubscriptionStatus();
  const createCheckout = useCreateCheckout();
  const createPortal = useCreatePortal();

  const handleCheckout = async (priceId: string) => {
    try {
      const result = await createCheckout.mutateAsync(priceId);
      if (result.checkout_url) {
        await WebBrowser.openBrowserAsync(result.checkout_url);
      }
    } catch {
      Alert.alert('Error', 'Failed to start checkout. Please try again.');
    }
  };

  const handleManage = async () => {
    try {
      const result = await createPortal.mutateAsync();
      if (result.portal_url) {
        await WebBrowser.openBrowserAsync(result.portal_url);
      }
    } catch {
      Alert.alert('Error', 'Failed to open billing portal.');
    }
  };

  const isPremium = profile?.is_premium || subStatus?.is_premium;

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

      {/* Subscription Status / Pricing */}
      {isPremium ? (
        <View style={styles.pricing}>
          <Surface style={[styles.statusCard, { backgroundColor: theme.colors.primaryContainer }]} elevation={0}>
            <MaterialCommunityIcons name="check-circle" size={24} color={theme.colors.primary} />
            <Text variant="titleMedium" style={{ color: theme.colors.onPrimaryContainer, marginLeft: 8 }}>
              Premium Active
            </Text>
          </Surface>
          {subStatus?.current_period_end && (
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, textAlign: 'center' }}>
              {subStatus.cancel_at_period_end ? 'Cancels' : 'Renews'} on {subStatus.current_period_end}
            </Text>
          )}
          <Button
            mode="outlined"
            onPress={handleManage}
            loading={createPortal.isPending}
            style={styles.priceButton}
          >
            Manage Subscription
          </Button>
        </View>
      ) : (
        <View style={styles.pricing}>
          <Button
            mode="contained"
            onPress={() => handleCheckout(MONTHLY_PRICE_ID)}
            loading={createCheckout.isPending}
            style={styles.priceButton}
            contentStyle={styles.priceButtonContent}
          >
            $4.99/month
          </Button>
          <Button
            mode="outlined"
            onPress={() => handleCheckout(YEARLY_PRICE_ID)}
            loading={createCheckout.isPending}
            style={styles.priceButton}
            contentStyle={styles.priceButtonContent}
          >
            $39.99/year (Save 33%)
          </Button>
        </View>
      )}
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
  statusCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
  },
});
