import React from 'react';
import { View, StyleSheet, ScrollView, FlatList, Pressable } from 'react-native';
import { Text, Surface, useTheme } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { LoadingState } from '../../../src/components/layout/LoadingState';
import { PersonalityAvatar } from '../../../src/components/personality/PersonalityAvatar';
import { CardImage } from '../../../src/components/ui/CardImage';
import { usePersonalityDetail } from '../../../src/hooks/usePersonality';

export default function PersonalityDetailScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { data: personality, isLoading } = usePersonalityDetail(slug);
  const router = useRouter();
  const theme = useTheme();

  if (isLoading || !personality) {
    return <LoadingState message="Loading personality..." />;
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.content}
    >
      {/* Avatar & Name */}
      <View style={styles.header}>
        <PersonalityAvatar slug={personality.slug || slug} size={120} />
        <Text variant="headlineSmall" style={styles.name}>
          {personality.name}
        </Text>
        {personality.match_score != null && (
          <Text variant="labelLarge" style={{ color: theme.colors.primary, marginTop: 4 }}>
            {personality.match_score}% Match
          </Text>
        )}
      </View>

      {/* Description */}
      {personality.description && (
        <Text variant="bodyMedium" style={styles.description}>
          {personality.description}
        </Text>
      )}

      {/* Card Slots */}
      {personality.slots?.map((slot: any, idx: number) => (
        <View key={idx} style={styles.slotSection}>
          <Text variant="titleSmall" style={{ fontFamily: 'Outfit-Medium', marginBottom: 8 }}>
            {slot.name}
          </Text>
          {slot.description && (
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 8 }}>
              {slot.description}
            </Text>
          )}
          <FlatList
            data={slot.hydrated_cards || []}
            horizontal
            showsHorizontalScrollIndicator={false}
            renderItem={({ item: card }) => (
              <Pressable
                onPress={() => router.push(`/stacks/card-detail/${card.slug || card.id}` as any)}
              >
                <Surface
                  style={[styles.cardChip, { backgroundColor: theme.colors.elevation.level1 }]}
                  elevation={1}
                >
                  <CardImage slug={card.slug || card.id} size="small" style={{ marginRight: 8 }} />
                  <View>
                    <Text variant="labelMedium" numberOfLines={1}>
                      {card.name}
                    </Text>
                    <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
                      {card.issuer}
                    </Text>
                  </View>
                </Surface>
              </Pressable>
            )}
            keyExtractor={(item) => item.id || item.slug}
            contentContainerStyle={{ gap: 8 }}
          />
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  name: {
    fontFamily: 'Outfit-SemiBold',
    marginTop: 16,
  },
  description: {
    lineHeight: 22,
    marginBottom: 24,
  },
  slotSection: {
    marginBottom: 20,
  },
  cardChip: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    borderRadius: 12,
    minWidth: 180,
  },
});
