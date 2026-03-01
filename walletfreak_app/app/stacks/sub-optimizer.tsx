import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, TextInput as RNTextInput, Pressable } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

const TIMEFRAME_OPTIONS = [
  { value: '1', label: '1 mo' },
  { value: '2', label: '2 mo' },
  { value: '3', label: '3 mo' },
  { value: '6', label: '6 mo' },
];

export default function SubOptimizerScreen() {
  const theme = useTheme();
  const router = useRouter();
  const [spend, setSpend] = useState('4000');
  const [timeframe, setTimeframe] = useState('3');
  const [sortBy, setSortBy] = useState('recommended');

  const handleCalculate = () => {
    router.push({
      pathname: '/stacks/sub-optimizer-results' as any,
      params: { spend, timeframe, sortBy },
    });
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ paddingBottom: 40 }}
    >
      {/* Dark Hero Section */}
      <LinearGradient
        colors={['#0F0F1A', '#1A1A2E', '#16213E']}
        style={styles.heroSection}
      >
        {/* Background orbs */}
        <View style={styles.orbContainer} pointerEvents="none">
          <View style={styles.yellowOrb} />
          <View style={styles.blueOrb} />
        </View>

        {/* Badge */}
        <View style={styles.heroBadge}>
          <MaterialCommunityIcons name="lightning-bolt" size={14} color="#FACC15" />
          <Text style={styles.heroBadgeText}>SIGN-UP BONUS INTEL</Text>
        </View>

        {/* Headline */}
        <Text style={styles.heroHeadline}>Target your next{'\n'}big haul.</Text>
        <Text style={styles.heroSubheadline}>
          Analyze sign-up bonus ROI across all cards and find the best value for your spend.
        </Text>

        {/* Glass Form */}
        <View style={styles.glassForm}>
          {/* Planned Spend */}
          <Text style={styles.formLabel}>Planned Spend</Text>
          <View style={styles.darkInput}>
            <Text style={styles.dollarPrefix}>$</Text>
            <RNTextInput
              style={styles.darkInputText}
              value={spend}
              onChangeText={setSpend}
              keyboardType="numeric"
              placeholder="4000"
              placeholderTextColor="rgba(255,255,255,0.3)"
            />
          </View>

          {/* Timeframe */}
          <Text style={[styles.formLabel, { marginTop: 16 }]}>Timeframe</Text>
          <View style={styles.timeframeRow}>
            {TIMEFRAME_OPTIONS.map((opt) => (
              <Pressable
                key={opt.value}
                style={[
                  styles.timeframeButton,
                  timeframe === opt.value && styles.timeframeButtonActive,
                ]}
                onPress={() => setTimeframe(opt.value)}
              >
                <Text
                  style={[
                    styles.timeframeButtonText,
                    timeframe === opt.value && styles.timeframeButtonTextActive,
                  ]}
                >
                  {opt.label}
                </Text>
              </Pressable>
            ))}
          </View>

          {/* Strategy */}
          <Text style={[styles.formLabel, { marginTop: 16 }]}>Strategy</Text>
          <View style={styles.strategyRow}>
            <Pressable
              style={[
                styles.strategyCard,
                sortBy === 'recommended' && styles.strategyCardActive,
              ]}
              onPress={() => setSortBy('recommended')}
            >
              <MaterialCommunityIcons
                name="lightning-bolt"
                size={20}
                color={sortBy === 'recommended' ? '#0F0F1A' : 'rgba(255,255,255,0.6)'}
              />
              <Text
                style={[
                  styles.strategyCardText,
                  sortBy === 'recommended' && styles.strategyCardTextActive,
                ]}
              >
                Freak Score
              </Text>
            </Pressable>
            <Pressable
              style={[
                styles.strategyCard,
                sortBy === 'value' && styles.strategyCardActive,
              ]}
              onPress={() => setSortBy('value')}
            >
              <MaterialCommunityIcons
                name="diamond-stone"
                size={20}
                color={sortBy === 'value' ? '#0F0F1A' : 'rgba(255,255,255,0.6)'}
              />
              <Text
                style={[
                  styles.strategyCardText,
                  sortBy === 'value' && styles.strategyCardTextActive,
                ]}
              >
                Pure Value
              </Text>
            </Pressable>
          </View>

          {/* CTA Button */}
          <Pressable
            style={styles.ctaButton}
            onPress={handleCalculate}
          >
            <MaterialCommunityIcons name="target" size={18} color="#0F0F1A" />
            <Text style={styles.ctaButtonText}>Scan ROI Leaderboard</Text>
          </Pressable>
        </View>
      </LinearGradient>

    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  // Hero Section
  heroSection: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 28,
    position: 'relative',
    overflow: 'hidden',
  },
  orbContainer: {
    ...StyleSheet.absoluteFillObject,
  },
  yellowOrb: {
    position: 'absolute',
    top: -40,
    right: -30,
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: 'rgba(250, 204, 21, 0.08)',
  },
  blueOrb: {
    position: 'absolute',
    bottom: -60,
    left: -40,
    width: 180,
    height: 180,
    borderRadius: 90,
    backgroundColor: 'rgba(79, 70, 229, 0.1)',
  },
  heroBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 6,
    backgroundColor: 'rgba(250, 204, 21, 0.12)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginBottom: 16,
  },
  heroBadgeText: {
    fontSize: 11,
    fontFamily: 'Outfit-Bold',
    color: '#FACC15',
    letterSpacing: 1,
  },
  heroHeadline: {
    fontSize: 32,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
    lineHeight: 38,
    marginBottom: 8,
  },
  heroSubheadline: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: 'rgba(255,255,255,0.5)',
    lineHeight: 20,
    marginBottom: 24,
  },
  // Glass Form
  glassForm: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  formLabel: {
    fontSize: 12,
    fontFamily: 'Outfit-SemiBold',
    color: 'rgba(255,255,255,0.6)',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  darkInput: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  dollarPrefix: {
    fontSize: 24,
    fontFamily: 'Outfit-Bold',
    color: 'rgba(255,255,255,0.5)',
    marginRight: 4,
  },
  darkInputText: {
    flex: 1,
    fontSize: 24,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
  },
  // Timeframe
  timeframeRow: {
    flexDirection: 'row',
    gap: 8,
  },
  timeframeButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    alignItems: 'center',
  },
  timeframeButtonActive: {
    backgroundColor: 'rgba(250, 204, 21, 0.15)',
    borderColor: '#FACC15',
  },
  timeframeButtonText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    color: 'rgba(255,255,255,0.5)',
  },
  timeframeButtonTextActive: {
    color: '#FACC15',
  },
  // Strategy
  strategyRow: {
    flexDirection: 'row',
    gap: 10,
  },
  strategyCard: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  strategyCardActive: {
    backgroundColor: '#FACC15',
    borderColor: '#FACC15',
  },
  strategyCardText: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    color: 'rgba(255,255,255,0.6)',
  },
  strategyCardTextActive: {
    color: '#0F0F1A',
  },
  // CTA Button
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#FACC15',
    borderRadius: 12,
    paddingVertical: 16,
    marginTop: 20,
  },
  ctaButtonText: {
    fontSize: 16,
    fontFamily: 'Outfit-Bold',
    color: '#0F0F1A',
  },
});
