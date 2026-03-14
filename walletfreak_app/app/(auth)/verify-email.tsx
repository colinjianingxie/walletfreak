import React, { useState, useEffect, useCallback } from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button, useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { firebaseAuth } from '../../src/firebase/config';
import { resendVerification, logout } from '../../src/firebase/auth';

export default function VerifyEmailScreen() {
  const [checking, setChecking] = useState(false);
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);
  const router = useRouter();
  const theme = useTheme();

  const checkVerification = useCallback(async () => {
    setChecking(true);
    try {
      await firebaseAuth.currentUser?.reload();
      if (firebaseAuth.currentUser?.emailVerified) {
        // User is now verified - auth listener will navigate
        return;
      }
    } catch (err) {
      console.error('Error checking verification:', err);
    } finally {
      setChecking(false);
    }
  }, []);

  // Poll for verification every 3 seconds
  useEffect(() => {
    const interval = setInterval(checkVerification, 3000);
    return () => clearInterval(interval);
  }, [checkVerification]);

  const handleResend = async () => {
    setResending(true);
    try {
      await resendVerification();
      setResent(true);
      setTimeout(() => setResent(false), 5000);
    } catch {
      // Silently fail
    } finally {
      setResending(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.replace('/login' as any);
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <MaterialCommunityIcons
        name="email-check-outline"
        size={80}
        color={theme.colors.primary}
      />
      <Text variant="headlineMedium" style={styles.title}>
        Verify Your Email
      </Text>
      <Text
        variant="bodyMedium"
        style={[styles.message, { color: theme.colors.onSurfaceVariant }]}
      >
        We've sent a verification email to{'\n'}
        <Text style={{ fontWeight: '600' }}>
          {firebaseAuth.currentUser?.email}
        </Text>
        {'\n\n'}
        Please check your inbox and click the verification link.
      </Text>

      <Button
        mode="contained"
        onPress={checkVerification}
        loading={checking}
        disabled={checking}
        style={styles.button}
      >
        I've Verified My Email
      </Button>

      <Button
        mode="outlined"
        onPress={handleResend}
        loading={resending}
        disabled={resending || resent}
        style={styles.button}
      >
        {resent ? 'Email Sent!' : 'Resend Verification Email'}
      </Button>

      <Button mode="text" onPress={handleLogout} style={styles.logoutButton}>
        Use a Different Account
      </Button>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  title: {
    fontFamily: 'Outfit-SemiBold',
    marginTop: 24,
    textAlign: 'center',
  },
  message: {
    marginTop: 12,
    textAlign: 'center',
    lineHeight: 22,
  },
  button: {
    marginTop: 16,
    width: '100%',
    borderRadius: 12,
  },
  logoutButton: {
    marginTop: 24,
  },
});
