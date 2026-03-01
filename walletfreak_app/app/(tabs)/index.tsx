import React, { useState, useCallback, useRef } from 'react';
import { View, StyleSheet, FlatList, Pressable, SectionList } from 'react-native';
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
import BottomSheet from '@gorhom/bottom-sheet';
import { ScreenContainer } from '../../src/components/layout/ScreenContainer';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { CardImage } from '../../src/components/ui/CardImage';
import { CardActionsSheet } from '../../src/components/wallet/CardActionsSheet';
import { PersonalityAvatar } from '../../src/components/personality/PersonalityAvatar';
import { useWallet } from '../../src/hooks/useWallet';
import { useAuthStore } from '../../src/stores/authStore';
import { formatCurrency } from '../../src/utils/formatters';
import { colors } from '../../src/theme';
import type { BenefitDisplay } from '../../src/types/card';

export default function WalletScreen() {
  const [segment, setSegment] = useState('active');
  const [viewMode, setViewMode] = useState<'cards' | 'benefits'>('cards');
  const [selectedCard, setSelectedCard] = useState<any>(null);
  const { data, isLoading, refetch } = useWallet();
  const { profile } = useAuthStore();
  const router = useRouter();
  const theme = useTheme();
  const sheetRef = useRef<BottomSheet>(null);

  const walletData = data;

  const cards =
    segment === 'active'
      ? walletData?.active_cards
      : segment === 'inactive'
        ? walletData?.inactive_cards
        : walletData?.eyeing_cards;

  const handleLongPress = useCallback((item: any) => {
    setSelectedCard(item);
    sheetRef.current?.snapToIndex(0);
  }, []);

  const handleSheetDismiss = useCallback(() => {
    setSelectedCard(null);
    sheetRef.current?.close();
  }, []);

  const benefitSections = [
    {
      title: 'Action Needed',
      data: walletData?.action_needed_benefits ?? [],
      icon: 'alert-circle-outline' as const,
      color: colors.warning,
    },
    {
      title: 'Maxed Out',
      data: walletData?.maxed_out_benefits ?? [],
      icon: 'check-circle-outline' as const,
      color: colors.success,
    },
    {
      title: 'Ignored',
      data: walletData?.ignored_benefits ?? [],
      icon: 'eye-off-outline' as const,
      color: theme.colors.outlineVariant,
    },
  ].filter((s) => s.data.length > 0);

  const renderCardItem = useCallback(
    ({ item }: { item: any }) => (
      <Surface style={[styles.cardItem, { backgroundColor: theme.colors.elevation.level1 }]} elevation={1}>
        <Pressable
          onPress={() => router.push(`/stacks/wallet-card/${item.user_card_id}` as any)}
          onLongPress={() => handleLongPress(item)}
          style={styles.cardPressable}
        >
          <CardImage slug={item.card_id} size="small" style={{ marginRight: 12 }} />
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
    [router, theme, handleLongPress]
  );

  const renderBenefitItem = useCallback(
    ({ item }: { item: BenefitDisplay }) => {
      const statusColor =
        item.current_period_status === 'full'
          ? colors.success
          : item.current_period_status === 'partial'
            ? colors.warning
            : theme.colors.outlineVariant;

      return (
        <Surface style={[styles.cardItem, { backgroundColor: theme.colors.elevation.level1 }]} elevation={1}>
          <Pressable
            onPress={() => router.push(`/stacks/wallet-card/${item.user_card_id}` as any)}
            style={styles.cardPressable}
          >
            <View style={[styles.benefitDot, { backgroundColor: statusColor }]} />
            <View style={styles.cardInfo}>
              <Text variant="titleSmall" numberOfLines={1}>
                {item.benefit_name}
              </Text>
              <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                {item.card_name}
              </Text>
            </View>
            <View style={{ alignItems: 'flex-end' }}>
              <Text variant="labelMedium" style={{ color: theme.colors.primary }}>
                {formatCurrency(item.amount)}
              </Text>
              <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
                {item.frequency}
              </Text>
            </View>
          </Pressable>
        </Surface>
      );
    },
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
          <PersonalityAvatar slug={walletData.personality.id} size={28} style={{ marginRight: 8 }} />
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

      {/* View Mode Toggle: Cards | Benefits */}
      <SegmentedButtons
        value={viewMode}
        onValueChange={(v) => setViewMode(v as 'cards' | 'benefits')}
        buttons={[
          { value: 'cards', label: 'Cards' },
          { value: 'benefits', label: 'Benefits' },
        ]}
        style={styles.viewModeSegment}
      />

      {viewMode === 'cards' ? (
        <>
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
              onAction={() => router.push('/(tabs)/explore' as any)}
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
        </>
      ) : (
        /* Benefits View */
        benefitSections.length === 0 ? (
          <EmptyState
            icon="gift-outline"
            title="No benefits to track"
            message="Add cards with benefits to start tracking your value extraction."
          />
        ) : (
          <SectionList
            sections={benefitSections}
            renderItem={renderBenefitItem}
            renderSectionHeader={({ section }) => (
              <View style={styles.sectionHeader}>
                <MaterialCommunityIcons
                  name={section.icon as any}
                  size={18}
                  color={section.color}
                />
                <Text variant="labelLarge" style={{ marginLeft: 8, color: section.color }}>
                  {section.title} ({section.data.length})
                </Text>
              </View>
            )}
            keyExtractor={(item) => `${item.user_card_id}-${item.benefit_id}`}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            stickySectionHeadersEnabled={false}
          />
        )
      )}

      {/* FAB */}
      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        color={theme.colors.onPrimary}
        onPress={() => router.push('/(tabs)/explore' as any)}
      />

      {/* Card Actions Sheet */}
      <CardActionsSheet
        card={selectedCard}
        sheetRef={sheetRef}
        onDismiss={handleSheetDismiss}
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
    flexDirection: 'row',
    alignItems: 'center',
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
  viewModeSegment: {
    marginBottom: 8,
  },
  segments: {
    marginBottom: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    marginTop: 4,
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
  benefitDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 12,
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    borderRadius: 16,
  },
});
