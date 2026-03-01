import React from 'react';
import { StyleSheet, FlatList, Pressable } from 'react-native';
import { Text, Surface, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { PersonalityAvatar } from '../../src/components/personality/PersonalityAvatar';
import { usePersonalities } from '../../src/hooks/usePersonality';
import { useAuthStore } from '../../src/stores/authStore';

export default function PersonalityListScreen() {
  const { data, isLoading } = usePersonalities();
  const { profile } = useAuthStore();
  const router = useRouter();
  const theme = useTheme();

  if (isLoading || !data) {
    return <LoadingState message="Loading personalities..." />;
  }

  const personalities = data.personalities ?? [];
  const assignedId = data.assigned_personality?.id || profile?.assigned_personality;

  return (
    <FlatList
      data={personalities}
      numColumns={2}
      contentContainerStyle={styles.list}
      style={{ backgroundColor: theme.colors.background }}
      renderItem={({ item }) => {
        const isAssigned = item.id === assignedId;
        return (
          <Surface
            style={[
              styles.card,
              {
                backgroundColor: theme.colors.elevation.level1,
                borderColor: isAssigned ? theme.colors.primary : 'transparent',
                borderWidth: isAssigned ? 2 : 0,
              },
            ]}
            elevation={1}
          >
            <Pressable
              onPress={() => router.push(`/stacks/personality/${item.slug || item.id}` as any)}
              style={styles.cardContent}
            >
              <PersonalityAvatar slug={item.slug || item.id} size={64} />
              <Text variant="labelLarge" style={styles.cardName} numberOfLines={2}>
                {item.name}
              </Text>
              {isAssigned && (
                <Text variant="labelSmall" style={{ color: theme.colors.primary }}>
                  Your Personality
                </Text>
              )}
            </Pressable>
          </Surface>
        );
      }}
      keyExtractor={(item) => item.id || item.slug}
    />
  );
}

const styles = StyleSheet.create({
  list: {
    padding: 12,
  },
  card: {
    flex: 1,
    borderRadius: 16,
    margin: 4,
    overflow: 'hidden',
  },
  cardContent: {
    alignItems: 'center',
    padding: 16,
  },
  cardName: {
    fontFamily: 'Outfit-Medium',
    textAlign: 'center',
    marginTop: 8,
  },
});
