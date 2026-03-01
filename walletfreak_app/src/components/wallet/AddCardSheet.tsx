import React, { useMemo, useState } from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text, Searchbar, useTheme } from 'react-native-paper';
import BottomSheet, { BottomSheetBackdrop, BottomSheetView, BottomSheetFlatList } from '@gorhom/bottom-sheet';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { CardImage } from '../ui/CardImage';
import { useCardList } from '../../hooks/useCards';
import { useAddCard } from '../../hooks/useWallet';

interface AddCardSheetProps {
  sheetRef: React.RefObject<BottomSheet | null>;
  existingCardIds: string[];
  onDismiss: () => void;
}

export const AddCardSheet: React.FC<AddCardSheetProps> = ({
  sheetRef,
  existingCardIds,
  onDismiss,
}) => {
  const theme = useTheme();
  const snapPoints = useMemo(() => ['70%'], []);
  const [search, setSearch] = useState('');
  const addCard = useAddCard();

  const { data } = useCardList({ page_size: 500 });
  const allCards = data?.cards ?? [];

  const availableCards = useMemo(() => {
    const existing = new Set(existingCardIds);
    let filtered = allCards.filter((c: any) => !existing.has(c.id) && !existing.has(c.slug));
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter((c: any) =>
        (c.name || '').toLowerCase().includes(q) ||
        (c.issuer || '').toLowerCase().includes(q)
      );
    }
    return filtered;
  }, [allCards, existingCardIds, search]);

  const handleAdd = (cardId: string) => {
    addCard.mutate({ cardId }, {
      onSuccess: () => {
        onDismiss();
      },
    });
  };

  return (
    <BottomSheet
      ref={sheetRef}
      index={-1}
      snapPoints={snapPoints}
      enablePanDownToClose
      onClose={onDismiss}
      backdropComponent={(props) => (
        <BottomSheetBackdrop {...props} disappearsOnIndex={-1} appearsOnIndex={0} />
      )}
      backgroundStyle={{ backgroundColor: theme.colors.surface }}
      handleIndicatorStyle={{ backgroundColor: 'transparent' }}
    >
      <BottomSheetView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Add Credit Card</Text>
          <Pressable onPress={onDismiss} style={styles.closeButton}>
            <MaterialCommunityIcons name="close" size={22} color={theme.colors.onSurfaceVariant} />
          </Pressable>
        </View>

        {/* Divider */}
        <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />

        {/* Search */}
        <Searchbar
          placeholder="Search cards (e.g. Gold, Sapphire)..."
          onChangeText={setSearch}
          value={search}
          style={[styles.searchbar, { borderColor: theme.colors.primary }]}
          inputStyle={{ fontFamily: 'Outfit', fontSize: 14 }}
        />

        {/* Suggested Label */}
        <Text style={[styles.suggestedLabel, { color: theme.colors.onSurfaceVariant }]}>
          SUGGESTED
        </Text>

        {/* Card List */}
        <BottomSheetFlatList
          data={availableCards}
          keyExtractor={(item: any) => item.id || item.slug}
          renderItem={({ item }: { item: any }) => (
            <Pressable
              style={styles.cardRow}
              onPress={() => handleAdd(item.id || item.slug)}
            >
              <CardImage slug={item.slug || item.id} size="small" style={{ marginRight: 12 }} />
              <View style={{ flex: 1 }}>
                <Text variant="titleSmall" numberOfLines={1} style={{ fontFamily: 'Outfit-SemiBold' }}>
                  {item.name}
                </Text>
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                  {item.issuer}
                </Text>
              </View>
              <MaterialCommunityIcons name="chevron-right" size={20} color={theme.colors.onSurfaceVariant} />
            </Pressable>
          )}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 20 }}
          ListEmptyComponent={
            <Text
              variant="bodyMedium"
              style={{ color: theme.colors.onSurfaceVariant, textAlign: 'center', marginTop: 24 }}
            >
              {search ? 'No cards found' : 'All cards already added'}
            </Text>
          }
        />
      </BottomSheetView>
    </BottomSheet>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  headerTitle: {
    fontSize: 20,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
  },
  closeButton: {
    padding: 4,
  },
  divider: {
    height: 1,
    marginVertical: 12,
  },
  searchbar: {
    borderRadius: 12,
    elevation: 0,
    backgroundColor: '#F5F5F5',
    borderWidth: 1,
    marginBottom: 16,
  },
  suggestedLabel: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    letterSpacing: 1,
    marginBottom: 12,
  },
  cardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
});
