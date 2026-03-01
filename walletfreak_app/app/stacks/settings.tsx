import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Alert, ScrollView } from 'react-native';
import { Text, TextInput, Button, useTheme } from 'react-native-paper';
import { PersonalityAvatar } from '../../src/components/personality/PersonalityAvatar';
import { useProfile, useSyncProfile } from '../../src/hooks/useProfile';
import { LoadingState } from '../../src/components/layout/LoadingState';

export default function SettingsScreen() {
  const theme = useTheme();
  const { data: profile, isLoading } = useProfile();
  const syncProfile = useSyncProfile();

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [username, setUsername] = useState('');

  useEffect(() => {
    if (profile) {
      setFirstName(profile.first_name || '');
      setLastName(profile.last_name || '');
      setUsername(profile.username || '');
    }
  }, [profile]);

  const handleSaveProfile = () => {
    syncProfile.mutate(
      { first_name: firstName, last_name: lastName, username },
      {
        onSuccess: () => Alert.alert('Saved', 'Profile updated successfully.'),
        onError: (err: any) =>
          Alert.alert('Error', err?.response?.data?.detail || 'Failed to update profile.'),
      }
    );
  };

  if (isLoading) {
    return <LoadingState message="Loading settings..." />;
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.content}
    >
      {/* Avatar */}
      <View style={styles.avatarSection}>
        {profile?.photo_url && (
          <PersonalityAvatar
            slug={profile.photo_url.replace('/static/images/personalities/', '').replace('.png', '')}
            size={80}
          />
        )}
      </View>

      {/* Profile Info */}
      <Text variant="titleMedium" style={styles.sectionTitle}>Profile</Text>
      <TextInput
        label="First Name"
        value={firstName}
        onChangeText={setFirstName}
        mode="outlined"
        style={styles.input}
      />
      <TextInput
        label="Last Name"
        value={lastName}
        onChangeText={setLastName}
        mode="outlined"
        style={styles.input}
      />
      <TextInput
        label="Username"
        value={username}
        onChangeText={setUsername}
        mode="outlined"
        style={styles.input}
      />
      <Button
        mode="contained"
        onPress={handleSaveProfile}
        loading={syncProfile.isPending}
        style={styles.saveButton}
      >
        Save Profile
      </Button>
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
  avatarSection: {
    alignItems: 'center',
    marginBottom: 24,
  },
  sectionTitle: {
    fontFamily: 'Outfit-Medium',
    marginBottom: 12,
  },
  input: {
    marginBottom: 12,
  },
  saveButton: {
    borderRadius: 12,
    marginTop: 8,
  },
});
