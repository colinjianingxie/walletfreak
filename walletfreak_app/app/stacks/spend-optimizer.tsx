import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Pressable, TextInput as RNTextInput } from 'react-native';
import { Text, Surface, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { useSpendCategories } from '../../src/hooks/useCalculators';

const CATEGORY_ICONS: Record<string, string> = {
  airplane: 'airplane',
  'office-building': 'office-building',
  'silverware-fork-knife': 'silverware-fork-knife',
  cart: 'cart',
  'gas-station': 'gas-station',
  train: 'train',
  car: 'car',
  shopping: 'shopping',
  ticket: 'ticket',
  briefcase: 'briefcase',
  'heart-pulse': 'heart-pulse',
  spa: 'spa',
  earth: 'earth',
  sofa: 'sofa',
  'truck-delivery': 'truck-delivery',
  hammer: 'hammer',
  'lightning-bolt': 'lightning-bolt',
  cellphone: 'cellphone',
  television: 'television',
  school: 'school',
  paw: 'paw',
  calendar: 'calendar',
  ferry: 'ferry',
  'circle-outline': 'circle-outline',
};

export default function SpendOptimizerScreen() {
  const theme = useTheme();
  const router = useRouter();
  const [amount, setAmount] = useState('500');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const { data: categoriesData, isLoading: loadingCategories } = useSpendCategories();

  const categories = categoriesData?.categories ?? [];

  const handleNext = () => {
    if (!selectedCategory) return;
    const currentCategory = categories.find((c) => c.name === selectedCategory);
    const hasSubCategories = currentCategory && currentCategory.sub_categories.length > 0;

    if (hasSubCategories) {
      router.push({
        pathname: '/stacks/spend-optimizer-step2' as any,
        params: { amount, category: selectedCategory },
      });
    } else {
      // Skip step 2 — go directly to results
      router.push({
        pathname: '/stacks/spend-optimizer-results' as any,
        params: { amount, category: selectedCategory, subCategory: '' },
      });
    }
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={{ paddingBottom: 40 }}
    >
      {/* Amount Input */}
      <View style={styles.section}>
        <Text variant="labelLarge" style={[styles.sectionLabel, { color: theme.colors.onSurface }]}>
          Purchase Amount
        </Text>
        <Surface style={[styles.amountContainer, { backgroundColor: theme.colors.elevation.level1 }]} elevation={1}>
          <Text style={[styles.dollarSign, { color: theme.colors.onSurfaceVariant }]}>$</Text>
          <RNTextInput
            style={[styles.amountInput, { color: theme.colors.onSurface }]}
            value={amount}
            onChangeText={setAmount}
            keyboardType="numeric"
            placeholder="500"
            placeholderTextColor={theme.colors.onSurfaceVariant}
          />
        </Surface>
      </View>

      {/* Category Grid */}
      <View style={styles.section}>
        <Text variant="labelLarge" style={[styles.sectionLabel, { color: theme.colors.onSurface }]}>
          What are you spending on?
        </Text>
        {loadingCategories ? (
          <LoadingState message="Loading categories..." />
        ) : (
          <View style={styles.categoryGrid}>
            {categories.map((cat) => (
              <Pressable
                key={cat.name}
                onPress={() => setSelectedCategory(cat.name)}
                style={[
                  styles.categoryItem,
                  {
                    backgroundColor:
                      selectedCategory === cat.name
                        ? theme.colors.primaryContainer
                        : theme.colors.elevation.level1,
                    borderColor:
                      selectedCategory === cat.name
                        ? theme.colors.primary
                        : 'transparent',
                  },
                ]}
              >
                <MaterialCommunityIcons
                  name={(CATEGORY_ICONS[cat.icon] || 'circle-outline') as any}
                  size={24}
                  color={
                    selectedCategory === cat.name
                      ? theme.colors.primary
                      : theme.colors.onSurfaceVariant
                  }
                />
                <Text
                  variant="labelSmall"
                  numberOfLines={2}
                  style={{
                    textAlign: 'center',
                    marginTop: 4,
                    color:
                      selectedCategory === cat.name
                        ? theme.colors.onPrimaryContainer
                        : theme.colors.onSurfaceVariant,
                  }}
                >
                  {cat.name}
                </Text>
              </Pressable>
            ))}
          </View>
        )}
      </View>

      {/* Next Button */}
      <View style={styles.section}>
        <Pressable
          style={[
            styles.nextButton,
            !selectedCategory && styles.nextButtonDisabled,
          ]}
          onPress={handleNext}
          disabled={!selectedCategory}
        >
          <Text style={styles.nextButtonText}>Next</Text>
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
  sectionLabel: {
    fontFamily: 'Outfit-SemiBold',
    marginBottom: 10,
  },
  amountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  dollarSign: {
    fontSize: 24,
    fontFamily: 'Outfit-Bold',
    marginRight: 4,
  },
  amountInput: {
    flex: 1,
    fontSize: 24,
    fontFamily: 'Outfit-Bold',
  },
  categoryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  categoryItem: {
    width: '22%',
    aspectRatio: 1,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 8,
    borderWidth: 2,
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
