import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Pressable } from 'react-native';
import { Text, Button, useTheme, Surface } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as WebBrowser from 'expo-web-browser';
import { LoadingState } from '../../../src/components/layout/LoadingState';
import { CardImage } from '../../../src/components/ui/CardImage';
import { useCardDetail } from '../../../src/hooks/useCards';
import { useAddCard, useWallet } from '../../../src/hooks/useWallet';
import { formatCurrency } from '../../../src/utils/formatters';

type TabKey = 'overview' | 'earning' | 'benefits';

export default function CardDetailScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { data: card, isLoading } = useCardDetail(slug);
  const { data: walletData } = useWallet();
  const addCard = useAddCard();
  const router = useRouter();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [activeTab, setActiveTab] = useState<TabKey>('overview');

  const isInWallet = walletData
    ? [...(walletData.active_cards || []), ...(walletData.inactive_cards || []), ...(walletData.eyeing_cards || [])]
        .some((c: any) => c.card_id === (card?.id || slug))
    : false;

  if (isLoading || !card) {
    return <LoadingState message="Loading card..." />;
  }

  // Parse sign-up bonus from structured object or string fields
  const signUpBonus = card.sign_up_bonus || null;
  const bonusValue = signUpBonus?.value || card.signup_bonus || card.welcome_bonus || '';
  const bonusTerms = signUpBonus?.terms || card.welcome_requirement || '';
  const bonusCurrency = signUpBonus?.currency || 'Points';

  // Separate benefits into multiplier/cashback (earning) and other (benefits)
  const earningRates = card.earning_rates ?? [];
  const benefits = (card.benefits ?? []).filter(
    (b: any) => b.benefit_type !== 'Multiplier' && b.benefit_type !== 'Cashback'
  );

  const formatBenefitValue = (b: any) => {
    const val = b.dollar_value || b.numeric_value || b.value || b.amount;
    const type = b.numeric_type || '';
    if (!val || val === 0) return 'Included';
    if (type === 'percent') return `${val}%`;
    if (type === 'cash' || b.dollar_value) return formatCurrency(val);
    return String(val);
  };

  const formatRate = (rate: any) => {
    const r = rate.rate || rate.multiplier || rate.value || '';
    const rStr = String(r);
    if (rStr.includes('%')) return rStr;
    if (rStr.includes('x') || rStr.includes('X')) return rStr;
    const num = parseFloat(rStr);
    if (!isNaN(num)) {
      if (num < 1) return `${num * 100}%`;
      return `${num}x`;
    }
    return rStr;
  };

  const TABS: { key: TabKey; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'earning', label: 'Earning' },
    { key: 'benefits', label: 'Benefits' },
  ];

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Card Image Section */}
        <View style={styles.imageSection}>
          <CardImage slug={slug || ''} size="large" style={styles.cardImage} />
        </View>

        {/* Card Identity */}
        <View style={styles.identity}>
          <Text style={styles.cardName}>{card.name}</Text>

          {/* Badges Row */}
          <View style={styles.badgesRow}>
            {card.match_score !== undefined && card.match_score !== null && (
              <View style={styles.badge}>
                <Text style={styles.badgeStar}>★</Text>
                <Text style={styles.badgeText}>{card.match_score}% Match</Text>
              </View>
            )}
            <View style={styles.badge}>
              <Text style={styles.badgeLabelSmall}>FEE</Text>
              <Text style={styles.badgeText}>{formatCurrency(card.annual_fee)}</Text>
            </View>
          </View>
        </View>

        {/* Tabs */}
        <View style={styles.tabsRow}>
          {TABS.map((tab) => (
            <Pressable
              key={tab.key}
              onPress={() => setActiveTab(tab.key)}
              style={[
                styles.tab,
                activeTab === tab.key && styles.tabActive,
              ]}
            >
              <Text
                style={[
                  styles.tabText,
                  activeTab === tab.key && styles.tabTextActive,
                ]}
              >
                {tab.label}
              </Text>
            </Pressable>
          ))}
        </View>

        {/* Tab Content */}
        <View style={styles.tabContent}>
          {activeTab === 'overview' && (
            <>
              {/* Freak Verdict */}
              <View style={styles.verdictBox}>
                <View style={styles.verdictHeader}>
                  <View style={styles.verdictIconCircle}>
                    <MaterialCommunityIcons name="lightning-bolt" size={16} color="#6366F1" />
                  </View>
                  <Text style={styles.verdictTitle}>THE FREAK VERDICT</Text>
                </View>
                <Text style={styles.verdictText}>
                  {card.freak_verdict || 'No verdict available.'}
                </Text>
              </View>

              {/* Welcome Offer */}
              {bonusValue ? (
                <View style={styles.welcomeBox}>
                  <View style={styles.welcomeHeader}>
                    <MaterialCommunityIcons name="gift-outline" size={18} color="#64748B" />
                    <Text style={styles.welcomeLabel}>WELCOME OFFER</Text>
                  </View>
                  <View style={styles.welcomeContent}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.welcomeValue}>
                        {bonusValue}
                      </Text>
                      <Text style={styles.welcomeCurrency}>{bonusCurrency}</Text>
                    </View>
                    {bonusTerms ? (
                      <Text style={styles.welcomeTerms}>{bonusTerms}</Text>
                    ) : null}
                  </View>
                </View>
              ) : null}

              {/* Credits Value */}
              {card.credits_value > 0 && (
                <View style={styles.creditsBox}>
                  <Text style={styles.creditsLabel}>APPROXIMATE CREDITS VALUE</Text>
                  <Text style={styles.creditsValue}>
                    {formatCurrency(card.credits_value)}
                  </Text>
                </View>
              )}
            </>
          )}

          {activeTab === 'earning' && (
            <>
              {earningRates.length > 0 ? (
                earningRates.map((rate: any, idx: number) => (
                  <View key={idx} style={styles.earningRow}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.earningCategory}>
                        {rate.category || rate.description || 'Other'}
                      </Text>
                      {rate.details && (
                        <Text style={styles.earningDetails}>{rate.details}</Text>
                      )}
                    </View>
                    <View style={styles.rateBadge}>
                      <Text style={styles.rateBadgeText}>
                        {formatRate(rate)}
                      </Text>
                    </View>
                  </View>
                ))
              ) : (
                <Text style={[styles.emptyText, { color: theme.colors.onSurfaceVariant }]}>
                  No earning rates available for this card.
                </Text>
              )}
            </>
          )}

          {activeTab === 'benefits' && (
            <>
              {benefits.length > 0 ? (
                benefits.map((benefit: any, idx: number) => (
                  <View key={idx}>
                    <View style={styles.benefitRow}>
                      <Text style={styles.benefitName} numberOfLines={2}>
                        {benefit.short_description || benefit.name || benefit.title || benefit.description}
                      </Text>
                      <Text
                        style={[
                          styles.benefitValue,
                          !benefit.dollar_value && styles.benefitValueIncluded,
                        ]}
                      >
                        {formatBenefitValue(benefit)}
                      </Text>
                    </View>
                    {benefit.description && benefit.short_description && (
                      <Text style={styles.benefitDescription} numberOfLines={3}>
                        {benefit.description}
                      </Text>
                    )}
                    {benefit.time_category && (
                      <Text style={styles.benefitFrequency}>
                        {benefit.time_category}
                      </Text>
                    )}
                    {idx < benefits.length - 1 && <View style={styles.benefitDivider} />}
                  </View>
                ))
              ) : (
                <Text style={[styles.emptyText, { color: theme.colors.onSurfaceVariant }]}>
                  No additional benefits listed for this card.
                </Text>
              )}
            </>
          )}
        </View>
      </ScrollView>

      {/* Fixed Footer Buttons */}
      <View style={[styles.footer, { backgroundColor: theme.colors.surface, borderTopColor: '#E2E8F0', paddingBottom: Math.max(insets.bottom, 16) }]}>
        {isInWallet ? (
          <Pressable style={[styles.footerBtnPrimary, styles.footerBtnDisabled]}>
            <MaterialCommunityIcons name="check-circle" size={18} color="#94A3B8" />
            <Text style={[styles.footerBtnText, { color: '#94A3B8' }]}>Already in Wallet</Text>
          </Pressable>
        ) : (
          <Pressable
            style={styles.footerBtnPrimary}
            onPress={() => addCard.mutate({ cardId: card.id || slug })}
            disabled={addCard.isPending}
          >
            <MaterialCommunityIcons name="plus" size={18} color="#FFFFFF" />
            <Text style={styles.footerBtnText}>
              {addCard.isPending ? 'Adding...' : 'Add to Wallet'}
            </Text>
          </Pressable>
        )}
        {card.referral_url ? (
          <Pressable
            style={styles.footerBtnSecondary}
            onPress={() => WebBrowser.openBrowserAsync(card.referral_url)}
          >
            <MaterialCommunityIcons name="open-in-new" size={18} color="#0F172A" />
            <Text style={[styles.footerBtnText, { color: '#0F172A' }]}>Apply Now</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 120,
  },
  imageSection: {
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    paddingVertical: 24,
    paddingHorizontal: 40,
  },
  cardImage: {
    width: 260,
    height: 164,
  },
  identity: {
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
  },
  cardName: {
    fontSize: 20,
    fontFamily: 'Outfit-Bold',
    color: '#0F172A',
    textAlign: 'center',
    marginBottom: 10,
  },
  badgesRow: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    backgroundColor: '#FFFFFF',
    gap: 4,
  },
  badgeStar: {
    fontSize: 12,
    color: '#F59E0B',
  },
  badgeLabelSmall: {
    fontSize: 9,
    fontFamily: 'Outfit-SemiBold',
    color: '#94A3B8',
    letterSpacing: 0.5,
  },
  badgeText: {
    fontSize: 13,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  tabsRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    paddingHorizontal: 16,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  tabActive: {
    borderBottomWidth: 2,
    borderBottomColor: '#3B82F6',
  },
  tabText: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    color: '#94A3B8',
  },
  tabTextActive: {
    color: '#3B82F6',
    fontFamily: 'Outfit-SemiBold',
  },
  tabContent: {
    padding: 16,
  },
  // Overview tab
  verdictBox: {
    backgroundColor: '#F5F3FF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  verdictHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  verdictIconCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#EDE9FE',
    justifyContent: 'center',
    alignItems: 'center',
  },
  verdictTitle: {
    fontSize: 12,
    fontFamily: 'Outfit-Bold',
    color: '#6366F1',
    letterSpacing: 0.5,
  },
  verdictText: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: '#334155',
    lineHeight: 20,
  },
  welcomeBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  welcomeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 10,
  },
  welcomeLabel: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    color: '#64748B',
    letterSpacing: 0.5,
  },
  welcomeContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  welcomeValue: {
    fontSize: 24,
    fontFamily: 'Outfit-Bold',
    color: '#0F172A',
  },
  welcomeCurrency: {
    fontSize: 12,
    fontFamily: 'Outfit-Medium',
    color: '#64748B',
  },
  welcomeTerms: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#64748B',
    textAlign: 'right',
    flex: 1,
  },
  creditsBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: 16,
    padding: 16,
  },
  creditsLabel: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    color: '#64748B',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  creditsValue: {
    fontSize: 24,
    fontFamily: 'Outfit-Bold',
    color: '#10B981',
  },
  // Earning tab
  earningRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  earningCategory: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  earningDetails: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#64748B',
    marginTop: 2,
  },
  rateBadge: {
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    marginLeft: 8,
  },
  rateBadgeText: {
    fontSize: 13,
    fontFamily: 'Outfit-Bold',
    color: '#3B82F6',
  },
  // Benefits tab
  benefitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingTop: 12,
  },
  benefitName: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
    flex: 1,
    marginRight: 8,
  },
  benefitValue: {
    fontSize: 14,
    fontFamily: 'Outfit-Bold',
    color: '#10B981',
  },
  benefitValueIncluded: {
    color: '#3B82F6',
    fontSize: 12,
  },
  benefitDescription: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#64748B',
    marginTop: 4,
    lineHeight: 16,
  },
  benefitFrequency: {
    fontSize: 11,
    fontFamily: 'Outfit-Medium',
    color: '#94A3B8',
    marginTop: 4,
  },
  benefitDivider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginTop: 12,
  },
  emptyText: {
    fontSize: 14,
    fontFamily: 'Outfit',
    textAlign: 'center',
    paddingVertical: 24,
  },
  // Footer
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    padding: 16,
    gap: 12,
    borderTopWidth: 1,
  },
  footerBtnPrimary: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0F172A',
    paddingVertical: 14,
    borderRadius: 12,
    gap: 6,
  },
  footerBtnDisabled: {
    backgroundColor: '#E2E8F0',
  },
  footerBtnSecondary: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 6,
  },
  footerBtnText: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    color: '#FFFFFF',
  },
});
