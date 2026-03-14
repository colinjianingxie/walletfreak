import React, { useState, useMemo } from 'react';
import { View, StyleSheet, Alert, Pressable, ScrollView } from 'react-native';
import { Text, TextInput, Button, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { CardImage } from '../../src/components/ui/CardImage';
import { useWallet } from '../../src/hooks/useWallet';
import { useSubmitDatapoint } from '../../src/hooks/useDatapoints';

export default function DatapointSubmitScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { data: walletData } = useWallet();
  const submitDatapoint = useSubmitDatapoint();

  const [selectedCard, setSelectedCard] = useState<any>(null);
  const [selectedBenefit, setSelectedBenefit] = useState<any>(null);
  const [status, setStatus] = useState<'Success' | 'Failed'>('Success');
  const [content, setContent] = useState('');

  const allCards = useMemo(() => [
    ...(walletData?.active_cards ?? []),
    ...(walletData?.inactive_cards ?? []),
  ], [walletData]);

  // Benefits are returned separately by the wallet API, not on card objects.
  // Gather from all benefit arrays and filter by selected card.
  const allBenefits = useMemo(() => [
    ...(walletData?.action_needed_benefits ?? []),
    ...(walletData?.maxed_out_benefits ?? []),
    ...(walletData?.ignored_benefits ?? []),
  ], [walletData]);

  const benefits = useMemo(() => {
    if (!selectedCard) return [];
    const cardId = selectedCard.card_id || selectedCard.id;
    return allBenefits.filter((b: any) => b.card_id === cardId);
  }, [selectedCard, allBenefits]);

  const handleSelectCard = (card: any) => {
    setSelectedCard(card);
    setSelectedBenefit(null);
  };

  const handleSubmit = () => {
    if (!selectedCard || !selectedBenefit || !content.trim()) {
      Alert.alert('Missing Fields', 'Please select a card, benefit, and add details.');
      return;
    }
    submitDatapoint.mutate(
      {
        card_slug: selectedCard.card_id || selectedCard.slug,
        card_name: selectedCard.name,
        benefit_name: selectedBenefit.benefit_name,
        benefit_id: selectedBenefit.benefit_id,
        status,
        content: content.trim(),
      },
      {
        onSuccess: () => {
          Alert.alert('Success', 'Data point submitted!', [
            { text: 'OK', onPress: () => router.back() },
          ]);
        },
        onError: () => {
          Alert.alert('Error', 'Failed to submit data point.');
        },
      }
    );
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.scrollContent}
      keyboardShouldPersistTaps="handled"
    >
      <Text variant="titleLarge" style={styles.title}>
        Submit a Data Point
      </Text>
      <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 24 }}>
        Share useful data about credit card benefits with the community.
      </Text>

      {/* Step 1: Card Selection */}
      <Text variant="labelLarge" style={styles.stepLabel}>1. Select Card</Text>
      <View style={styles.cardList}>
        {allCards.map((card: any) => {
          const isSelected = selectedCard?.id === card.id;
          return (
            <Pressable
              key={card.id}
              style={[
                styles.cardRow,
                {
                  backgroundColor: isSelected ? theme.colors.primaryContainer : theme.colors.elevation.level1,
                  borderColor: isSelected ? theme.colors.primary : theme.colors.outlineVariant,
                },
              ]}
              onPress={() => handleSelectCard(card)}
            >
              <CardImage slug={card.card_id || card.slug} size="small" />
              <Text
                variant="bodyMedium"
                numberOfLines={2}
                style={[
                  styles.cardRowName,
                  { color: isSelected ? theme.colors.onPrimaryContainer : theme.colors.onSurface },
                ]}
              >
                {card.name}
              </Text>
              {isSelected && (
                <MaterialCommunityIcons name="check-circle" size={20} color={theme.colors.primary} />
              )}
            </Pressable>
          );
        })}
      </View>

      {/* Step 2: Benefit Selection */}
      {selectedCard && (
        <>
          <Text variant="labelLarge" style={styles.stepLabel}>2. Select Benefit</Text>
          {benefits.length === 0 ? (
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 16 }}>
              No trackable benefits found for this card.
            </Text>
          ) : (
            <View style={styles.benefitList}>
              {benefits.map((benefit: any) => {
                const isSelected = selectedBenefit?.benefit_id === benefit.benefit_id;
                return (
                  <Pressable
                    key={benefit.benefit_id}
                    style={[
                      styles.benefitOption,
                      {
                        backgroundColor: isSelected ? theme.colors.primaryContainer : theme.colors.elevation.level1,
                        borderColor: isSelected ? theme.colors.primary : theme.colors.outlineVariant,
                      },
                    ]}
                    onPress={() => setSelectedBenefit(benefit)}
                  >
                    <View style={{ flex: 1 }}>
                      <Text
                        variant="bodyMedium"
                        style={{
                          fontFamily: 'Outfit-Medium',
                          color: isSelected ? theme.colors.onPrimaryContainer : theme.colors.onSurface,
                        }}
                      >
                        {benefit.benefit_name}
                      </Text>
                      {benefit.additional_details ? (
                        <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 2 }}>
                          {benefit.additional_details}
                        </Text>
                      ) : null}
                    </View>
                    <Text
                      variant="labelMedium"
                      style={{
                        fontFamily: 'Outfit-SemiBold',
                        color: isSelected ? theme.colors.primary : theme.colors.onSurfaceVariant,
                      }}
                    >
                      ${benefit.amount}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          )}
        </>
      )}

      {/* Step 3: Status */}
      {selectedBenefit && (
        <>
          <Text variant="labelLarge" style={styles.stepLabel}>3. Status</Text>
          <View style={styles.statusRow}>
            <Pressable
              style={[
                styles.statusButton,
                {
                  backgroundColor: status === 'Success' ? '#ECFDF5' : theme.colors.elevation.level1,
                  borderColor: status === 'Success' ? '#16A34A' : theme.colors.outlineVariant,
                },
              ]}
              onPress={() => setStatus('Success')}
            >
              <MaterialCommunityIcons
                name="check-circle"
                size={18}
                color={status === 'Success' ? '#16A34A' : '#94A3B8'}
              />
              <Text style={[styles.statusText, { color: status === 'Success' ? '#16A34A' : theme.colors.onSurfaceVariant }]}>
                Success
              </Text>
            </Pressable>
            <Pressable
              style={[
                styles.statusButton,
                {
                  backgroundColor: status === 'Failed' ? '#FEF2F2' : theme.colors.elevation.level1,
                  borderColor: status === 'Failed' ? '#DC2626' : theme.colors.outlineVariant,
                },
              ]}
              onPress={() => setStatus('Failed')}
            >
              <MaterialCommunityIcons
                name="close-circle"
                size={18}
                color={status === 'Failed' ? '#DC2626' : '#94A3B8'}
              />
              <Text style={[styles.statusText, { color: status === 'Failed' ? '#DC2626' : theme.colors.onSurfaceVariant }]}>
                Failed
              </Text>
            </Pressable>
          </View>

          {/* Step 4: Details */}
          <Text variant="labelLarge" style={styles.stepLabel}>4. Details</Text>
          <TextInput
            value={content}
            onChangeText={setContent}
            mode="outlined"
            style={styles.input}
            multiline
            numberOfLines={4}
            placeholder="Describe your experience..."
          />

          <Button
            mode="contained"
            onPress={handleSubmit}
            loading={submitDatapoint.isPending}
            disabled={!content.trim() || submitDatapoint.isPending}
            style={styles.submitButton}
            labelStyle={{ fontFamily: 'Outfit-Medium' }}
          >
            Submit Data Point
          </Button>
        </>
      )}
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
  title: {
    fontFamily: 'Outfit-SemiBold',
    marginBottom: 8,
  },
  stepLabel: {
    fontFamily: 'Outfit-SemiBold',
    marginBottom: 10,
    marginTop: 8,
  },
  // Card picker
  cardList: {
    gap: 8,
    marginBottom: 16,
  },
  cardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 10,
    borderWidth: 1.5,
    gap: 12,
  },
  cardRowName: {
    fontFamily: 'Outfit-Medium',
    flex: 1,
  },
  // Benefit picker
  benefitList: {
    gap: 8,
    marginBottom: 8,
  },
  benefitOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    gap: 12,
  },
  // Status
  statusRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 16,
  },
  statusButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderRadius: 10,
    borderWidth: 1.5,
  },
  statusText: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
  },
  input: {
    marginBottom: 16,
  },
  submitButton: {
    borderRadius: 12,
    paddingVertical: 4,
  },
});
