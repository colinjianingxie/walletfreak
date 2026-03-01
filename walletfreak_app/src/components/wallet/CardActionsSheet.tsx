import React, { useCallback, useMemo, useState } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { Text, Button, SegmentedButtons, useTheme } from 'react-native-paper';
import BottomSheet, { BottomSheetBackdrop, BottomSheetView } from '@gorhom/bottom-sheet';
import { useUpdateCardStatus, useUpdateAnniversary, useRemoveCard, useCheckDelete } from '../../hooks/useWallet';
import type { UserCard } from '../../types/card';

interface CardActionsSheetProps {
  card: UserCard | null;
  sheetRef: React.RefObject<BottomSheet | null>;
  onDismiss: () => void;
}

export const CardActionsSheet: React.FC<CardActionsSheetProps> = ({ card, sheetRef, onDismiss }) => {
  const theme = useTheme();
  const snapPoints = useMemo(() => ['45%'], []);
  const updateStatus = useUpdateCardStatus();
  const removeCard = useRemoveCard();

  const renderBackdrop = useCallback(
    (props: any) => <BottomSheetBackdrop {...props} disappearsOnIndex={-1} appearsOnIndex={0} />,
    []
  );

  const handleStatusChange = (status: string) => {
    if (!card) return;
    updateStatus.mutate(
      { userCardId: card.user_card_id, status },
      { onSuccess: onDismiss }
    );
  };

  const handleRemove = () => {
    if (!card) return;
    Alert.alert(
      'Remove Card',
      `Are you sure you want to remove ${card.name} from your wallet?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () =>
            removeCard.mutate(
              { userCardId: card.user_card_id },
              { onSuccess: onDismiss }
            ),
        },
      ]
    );
  };

  if (!card) return null;

  return (
    <BottomSheet
      ref={sheetRef}
      index={-1}
      snapPoints={snapPoints}
      enablePanDownToClose
      onClose={onDismiss}
      backdropComponent={renderBackdrop}
      backgroundStyle={{ backgroundColor: theme.colors.surface }}
      handleIndicatorStyle={{ backgroundColor: theme.colors.onSurfaceVariant }}
    >
      <BottomSheetView style={styles.content}>
        <Text variant="titleMedium" style={styles.title}>
          {card.name}
        </Text>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 16 }}>
          {card.issuer}
        </Text>

        <Text variant="labelLarge" style={{ marginBottom: 8 }}>Change Status</Text>
        <SegmentedButtons
          value={card.status}
          onValueChange={handleStatusChange}
          buttons={[
            { value: 'active', label: 'Active' },
            { value: 'inactive', label: 'Inactive' },
            { value: 'eyeing', label: 'Eyeing' },
          ]}
          style={{ marginBottom: 16 }}
        />

        {card.anniversary_date && (
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 16 }}>
            Anniversary: {card.anniversary_date}
          </Text>
        )}

        <Button
          mode="outlined"
          onPress={handleRemove}
          textColor={theme.colors.error}
          style={[styles.removeButton, { borderColor: theme.colors.error }]}
          icon="delete-outline"
          loading={removeCard.isPending}
        >
          Remove from Wallet
        </Button>
      </BottomSheetView>
    </BottomSheet>
  );
};

const styles = StyleSheet.create({
  content: {
    padding: 24,
  },
  title: {
    fontFamily: 'Outfit-SemiBold',
  },
  removeButton: {
    borderRadius: 12,
    marginTop: 8,
  },
});
