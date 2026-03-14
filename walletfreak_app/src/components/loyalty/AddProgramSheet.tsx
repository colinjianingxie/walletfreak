import React, { useMemo, useState } from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text, Searchbar, useTheme } from 'react-native-paper';
import BottomSheet, { BottomSheetBackdrop, BottomSheetView, BottomSheetFlatList } from '@gorhom/bottom-sheet';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useAddLoyaltyProgram } from '../../hooks/useLoyalty';

interface AllProgram {
  id: string;
  program_name: string;
  type?: string;
  currency_group?: string;
}

interface AddProgramSheetProps {
  sheetRef: React.RefObject<BottomSheet | null>;
  allPrograms: AllProgram[];
  existingProgramIds: string[];
  onDismiss: () => void;
}

export const AddProgramSheet: React.FC<AddProgramSheetProps> = ({
  sheetRef,
  allPrograms,
  existingProgramIds,
  onDismiss,
}) => {
  const theme = useTheme();
  const snapPoints = useMemo(() => ['70%'], []);
  const [search, setSearch] = useState('');
  const addProgram = useAddLoyaltyProgram();

  const availablePrograms = useMemo(() => {
    const existing = new Set(existingProgramIds);
    let filtered = allPrograms.filter((p) => !existing.has(p.id));
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter((p) =>
        (p.program_name || '').toLowerCase().includes(q)
      );
    }
    return filtered.sort((a, b) =>
      (a.program_name || '').localeCompare(b.program_name || '')
    );
  }, [allPrograms, existingProgramIds, search]);

  const handleAdd = (programId: string) => {
    addProgram.mutate(programId, {
      onSuccess: () => {
        onDismiss();
      },
    });
  };

  const getProgramIcon = (type?: string): string => {
    switch (type) {
      case 'miles': return 'airplane';
      case 'points': return 'star-circle-outline';
      case 'cash': return 'cash';
      default: return 'star-circle-outline';
    }
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
          <Text style={styles.headerTitle}>Add Loyalty Program</Text>
          <Pressable onPress={onDismiss} style={styles.closeButton}>
            <MaterialCommunityIcons name="close" size={22} color={theme.colors.onSurfaceVariant} />
          </Pressable>
        </View>

        {/* Divider */}
        <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />

        {/* Search */}
        <Searchbar
          placeholder="Search programs (e.g. United, Marriott)..."
          onChangeText={setSearch}
          value={search}
          style={[styles.searchbar, { borderColor: theme.colors.primary }]}
          inputStyle={{ fontFamily: 'Outfit', fontSize: 14 }}
        />

        {/* Suggested Label */}
        <Text style={[styles.suggestedLabel, { color: theme.colors.onSurfaceVariant }]}>
          SUGGESTED
        </Text>

        {/* Program List */}
        <BottomSheetFlatList
          data={availablePrograms}
          keyExtractor={(item: any) => item.id}
          renderItem={({ item }: { item: any }) => (
            <Pressable
              style={styles.programRow}
              onPress={() => handleAdd(item.id)}
            >
              <View style={[styles.iconCircle, { backgroundColor: theme.colors.primaryContainer }]}>
                <MaterialCommunityIcons
                  name={getProgramIcon(item.type) as any}
                  size={20}
                  color={theme.colors.onPrimaryContainer}
                />
              </View>
              <View style={{ flex: 1 }}>
                <Text variant="titleSmall" numberOfLines={1} style={{ fontFamily: 'Outfit-SemiBold' }}>
                  {item.program_name}
                </Text>
                {item.currency_group && (
                  <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                    {item.currency_group}
                  </Text>
                )}
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
              {search ? 'No programs found' : 'All programs already added'}
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
  programRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    gap: 12,
  },
  iconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
