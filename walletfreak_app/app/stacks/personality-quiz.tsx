import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Pressable } from 'react-native';
import { Text, Button, ProgressBar, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { PersonalityAvatar } from '../../src/components/personality/PersonalityAvatar';
import { usePersonalities, useSubmitQuiz } from '../../src/hooks/usePersonality';

interface QuizOption {
  text: string;
  personalities: string[];
}

interface QuizQuestion {
  question: string;
  subtitle?: string;
  max_selections: number;
  options: QuizOption[];
}

export default function PersonalityQuizScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { data, isLoading } = usePersonalities();
  const submitQuiz = useSubmitQuiz();

  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<number, Set<number>>>({});
  const [resultSlug, setResultSlug] = useState<string | null>(null);
  const [showLoading, setShowLoading] = useState(false);

  const questions: QuizQuestion[] = data?.quiz_questions ?? [];
  const personalities = data?.personalities ?? [];

  const currentQuestion = questions[currentStep];
  const totalSteps = questions.length;
  const progress = totalSteps > 0 ? (currentStep + 1) / totalSteps : 0;

  const currentSelections = answers[currentStep] ?? new Set<number>();

  const toggleOption = (idx: number) => {
    const newSelections = new Set(currentSelections);
    if (newSelections.has(idx)) {
      newSelections.delete(idx);
    } else {
      if (currentQuestion?.max_selections === 1) {
        newSelections.clear();
      } else if (currentQuestion?.max_selections && newSelections.size >= currentQuestion.max_selections) {
        return;
      }
      newSelections.add(idx);
    }
    setAnswers({ ...answers, [currentStep]: newSelections });
  };

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      calculateResult();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const calculateResult = () => {
    setShowLoading(true);

    // Tally votes
    const votes: Record<string, number> = {};
    for (const [stepIdx, selections] of Object.entries(answers)) {
      const q = questions[parseInt(stepIdx)];
      if (!q) continue;
      for (const optIdx of selections) {
        const option = q.options[optIdx];
        if (!option) continue;
        for (const slug of option.personalities) {
          votes[slug] = (votes[slug] || 0) + 1;
        }
      }
    }

    // Find winner
    let bestSlug = 'student-starter';
    let bestCount = 0;
    for (const [slug, count] of Object.entries(votes)) {
      if (count > bestCount) {
        bestCount = count;
        bestSlug = slug;
      }
    }

    // Delay for effect
    setTimeout(() => {
      setResultSlug(bestSlug);
      setShowLoading(false);
      submitQuiz.mutate({ personalityId: bestSlug, score: bestCount });
    }, 2000);
  };

  const handleViewStack = () => {
    if (resultSlug) {
      router.replace(`/stacks/personality/${resultSlug}` as any);
    }
  };

  const handleStartOver = () => {
    setCurrentStep(0);
    setAnswers({});
    setResultSlug(null);
  };

  if (isLoading) {
    return <LoadingState message="Loading quiz..." />;
  }

  if (showLoading) {
    return (
      <View style={[styles.centerContainer, { backgroundColor: theme.colors.background }]}>
        <MaterialCommunityIcons name="brain" size={48} color={theme.colors.primary} />
        <Text variant="titleMedium" style={{ marginTop: 16, fontFamily: 'Outfit-SemiBold' }}>
          Analyzing your preferences...
        </Text>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant, marginTop: 8 }}>
          Finding your match...
        </Text>
      </View>
    );
  }

  if (resultSlug) {
    const resultPersonality = personalities.find((p: any) => p.id === resultSlug || p.slug === resultSlug);
    return (
      <View style={[styles.centerContainer, { backgroundColor: theme.colors.background }]}>
        <PersonalityAvatar slug={resultSlug} size={96} />
        <Text variant="headlineSmall" style={styles.resultTitle}>
          {resultPersonality?.name || resultSlug}
        </Text>
        <Text variant="bodyMedium" style={[styles.resultDescription, { color: theme.colors.onSurfaceVariant }]}>
          {resultPersonality?.description || 'Your financial personality has been determined!'}
        </Text>
        <Button
          mode="contained"
          onPress={handleViewStack}
          style={styles.resultButton}
          labelStyle={{ fontFamily: 'Outfit-Medium' }}
        >
          View Your Stack
        </Button>
        <Button
          mode="text"
          onPress={handleStartOver}
          style={{ marginTop: 8 }}
          labelStyle={{ fontFamily: 'Outfit' }}
        >
          Start Over
        </Button>
      </View>
    );
  }

  if (!currentQuestion) {
    return (
      <View style={[styles.centerContainer, { backgroundColor: theme.colors.background }]}>
        <Text variant="bodyLarge" style={{ color: theme.colors.onSurfaceVariant }}>
          Quiz questions not available.
        </Text>
      </View>
    );
  }

  const selectionText = currentQuestion.max_selections === 1
    ? 'Pick one'
    : `Pick up to ${currentQuestion.max_selections}`;

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Progress */}
      <View style={styles.progressHeader}>
        <Text style={[styles.progressLabel, { color: theme.colors.onSurfaceVariant }]}>
          QUESTION {currentStep + 1} OF {totalSteps}
        </Text>
        <ProgressBar progress={progress} style={styles.progressBar} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Text variant="titleLarge" style={styles.questionText}>
          {currentQuestion.question}
        </Text>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 20 }}>
          {currentQuestion.subtitle || selectionText}
        </Text>

        {/* Options Grid */}
        <View style={styles.optionsGrid}>
          {currentQuestion.options.map((option, idx) => {
            const isSelected = currentSelections.has(idx);
            return (
              <Pressable
                key={idx}
                onPress={() => toggleOption(idx)}
                style={[
                  styles.optionCard,
                  {
                    backgroundColor: isSelected
                      ? theme.colors.primaryContainer
                      : theme.colors.elevation.level1,
                    borderColor: isSelected
                      ? theme.colors.primary
                      : 'transparent',
                  },
                ]}
              >
                <Text
                  style={[
                    styles.optionText,
                    {
                      color: isSelected
                        ? theme.colors.onPrimaryContainer
                        : theme.colors.onSurface,
                    },
                  ]}
                  numberOfLines={3}
                >
                  {option.text}
                </Text>
                {isSelected && (
                  <View style={[styles.checkMark, { backgroundColor: theme.colors.primary }]}>
                    <MaterialCommunityIcons name="check" size={12} color="#FFFFFF" />
                  </View>
                )}
              </Pressable>
            );
          })}
        </View>
      </ScrollView>

      {/* Navigation */}
      <View style={styles.navRow}>
        {currentStep > 0 ? (
          <Button mode="text" onPress={handleBack} labelStyle={{ fontFamily: 'Outfit' }}>
            Back
          </Button>
        ) : (
          <View />
        )}
        <Button
          mode="contained"
          onPress={handleNext}
          disabled={currentSelections.size === 0}
          labelStyle={{ fontFamily: 'Outfit-Medium' }}
        >
          {currentStep < totalSteps - 1 ? 'Continue' : 'Reveal Match'}
        </Button>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  progressHeader: {
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  progressLabel: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    letterSpacing: 1,
    marginBottom: 8,
  },
  progressBar: {
    borderRadius: 4,
    height: 6,
  },
  content: {
    padding: 16,
    paddingBottom: 100,
  },
  questionText: {
    fontFamily: 'Outfit-Bold',
    marginBottom: 8,
  },
  optionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  optionCard: {
    width: '47%',
    flexGrow: 1,
    borderRadius: 12,
    padding: 16,
    minHeight: 70,
    borderWidth: 2,
    justifyContent: 'center',
  },
  optionText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    lineHeight: 18,
  },
  checkMark: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 20,
    height: 20,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  navRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  resultCircle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  resultTitle: {
    fontFamily: 'Outfit-Bold',
    textAlign: 'center',
    marginBottom: 12,
  },
  resultDescription: {
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: 24,
    marginBottom: 24,
  },
  resultButton: {
    borderRadius: 12,
    paddingHorizontal: 24,
  },
});
