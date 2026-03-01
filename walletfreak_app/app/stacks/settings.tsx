import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Alert, ScrollView } from 'react-native';
import { Text, TextInput, Button, Switch, Divider, useTheme } from 'react-native-paper';
import { PersonalityAvatar } from '../../src/components/personality/PersonalityAvatar';
import { useProfile, useSyncProfile, useUpdateNotifications } from '../../src/hooks/useProfile';
import { usePersonalities } from '../../src/hooks/usePersonality';
import { LoadingState } from '../../src/components/layout/LoadingState';

export default function SettingsScreen() {
  const theme = useTheme();
  const { data: profile, isLoading } = useProfile();
  const { data: personalityData } = usePersonalities();
  const syncProfile = useSyncProfile();
  const updateNotifications = useUpdateNotifications();

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [username, setUsername] = useState('');
  const [emailUpdates, setEmailUpdates] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(true);

  useEffect(() => {
    if (profile) {
      setFirstName(profile.first_name || '');
      setLastName(profile.last_name || '');
      setUsername(profile.username || '');
      setEmailUpdates(profile.notification_preferences?.email_updates ?? true);
      setPushNotifications(profile.notification_preferences?.push_notifications ?? true);
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

  const handleSaveNotifications = () => {
    updateNotifications.mutate(
      { email_updates: emailUpdates, push_notifications: pushNotifications },
      { onSuccess: () => Alert.alert('Saved', 'Notification preferences updated.') }
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

      <Divider style={styles.divider} />

      {/* Notifications */}
      <Text variant="titleMedium" style={styles.sectionTitle}>Notifications</Text>
      <View style={styles.switchRow}>
        <Text variant="bodyMedium">Email Updates</Text>
        <Switch value={emailUpdates} onValueChange={setEmailUpdates} />
      </View>
      <View style={styles.switchRow}>
        <Text variant="bodyMedium">Push Notifications</Text>
        <Switch value={pushNotifications} onValueChange={setPushNotifications} />
      </View>
      <Button
        mode="contained-tonal"
        onPress={handleSaveNotifications}
        loading={updateNotifications.isPending}
        style={styles.saveButton}
      >
        Save Notifications
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
  divider: {
    marginVertical: 24,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
});
