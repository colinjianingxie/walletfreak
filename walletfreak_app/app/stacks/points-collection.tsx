import React, { useRef, useState } from 'react';
import { View, StyleSheet, FlatList } from 'react-native';
import { Text, FAB, useTheme } from 'react-native-paper';
import BottomSheet from '@gorhom/bottom-sheet';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { LoyaltyProgramCard } from '../../src/components/loyalty/LoyaltyProgramCard';
import { EditBalanceSheet } from '../../src/components/loyalty/EditBalanceSheet';
import { AddProgramSheet } from '../../src/components/loyalty/AddProgramSheet';
import { useLoyaltyPrograms } from '../../src/hooks/useLoyalty';
import { formatCurrency } from '../../src/utils/formatters';
import type { LoyaltyProgram } from '../../src/types/loyalty';

export default function PointsCollectionScreen() {
  const { data, isLoading } = useLoyaltyPrograms();
  const theme = useTheme();
  const editSheetRef = useRef<BottomSheet>(null);
  const addSheetRef = useRef<BottomSheet>(null);
  const [selectedProgram, setSelectedProgram] = useState<LoyaltyProgram | null>(null);

  const handleProgramPress = (program: LoyaltyProgram) => {
    setSelectedProgram(program);
    editSheetRef.current?.snapToIndex(0);
  };

  if (isLoading) {
    return <LoadingState message="Loading loyalty programs..." />;
  }

  const programs = data?.programs ?? [];
  const allPrograms = data?.all_programs ?? [];
  const totalValue = data?.total_est_value ?? 0;
  const existingProgramIds = programs.map((p: LoyaltyProgram) => p.program_id);

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Total Value Header */}
      <View style={[styles.totalHeader, { backgroundColor: theme.colors.primaryContainer }]}>
        <Text variant="labelMedium" style={{ color: theme.colors.onPrimaryContainer }}>
          Total Estimated Value
        </Text>
        <Text variant="headlineMedium" style={{ color: theme.colors.onPrimaryContainer, fontFamily: 'Outfit-Bold' }}>
          {formatCurrency(totalValue)}
        </Text>
      </View>

      {programs.length === 0 ? (
        <EmptyState
          icon="star-circle-outline"
          title="No loyalty programs"
          message="Add loyalty programs to track your points, miles, and cash back."
        />
      ) : (
        <FlatList
          data={programs}
          renderItem={({ item }) => (
            <LoyaltyProgramCard program={item} onPress={handleProgramPress} />
          )}
          keyExtractor={(item) => item.program_id}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
        />
      )}

      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        color={theme.colors.onPrimary}
        onPress={() => addSheetRef.current?.snapToIndex(0)}
      />

      <EditBalanceSheet
        program={selectedProgram}
        sheetRef={editSheetRef}
        onDismiss={() => {
          setSelectedProgram(null);
          editSheetRef.current?.close();
        }}
      />

      <AddProgramSheet
        sheetRef={addSheetRef}
        allPrograms={allPrograms}
        existingProgramIds={existingProgramIds}
        onDismiss={() => addSheetRef.current?.close()}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
  },
  totalHeader: {
    alignItems: 'center',
    padding: 20,
    borderRadius: 16,
    marginVertical: 16,
  },
  list: {
    paddingBottom: 80,
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    borderRadius: 16,
  },
});
