import React, { useCallback } from 'react';
import { View, StyleSheet, FlatList, Pressable } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LoadingState } from '../../../src/components/layout/LoadingState';
import { EmptyState } from '../../../src/components/layout/EmptyState';
import { CardImage } from '../../../src/components/ui/CardImage';
import { BenefitPeriodTracker } from '../../../src/components/wallet/BenefitPeriodTracker';
import { useWallet, useToggleIgnoreBenefit } from '../../../src/hooks/useWallet';
import { formatCurrency } from '../../../src/utils/formatters';
import type { BenefitDisplay } from '../../../src/types/card';

export default function WalletCardDetailScreen() {
  const { userCardId } = useLocalSearchParams<{ userCardId: string }>();
  const { data: walletData, isLoading } = useWallet();
  const toggleIgnore = useToggleIgnoreBenefit();
  const theme = useTheme();
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const allCards = [
    ...(walletData?.active_cards ?? []),
    ...(walletData?.inactive_cards ?? []),
    ...(walletData?.eyeing_cards ?? []),
  ];
  const card = allCards.find((c: any) => c.user_card_id === userCardId);

  // Collect all benefits for this card, sorted by expiring soon
  const allBenefits = [
    ...(walletData?.action_needed_benefits ?? []),
    ...(walletData?.maxed_out_benefits ?? []),
    ...(walletData?.ignored_benefits ?? []),
  ]
    .filter((b) => b.user_card_id === userCardId)
    .sort((a, b) => (a.days_until_expiration ?? 999) - (b.days_until_expiration ?? 999));

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

  const statusColor =
    card.status === 'active' ? '#10B981' :
    card.status === 'inactive' ? '#94A3B8' : '#60A5FA';

  return (
    <View style={styles.container}>
      {/* Dark Gradient Header */}
      <LinearGradient
        colors={['#0F1629', '#1A2332', '#1E293B']}
        style={[styles.gradientHeader, { paddingTop: insets.top + 12 }]}
      >
        {/* Background orbs */}
        <View style={styles.orbContainer} pointerEvents="none">
          <View style={styles.blueOrb} />
          <View style={styles.purpleOrb} />
        </View>

        {/* Back button */}
        <Pressable
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <MaterialCommunityIcons name="arrow-left" size={20} color="#94A3B8" />
          <Text style={styles.backText}>Back to Wallet</Text>
        </Pressable>

        {/* Card Info Row */}
        <View style={styles.cardInfoRow}>
          <CardImage slug={card.card_id} size="medium" style={{ marginRight: 16 }} />
          <View style={{ flex: 1 }}>
            <Text style={styles.cardName}>{card.name}</Text>
            <Text style={styles.cardIssuer}>
              {card.issuer} · {formatCurrency(card.annual_fee)}/yr
            </Text>
          </View>
          <View style={[styles.statusBadge, { borderColor: statusColor }]}>
            <Text style={[styles.statusText, { color: statusColor }]}>
              {card.status?.toUpperCase() || 'ACTIVE'}
            </Text>
          </View>
        </View>
      </LinearGradient>

      {/* Benefits List */}
      {allBenefits.length === 0 ? (
        <View style={styles.emptyContainer}>
          <EmptyState
            icon="gift-outline"
            title="No trackable benefits"
            message="This card doesn't have any benefits with dollar values to track."
          />
        </View>
      ) : (
        <FlatList
          data={allBenefits}
          renderItem={({ item }) => (
            <BenefitPeriodTracker
              benefit={item}
              onToggleIgnore={handleToggleIgnore}
              isIgnoring={toggleIgnore.isPending && toggleIgnore.variables?.benefitId === item.benefit_id}
            />
          )}
          keyExtractor={(item) => `${item.user_card_id}-${item.benefit_id}`}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  gradientHeader: {
    paddingHorizontal: 20,
    paddingBottom: 24,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
    overflow: 'hidden',
    position: 'relative',
  },
  orbContainer: {
    ...StyleSheet.absoluteFillObject,
  },
  blueOrb: {
    position: 'absolute',
    top: '-20%',
    right: '-10%',
    width: 250,
    height: 250,
    borderRadius: 125,
    backgroundColor: 'rgba(37, 99, 235, 0.2)',
  },
  purpleOrb: {
    position: 'absolute',
    bottom: '-15%',
    left: '-15%',
    width: 180,
    height: 180,
    borderRadius: 90,
    backgroundColor: 'rgba(124, 58, 237, 0.12)',
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 16,
  },
  backText: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: '#94A3B8',
  },
  cardInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cardName: {
    fontSize: 22,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
  },
  cardIssuer: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: '#94A3B8',
    marginTop: 2,
  },
  statusBadge: {
    borderWidth: 1.5,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  statusText: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    letterSpacing: 0.5,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  listContent: {
    padding: 16,
    paddingBottom: 32,
  },
});
