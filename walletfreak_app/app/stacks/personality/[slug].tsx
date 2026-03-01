import React, { useMemo } from 'react';
import { View, StyleSheet, ScrollView, FlatList, Pressable } from 'react-native';
import { Text, Surface, useTheme } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../../src/components/layout/LoadingState';
import { PersonalityAvatar } from '../../../src/components/personality/PersonalityAvatar';
import { CardImage } from '../../../src/components/ui/CardImage';
import { usePersonalityDetail } from '../../../src/hooks/usePersonality';
import { formatCurrency } from '../../../src/utils/formatters';
import type { PersonalitySlot, HydratedCard } from '../../../src/types/personality';

export default function PersonalityDetailScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { data: personality, isLoading } = usePersonalityDetail(slug);
  const router = useRouter();
  const theme = useTheme();

  // Calculate stats from slot cards
  const stats = useMemo(() => {
    if (!personality?.slots) return { annualFees: 0, creditValue: 0, netValue: 0, cardCount: 0 };

    let totalAnnualFees = 0;
    let cardCount = 0;

    personality.slots.forEach((slot: PersonalitySlot) => {
      const cards = slot.hydrated_cards ?? [];
      if (cards.length > 0) {
        // Use the first card in each slot as the "recommended" card
        totalAnnualFees += cards[0].annual_fee ?? 0;
        cardCount += 1;
      }
    });

    return {
      annualFees: totalAnnualFees,
      creditValue: 0, // Computed server-side if available
      netValue: 0,
      cardCount,
    };
  }, [personality]);

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

          {/* Tagline pill */}
          {personality.tagline ? (
            <View style={styles.taglinePill}>
              <Text style={styles.taglineText}>{personality.tagline}</Text>
            </View>
          ) : null}

          <Text style={styles.name}>{personality.name}</Text>

          {personality.match_score != null && (
            <View style={styles.matchBadge}>
              <MaterialCommunityIcons name="lightning-bolt" size={14} color="#4F46E5" />
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
                <MaterialCommunityIcons name="wallet-outline" size={16} color="#60A5FA" />
                <Text style={styles.statLabel}>Cards</Text>
              </View>
              <Text style={styles.statValue}>{stats.cardCount}</Text>
            </View>
          </View>
          <View style={styles.statsRow}>
            <View style={[styles.statCard, { borderColor: theme.colors.outlineVariant }]}>
              <View style={styles.statIconRow}>
                <MaterialCommunityIcons name="star-outline" size={16} color="#A78BFA" />
                <Text style={styles.statLabel}>Slots</Text>
              </View>
              <Text style={styles.statValue}>{personality.slots?.length ?? 0}</Text>
            </View>
            <View style={[styles.statCard, { borderColor: theme.colors.outlineVariant }]}>
              <View style={styles.statIconRow}>
                <MaterialCommunityIcons name="tag-outline" size={16} color="#34D399" />
                <Text style={styles.statLabel}>Categories</Text>
              </View>
              <Text style={styles.statValue}>{personality.categories?.length ?? 0}</Text>
            </View>
          </View>
        </View>

        {/* Build Your Loadout Section */}
        {personality.slots && personality.slots.length > 0 && (
          <View style={styles.loadoutSection}>
            <View style={styles.sectionHeaderRow}>
              <MaterialCommunityIcons name="lightning-bolt" size={20} color="#4F46E5" />
              <Text style={styles.sectionTitle}>Build Your Loadout</Text>
            </View>

            {personality.slots.map((slot: PersonalitySlot, idx: number) => (
              <View key={idx} style={styles.slotContainer}>
                {/* Slot badge + info */}
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

                {/* Card carousel */}
                <FlatList
                  data={slot.hydrated_cards ?? []}
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  renderItem={({ item: card }: { item: HydratedCard }) => (
                    <Pressable
                      onPress={() => router.push(`/stacks/card-detail/${card.slug || card.id}` as any)}
                    >
                      <Surface
                        style={[styles.cardSlide, { backgroundColor: theme.colors.elevation.level1 }]}
                        elevation={1}
                      >
                        <CardImage slug={card.slug || card.id} size="small" style={styles.cardImage} />
                        <Text style={styles.cardName} numberOfLines={1}>{card.name}</Text>
                        <Text style={[styles.cardIssuer, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
                          {card.issuer}
                        </Text>
                        <Text style={styles.cardFee}>
                          {card.annual_fee > 0 ? `${formatCurrency(card.annual_fee)}/yr` : 'No fee'}
                        </Text>
                      </Surface>
                    </Pressable>
                  )}
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
              <MaterialCommunityIcons name="shield-check-outline" size={20} color="#4F46E5" />
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
  container: {
    flex: 1,
  },
  content: {
    paddingBottom: 40,
  },
  // Hero
  hero: {
    alignItems: 'center',
    paddingTop: 20,
    paddingHorizontal: 24,
    paddingBottom: 24,
  },
  taglinePill: {
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 20,
    marginTop: 16,
  },
  taglineText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    color: '#4F46E5',
  },
  name: {
    fontSize: 28,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
    marginTop: 12,
    textAlign: 'center',
  },
  matchBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 8,
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  matchText: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    color: '#4F46E5',
  },
  description: {
    fontSize: 15,
    fontFamily: 'Outfit',
    lineHeight: 22,
    marginTop: 16,
    textAlign: 'center',
  },
  // Stats Grid
  statsGrid: {
    paddingHorizontal: 16,
    gap: 10,
    marginBottom: 24,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  statCard: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    backgroundColor: '#FFFFFF',
  },
  statIconRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  statLabel: {
    fontSize: 11,
    fontFamily: 'Outfit-Medium',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  statValue: {
    fontSize: 22,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
  },
  // Loadout Section
  loadoutSection: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
  },
  slotContainer: {
    marginBottom: 20,
  },
  slotHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    marginBottom: 12,
  },
  slotBadge: {
    backgroundColor: '#4F46E5',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    marginTop: 2,
  },
  slotBadgeText: {
    fontSize: 10,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
    letterSpacing: 0.5,
  },
  slotName: {
    fontSize: 16,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
  },
  slotDescription: {
    fontSize: 13,
    fontFamily: 'Outfit',
    lineHeight: 18,
    marginTop: 2,
  },
  // Card carousel
  cardSlide: {
    width: 150,
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
  },
  cardImage: {
    marginBottom: 8,
  },
  cardName: {
    fontSize: 13,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
    textAlign: 'center',
  },
  cardIssuer: {
    fontSize: 11,
    fontFamily: 'Outfit',
    marginTop: 2,
    textAlign: 'center',
  },
  cardFee: {
    fontSize: 12,
    fontFamily: 'Outfit-Medium',
    color: '#4F46E5',
    marginTop: 4,
  },
  emptySlotText: {
    fontSize: 13,
    fontFamily: 'Outfit',
    fontStyle: 'italic',
    paddingVertical: 8,
  },
  // Rules of Engagement
  rulesSection: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  ruleItem: {
    flexDirection: 'row',
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    gap: 12,
    backgroundColor: '#FFFFFF',
  },
  ruleNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#EEF2FF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  ruleNumberText: {
    fontSize: 14,
    fontFamily: 'Outfit-Bold',
    color: '#4F46E5',
  },
  ruleTitle: {
    fontSize: 15,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
    marginBottom: 2,
  },
  ruleDescription: {
    fontSize: 13,
    fontFamily: 'Outfit',
    lineHeight: 18,
  },
});
