import React, { useState } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { Text, TextInput, Button, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { ScreenContainer } from '../../src/components/layout/ScreenContainer';
import { useWallet } from '../../src/hooks/useWallet';
import { useSubmitDatapoint } from '../../src/hooks/useDatapoints';

export default function DatapointSubmitScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { data: walletData } = useWallet();
  const submitDatapoint = useSubmitDatapoint();

  const [cardId, setCardId] = useState('');
  const [benefit, setBenefit] = useState('');
  const [content, setContent] = useState('');

  const allCards = [
    ...(walletData?.active_cards ?? []),
    ...(walletData?.inactive_cards ?? []),
  ];

  const handleSubmit = () => {
    if (!cardId || !benefit || !content) {
      Alert.alert('Missing Fields', 'Please fill in all fields.');
      return;
    }
    submitDatapoint.mutate(
      { card_id: cardId, benefit, data: content },
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
    <ScreenContainer>
      <Text variant="titleLarge" style={styles.title}>
        Submit a Data Point
      </Text>
      <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 24 }}>
        Share useful data about credit card benefits with the community.
      </Text>

      <TextInput
        label="Card"
        value={cardId}
        onChangeText={setCardId}
        mode="outlined"
        style={styles.input}
        placeholder="Select a card"
      />

      <TextInput
        label="Benefit"
        value={benefit}
        onChangeText={setBenefit}
        mode="outlined"
        style={styles.input}
        placeholder="e.g., Travel Credit, Dining Credit"
      />

      <TextInput
        label="Details"
        value={content}
        onChangeText={setContent}
        mode="outlined"
        style={styles.input}
        multiline
        numberOfLines={4}
        placeholder="Share your experience or data..."
      />

      <Button
        mode="contained"
        onPress={handleSubmit}
        loading={submitDatapoint.isPending}
        disabled={!cardId || !benefit || !content}
        style={styles.submitButton}
      >
        Submit
      </Button>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: {
    fontFamily: 'Outfit-SemiBold',
    marginBottom: 8,
  },
  input: {
    marginBottom: 16,
  },
  submitButton: {
    borderRadius: 12,
    marginTop: 8,
  },
});
