import React, { useMemo, useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, TextInput, Button, Switch, useTheme } from 'react-native-paper';
import BottomSheet, { BottomSheetBackdrop, BottomSheetView } from '@gorhom/bottom-sheet';
import { useUpdateBenefit } from '../../hooks/useWallet';
import type { BenefitDisplay } from '../../types/card';

interface BenefitUsageModalProps {
  benefit: BenefitDisplay | null;
  sheetRef: React.RefObject<BottomSheet | null>;
  onDismiss: () => void;
}

export const BenefitUsageModal: React.FC<BenefitUsageModalProps> = ({
  benefit,
  sheetRef,
  onDismiss,
}) => {
  const theme = useTheme();
  const snapPoints = useMemo(() => ['40%'], []);
  const [amount, setAmount] = useState('');
  const [markFull, setMarkFull] = useState(false);
  const updateBenefit = useUpdateBenefit();

  const currentPeriod = benefit?.periods.find((p) => p.is_current);

  const handleSubmit = () => {
    if (!benefit || !currentPeriod) return;
    updateBenefit.mutate(
      {
        userCardId: benefit.user_card_id,
        benefitId: benefit.benefit_id,
        amount: parseFloat(amount) || 0,
        periodKey: currentPeriod.key,
        isFull: markFull,
        increment: true,
      },
      {
        onSuccess: () => {
          setAmount('');
          setMarkFull(false);
          onDismiss();
        },
      }
    );
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
          Mark Benefit Used
        </Text>
        {benefit && (
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 16 }}>
            {benefit.benefit_name} — {benefit.card_name}
          </Text>
        )}

        <TextInput
          label="Amount Used ($)"
          value={amount}
          onChangeText={setAmount}
          keyboardType="decimal-pad"
          mode="outlined"
          style={{ marginBottom: 16 }}
        />

        <View style={styles.switchRow}>
          <Text variant="bodyMedium">Mark as Fully Used</Text>
          <Switch value={markFull} onValueChange={setMarkFull} />
        </View>

        <Button
          mode="contained"
          onPress={handleSubmit}
          loading={updateBenefit.isPending}
          disabled={!amount && !markFull}
          style={{ borderRadius: 12, marginTop: 16 }}
        >
          Submit
        </Button>
      </BottomSheetView>
    </BottomSheet>
  );
};

const styles = StyleSheet.create({
  content: {
    padding: 24,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
});
