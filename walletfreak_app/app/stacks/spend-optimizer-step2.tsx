import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Pressable } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { useSpendCategories } from '../../src/hooks/useCalculators';

export default function SpendOptimizerStep2Screen() {
  const theme = useTheme();
  const router = useRouter();
  const { amount, category } = useLocalSearchParams<{ amount: string; category: string }>();
  const [selectedSub, setSelectedSub] = useState<string | null>(null);
  const { data: categoriesData, isLoading } = useSpendCategories();

  const categories = categoriesData?.categories ?? [];
  const currentCategory = categories.find((c) => c.name === category);
  const subCategories = currentCategory?.sub_categories ?? [];

  const handleNext = () => {
    router.push({
      pathname: '/stacks/spend-optimizer-results' as any,
      params: { amount, category, subCategory: selectedSub || '' },
    });
  };

  if (isLoading) {
    return <LoadingState message="Loading..." />;
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={{ paddingBottom: 40 }}
    >
      {/* Header */}
      <View style={styles.section}>
        <View style={styles.stepBadge}>
          <Text style={styles.stepBadgeText}>STEP 2 OF 2</Text>
        </View>
        <Text style={styles.heading}>What specifically?</Text>
        <Text style={[styles.subheading, { color: theme.colors.onSurfaceVariant }]}>
          Spending {amount ? `$${amount}` : ''} on {category}
        </Text>
      </View>

      {/* Sub-Category List */}
      <View style={styles.section}>
        <Text variant="labelLarge" style={[styles.sectionLabel, { color: theme.colors.onSurface }]}>
          Choose a sub-category
        </Text>
        <View style={styles.subList}>
          {subCategories.map((sub) => (
            <Pressable
              key={sub}
              style={[
                styles.subItem,
                {
                  backgroundColor:
                    selectedSub === sub
                      ? theme.colors.primaryContainer
                      : theme.colors.elevation.level1,
                  borderColor:
                    selectedSub === sub
                      ? theme.colors.primary
                      : theme.colors.outlineVariant,
                },
              ]}
              onPress={() => setSelectedSub(sub)}
            >
              {selectedSub === sub && (
                <MaterialCommunityIcons name="check-circle" size={20} color={theme.colors.primary} />
              )}
              <Text
                style={[
                  styles.subItemText,
                  {
                    color: selectedSub === sub
                      ? theme.colors.onPrimaryContainer
                      : theme.colors.onSurface,
                  },
                ]}
              >
                {sub}
              </Text>
            </Pressable>
          ))}
        </View>

        {/* Skip option */}
        <Pressable style={styles.skipRow} onPress={() => setSelectedSub('')}>
          <MaterialCommunityIcons
            name={selectedSub === '' ? 'radiobox-marked' : 'radiobox-blank'}
            size={20}
            color={selectedSub === '' ? theme.colors.primary : theme.colors.onSurfaceVariant}
          />
          <Text style={[styles.skipText, { color: theme.colors.onSurfaceVariant }]}>
            Skip — show all {category} results
          </Text>
        </Pressable>
      </View>

      {/* Next Button */}
      <View style={styles.section}>
        <Pressable
          style={[
            styles.nextButton,
            selectedSub == null && styles.nextButtonDisabled,
          ]}
          onPress={handleNext}
          disabled={selectedSub == null}
        >
          <Text style={styles.nextButtonText}>See Results</Text>
          <MaterialCommunityIcons name="arrow-right" size={18} color="#FFFFFF" />
        </Pressable>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
  },
  section: {
    marginTop: 16,
  },
  stepBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 12,
  },
  stepBadgeText: {
    fontSize: 11,
    fontFamily: 'Outfit-Bold',
    color: '#4F46E5',
    letterSpacing: 0.5,
  },
  heading: {
    fontSize: 26,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
    marginBottom: 4,
  },
  subheading: {
    fontSize: 14,
    fontFamily: 'Outfit',
    lineHeight: 20,
  },
  sectionLabel: {
    fontFamily: 'Outfit-SemiBold',
    marginBottom: 10,
  },
  subList: {
    gap: 8,
  },
  subItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    borderWidth: 1.5,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  subItemText: {
    fontSize: 15,
    fontFamily: 'Outfit-Medium',
  },
  skipRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 4,
    marginTop: 4,
  },
  skipText: {
    fontSize: 14,
    fontFamily: 'Outfit',
  },
  nextButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#0F172A',
    paddingVertical: 16,
    borderRadius: 12,
  },
  nextButtonDisabled: {
    opacity: 0.4,
  },
  nextButtonText: {
    fontSize: 16,
    fontFamily: 'Outfit-SemiBold',
    color: '#FFFFFF',
  },
});
