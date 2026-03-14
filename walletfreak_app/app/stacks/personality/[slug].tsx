import React, { useMemo, useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, FlatList, Pressable } from 'react-native';
import { Text, Surface, useTheme } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../../src/components/layout/LoadingState';
import { PersonalityAvatar } from '../../../src/components/personality/PersonalityAvatar';
import { CardImage } from '../../../src/components/ui/CardImage';
import { usePersonalityDetail } from '../../../src/hooks/usePersonality';
import { useWallet } from '../../../src/hooks/useWallet';
import { formatCurrency } from '../../../src/utils/formatters';
import type { PersonalitySlot, HydratedCard } from '../../../src/types/personality';

export default function PersonalityDetailScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { data: personality, isLoading } = usePersonalityDetail(slug);
  const { data: walletData } = useWallet();
  const router = useRouter();
  const theme = useTheme();

  // Card selection state
  const [selectedCardIds, setSelectedCardIds] = useState<Set<string>>(new Set());

  // Get user's wallet card IDs
  const walletCardIds = useMemo(() => {
    const ids = new Set<string>();
    [...(walletData?.active_cards || []), ...(walletData?.inactive_cards || [])].forEach((c: any) => {
      if (c.card_id) ids.add(c.card_id);
    });
    return ids;
  }, [walletData]);

  // Auto-select cards: prefer wallet cards, fallback to first card per slot
  useEffect(() => {
    if (!personality?.slots) return;
    const initial = new Set<string>();
    personality.slots.forEach((slot: PersonalitySlot) => {
      const cards = slot.hydrated_cards ?? [];
      // First try to find a card the user owns
      const walletCard = cards.find((c) => walletCardIds.has(c.id));
      if (walletCard) {
        initial.add(walletCard.id);
      } else if (cards.length > 0) {
        initial.add(cards[0].id);
      }
    });
    setSelectedCardIds(initial);
  }, [personality, walletCardIds]);

  // Toggle card selection
  const toggleCard = (cardId: string) => {
    setSelectedCardIds((prev) => {
      const next = new Set(prev);
      if (next.has(cardId)) {
        next.delete(cardId);
      } else {
        next.add(cardId);
      }
      return next;
    });
  };

  // Build a map of all slot cards for stats
  const allCardsMap = useMemo(() => {
    const map = new Map<string, HydratedCard>();
    if (personality?.slots) {
      personality.slots.forEach((slot: PersonalitySlot) => {
        (slot.hydrated_cards ?? []).forEach((card: HydratedCard) => {
          map.set(card.id, card);
        });
      });
    }
    return map;
  }, [personality]);

  // Calculate stats from selected cards
  const stats = useMemo(() => {
    let totalAnnualFees = 0;
    let totalCreditValue = 0;
    let totalPointsMiles = 0;

    selectedCardIds.forEach((cardId) => {
      const card = allCardsMap.get(cardId);
      if (!card) return;

      totalAnnualFees += card.annual_fee ?? 0;

      (card.benefits ?? []).forEach((b: any) => {
        const numericType = b.numeric_type || '';
        const dollarValue = b.dollar_value ?? 0;
        if (numericType === 'points' || numericType === 'miles') {
          totalPointsMiles += dollarValue;
        } else {
          totalCreditValue += dollarValue;
        }
      });

      if (totalCreditValue === 0 && card.credits_value) {
        totalCreditValue += card.credits_value;
      }
    });

    return {
      annualFees: totalAnnualFees,
      creditValue: totalCreditValue,
      pointsMiles: totalPointsMiles,
      netValue: totalCreditValue - totalAnnualFees,
    };
  }, [selectedCardIds, allCardsMap]);

  if (isLoading || !personality) {
    return <LoadingState message="Loading personality..." />;
  }

  return (
    <View style={styles.container}>
      <ScrollView
        style={{ backgroundColor: theme.colors.background }}
        contentContainerStyle={styles.content}
      >
        {/* Hero Section */}
        <View style={styles.hero}>
          <PersonalityAvatar slug={personality.slug || slug} size={100} />

          {personality.tagline ? (
            <View style={styles.taglinePill}>
              <Text style={styles.taglineText}>{personality.tagline}</Text>
            </View>
          ) : null}

          <Text style={styles.name}>{personality.name}</Text>

          {personality.match_score != null && (
            <View style={styles.matchBadge}>
              <MaterialCommunityIcons name="lightning-bolt" size={14} color="#4361EE" />
              <Text style={styles.matchText}>{personality.match_score}% Match</Text>
            </View>
          )}

          {personality.description ? (
            <Text style={[styles.description, { color: theme.colors.onSurfaceVariant }]}>
              {personality.description}
            </Text>
          ) : null}
        </View>

        {/* Stats Grid (2x2) */}
        <View style={styles.statsGrid}>
          <View style={styles.statsRow}>
            <View style={[styles.statCard, { borderColor: theme.colors.outlineVariant }]}>
              <View style={styles.statIconRow}>
                <MaterialCommunityIcons name="credit-card-outline" size={16} color="#FB923C" />
                <Text style={styles.statLabel}>Annual Fees</Text>
              </View>
              <Text style={styles.statValue}>{formatCurrency(stats.annualFees)}</Text>
            </View>
            <View style={[styles.statCard, { borderColor: theme.colors.outlineVariant }]}>
              <View style={styles.statIconRow}>
                <MaterialCommunityIcons name="gift-outline" size={16} color="#60A5FA" />
                <Text style={styles.statLabel}>Credits Value</Text>
              </View>
              <Text style={styles.statValue}>{formatCurrency(stats.creditValue)}</Text>
            </View>
          </View>
          <View style={styles.statsRow}>
            <View style={[styles.statCard, { borderColor: theme.colors.outlineVariant }]}>
              <View style={styles.statIconRow}>
                <MaterialCommunityIcons name="chart-line" size={16} color={stats.netValue >= 0 ? '#34D399' : '#EF4444'} />
                <Text style={styles.statLabel}>Net Value</Text>
              </View>
              <Text style={[styles.statValue, { color: stats.netValue >= 0 ? '#10B981' : '#EF4444' }]}>
                {stats.netValue >= 0 ? '+' : ''}{formatCurrency(stats.netValue)}
              </Text>
            </View>
            <View style={[styles.statCard, { borderColor: theme.colors.outlineVariant }]}>
              <View style={styles.statIconRow}>
                <MaterialCommunityIcons name="star-outline" size={16} color="#A78BFA" />
                <Text style={styles.statLabel}>Points/Miles</Text>
              </View>
              <Text style={styles.statValue}>{formatCurrency(stats.pointsMiles)}</Text>
            </View>
          </View>
        </View>

        {/* Build Your Loadout Section */}
        {personality.slots && personality.slots.length > 0 && (
          <View style={styles.loadoutSection}>
            <View style={styles.sectionHeaderRow}>
              <MaterialCommunityIcons name="lightning-bolt" size={20} color="#4361EE" />
              <Text style={styles.sectionTitle}>Build Your Loadout</Text>
            </View>

            {personality.slots.map((slot: PersonalitySlot, idx: number) => (
              <View key={idx} style={styles.slotContainer}>
                <View style={styles.slotHeader}>
                  <View style={styles.slotBadge}>
                    <Text style={styles.slotBadgeText}>SLOT {idx + 1}</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.slotName}>{slot.name}</Text>
                    {slot.description ? (
                      <Text style={[styles.slotDescription, { color: theme.colors.onSurfaceVariant }]}>
                        {slot.description}
                      </Text>
                    ) : null}
                  </View>
                </View>

                <FlatList
                  data={slot.hydrated_cards ?? []}
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  renderItem={({ item: card }: { item: HydratedCard }) => {
                    const isSelected = selectedCardIds.has(card.id);
                    const isInWallet = walletCardIds.has(card.id);
                    return (
                      <Pressable onPress={() => toggleCard(card.id)}>
                        <Surface
                          style={[
                            styles.cardSlide,
                            { backgroundColor: theme.colors.elevation.level1 },
                            isSelected && styles.cardSlideSelected,
                          ]}
                          elevation={1}
                        >
                          {/* Selection indicator */}
                          {isSelected && (
                            <View style={styles.checkmarkBadge}>
                              <MaterialCommunityIcons name="check-circle" size={20} color="#4361EE" />
                            </View>
                          )}
                          {/* In wallet indicator */}
                          {isInWallet && (
                            <View style={styles.walletBadge}>
                              <MaterialCommunityIcons name="wallet" size={10} color="#FFFFFF" />
                            </View>
                          )}
                          <CardImage slug={card.slug || card.id} size="medium" style={styles.cardImage} />
                          <Text style={styles.cardName} numberOfLines={2}>{card.name}</Text>
                          <Text style={[styles.cardIssuer, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
                            {card.issuer}
                          </Text>
                          <Text style={styles.cardFee}>
                            {card.annual_fee > 0 ? `${formatCurrency(card.annual_fee)}/yr` : 'No fee'}
                          </Text>
                          {/* View Details button */}
                          <Pressable
                            style={styles.viewDetailsBtn}
                            onPress={() => router.push(`/stacks/card-detail/${card.slug || card.id}` as any)}
                          >
                            <Text style={styles.viewDetailsBtnText}>View Details</Text>
                          </Pressable>
                        </Surface>
                      </Pressable>
                    );
                  }}
                  keyExtractor={(item) => item.id || item.slug || String(Math.random())}
                  contentContainerStyle={{ gap: 10, paddingRight: 8 }}
                  ListEmptyComponent={
                    <Text style={[styles.emptySlotText, { color: theme.colors.onSurfaceVariant }]}>
                      No cards recommended for this slot yet.
                    </Text>
                  }
                />
              </View>
            ))}
          </View>
        )}

        {/* Rules of Engagement */}
        {personality.rules && personality.rules.length > 0 && (
          <View style={styles.rulesSection}>
            <View style={styles.sectionHeaderRow}>
              <MaterialCommunityIcons name="shield-check-outline" size={20} color="#4361EE" />
              <Text style={styles.sectionTitle}>Rules of Engagement</Text>
            </View>
            {personality.rules.map((rule: { title: string; description: string }, idx: number) => (
              <View key={idx} style={[styles.ruleItem, { borderColor: theme.colors.outlineVariant }]}>
                <View style={styles.ruleNumber}>
                  <Text style={styles.ruleNumberText}>{idx + 1}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.ruleTitle}>{rule.title}</Text>
                  <Text style={[styles.ruleDescription, { color: theme.colors.onSurfaceVariant }]}>
                    {rule.description}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { paddingBottom: 40 },
  hero: { alignItems: 'center', paddingTop: 20, paddingHorizontal: 24, paddingBottom: 24 },
  taglinePill: { backgroundColor: '#EEF2FF', paddingHorizontal: 16, paddingVertical: 6, borderRadius: 20, marginTop: 16 },
  taglineText: { fontSize: 13, fontFamily: 'Outfit-Medium', color: '#4361EE' },
  name: { fontSize: 28, fontFamily: 'Outfit-Bold', color: '#1C1B1F', marginTop: 12, textAlign: 'center' },
  matchBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 8, backgroundColor: '#EEF2FF', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  matchText: { fontSize: 14, fontFamily: 'Outfit-SemiBold', color: '#4361EE' },
  description: { fontSize: 15, fontFamily: 'Outfit', lineHeight: 22, marginTop: 16, textAlign: 'center' },
  statsGrid: { paddingHorizontal: 16, gap: 10, marginBottom: 24 },
  statsRow: { flexDirection: 'row', gap: 10 },
  statCard: { flex: 1, borderWidth: 1, borderRadius: 12, padding: 14, backgroundColor: '#FFFFFF' },
  statIconRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 8 },
  statLabel: { fontSize: 11, fontFamily: 'Outfit-Medium', color: '#64748B', textTransform: 'uppercase', letterSpacing: 0.3 },
  statValue: { fontSize: 22, fontFamily: 'Outfit-Bold', color: '#1C1B1F' },
  loadoutSection: { paddingHorizontal: 16, marginBottom: 24 },
  sectionHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 },
  sectionTitle: { fontSize: 20, fontFamily: 'Outfit-Bold', color: '#1C1B1F' },
  slotContainer: { marginBottom: 20 },
  slotHeader: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 12 },
  slotBadge: { backgroundColor: '#4361EE', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 6, marginTop: 2 },
  slotBadgeText: { fontSize: 10, fontFamily: 'Outfit-Bold', color: '#FFFFFF', letterSpacing: 0.5 },
  slotName: { fontSize: 16, fontFamily: 'Outfit-SemiBold', color: '#1C1B1F' },
  slotDescription: { fontSize: 13, fontFamily: 'Outfit', lineHeight: 18, marginTop: 2 },
  cardSlide: { width: 160, borderRadius: 12, padding: 14, alignItems: 'center', overflow: 'visible' },
  cardSlideSelected: { borderWidth: 2, borderColor: '#4361EE' },
  cardImage: { marginBottom: 8 },
  cardName: { fontSize: 13, fontFamily: 'Outfit-SemiBold', color: '#1C1B1F', textAlign: 'center' },
  cardIssuer: { fontSize: 11, fontFamily: 'Outfit', marginTop: 2, textAlign: 'center' },
  cardFee: { fontSize: 12, fontFamily: 'Outfit-Medium', color: '#4361EE', marginTop: 4 },
  checkmarkBadge: { position: 'absolute', top: 6, right: 6, zIndex: 1 },
  walletBadge: { position: 'absolute', top: 6, left: 6, zIndex: 1, backgroundColor: '#10B981', width: 18, height: 18, borderRadius: 9, justifyContent: 'center', alignItems: 'center' },
  viewDetailsBtn: { marginTop: 8, backgroundColor: '#F1F5F9', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  viewDetailsBtnText: { fontSize: 11, fontFamily: 'Outfit-SemiBold', color: '#4361EE' },
  emptySlotText: { fontSize: 13, fontFamily: 'Outfit', fontStyle: 'italic', paddingVertical: 8 },
  rulesSection: { paddingHorizontal: 16, marginBottom: 24 },
  ruleItem: { flexDirection: 'row', borderWidth: 1, borderRadius: 12, padding: 14, marginBottom: 10, gap: 12, backgroundColor: '#FFFFFF' },
  ruleNumber: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#EEF2FF', justifyContent: 'center', alignItems: 'center' },
  ruleNumberText: { fontSize: 14, fontFamily: 'Outfit-Bold', color: '#4361EE' },
  ruleTitle: { fontSize: 15, fontFamily: 'Outfit-SemiBold', color: '#1C1B1F', marginBottom: 2 },
  ruleDescription: { fontSize: 13, fontFamily: 'Outfit', lineHeight: 18 },
});
