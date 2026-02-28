import React, { useState, useCallback } from 'react';
import { View, StyleSheet, FlatList, Pressable } from 'react-native';
import {
  Text,
  useTheme,
  SegmentedButtons,
  FAB,
  Chip,
  Surface,
} from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ScreenContainer } from '../../src/components/layout/ScreenContainer';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { useWallet } from '../../src/hooks/useWallet';
import { useAuthStore } from '../../src/stores/authStore';
import { formatCurrency } from '../../src/utils/formatters';
import { colors } from '../../src/theme';

export default function WalletScreen() {
  const [segment, setSegment] = useState('active');
  const { data, isLoading, refetch } = useWallet();
  const { profile } = useAuthStore();
  const router = useRouter();
  const theme = useTheme();

  const walletData = data;

  const cards =
    segment === 'active'
      ? walletData?.active_cards
      : segment === 'inactive'
        ? walletData?.inactive_cards
        : walletData?.eyeing_cards;

  const renderCardItem = useCallback(
    ({ item }: { item: any }) => (
      <Surface style={[styles.cardItem, { backgroundColor: theme.colors.elevation.level1 }]} elevation={1}>
        <Pressable
          onPress={() => router.push(`/stacks/card-detail/${item.card_id}` as any)}
          style={styles.cardPressable}
        >
          <View style={styles.cardInfo}>
            <Text variant="titleSmall" numberOfLines={1}>
              {item.name}
            </Text>
            <Text
              variant="bodySmall"
              style={{ color: theme.colors.onSurfaceVariant }}
            >
              {item.issuer}
            </Text>
          </View>
          <MaterialCommunityIcons
            name="chevron-right"
            size={20}
            color={theme.colors.onSurfaceVariant}
          />
        </Pressable>
      </Surface>
    ),
    [router, theme]
  );

  if (isLoading) {
    return <LoadingState message="Loading wallet..." />;
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Personality Badge */}
      {walletData?.personality && (
        <Pressable
          style={[styles.personalityBadge, { backgroundColor: theme.colors.primaryContainer }]}
          onPress={() =>
            router.push(`/stacks/personality/${walletData.personality.id}` as any)
          }
        >
          <Text variant="labelLarge" style={{ color: theme.colors.onPrimaryContainer }}>
            {walletData.personality.name}
          </Text>
        </Pressable>
      )}

      {/* Stats Row */}
      <View style={styles.statsRow}>
        <View style={styles.statItem}>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            Extracted
          </Text>
          <Text variant="titleMedium" style={{ color: colors.success }}>
            {formatCurrency(walletData?.total_extracted_value ?? 0)}
          </Text>
        </View>
        <View style={styles.statItem}>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            Potential
          </Text>
          <Text variant="titleMedium">
            {formatCurrency(walletData?.total_potential_value ?? 0)}
          </Text>
        </View>
        <View style={styles.statItem}>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            Fees
          </Text>
          <Text variant="titleMedium" style={{ color: theme.colors.error }}>
            {formatCurrency(walletData?.total_annual_fee ?? 0)}
          </Text>
        </View>
        <View style={styles.statItem}>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            Net
          </Text>
          <Text
            variant="titleMedium"
            style={{
              color:
                (walletData?.net_performance ?? 0) >= 0
                  ? colors.success
                  : theme.colors.error,
            }}
          >
            {formatCurrency(walletData?.net_performance ?? 0)}
          </Text>
        </View>
      </View>

      {/* Chase 5/24 Badge */}
      {walletData?.chase_524_count !== undefined && (
        <Chip
          icon="information-outline"
          style={[styles.chase524, {
            backgroundColor: walletData.chase_524_count < 5
              ? theme.colors.primaryContainer
              : theme.colors.errorContainer,
          }]}
        >
          Chase 5/24: {walletData.chase_524_count}/5
        </Chip>
      )}

      {/* Segment Control */}
      <SegmentedButtons
        value={segment}
        onValueChange={setSegment}
        buttons={[
          { value: 'active', label: `Active (${walletData?.active_cards?.length ?? 0})` },
          { value: 'inactive', label: `Inactive (${walletData?.inactive_cards?.length ?? 0})` },
          { value: 'eyeing', label: `Eyeing (${walletData?.eyeing_cards?.length ?? 0})` },
        ]}
        style={styles.segments}
      />

      {/* Cards List */}
      {!cards || cards.length === 0 ? (
        <EmptyState
          icon="credit-card-plus-outline"
          title={`No ${segment} cards`}
          message="Add cards to your wallet to start tracking benefits."
          actionLabel="Add Card"
          onAction={() => {
            // Will open AddCardSheet
          }}
        />
      ) : (
        <FlatList
          data={cards}
          renderItem={renderCardItem}
          keyExtractor={(item) => item.user_card_id || item.id}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        />
      )}

      {/* FAB */}
      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        color={theme.colors.onPrimary}
        onPress={() => {
          // Will open AddCardSheet
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
  },
  personalityBadge: {
    alignSelf: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginTop: 8,
    marginBottom: 12,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  chase524: {
    alignSelf: 'center',
    marginBottom: 12,
  },
  segments: {
    marginBottom: 12,
  },
  listContent: {
    paddingBottom: 80,
  },
  cardItem: {
    borderRadius: 12,
    marginBottom: 8,
  },
  cardPressable: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  cardInfo: {
    flex: 1,
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    borderRadius: 16,
  },
});
