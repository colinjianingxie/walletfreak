import React, { useState, useCallback, useRef } from 'react';
import { View, StyleSheet, Pressable, SectionList } from 'react-native';
import {
  Text,
  useTheme,
  FAB,
  Surface,
} from 'react-native-paper';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  useAnimatedScrollHandler,
  interpolate,
  Extrapolation,
} from 'react-native-reanimated';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import BottomSheet from '@gorhom/bottom-sheet';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { CardImage } from '../../src/components/ui/CardImage';
import { CardActionsSheet } from '../../src/components/wallet/CardActionsSheet';
import { AddCardSheet } from '../../src/components/wallet/AddCardSheet';
import { PersonalityAvatar } from '../../src/components/personality/PersonalityAvatar';
import { useWallet } from '../../src/hooks/useWallet';
import { useLoyaltyPrograms } from '../../src/hooks/useLoyalty';
import { formatCurrency } from '../../src/utils/formatters';
import { LoyaltyProgramCard } from '../../src/components/loyalty/LoyaltyProgramCard';
import { EditBalanceSheet } from '../../src/components/loyalty/EditBalanceSheet';
import { AddProgramSheet } from '../../src/components/loyalty/AddProgramSheet';
import type { BenefitDisplay } from '../../src/types/card';
import type { LoyaltyProgram } from '../../src/types/loyalty';

const AnimatedLinearGradient = Animated.createAnimatedComponent(LinearGradient);
const AnimatedSectionList = Animated.createAnimatedComponent(SectionList);

const COLLAPSE_DISTANCE = 160;

// Benefit type icon/color mapping
const BENEFIT_TYPE_MAP: Record<string, { icon: string; color: string }> = {
  Credit: { icon: 'credit-card-check-outline', color: '#60A5FA' },
  'Free Night': { icon: 'bed-outline', color: '#A78BFA' },
  Security: { icon: 'shield-check-outline', color: '#34D399' },
  Upgrade: { icon: 'arrow-up-circle-outline', color: '#FB923C' },
  Savings: { icon: 'piggy-bank-outline', color: '#4ADE80' },
  Membership: { icon: 'card-account-details-outline', color: '#F472B6' },
  Financing: { icon: 'percent-outline', color: '#FBBF24' },
  Access: { icon: 'key-outline', color: '#818CF8' },
  Other: { icon: 'gift-outline', color: '#9CA3AF' },
};

type ViewMode = 'cards' | 'benefits' | 'loyalty';

export default function WalletScreen() {
  const [viewMode, setViewMode] = useState<ViewMode>('cards');
  const [selectedCard, setSelectedCard] = useState<any>(null);
  const [selectedLoyaltyProgram, setSelectedLoyaltyProgram] = useState<LoyaltyProgram | null>(null);
  const { data, isLoading, refetch } = useWallet();
  const { data: loyaltyData } = useLoyaltyPrograms();
  const router = useRouter();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const sheetRef = useRef<BottomSheet>(null);
  const addCardSheetRef = useRef<BottomSheet>(null);
  const editBalanceSheetRef = useRef<BottomSheet>(null);
  const addProgramSheetRef = useRef<BottomSheet>(null);

  // Scroll-driven animation
  const scrollY = useSharedValue(0);
  const scrollHandler = useAnimatedScrollHandler({
    onScroll: (event) => {
      scrollY.value = event.contentOffset.y;
    },
  });

  const walletData = data;
  const activeCards = walletData?.active_cards ?? [];

  const handleLongPress = useCallback((item: any) => {
    setSelectedCard(item);
    sheetRef.current?.snapToIndex(0);
  }, []);

  const handleSheetDismiss = useCallback(() => {
    setSelectedCard(null);
    sheetRef.current?.close();
  }, []);

  const handleTabSwitch = useCallback((mode: ViewMode) => {
    setViewMode(mode);
    scrollY.value = 0;
  }, [scrollY]);

  // Group benefits by benefit_type, sorted by expiring soon
  const benefitsByCategory = useCallback(() => {
    const allBenefits = [
      ...(walletData?.action_needed_benefits ?? []),
      ...(walletData?.maxed_out_benefits ?? []),
      ...(walletData?.ignored_benefits ?? []),
    ].sort((a, b) => (a.days_until_expiration ?? 999) - (b.days_until_expiration ?? 999));

    const groups: Record<string, BenefitDisplay[]> = {};
    allBenefits.forEach((b) => {
      const category = b.benefit_type || 'Other';
      if (!groups[category]) groups[category] = [];
      groups[category].push(b);
    });

    return Object.entries(groups).map(([title, data]) => ({
      title,
      data,
    }));
  }, [walletData]);

  // --- Animated Styles ---
  const animatedStatsGrid = useAnimatedStyle(() => ({
    opacity: interpolate(scrollY.value, [0, 84], [1, 0], Extrapolation.CLAMP),
    height: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [160, 0], Extrapolation.CLAMP),
    marginBottom: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [16, 0], Extrapolation.CLAMP),
    overflow: 'hidden' as const,
  }));

  const animatedTitle = useAnimatedStyle(() => ({
    fontSize: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [32, 20], Extrapolation.CLAMP),
  }));

  const animatedSubtitle = useAnimatedStyle(() => ({
    opacity: interpolate(scrollY.value, [0, 70], [1, 0], Extrapolation.CLAMP),
    height: interpolate(scrollY.value, [0, 70], [22, 0], Extrapolation.CLAMP),
    overflow: 'hidden' as const,
  }));

  const animatedInlineNetValue = useAnimatedStyle(() => ({
    opacity: interpolate(scrollY.value, [70, COLLAPSE_DISTANCE], [0, 1], Extrapolation.CLAMP),
  }));

  const animatedHeaderRow = useAnimatedStyle(() => ({
    marginBottom: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [16, 8], Extrapolation.CLAMP),
  }));

  const animatedHeaderPadding = useAnimatedStyle(() => ({
    paddingBottom: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [20, 12], Extrapolation.CLAMP),
  }));

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
            <Text variant="titleSmall" numberOfLines={1} style={{ fontFamily: 'Outfit-SemiBold' }}>
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
      const usedAmount = item.ytd_used ?? item.used ?? 0;
      const totalAmount = item.amount ?? 0;
      const progress = totalAmount > 0 ? Math.min(usedAmount / totalAmount, 1) : 0;

      const typeInfo = BENEFIT_TYPE_MAP[item.benefit_type || 'Other'] || BENEFIT_TYPE_MAP.Other;
      const barColor = typeInfo.color;

      return (
        <Pressable
          style={styles.benefitRow}
          onPress={() => router.push(`/stacks/wallet-card/${item.user_card_id}` as any)}
        >
          <View style={styles.benefitInfo}>
            <CardImage slug={item.card_id} size="small" style={{ marginRight: 10 }} />
            <View style={{ flex: 1 }}>
              <Text variant="bodyMedium" style={{ fontFamily: 'Outfit' }}>
                {item.benefit_name}
              </Text>
              <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
                {item.card_name}
              </Text>
            </View>
            <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant, textAlign: 'right' }}>
              {formatCurrency(usedAmount)} / {formatCurrency(totalAmount)}
            </Text>
          </View>
          <View style={[styles.progressBarBg, { marginLeft: 58 }]}>
            <View
              style={[
                styles.progressBarFill,
                {
                  width: `${progress * 100}%`,
                  backgroundColor: barColor,
                },
              ]}
            />
          </View>
        </Pressable>
      );
    },
    [theme, router]
  );

  const renderBenefitSectionHeader = useCallback(
    ({ section }: { section: { title: string; data: BenefitDisplay[] } }) => {
      const typeInfo = BENEFIT_TYPE_MAP[section.title] || BENEFIT_TYPE_MAP.Other;
      return (
        <View style={styles.benefitSectionHeader}>
          <View style={[styles.benefitSectionIcon, { backgroundColor: typeInfo.color + '20' }]}>
            <MaterialCommunityIcons
              name={typeInfo.icon as any}
              size={16}
              color={typeInfo.color}
            />
          </View>
          <Text variant="titleMedium" style={[styles.benefitSectionTitle, { color: theme.colors.onSurface }]}>
            {section.title}
          </Text>
          <View style={[styles.benefitSectionCount, { backgroundColor: typeInfo.color + '20' }]}>
            <Text style={[styles.benefitSectionCountText, { color: typeInfo.color }]}>
              {section.data.length}
            </Text>
          </View>
        </View>
      );
    },
    [theme]
  );

  if (isLoading) {
    return <LoadingState message="Loading wallet..." />;
  }

  const chase524Count = walletData?.chase_524_count ?? 0;
  const chaseEligible = walletData?.chase_eligible ?? true;
  const netPerformance = walletData?.net_performance ?? 0;

  return (
    <View style={styles.container}>
      {/* Collapsible Dark Gradient Header */}
      <AnimatedLinearGradient
        colors={['#0F1629', '#1A2332', '#1E293B']}
        style={[styles.gradientHeader, { paddingTop: insets.top + 12 }, animatedHeaderPadding]}
      >
        {/* Background gradient orbs */}
        <View style={styles.orbContainer} pointerEvents="none">
          <View style={styles.blueOrb} />
          <View style={styles.purpleOrb} />
          <View style={styles.gradientLine} />
        </View>

        {/* Title Row */}
        <Animated.View style={[styles.headerRow, animatedHeaderRow]}>
          <View>
            <View style={styles.titleInlineRow}>
              <Animated.Text style={[styles.headerTitle, animatedTitle]}>
                Wallet
              </Animated.Text>
              {/* Inline mode chip — visible when collapsed */}
              <Animated.View style={[
                styles.inlineNetValueChip,
                animatedInlineNetValue,
                {
                  backgroundColor: netPerformance > 10
                    ? 'rgba(52, 211, 153, 0.15)'
                    : netPerformance >= -10
                      ? 'rgba(251, 191, 36, 0.15)'
                      : 'rgba(239, 68, 68, 0.15)',
                },
              ]}>
                <View style={[styles.statusDot, {
                  backgroundColor: netPerformance > 10 ? '#34D399' : netPerformance >= -10 ? '#FBBF24' : '#EF4444',
                }]} />
                <Text style={[styles.inlineNetValueText, {
                  color: netPerformance > 10 ? '#34D399' : netPerformance >= -10 ? '#FBBF24' : '#EF4444',
                }]}>
                  {netPerformance > 10 ? 'Profit Mode' : netPerformance >= -10 ? 'Break Even' : 'Underutilizing'}
                </Text>
              </Animated.View>
            </View>
            <Animated.View style={[styles.subtitleRow, animatedSubtitle]}>
              <Text style={styles.subtitleText}>Overview</Text>
              <Text style={styles.subtitleDot}> · </Text>
              <View style={styles.statusBadge}>
                <View style={[styles.statusDot, { backgroundColor: chaseEligible ? '#34D399' : '#EF4444' }]} />
                <Text style={[styles.statusText, { color: chaseEligible ? '#E2E8F0' : '#FCA5A5' }]}>{chase524Count}/24 Status</Text>
              </View>
            </Animated.View>
          </View>
          {walletData?.personality ? (
            <Pressable
              style={styles.headerIconButton}
              onPress={() => router.push(`/stacks/personality/${walletData.personality.id}` as any)}
            >
              <PersonalityAvatar slug={walletData.personality.id} size={34} />
            </Pressable>
          ) : (
            <Pressable
              style={styles.headerIconButton}
              onPress={() => router.push('/stacks/personality-quiz' as any)}
            >
              <MaterialCommunityIcons name="help-circle-outline" size={22} color="#60A5FA" />
            </Pressable>
          )}
        </Animated.View>

        {/* Stats Grid 2x2 — collapses on scroll */}
        <Animated.View style={[styles.statsGrid, animatedStatsGrid]}>
          <View style={styles.statsGridRow}>
            <View style={styles.statBox}>
              <View style={styles.statLabelRow}>
                <MaterialCommunityIcons name="arrow-top-right" size={14} color="#60A5FA" />
                <Text style={[styles.statLabel, { color: '#60A5FA' }]}>REWARDS YTD</Text>
              </View>
              <Text style={styles.statValue}>
                {formatCurrency(walletData?.total_potential_value ?? 0)}
              </Text>
            </View>
            <View style={styles.statBox}>
              <View style={styles.statLabelRow}>
                <MaterialCommunityIcons name="check-circle-outline" size={14} color="#34D399" />
                <Text style={[styles.statLabel, { color: '#34D399' }]}>CREDITS USED</Text>
              </View>
              <Text style={styles.statValue}>
                {formatCurrency(walletData?.total_extracted_value ?? 0)}
              </Text>
            </View>
          </View>
          <View style={styles.statsGridRow}>
            <View style={styles.statBox}>
              <View style={styles.statLabelRow}>
                <MaterialCommunityIcons name="credit-card-outline" size={14} color="#FB923C" />
                <Text style={[styles.statLabel, { color: '#FB923C' }]}>ANNUAL FEES</Text>
              </View>
              <Text style={styles.statValue}>
                {formatCurrency(walletData?.total_annual_fee ?? 0)}
              </Text>
            </View>
            <View style={styles.statBox}>
              <View style={styles.statLabelRow}>
                <MaterialCommunityIcons name="chart-line" size={14} color="#34D399" />
                <Text style={[styles.statLabel, { color: '#34D399' }]}>NET VALUE</Text>
              </View>
              <Text style={styles.statValue}>
                {netPerformance >= 0 ? '+' : ''}
                {formatCurrency(netPerformance)}
              </Text>
            </View>
          </View>
        </Animated.View>

        {/* Tab Switcher — always visible */}
        <View style={styles.tabSwitcher}>
          {(['cards', 'benefits', 'loyalty'] as ViewMode[]).map((mode) => (
            <Pressable
              key={mode}
              style={[
                styles.tabButton,
                viewMode === mode && styles.tabButtonActive,
              ]}
              onPress={() => handleTabSwitch(mode)}
            >
              <Text
                style={[
                  styles.tabButtonText,
                  viewMode === mode && styles.tabButtonTextActive,
                ]}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </Text>
            </Pressable>
          ))}
        </View>
      </AnimatedLinearGradient>

      {/* Content Area */}
      <View style={[styles.contentArea, { backgroundColor: theme.colors.background }]}>
        {viewMode === 'loyalty' ? (
          <>
            {loyaltyData?.programs && loyaltyData.programs.length > 0 ? (
              <>
                <View style={[styles.loyaltyTotalHeader, { backgroundColor: theme.colors.primaryContainer }]}>
                  <Text variant="labelMedium" style={{ color: theme.colors.onPrimaryContainer }}>
                    Total Estimated Value
                  </Text>
                  <Text variant="headlineSmall" style={{ color: theme.colors.onPrimaryContainer, fontFamily: 'Outfit-Bold' }}>
                    {formatCurrency(loyaltyData?.total_est_value ?? 0)}
                  </Text>
                </View>
                <Animated.FlatList
                  data={loyaltyData.programs}
                  renderItem={({ item }: { item: LoyaltyProgram }) => (
                    <LoyaltyProgramCard
                      program={item}
                      onPress={(p) => {
                        setSelectedLoyaltyProgram(p);
                        editBalanceSheetRef.current?.snapToIndex(0);
                      }}
                    />
                  )}
                  keyExtractor={(item) => item.program_id}
                  contentContainerStyle={styles.listContent}
                  showsVerticalScrollIndicator={false}
                  onScroll={scrollHandler}
                  scrollEventThrottle={16}
                />
              </>
            ) : (
              <EmptyState
                icon="star-circle-outline"
                title="No loyalty programs"
                message="Add loyalty programs to track your points, miles, and cash back."
                actionLabel="Add Program"
                onAction={() => addProgramSheetRef.current?.snapToIndex(0)}
              />
            )}
          </>
        ) : viewMode === 'cards' ? (
          <>
            {activeCards.length === 0 ? (
              <EmptyState
                icon="credit-card-plus-outline"
                title="No cards yet"
                message="Add cards to your wallet to start tracking benefits."
                actionLabel="Add Card"
                onAction={() => addCardSheetRef.current?.snapToIndex(0)}
              />
            ) : (
              <Animated.FlatList
                data={activeCards}
                renderItem={renderCardItem}
                keyExtractor={(item: any) => item.user_card_id || item.id}
                contentContainerStyle={styles.listContent}
                showsVerticalScrollIndicator={false}
                onScroll={scrollHandler}
                scrollEventThrottle={16}
              />
            )}
          </>
        ) : (
          /* Benefits View - Grouped by benefit_type with progress bars */
          (() => {
            const sections = benefitsByCategory();
            return sections.length === 0 ? (
              <EmptyState
                icon="gift-outline"
                title="No benefits to track"
                message="Add cards with benefits to start tracking your value extraction."
              />
            ) : (
              <AnimatedSectionList
                sections={sections}
                renderItem={renderBenefitItem as any}
                renderSectionHeader={renderBenefitSectionHeader as any}
                keyExtractor={(item: any) => `${item.user_card_id}-${item.benefit_id}`}
                contentContainerStyle={styles.listContent}
                showsVerticalScrollIndicator={false}
                stickySectionHeadersEnabled={false}
                onScroll={scrollHandler}
                scrollEventThrottle={16}
              />
            );
          })()
        )}
      </View>

      {/* FAB */}
      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        color={theme.colors.onPrimary}
        onPress={() => {
          if (viewMode === 'loyalty') {
            addProgramSheetRef.current?.snapToIndex(0);
          } else {
            addCardSheetRef.current?.snapToIndex(0);
          }
        }}
      />

      {/* Add Card Sheet */}
      <AddCardSheet
        sheetRef={addCardSheetRef}
        existingCardIds={activeCards.map((c: any) => c.card_id)}
        onDismiss={() => addCardSheetRef.current?.close()}
      />

      {/* Card Actions Sheet */}
      <CardActionsSheet
        card={selectedCard}
        sheetRef={sheetRef}
        onDismiss={handleSheetDismiss}
      />

      {/* Loyalty Sheets */}
      <EditBalanceSheet
        program={selectedLoyaltyProgram}
        sheetRef={editBalanceSheetRef}
        onDismiss={() => {
          setSelectedLoyaltyProgram(null);
          editBalanceSheetRef.current?.close();
        }}
      />
      <AddProgramSheet
        sheetRef={addProgramSheetRef}
        allPrograms={loyaltyData?.all_programs ?? []}
        existingProgramIds={(loyaltyData?.programs ?? []).map((p: LoyaltyProgram) => p.program_id)}
        onDismiss={() => addProgramSheetRef.current?.close()}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradientHeader: {
    paddingHorizontal: 20,
    paddingBottom: 20,
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
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: 'rgba(37, 99, 235, 0.25)',
  },
  purpleOrb: {
    position: 'absolute',
    bottom: '-10%',
    left: '-20%',
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: 'rgba(124, 58, 237, 0.15)',
  },
  gradientLine: {
    position: 'absolute',
    top: '25%',
    left: '10%',
    right: 0,
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  titleInlineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  headerTitle: {
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
  },
  inlineNetValueChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(52, 211, 153, 0.15)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 5,
  },
  inlineNetValueText: {
    fontSize: 13,
    fontFamily: 'Outfit-SemiBold',
    color: '#34D399',
  },
  subtitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  subtitleText: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: '#94A3B8',
  },
  subtitleDot: {
    fontSize: 14,
    color: '#94A3B8',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.1)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    gap: 4,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    fontSize: 12,
    fontFamily: 'Outfit-Medium',
    color: '#E2E8F0',
  },
  headerIconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.08)',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 4,
  },
  statsGrid: {
    gap: 10,
    marginBottom: 16,
  },
  statsGridRow: {
    flexDirection: 'row',
    gap: 10,
  },
  statBox: {
    flex: 1,
    borderWidth: 1,
    borderColor: 'rgba(148, 163, 184, 0.2)',
    borderRadius: 12,
    padding: 14,
    backgroundColor: 'rgba(255,255,255,0.03)',
  },
  statLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  statLabel: {
    fontSize: 10,
    fontFamily: 'Outfit-SemiBold',
    letterSpacing: 0.5,
  },
  statValue: {
    fontSize: 22,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
  },
  tabSwitcher: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: 12,
    padding: 3,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 10,
  },
  tabButtonActive: {
    backgroundColor: 'rgba(255,255,255,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(148, 163, 184, 0.3)',
  },
  tabButtonText: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    color: '#94A3B8',
  },
  tabButtonTextActive: {
    color: '#FFFFFF',
  },
  contentArea: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 12,
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
  // Benefits styles
  benefitSectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    marginBottom: 8,
    gap: 8,
  },
  benefitSectionIcon: {
    width: 28,
    height: 28,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  benefitSectionTitle: {
    fontFamily: 'Outfit-SemiBold',
    flex: 1,
  },
  benefitSectionCount: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  benefitSectionCountText: {
    fontSize: 12,
    fontFamily: 'Outfit-SemiBold',
  },
  benefitRow: {
    marginBottom: 12,
  },
  benefitInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  progressBarBg: {
    height: 6,
    backgroundColor: '#E5E7EB',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  loyaltyTotalHeader: {
    alignItems: 'center',
    padding: 16,
    borderRadius: 16,
    marginBottom: 12,
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    borderRadius: 16,
  },
});
