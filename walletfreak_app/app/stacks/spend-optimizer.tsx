import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Pressable, TextInput as RNTextInput } from 'react-native';
import { Text, Button, Surface, Chip, useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { CardImage } from '../../src/components/ui/CardImage';
import { useSpendCategories, useCalculateSpendIt } from '../../src/hooks/useCalculators';
import { formatCurrency } from '../../src/utils/formatters';
import { colors } from '../../src/theme';
import type { SpendItResultItem } from '../../src/api/endpoints/calculators';

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
  const [amount, setAmount] = useState('500');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedSubCategory, setSelectedSubCategory] = useState<string | null>(null);
  const { data: categoriesData, isLoading: loadingCategories } = useSpendCategories();
  const calculateMutation = useCalculateSpendIt();

  const categories = categoriesData?.categories ?? [];
  const currentCategory = categories.find((c) => c.name === selectedCategory);

  const handleCalculate = () => {
    if (!selectedCategory) return;
    const amt = parseFloat(amount) || 500;
    calculateMutation.mutate({
      amount: amt,
      category: selectedCategory,
      subCategory: selectedSubCategory || undefined,
    });
  };

  const handleCategorySelect = (catName: string) => {
    setSelectedCategory(catName);
    setSelectedSubCategory(null);
    calculateMutation.reset();
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={{ paddingBottom: 40 }}
    >
      {/* Amount Input */}
      <View style={{ marginTop: 16 }}></View>
          <Text variant="labelLarge" style={{ color: theme.colors.onSurface, marginBottom: 8 }}>
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

          {/* Category Grid */}
          <Text variant="labelLarge" style={{ color: theme.colors.onSurface, marginTop: 16, marginBottom: 12 }}>
            Category
          </Text>
          {loadingCategories ? (
            <LoadingState message="Loading categories..." />
          ) : (
            <View style={styles.categoryGrid}>
              {categories.map((cat) => (
                <Pressable
                  key={cat.name}
                  onPress={() => handleCategorySelect(cat.name)}
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

          {/* Sub-categories */}
          {currentCategory && currentCategory.sub_categories.length > 0 && (
            <>
              <Text variant="labelLarge" style={{ color: theme.colors.onSurface, marginTop: 16, marginBottom: 8 }}>
                Specific (Optional)
              </Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.subCategoryRow}>
                {currentCategory.sub_categories.map((sub) => (
                  <Chip
                    key={sub}
                    selected={selectedSubCategory === sub}
                    onPress={() =>
                      setSelectedSubCategory(selectedSubCategory === sub ? null : sub)
                    }
                    style={styles.subChip}
                    compact
                  >
                    {sub}
                  </Chip>
                ))}
              </ScrollView>
            </>
          )}

          {/* Calculate Button */}
          <Button
            mode="contained"
            onPress={handleCalculate}
            loading={calculateMutation.isPending}
            disabled={!selectedCategory}
            style={styles.calculateButton}
            labelStyle={{ fontFamily: 'Outfit-Medium' }}
          >
            Find Best Card
          </Button>

          {/* Results */}
          {calculateMutation.data && (
            <View style={styles.results}>
              {/* Wallet Results */}
              {calculateMutation.data.wallet_results.length > 0 && (
                <>
                  <Text variant="titleMedium" style={{ fontFamily: 'Outfit-SemiBold', marginBottom: 12 }}>
                    Your Best Moves
                  </Text>
                  {calculateMutation.data.wallet_results.map((item, idx) => (
                    <ResultCard key={item.slug} item={item} rank={idx + 1} theme={theme} />
                  ))}
                </>
              )}

              {/* Opportunity Results */}
              {calculateMutation.data.opportunity_results.length > 0 && (
                <>
                  <Text
                    variant="titleMedium"
                    style={{ fontFamily: 'Outfit-SemiBold', marginTop: 16, marginBottom: 12 }}
                  >
                    New Opportunities
                  </Text>
                  {calculateMutation.data.opportunity_results.map((item, idx) => (
                    <ResultCard key={item.slug} item={item} rank={idx + 1} theme={theme} isOpportunity />
                  ))}
                </>
              )}

              {calculateMutation.data.wallet_results.length === 0 &&
                calculateMutation.data.opportunity_results.length === 0 && (
                  <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant, textAlign: 'center', marginTop: 24 }}>
                    No results found for this category and amount.
                  </Text>
                )}
            </View>
          )}
    </ScrollView>
  );
}

function ResultCard({
  item,
  rank,
  theme,
  isOpportunity,
}: {
  item: SpendItResultItem;
  rank: number;
  theme: any;
  isOpportunity?: boolean;
}) {
  return (
    <Surface
      style={[
        resultStyles.card,
        {
          backgroundColor: theme.colors.elevation.level1,
          borderColor: item.is_winner ? '#6750A4' : 'transparent',
          borderWidth: item.is_winner ? 2 : 0,
        },
      ]}
      elevation={1}
    >
      <View style={resultStyles.row}>
        <View style={resultStyles.rankCircle}>
          <Text style={resultStyles.rankText}>{rank}</Text>
        </View>
        <CardImage slug={item.slug} size="small" style={{ marginRight: 12 }} />
        <View style={{ flex: 1 }}>
          <Text variant="titleSmall" numberOfLines={1}>
            {item.card_name}
          </Text>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {item.issuer} · {item.earning_rate} {item.currency_display}
          </Text>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            Matched: {item.category_matched}
          </Text>
        </View>
        <View style={{ alignItems: 'flex-end' }}>
          <Text
            variant="titleSmall"
            style={{ color: colors.success, fontFamily: 'Outfit-Bold' }}
          >
            {formatCurrency(item.est_value)}
          </Text>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            est. value
          </Text>
        </View>
      </View>
      {item.is_winner && (
        <View style={resultStyles.winnerBadge}>
          <MaterialCommunityIcons name="crown" size={14} color="#6750A4" />
          <Text style={resultStyles.winnerText}>Best Pick</Text>
        </View>
      )}
    </Surface>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
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
  subCategoryRow: {
    gap: 8,
    paddingBottom: 4,
  },
  subChip: {
    marginRight: 4,
  },
  calculateButton: {
    marginTop: 20,
    borderRadius: 12,
    paddingVertical: 4,
  },
  results: {
    marginTop: 24,
  },
});

const resultStyles = StyleSheet.create({
  card: {
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rankCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#E5E7EB',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  rankText: {
    fontSize: 12,
    fontFamily: 'Outfit-Bold',
    color: '#374151',
  },
  winnerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    marginTop: 8,
    marginLeft: 32,
    backgroundColor: '#F3E8FF',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  winnerText: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    color: '#6750A4',
    marginLeft: 4,
  },
});
