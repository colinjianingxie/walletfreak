import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Switch } from 'react-native';
import { Text, Button, Surface, RadioButton, useTheme } from 'react-native-paper';
import { useLocalSearchParams } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { CardImage } from '../../src/components/ui/CardImage';
import { useWorthItQuestions, useCalculateWorthIt } from '../../src/hooks/useCalculators';
import { formatCurrency } from '../../src/utils/formatters';
import { colors } from '../../src/theme';
import type { WorthItResponse, WorthItResult } from '../../src/api/endpoints/calculators';

export default function WorthItAuditScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const theme = useTheme();
  const { data, isLoading } = useWorthItQuestions(slug || '');
  const calculateMutation = useCalculateWorthIt();
  const [responses, setResponses] = useState<Record<number, number>>({});
  const [result, setResult] = useState<WorthItResult | null>(null);

  const updateResponse = (index: number, value: number) => {
    setResponses((prev) => ({ ...prev, [index]: value }));
  };

  const handleCalculate = () => {
    if (!slug) return;
    const responseArr: WorthItResponse[] = Object.entries(responses).map(
      ([index, value]) => ({
        index: parseInt(index),
        value,
      })
    );
    calculateMutation.mutate(
      { slug, responses: responseArr },
      {
        onSuccess: (data) => setResult(data),
      }
    );
  };

  if (isLoading) {
    return <LoadingState message="Loading audit..." />;
  }

  if (!data) {
    return <LoadingState message="Card not found" />;
  }

  // Show result screen
  if (result) {
    const scoreColor = result.is_worth_it ? colors.success : theme.colors.error;

    return (
      <ScrollView
        style={[styles.container, { backgroundColor: theme.colors.background }]}
        contentContainerStyle={styles.resultContainer}
      >
        <CardImage slug={slug || ''} size="medium" style={{ alignSelf: 'center', marginBottom: 16 }} />
        <Text variant="titleLarge" style={{ textAlign: 'center', fontFamily: 'Outfit-SemiBold' }}>
          {data.card.name}
        </Text>

        {/* Score Circle */}
        <View style={[styles.scoreCircle, { borderColor: scoreColor }]}>
          <Text style={[styles.scoreText, { color: scoreColor }]}>
            {result.optimization_score}%
          </Text>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            Fit Score
          </Text>
        </View>

        {/* Verdict */}
        <View style={[styles.verdictBadge, { backgroundColor: result.is_worth_it ? '#ECFDF5' : '#FEF2F2' }]}>
          <MaterialCommunityIcons
            name={result.is_worth_it ? 'check-circle' : 'close-circle'}
            size={20}
            color={scoreColor}
          />
          <Text
            variant="labelLarge"
            style={{ color: scoreColor, marginLeft: 8, fontFamily: 'Outfit-SemiBold' }}
          >
            {result.verdict}
          </Text>
        </View>

        {/* Breakdown */}
        <Surface style={[styles.breakdownCard, { backgroundColor: theme.colors.elevation.level1 }]} elevation={1}>
          <View style={styles.breakdownRow}>
            <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
              Total Benefits Value
            </Text>
            <Text variant="titleSmall" style={{ color: colors.success }}>
              {formatCurrency(result.total_value)}
            </Text>
          </View>
          <View style={styles.breakdownRow}>
            <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
              Annual Fee
            </Text>
            <Text variant="titleSmall" style={{ color: theme.colors.error }}>
              -{formatCurrency(result.annual_fee)}
            </Text>
          </View>
          <View style={[styles.breakdownRow, styles.breakdownTotal]}>
            <Text variant="titleSmall" style={{ fontFamily: 'Outfit-SemiBold' }}>
              Net {result.is_worth_it ? 'Profit' : 'Loss'}
            </Text>
            <Text
              variant="titleMedium"
              style={{ color: scoreColor, fontFamily: 'Outfit-Bold' }}
            >
              {result.net_profit >= 0 ? '+' : ''}
              {formatCurrency(result.net_profit)}
            </Text>
          </View>
        </Surface>

        <Button
          mode="outlined"
          onPress={() => setResult(null)}
          style={{ borderRadius: 12, marginTop: 16 }}
        >
          Re-take Audit
        </Button>
      </ScrollView>
    );
  }

  // Questionnaire screen
  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={{ paddingBottom: 40 }}
    >
      {/* Card Header */}
      <View style={styles.cardHeader}>
        <CardImage slug={slug || ''} size="small" style={{ marginRight: 12 }} />
        <View style={{ flex: 1 }}>
          <Text variant="titleSmall">{data.card.name}</Text>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            Annual Fee: {formatCurrency(data.card.annual_fee)}
          </Text>
        </View>
      </View>

      <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 16 }}>
        Rate your usage of each benefit to see if this card is worth the fee.
      </Text>

      {/* Questions */}
      {data.benefits.map((benefit, index) => (
        <Surface
          key={index}
          style={[styles.questionCard, { backgroundColor: theme.colors.elevation.level1 }]}
          elevation={1}
        >
          <Text variant="titleSmall" style={{ marginBottom: 4 }}>
            {benefit.question}
          </Text>
          {benefit.dollar_value > 0 && (
            <Text variant="labelSmall" style={{ color: theme.colors.primary, marginBottom: 12 }}>
              Value: {formatCurrency(benefit.dollar_value)} ({benefit.time_category})
            </Text>
          )}

          {benefit.input_type === 'toggle' ? (
            <View style={styles.toggleRow}>
              <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
                {responses[index] === 1 ? 'Yes, I use this' : 'No, I don\'t use this'}
              </Text>
              <Switch
                value={responses[index] === 1}
                onValueChange={(val) => updateResponse(index, val ? 1 : 0)}
                trackColor={{ false: theme.colors.surfaceVariant, true: theme.colors.primaryContainer }}
                thumbColor={responses[index] === 1 ? theme.colors.primary : theme.colors.outline}
              />
            </View>
          ) : (
            <RadioButton.Group
              onValueChange={(val) => updateResponse(index, parseInt(val))}
              value={String(responses[index] ?? -1)}
            >
              {benefit.choices.map((choice, choiceIdx) => (
                <RadioButton.Item
                  key={choiceIdx}
                  label={choice}
                  value={String(choiceIdx)}
                  labelStyle={{ fontFamily: 'Outfit', fontSize: 14 }}
                />
              ))}
            </RadioButton.Group>
          )}
        </Surface>
      ))}

      {/* Calculate Button */}
      <Button
        mode="contained"
        onPress={handleCalculate}
        loading={calculateMutation.isPending}
        style={styles.calculateButton}
        labelStyle={{ fontFamily: 'Outfit-Medium' }}
      >
        Calculate Worth It Score
      </Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
  },
  questionCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  toggleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  calculateButton: {
    marginTop: 16,
    borderRadius: 12,
    paddingVertical: 4,
  },
  resultContainer: {
    paddingVertical: 24,
    alignItems: 'center',
  },
  scoreCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 6,
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: 24,
  },
  scoreText: {
    fontSize: 32,
    fontFamily: 'Outfit-Bold',
  },
  verdictBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    marginBottom: 24,
  },
  breakdownCard: {
    borderRadius: 12,
    padding: 16,
    width: '100%',
  },
  breakdownRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  breakdownTotal: {
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    marginTop: 8,
    paddingTop: 12,
  },
});
