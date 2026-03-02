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

  const benefits = useMemo(() => {
    if (!selectedCard) return [];
    return (selectedCard.benefits ?? []).filter((b: any) => b.dollar_value > 0);
  }, [selectedCard]);

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
        benefit_name: selectedBenefit.description || selectedBenefit.short_description,
        benefit_id: selectedBenefit.id || selectedBenefit.benefit_id,
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
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.cardScroller}
        contentContainerStyle={styles.cardScrollerContent}
      >
        {allCards.map((card: any) => {
          const isSelected = selectedCard?.id === card.id;
          return (
            <Pressable
              key={card.id}
              style={[
                styles.cardOption,
                {
                  backgroundColor: isSelected ? theme.colors.primaryContainer : theme.colors.elevation.level1,
                  borderColor: isSelected ? theme.colors.primary : 'transparent',
                },
              ]}
              onPress={() => handleSelectCard(card)}
            >
              <CardImage slug={card.card_id || card.slug} size="small" />
              <Text
                variant="labelSmall"
                numberOfLines={2}
                style={[
                  styles.cardOptionName,
                  { color: isSelected ? theme.colors.onPrimaryContainer : theme.colors.onSurface },
                ]}
              >
                {card.name}
              </Text>
              {isSelected && (
                <View style={[styles.checkBadge, { backgroundColor: theme.colors.primary }]}>
                  <MaterialCommunityIcons name="check" size={10} color="#FFF" />
                </View>
              )}
            </Pressable>
          );
        })}
      </ScrollView>

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
                const isSelected = selectedBenefit?.id === benefit.id;
                return (
                  <Pressable
                    key={benefit.id}
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
                        {benefit.description}
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
                      ${benefit.dollar_value}
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
  cardScroller: {
    marginBottom: 16,
    marginHorizontal: -16,
  },
  cardScrollerContent: {
    paddingHorizontal: 16,
    gap: 10,
  },
  cardOption: {
    width: 90,
    alignItems: 'center',
    padding: 10,
    borderRadius: 12,
    borderWidth: 2,
  },
  cardOptionName: {
    fontFamily: 'Outfit-Medium',
    fontSize: 10,
    textAlign: 'center',
    marginTop: 6,
  },
  checkBadge: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 16,
    height: 16,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
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
