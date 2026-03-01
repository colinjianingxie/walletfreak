import React, { useCallback, useMemo, useState } from 'react';
import { View, StyleSheet, Pressable, Alert, Modal, ScrollView } from 'react-native';
import { Text, Button, useTheme } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  useAnimatedScrollHandler,
  interpolate,
  Extrapolation,
} from 'react-native-reanimated';
import { LoadingState } from '../../../src/components/layout/LoadingState';
import { EmptyState } from '../../../src/components/layout/EmptyState';
import { CardImage } from '../../../src/components/ui/CardImage';
import { BenefitPeriodTracker } from '../../../src/components/wallet/BenefitPeriodTracker';
import { useWallet, useToggleIgnoreBenefit, useUpdateAnniversary, useRemoveCard } from '../../../src/hooks/useWallet';
import { formatCurrency } from '../../../src/utils/formatters';
import type { BenefitDisplay } from '../../../src/types/card';

const AnimatedLinearGradient = Animated.createAnimatedComponent(LinearGradient);

const COLLAPSE_DISTANCE = 80;

const MONTHS = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

const currentYear = new Date().getFullYear();
const YEARS = Array.from({ length: 15 }, (_, i) => currentYear - i);

export default function WalletCardDetailScreen() {
  const { userCardId } = useLocalSearchParams<{ userCardId: string }>();
  const { data: walletData, isLoading } = useWallet();
  const toggleIgnore = useToggleIgnoreBenefit();
  const updateAnniversary = useUpdateAnniversary();
  const removeCard = useRemoveCard();
  const theme = useTheme();
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const [showAnniversaryModal, setShowAnniversaryModal] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState<number | null>(null);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [useDefault, setUseDefault] = useState(false);

  const scrollY = useSharedValue(0);
  const scrollHandler = useAnimatedScrollHandler({
    onScroll: (event) => {
      scrollY.value = event.contentOffset.y;
    },
  });

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

  const handleOpenAnniversaryModal = useCallback(() => {
    if (card?.anniversary_date && card.anniversary_date !== 'default') {
      const parts = card.anniversary_date.split('-');
      if (parts.length >= 3) {
        setSelectedYear(parseInt(parts[0], 10));
        setSelectedMonth(parseInt(parts[1], 10) - 1);
        setSelectedDay(parseInt(parts[2], 10));
        setUseDefault(false);
      } else {
        setSelectedMonth(null);
        setSelectedDay(null);
        setSelectedYear(null);
        setUseDefault(false);
      }
    } else {
      setSelectedMonth(null);
      setSelectedDay(null);
      setSelectedYear(null);
      setUseDefault(card?.anniversary_date === 'default');
    }
    setShowAnniversaryModal(true);
  }, [card]);

  const daysInMonth = useMemo(() => {
    if (selectedMonth === null || selectedYear === null) return 31;
    return new Date(selectedYear, selectedMonth + 1, 0).getDate();
  }, [selectedMonth, selectedYear]);

  const handleSaveAnniversary = useCallback(() => {
    if (!userCardId) return;
    let anniversaryDate: string;
    if (useDefault) {
      anniversaryDate = 'default';
    } else if (selectedMonth !== null && selectedYear !== null && selectedDay !== null) {
      const mm = String(selectedMonth + 1).padStart(2, '0');
      const dd = String(selectedDay).padStart(2, '0');
      anniversaryDate = `${selectedYear}-${mm}-${dd}`;
    } else {
      return;
    }

    updateAnniversary.mutate(
      { userCardId, anniversaryDate },
      {
        onSuccess: () => {
          setShowAnniversaryModal(false);
        },
      }
    );
  }, [userCardId, useDefault, selectedMonth, selectedDay, selectedYear, updateAnniversary]);

  const handleDeleteCard = useCallback(() => {
    if (!card) return;
    Alert.alert(
      'Remove Card',
      `Are you sure you want to remove ${card.name} from your wallet? This will delete all benefit tracking data.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () =>
            removeCard.mutate(
              { userCardId: card.user_card_id },
              { onSuccess: () => router.back() }
            ),
        },
      ]
    );
  }, [card, removeCard, router]);

  // Animated styles for collapsible header
  const animatedBackButton = useAnimatedStyle(() => ({
    opacity: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE * 0.5], [1, 0], Extrapolation.CLAMP),
    height: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE * 0.5], [36, 0], Extrapolation.CLAMP),
    overflow: 'hidden' as const,
  }));

  const animatedCardImage = useAnimatedStyle(() => ({
    opacity: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [1, 0], Extrapolation.CLAMP),
    width: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [80, 0], Extrapolation.CLAMP),
    marginRight: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [16, 0], Extrapolation.CLAMP),
    overflow: 'hidden' as const,
  }));

  const animatedCardName = useAnimatedStyle(() => ({
    fontSize: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [22, 16], Extrapolation.CLAMP),
  }));

  const animatedHeaderPadding = useAnimatedStyle(() => ({
    paddingBottom: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [24, 12], Extrapolation.CLAMP),
  }));

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

  const isDeprecated = card.is_active === false;
  const statusColor = isDeprecated ? '#EF4444' :
    card.status === 'active' ? '#10B981' :
    card.status === 'inactive' ? '#94A3B8' : '#60A5FA';
  const statusLabel = isDeprecated ? 'DISCONTINUED' : (card.status?.toUpperCase() || 'ACTIVE');

  return (
    <View style={styles.container}>
      {/* Collapsible Dark Gradient Header */}
      <AnimatedLinearGradient
        colors={['#0F1629', '#1A2332', '#1E293B']}
        style={[styles.gradientHeader, { paddingTop: insets.top + 12 }, animatedHeaderPadding]}
      >
        {/* Background orbs */}
        <View style={styles.orbContainer} pointerEvents="none">
          <View style={styles.blueOrb} />
          <View style={styles.purpleOrb} />
        </View>

        {/* Back button — collapses away */}
        <Animated.View style={animatedBackButton}>
          <Pressable
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <MaterialCommunityIcons name="arrow-left" size={20} color="#94A3B8" />
            <Text style={styles.backText}>Back to Wallet</Text>
          </Pressable>
        </Animated.View>

        {/* Card Info Row */}
        <View style={styles.cardInfoRow}>
          <Animated.View style={animatedCardImage}>
            <CardImage slug={card.card_id} size="medium" />
          </Animated.View>
          <View style={{ flex: 1 }}>
            <Animated.Text style={[styles.cardName, animatedCardName]} numberOfLines={2}>
              {card.name}
            </Animated.Text>
            <Text style={styles.cardIssuer}>
              {card.issuer} · {formatCurrency(card.annual_fee)}/yr
            </Text>
          </View>
        </View>

        {/* Status + Actions Row */}
        {isDeprecated && (
          <View style={styles.deprecationBanner}>
            <MaterialCommunityIcons name="alert-circle-outline" size={16} color="#FCA5A5" />
            <Text style={styles.deprecationText}>
              {card.deprecation_reason || 'This card has been discontinued'}
            </Text>
          </View>
        )}

        <View style={styles.statusActionsRow}>
          <View style={[styles.statusBadge, { borderColor: statusColor }]}>
            <Text style={[styles.statusText, { color: statusColor }]}>
              {statusLabel}
            </Text>
          </View>
          <View style={styles.actionButtons}>
            <Pressable style={styles.actionBtn} onPress={handleOpenAnniversaryModal}>
              <MaterialCommunityIcons name="calendar-edit" size={18} color="#94A3B8" />
              <Text style={styles.actionBtnLabel}>
                {card.anniversary_date && card.anniversary_date !== 'default'
                  ? (() => {
                      const parts = card.anniversary_date.split('-');
                      if (parts.length >= 3) {
                        const monthIdx = parseInt(parts[1], 10) - 1;
                        return `${MONTHS[monthIdx]} ${parseInt(parts[2], 10)}, ${parts[0]}`;
                      }
                      return 'Set Date';
                    })()
                  : 'Set Date'}
              </Text>
            </Pressable>
            <Pressable style={[styles.actionBtn, styles.actionBtnDanger]} onPress={handleDeleteCard}>
              <MaterialCommunityIcons name="delete-outline" size={18} color="#EF4444" />
              <Text style={[styles.actionBtnLabel, { color: '#EF4444' }]}>Remove</Text>
            </Pressable>
          </View>
        </View>

      </AnimatedLinearGradient>

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
        <Animated.FlatList
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
          onScroll={scrollHandler}
          scrollEventThrottle={16}
        />
      )}

      {/* Anniversary Edit Modal */}
      <Modal
        visible={showAnniversaryModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowAnniversaryModal(false)}
      >
        <View style={[styles.modalContainer, { backgroundColor: theme.colors.surface }]}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Edit Anniversary Date</Text>
            <Pressable onPress={() => setShowAnniversaryModal(false)} style={styles.modalClose}>
              <MaterialCommunityIcons name="close" size={24} color={theme.colors.onSurface} />
            </Pressable>
          </View>

          <View style={[styles.modalDivider, { backgroundColor: theme.colors.outlineVariant }]} />

          <ScrollView showsVerticalScrollIndicator={false}>

          <View style={styles.warningBox}>
            <MaterialCommunityIcons name="alert-circle-outline" size={20} color="#F59E0B" style={{ marginRight: 8 }} />
            <Text style={styles.warningText}>
              Changing your anniversary date will reset benefit tracking for this card.
            </Text>
          </View>

          <Text style={[styles.pickerLabel, { color: theme.colors.onSurface }]}>Month</Text>
          <View style={styles.monthGrid}>
            {MONTHS.map((m, i) => (
              <Pressable
                key={m}
                style={[
                  styles.monthChip,
                  {
                    backgroundColor: selectedMonth === i ? theme.colors.primary : theme.colors.surfaceVariant,
                    borderColor: selectedMonth === i ? theme.colors.primary : theme.colors.outlineVariant,
                  },
                ]}
                onPress={() => {
                  setSelectedMonth(i);
                  setUseDefault(false);
                  if (selectedDay !== null && selectedYear !== null) {
                    const maxDay = new Date(selectedYear, i + 1, 0).getDate();
                    if (selectedDay > maxDay) setSelectedDay(maxDay);
                  }
                }}
              >
                <Text
                  style={[
                    styles.chipText,
                    { color: selectedMonth === i ? '#FFFFFF' : theme.colors.onSurface },
                  ]}
                >
                  {m}
                </Text>
              </Pressable>
            ))}
          </View>

          <Text style={[styles.pickerLabel, { color: theme.colors.onSurface }]}>Day</Text>
          <View style={styles.dayGrid}>
            {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((d) => (
              <Pressable
                key={d}
                style={[
                  styles.dayChip,
                  {
                    backgroundColor: selectedDay === d ? theme.colors.primary : theme.colors.surfaceVariant,
                    borderColor: selectedDay === d ? theme.colors.primary : theme.colors.outlineVariant,
                  },
                ]}
                onPress={() => { setSelectedDay(d); setUseDefault(false); }}
              >
                <Text
                  style={[
                    styles.chipText,
                    { color: selectedDay === d ? '#FFFFFF' : theme.colors.onSurface },
                  ]}
                >
                  {d}
                </Text>
              </Pressable>
            ))}
          </View>

          <Text style={[styles.pickerLabel, { color: theme.colors.onSurface }]}>Year</Text>
          <View style={styles.yearGrid}>
            {YEARS.map((y) => (
              <Pressable
                key={y}
                style={[
                  styles.yearChip,
                  {
                    backgroundColor: selectedYear === y ? theme.colors.primary : theme.colors.surfaceVariant,
                    borderColor: selectedYear === y ? theme.colors.primary : theme.colors.outlineVariant,
                  },
                ]}
                onPress={() => {
                  setSelectedYear(y);
                  setUseDefault(false);
                  if (selectedDay !== null && selectedMonth !== null) {
                    const maxDay = new Date(y, selectedMonth + 1, 0).getDate();
                    if (selectedDay > maxDay) setSelectedDay(maxDay);
                  }
                }}
              >
                <Text
                  style={[
                    styles.chipText,
                    { color: selectedYear === y ? '#FFFFFF' : theme.colors.onSurface },
                  ]}
                >
                  {y}
                </Text>
              </Pressable>
            ))}
          </View>

          <Pressable
            style={[
              styles.defaultOption,
              {
                backgroundColor: useDefault ? theme.colors.primaryContainer : theme.colors.surfaceVariant,
                borderColor: useDefault ? theme.colors.primary : theme.colors.outlineVariant,
              },
            ]}
            onPress={() => {
              const next = !useDefault;
              setUseDefault(next);
              if (next) {
                setSelectedMonth(null);
                setSelectedDay(null);
                setSelectedYear(null);
              }
            }}
          >
            <MaterialCommunityIcons
              name={useDefault ? 'checkbox-marked-circle' : 'checkbox-blank-circle-outline'}
              size={20}
              color={useDefault ? theme.colors.primary : theme.colors.onSurfaceVariant}
              style={{ marginRight: 8 }}
            />
            <Text style={[styles.defaultOptionText, { color: theme.colors.onSurface }]}>
              I don't know my anniversary date
            </Text>
          </Pressable>

          <Button
            mode="contained"
            onPress={handleSaveAnniversary}
            loading={updateAnniversary.isPending}
            disabled={updateAnniversary.isPending || (!useDefault && (selectedMonth === null || selectedDay === null || selectedYear === null))}
            style={styles.saveButton}
            contentStyle={{ paddingVertical: 6 }}
          >
            Save Anniversary Date
          </Button>

          </ScrollView>
        </View>
      </Modal>
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
    alignItems: 'flex-start',
  },
  cardName: {
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
  },
  cardIssuer: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: '#94A3B8',
    marginTop: 2,
  },
  statusActionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 14,
  },
  statusBadge: {
    borderWidth: 1.5,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 4,
    alignItems: 'center',
  },
  statusText: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    letterSpacing: 0.5,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  actionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  actionBtnDanger: {
    backgroundColor: 'rgba(239,68,68,0.1)',
  },
  actionBtnLabel: {
    fontSize: 12,
    fontFamily: 'Outfit-Medium',
    color: '#94A3B8',
  },
  deprecationBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 10,
    marginTop: 12,
  },
  deprecationText: {
    flex: 1,
    fontSize: 13,
    fontFamily: 'Outfit',
    color: '#FCA5A5',
    lineHeight: 18,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  listContent: {
    padding: 16,
    paddingBottom: 32,
  },
  // Modal styles
  modalContainer: {
    flex: 1,
    padding: 24,
    paddingTop: 16,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  modalTitle: {
    fontSize: 20,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
  },
  modalClose: {
    padding: 4,
  },
  modalDivider: {
    height: 1,
    marginVertical: 16,
  },
  warningBox: {
    flexDirection: 'row',
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 14,
    marginBottom: 24,
    alignItems: 'flex-start',
  },
  warningText: {
    flex: 1,
    fontSize: 13,
    fontFamily: 'Outfit',
    color: '#92400E',
    lineHeight: 18,
  },
  pickerLabel: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    marginBottom: 8,
  },
  monthGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 20,
  },
  monthChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
  },
  dayGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 20,
  },
  dayChip: {
    width: 40,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  yearGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 20,
  },
  yearChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
  },
  chipText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
  },
  defaultOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    marginTop: 4,
    marginBottom: 24,
  },
  defaultOptionText: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
  },
  saveButton: {
    borderRadius: 12,
  },
});
