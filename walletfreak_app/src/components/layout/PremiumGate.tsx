import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button, useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../stores/authStore';

interface PremiumGateProps {
  children: React.ReactNode;
  feature?: string;
}

export const PremiumGate: React.FC<PremiumGateProps> = ({
  children,
  feature = 'This feature',
}) => {
  const { profile } = useAuthStore();
  const router = useRouter();
  const theme = useTheme();

  if (profile?.is_premium) {
    return <>{children}</>;
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.elevation.level1 }]}>
      <MaterialCommunityIcons
        name="crown-outline"
        size={48}
        color={theme.colors.primary}
      />
      <Text variant="titleMedium" style={styles.title}>
        Premium Feature
      </Text>
      <Text
        variant="bodyMedium"
        style={[styles.message, { color: theme.colors.onSurfaceVariant }]}
      >
        {feature} is available with WalletFreak Premium.
      </Text>
      <Button
        mode="contained"
        onPress={() => router.push('/stacks/subscription')}
        style={styles.button}
      >
        Upgrade to Premium
      </Button>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
    borderRadius: 16,
    margin: 16,
  },
  title: {
    marginTop: 16,
  },
  message: {
    marginTop: 8,
    textAlign: 'center',
  },
  button: {
    marginTop: 24,
  },
});
