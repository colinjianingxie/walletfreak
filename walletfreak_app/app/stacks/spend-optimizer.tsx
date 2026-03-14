import React from 'react';
import { View, StyleSheet, FlatList, Pressable, Dimensions } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
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

const NUM_COLUMNS = 4;
const GRID_GAP = 10;
const HORIZONTAL_PADDING = 16;
const screenWidth = Dimensions.get('window').width;
const tileSize = (screenWidth - HORIZONTAL_PADDING * 2 - GRID_GAP * (NUM_COLUMNS - 1)) / NUM_COLUMNS;

export default function SpendOptimizerScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { data: categoriesData, isLoading } = useSpendCategories();

  const categories = categoriesData?.categories ?? [];

  const handleSelect = (cat: any) => {
    const hasSubCategories = cat.sub_categories && cat.sub_categories.length > 0;
    if (hasSubCategories) {
      router.push({
        pathname: '/stacks/spend-optimizer-step2' as any,
        params: { category: cat.name },
      });
    } else {
      router.push({
        pathname: '/stacks/spend-optimizer-results' as any,
        params: { amount: '500', category: cat.name, subCategory: '' },
      });
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading categories..." />;
  }

  return (
    <FlatList
      data={categories}
      numColumns={NUM_COLUMNS}
      keyExtractor={(item) => item.name}
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.listContent}
      columnWrapperStyle={styles.row}
      ListHeaderComponent={
        <Text style={[styles.heading, { color: theme.colors.onSurface }]}>
          What are you spending on?
        </Text>
      }
      renderItem={({ item: cat }) => (
        <Pressable
          onPress={() => handleSelect(cat)}
          style={[styles.tile, { backgroundColor: theme.colors.surfaceVariant }]}
        >
          <MaterialCommunityIcons
            name={(CATEGORY_ICONS[cat.icon] || 'circle-outline') as any}
            size={28}
            color={theme.colors.onSurfaceVariant}
          />
          <Text
            numberOfLines={2}
            style={[styles.tileLabel, { color: theme.colors.onSurface }]}
          >
            {cat.name}
          </Text>
        </Pressable>
      )}
    />
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  listContent: {
    padding: HORIZONTAL_PADDING,
    paddingBottom: 40,
  },
  heading: {
    fontSize: 20,
    fontFamily: 'Outfit-Bold',
    marginBottom: 16,
  },
  row: {
    gap: GRID_GAP,
    marginBottom: GRID_GAP,
  },
  tile: {
    width: tileSize,
    height: tileSize,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 6,
  },
  tileLabel: {
    fontFamily: 'Outfit-Medium',
    textAlign: 'center',
    marginTop: 6,
    fontSize: 11,
  },
});
