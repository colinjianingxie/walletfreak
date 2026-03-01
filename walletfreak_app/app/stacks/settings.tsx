import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Alert, ScrollView, Pressable } from 'react-native';
import { Text, TextInput, Button, useTheme, Divider } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { PersonalityAvatar } from '../../src/components/personality/PersonalityAvatar';
import { useProfile, useSyncProfile } from '../../src/hooks/useProfile';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { logout } from '../../src/firebase/auth';

export default function SettingsScreen() {
  const theme = useTheme();
  const router = useRouter();
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

  const handleLogout = () => {
    Alert.alert('Log Out', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Log Out',
        style: 'destructive',
        onPress: () => logout(),
      },
    ]);
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

      {/* Legal Links */}
      <Divider style={styles.sectionDivider} />
      <Text variant="titleMedium" style={styles.sectionTitle}>Legal</Text>

      <Pressable
        style={[styles.linkRow, { borderColor: theme.colors.outlineVariant }]}
        onPress={() => router.push('/stacks/privacy-policy' as any)}
      >
        <MaterialCommunityIcons name="shield-lock-outline" size={22} color={theme.colors.onSurface} />
        <Text style={styles.linkText}>Privacy Policy</Text>
        <MaterialCommunityIcons name="chevron-right" size={22} color={theme.colors.onSurfaceVariant} />
      </Pressable>

      <Pressable
        style={[styles.linkRow, { borderColor: theme.colors.outlineVariant }]}
        onPress={() => router.push('/stacks/terms-of-service' as any)}
      >
        <MaterialCommunityIcons name="file-document-outline" size={22} color={theme.colors.onSurface} />
        <Text style={styles.linkText}>Terms of Service</Text>
        <MaterialCommunityIcons name="chevron-right" size={22} color={theme.colors.onSurfaceVariant} />
      </Pressable>

      {/* Log Out */}
      <Divider style={styles.sectionDivider} />
      <Button
        mode="outlined"
        onPress={handleLogout}
        textColor={theme.colors.error}
        style={[styles.logoutButton, { borderColor: theme.colors.error }]}
        icon="logout"
      >
        Log Out
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
    paddingBottom: 48,
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
  sectionDivider: {
    marginVertical: 24,
  },
  linkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderRadius: 12,
    marginBottom: 10,
  },
  linkText: {
    flex: 1,
    fontSize: 16,
    fontFamily: 'Outfit-Medium',
    marginLeft: 12,
    color: '#1C1B1F',
  },
  logoutButton: {
    borderRadius: 12,
  },
});
