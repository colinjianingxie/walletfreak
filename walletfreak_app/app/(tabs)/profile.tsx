import React from 'react';
import { View, StyleSheet, Pressable, Alert } from 'react-native';
import { Text, Avatar, Surface, Button, Divider, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ScreenContainer } from '../../src/components/layout/ScreenContainer';
import { useAuthStore } from '../../src/stores/authStore';
import { logout } from '../../src/firebase/auth';

type IconName = React.ComponentProps<typeof MaterialCommunityIcons>['name'];

export default function ProfileScreen() {
  const { profile, user } = useAuthStore();
  const router = useRouter();
  const theme = useTheme();

  const handleLogout = () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          await logout();
        },
      },
    ]);
  };

  const menuItems: Array<{
    icon: IconName;
    label: string;
    onPress: () => void;
    dividerAfter?: boolean;
  }> = [
    {
      icon: 'crown-outline',
      label: profile?.is_premium ? 'Manage Subscription' : 'Upgrade to Premium',
      onPress: () => router.push('/stacks/subscription' as any),
      dividerAfter: true,
    },
    {
      icon: 'cog-outline',
      label: 'Settings',
      onPress: () => router.push('/stacks/settings' as any),
    },
    {
      icon: 'bell-outline',
      label: 'Notifications',
      onPress: () => router.push('/stacks/settings' as any),
      dividerAfter: true,
    },
    {
      icon: 'shield-check-outline',
      label: 'Privacy Policy',
      onPress: () => {},
    },
    {
      icon: 'file-document-outline',
      label: 'Terms of Service',
      onPress: () => {},
    },
  ];

  return (
    <ScreenContainer>
      {/* Profile Header */}
      <View style={styles.header}>
        <Avatar.Text
          size={72}
          label={
            profile?.first_name
              ? `${profile.first_name[0]}${profile.last_name?.[0] || ''}`
              : '?'
          }
          style={{ backgroundColor: theme.colors.primaryContainer }}
          labelStyle={{ color: theme.colors.onPrimaryContainer }}
        />
        <Text variant="titleLarge" style={styles.name}>
          {profile?.first_name} {profile?.last_name}
        </Text>
        {profile?.username && (
          <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
            @{profile.username}
          </Text>
        )}
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {profile?.email || user?.email}
        </Text>

        {profile?.assigned_personality && (
          <View style={[styles.personalityChip, { backgroundColor: theme.colors.primaryContainer }]}>
            <Text variant="labelMedium" style={{ color: theme.colors.onPrimaryContainer }}>
              {profile.assigned_personality}
            </Text>
          </View>
        )}
      </View>

      <Divider style={styles.divider} />

      {/* Menu Items */}
      <View>
        {menuItems.map((item, index) => (
          <React.Fragment key={index}>
            <Pressable onPress={item.onPress} style={styles.menuItem}>
              <MaterialCommunityIcons
                name={item.icon}
                size={24}
                color={theme.colors.onSurfaceVariant}
              />
              <Text variant="bodyLarge" style={styles.menuLabel}>
                {item.label}
              </Text>
              <MaterialCommunityIcons
                name="chevron-right"
                size={20}
                color={theme.colors.onSurfaceVariant}
              />
            </Pressable>
            {item.dividerAfter && <Divider style={styles.menuDivider} />}
          </React.Fragment>
        ))}
      </View>

      <Divider style={styles.divider} />

      <Button
        mode="outlined"
        onPress={handleLogout}
        textColor={theme.colors.error}
        style={styles.logoutButton}
        icon="logout"
      >
        Sign Out
      </Button>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  name: {
    marginTop: 12,
    fontFamily: 'Outfit-SemiBold',
  },
  personalityChip: {
    marginTop: 8,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 16,
  },
  divider: {
    marginVertical: 8,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 4,
  },
  menuLabel: {
    flex: 1,
    marginLeft: 16,
  },
  menuDivider: {
    marginVertical: 4,
  },
  logoutButton: {
    marginTop: 16,
    borderColor: '#B3261E',
    borderRadius: 12,
  },
});
