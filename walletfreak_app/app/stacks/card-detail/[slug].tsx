import React from 'react';
import { View, StyleSheet, ScrollView, Pressable } from 'react-native';
import { Text, Button, Chip, Divider, useTheme, Surface } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import * as WebBrowser from 'expo-web-browser';
import { LoadingState } from '../../../src/components/layout/LoadingState';
import { useCardDetail } from '../../../src/hooks/useCards';
import { useAddCard } from '../../../src/hooks/useWallet';
import { formatCurrency } from '../../../src/utils/formatters';

export default function CardDetailScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { data: card, isLoading } = useCardDetail(slug);
  const addCard = useAddCard();
  const router = useRouter();
  const theme = useTheme();

  if (isLoading || !card) {
    return <LoadingState message="Loading card..." />;
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.content}
    >
      {/* Card Header */}
      <View style={styles.header}>
        <Text variant="headlineSmall" style={styles.cardName}>
          {card.name}
        </Text>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          {card.issuer}
        </Text>
        <Text variant="titleMedium" style={{ color: theme.colors.primary, marginTop: 8 }}>
          {formatCurrency(card.annual_fee)}/year
        </Text>
      </View>

      {/* Welcome Bonus */}
      {card.welcome_bonus && (
        <Surface style={[styles.section, { backgroundColor: theme.colors.primaryContainer }]} elevation={0}>
          <Text variant="labelLarge" style={{ color: theme.colors.onPrimaryContainer }}>
            Welcome Bonus
          </Text>
          <Text variant="bodyMedium" style={{ color: theme.colors.onPrimaryContainer, marginTop: 4 }}>
            {card.welcome_bonus}
          </Text>
          {card.welcome_requirement && (
            <Text variant="bodySmall" style={{ color: theme.colors.onPrimaryContainer, marginTop: 4 }}>
              {card.welcome_requirement}
            </Text>
          )}
        </Surface>
      )}

      {/* Benefits */}
      {card.benefits && card.benefits.length > 0 && (
        <View style={styles.section}>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Benefits
          </Text>
          {card.benefits.map((benefit: any, idx: number) => (
            <View key={idx} style={styles.benefitItem}>
              <View style={styles.benefitRow}>
                <Text variant="bodyMedium" style={{ flex: 1 }}>
                  {benefit.description}
                </Text>
                {benefit.dollar_value > 0 && (
                  <Text variant="labelLarge" style={{ color: theme.colors.primary }}>
                    {formatCurrency(benefit.dollar_value)}
                  </Text>
                )}
              </View>
              {benefit.time_category && (
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                  {benefit.time_category}
                </Text>
              )}
              {idx < card.benefits.length - 1 && <Divider style={styles.benefitDivider} />}
            </View>
          ))}
        </View>
      )}

      {/* Earning Rates */}
      {card.earning_rates && card.earning_rates.length > 0 && (
        <View style={styles.section}>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Earning Rates
          </Text>
          {card.earning_rates.map((rate: any, idx: number) => (
            <View key={idx} style={styles.rateItem}>
              <Text variant="bodyMedium">{rate.category}</Text>
              <Text variant="labelLarge" style={{ color: theme.colors.primary }}>
                {rate.rate}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Actions */}
      <View style={styles.actions}>
        <Button
          mode="contained"
          onPress={() =>
            addCard.mutate({ cardId: card.id || slug })
          }
          loading={addCard.isPending}
          style={styles.actionButton}
          icon="plus"
        >
          Add to Wallet
        </Button>
        {card.referral_url && (
          <Button
            mode="outlined"
            onPress={() => WebBrowser.openBrowserAsync(card.referral_url)}
            style={styles.actionButton}
            icon="open-in-new"
          >
            Apply Now
          </Button>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  cardName: {
    fontFamily: 'Outfit-SemiBold',
    textAlign: 'center',
  },
  section: {
    marginTop: 16,
    padding: 16,
    borderRadius: 12,
  },
  sectionTitle: {
    fontFamily: 'Outfit-Medium',
    marginBottom: 12,
  },
  benefitItem: {
    paddingVertical: 8,
  },
  benefitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  benefitDivider: {
    marginTop: 8,
  },
  rateItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  actions: {
    marginTop: 24,
    gap: 12,
  },
  actionButton: {
    borderRadius: 12,
  },
});
