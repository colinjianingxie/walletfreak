import React from 'react';
import { View, StyleSheet, ScrollView, Pressable } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { useSpendCategories } from '../../src/hooks/useCalculators';

export default function SpendOptimizerStep2Screen() {
  const theme = useTheme();
  const router = useRouter();
  const { category } = useLocalSearchParams<{ category: string }>();
  const { data: categoriesData, isLoading } = useSpendCategories();

  const categories = categoriesData?.categories ?? [];
  const currentCategory = categories.find((c) => c.name === category);
  const subCategories = currentCategory?.sub_categories ?? [];

  const handleSelect = (sub: string) => {
    router.push({
      pathname: '/stacks/spend-optimizer-results' as any,
      params: { amount: '500', category, subCategory: sub },
    });
  };

  if (isLoading) {
    return <LoadingState message="Loading..." />;
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.scrollContent}
    >
      <Text style={[styles.heading, { color: theme.colors.onSurface }]}>
        More specifically?
      </Text>

      <View style={styles.list}>
        {subCategories.map((sub) => (
          <Pressable
            key={sub}
            style={[styles.row, { backgroundColor: theme.colors.surfaceVariant }]}
            onPress={() => handleSelect(sub)}
          >
            <Text style={[styles.rowText, { color: theme.colors.onSurface }]}>{sub}</Text>
            <MaterialCommunityIcons name="chevron-right" size={22} color={theme.colors.onSurfaceVariant} />
          </Pressable>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  heading: {
    fontSize: 20,
    fontFamily: 'Outfit-Bold',
    marginBottom: 16,
  },
  list: {
    gap: 10,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: 14,
    paddingHorizontal: 18,
    paddingVertical: 18,
  },
  rowText: {
    fontSize: 16,
    fontFamily: 'Outfit-SemiBold',
  },
});
