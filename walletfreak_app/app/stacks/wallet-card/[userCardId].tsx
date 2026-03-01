import React, { useRef, useState, useCallback } from 'react';
import { View, StyleSheet, SectionList } from 'react-native';
import { Text, Chip, useTheme } from 'react-native-paper';
import { useLocalSearchParams } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import BottomSheet from '@gorhom/bottom-sheet';
import { LoadingState } from '../../../src/components/layout/LoadingState';
import { EmptyState } from '../../../src/components/layout/EmptyState';
import { CardImage } from '../../../src/components/ui/CardImage';
import { BenefitPeriodTracker } from '../../../src/components/wallet/BenefitPeriodTracker';
import { BenefitUsageModal } from '../../../src/components/wallet/BenefitUsageModal';
import { useWallet, useToggleIgnoreBenefit } from '../../../src/hooks/useWallet';
import { formatCurrency } from '../../../src/utils/formatters';
import { colors } from '../../../src/theme';
import type { BenefitDisplay } from '../../../src/types/card';

export default function WalletCardDetailScreen() {
  const { userCardId } = useLocalSearchParams<{ userCardId: string }>();
  const { data: walletData, isLoading } = useWallet();
  const toggleIgnore = useToggleIgnoreBenefit();
  const theme = useTheme();
  const usageSheetRef = useRef<BottomSheet>(null);
  const [selectedBenefit, setSelectedBenefit] = useState<BenefitDisplay | null>(null);

  // Find the card across all segments
  const allCards = [
    ...(walletData?.active_cards ?? []),
    ...(walletData?.inactive_cards ?? []),
    ...(walletData?.eyeing_cards ?? []),
  ];
  const card = allCards.find((c: any) => c.user_card_id === userCardId);

  // Filter benefits for this card
  const filterBenefits = (benefits: BenefitDisplay[]) =>
    benefits.filter((b) => b.user_card_id === userCardId);

  const sections = [
    {
      title: 'Action Needed',
      data: filterBenefits(walletData?.action_needed_benefits ?? []),
      icon: 'alert-circle-outline' as const,
      color: colors.warning,
    },
    {
      title: 'Maxed Out',
      data: filterBenefits(walletData?.maxed_out_benefits ?? []),
      icon: 'check-circle-outline' as const,
      color: colors.success,
    },
    {
      title: 'Ignored',
      data: filterBenefits(walletData?.ignored_benefits ?? []),
      icon: 'eye-off-outline' as const,
      color: theme.colors.outlineVariant,
    },
  ].filter((s) => s.data.length > 0);

  const handleMarkUsed = useCallback((benefit: BenefitDisplay) => {
    setSelectedBenefit(benefit);
    usageSheetRef.current?.snapToIndex(0);
  }, []);

  const handleToggleIgnore = useCallback((benefit: BenefitDisplay) => {
    toggleIgnore.mutate({
      userCardId: benefit.user_card_id,
      benefitId: benefit.benefit_id,
      isIgnored: !benefit.is_ignored,
    });
  }, [toggleIgnore]);

  if (isLoading) {
    return <LoadingState message="Loading card..." />;
  }

  if (!card) {
    return (
      <EmptyState
        icon="credit-card-off-outline"
        title="Card not found"
        message="This card may have been removed from your wallet."
      />
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Card Header */}
      <View style={styles.header}>
        <CardImage slug={card.card_id} size="medium" style={{ marginRight: 16 }} />
        <View style={{ flex: 1 }}>
          <Text variant="titleMedium" style={{ fontFamily: 'Outfit-SemiBold' }}>
            {card.name}
          </Text>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {card.issuer}
          </Text>
          <View style={styles.cardMeta}>
            <Chip compact style={{ marginRight: 8 }}>
              {card.status}
            </Chip>
            <Text variant="labelSmall" style={{ color: theme.colors.primary }}>
              {formatCurrency(card.annual_fee)}/yr
            </Text>
          </View>
          {card.anniversary_date && (
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 4 }}>
              Anniversary: {card.anniversary_date}
            </Text>
          )}
        </View>
      </View>

      {/* Benefits */}
      {sections.length === 0 ? (
        <EmptyState
          icon="gift-outline"
          title="No trackable benefits"
          message="This card doesn't have any benefits with dollar values to track."
        />
      ) : (
        <SectionList
          sections={sections}
          renderItem={({ item }) => (
            <BenefitPeriodTracker
              benefit={item}
              onMarkUsed={handleMarkUsed}
              onToggleIgnore={handleToggleIgnore}
            />
          )}
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
      )}

      {/* Usage Modal */}
      <BenefitUsageModal
        benefit={selectedBenefit}
        sheetRef={usageSheetRef}
        onDismiss={() => {
          setSelectedBenefit(null);
          usageSheetRef.current?.close();
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
  },
  cardMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    marginTop: 4,
  },
  listContent: {
    paddingBottom: 32,
  },
});
