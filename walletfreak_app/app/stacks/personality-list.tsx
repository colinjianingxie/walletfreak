import React from 'react';
import { View, StyleSheet, FlatList, Pressable } from 'react-native';
import { Text, Surface, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
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

  const ListHeader = () => (
    <Pressable
      style={[styles.findFreakButton, { backgroundColor: theme.colors.primary }]}
      onPress={() => router.push('/stacks/personality-quiz' as any)}
    >
      <MaterialCommunityIcons name="magnify" size={22} color="#FFFFFF" />
      <Text style={styles.findFreakText}>Find My Freak</Text>
      <MaterialCommunityIcons name="chevron-right" size={22} color="#FFFFFF" />
    </Pressable>
  );

  return (
    <FlatList
      data={personalities}
      numColumns={2}
      contentContainerStyle={styles.list}
      style={{ backgroundColor: theme.colors.background }}
      ListHeaderComponent={ListHeader}
      renderItem={({ item }) => {
        const isAssigned = item.id === assignedId;
        return (
          <Surface
            style={[
              styles.card,
              {
                backgroundColor: theme.colors.surface,
                borderColor: isAssigned ? theme.colors.primary : theme.colors.outlineVariant,
              },
            ]}
            elevation={0}
          >
            <Pressable
              onPress={() => router.push(`/stacks/personality/${item.slug || item.id}` as any)}
              style={styles.cardContent}
            >
              <PersonalityAvatar slug={item.slug || item.id} size={56} />
              <Text variant="labelLarge" style={styles.cardName} numberOfLines={2}>
                {item.name}
              </Text>
              {isAssigned && (
                <View style={[styles.assignedBadge, { backgroundColor: theme.colors.primaryContainer }]}>
                  <Text style={[styles.assignedText, { color: theme.colors.primary }]}>Your Freak</Text>
                </View>
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
    paddingBottom: 24,
  },
  findFreakButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    borderRadius: 14,
    marginHorizontal: 4,
    marginBottom: 16,
  },
  findFreakText: {
    fontSize: 16,
    fontFamily: 'Outfit-SemiBold',
    color: '#FFFFFF',
  },
  card: {
    flex: 1,
    borderRadius: 16,
    margin: 4,
    overflow: 'hidden',
    borderWidth: 1,
  },
  cardContent: {
    alignItems: 'center',
    paddingVertical: 24,
    paddingHorizontal: 12,
  },
  cardName: {
    fontFamily: 'Outfit-Medium',
    textAlign: 'center',
    marginTop: 10,
  },
  assignedBadge: {
    marginTop: 8,
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 10,
  },
  assignedText: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
  },
});
