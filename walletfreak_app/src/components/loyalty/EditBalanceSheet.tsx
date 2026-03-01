import React, { useMemo, useState, useEffect } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { Text, TextInput, Button, useTheme } from 'react-native-paper';
import BottomSheet, { BottomSheetBackdrop, BottomSheetView } from '@gorhom/bottom-sheet';
import { useUpdateLoyaltyBalance, useRemoveLoyaltyProgram } from '../../hooks/useLoyalty';
import type { LoyaltyProgram } from '../../types/loyalty';

interface EditBalanceSheetProps {
  program: LoyaltyProgram | null;
  sheetRef: React.RefObject<BottomSheet | null>;
  onDismiss: () => void;
}

export const EditBalanceSheet: React.FC<EditBalanceSheetProps> = ({
  program,
  sheetRef,
  onDismiss,
}) => {
  const theme = useTheme();
  const snapPoints = useMemo(() => ['40%'], []);
  const [balance, setBalance] = useState('');
  const updateBalance = useUpdateLoyaltyBalance();
  const removeProgram = useRemoveLoyaltyProgram();

  useEffect(() => {
    if (program) setBalance(String(program.balance));
  }, [program]);

  const handleSave = () => {
    if (!program) return;
    updateBalance.mutate(
      { programId: program.program_id, balance: parseInt(balance) || 0 },
      { onSuccess: onDismiss }
    );
  };

  const handleRemove = () => {
    if (!program) return;
    Alert.alert('Remove Program', `Remove ${program.name}?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: () => removeProgram.mutate(program.program_id, { onSuccess: onDismiss }),
      },
    ]);
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
      handleIndicatorStyle={{ backgroundColor: theme.colors.onSurfaceVariant }}
    >
      <BottomSheetView style={styles.content}>
        <Text variant="titleMedium" style={{ fontFamily: 'Outfit-SemiBold', marginBottom: 4 }}>
          {program?.name}
        </Text>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 16 }}>
          Update your {program?.type} balance
        </Text>

        <TextInput
          label="Balance"
          value={balance}
          onChangeText={setBalance}
          keyboardType="number-pad"
          mode="outlined"
          style={{ marginBottom: 16 }}
        />

        <Button mode="contained" onPress={handleSave} loading={updateBalance.isPending} style={{ borderRadius: 12 }}>
          Save
        </Button>
        <Button
          mode="text"
          onPress={handleRemove}
          textColor={theme.colors.error}
          style={{ marginTop: 8 }}
        >
          Remove Program
        </Button>
      </BottomSheetView>
    </BottomSheet>
  );
};

const styles = StyleSheet.create({
  content: {
    padding: 24,
  },
});
