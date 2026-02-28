import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { Text, TextInput, Button, useTheme, HelperText } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { registerWithEmail } from '../../src/firebase/auth';
import { isValidEmail, isValidPassword, getPasswordStrength } from '../../src/utils/validators';

export default function RegisterScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();
  const theme = useTheme();

  const passwordStrength = getPasswordStrength(password);

  const handleRegister = async () => {
    if (!email || !password || !confirmPassword) {
      setError('Please fill in all fields.');
      return;
    }
    if (!isValidEmail(email)) {
      setError('Please enter a valid email address.');
      return;
    }
    if (!isValidPassword(password)) {
      setError('Password must be at least 6 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await registerWithEmail(email, password);
      router.replace('/verify-email' as any);
    } catch (err: any) {
      const code = err?.code;
      if (code === 'auth/email-already-in-use') {
        setError('An account with this email already exists.');
      } else if (code === 'auth/weak-password') {
        setError('Password is too weak. Please use a stronger password.');
      } else {
        setError(err?.message || 'An error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const strengthColor =
    passwordStrength === 'strong'
      ? theme.colors.primary
      : passwordStrength === 'medium'
        ? '#ED6C02'
        : theme.colors.error;

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.form}>
          <Text variant="headlineMedium" style={styles.title}>
            Create Account
          </Text>
          <Text
            variant="bodyMedium"
            style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}
          >
            Start managing your credit card wallet
          </Text>

          <TextInput
            label="Email"
            value={email}
            onChangeText={(text) => {
              setEmail(text);
              setError('');
            }}
            mode="outlined"
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            left={<TextInput.Icon icon="email-outline" />}
            style={styles.input}
          />

          <TextInput
            label="Password"
            value={password}
            onChangeText={(text) => {
              setPassword(text);
              setError('');
            }}
            mode="outlined"
            secureTextEntry={!showPassword}
            left={<TextInput.Icon icon="lock-outline" />}
            right={
              <TextInput.Icon
                icon={showPassword ? 'eye-off' : 'eye'}
                onPress={() => setShowPassword(!showPassword)}
              />
            }
            style={styles.input}
          />

          {password.length > 0 && (
            <View style={styles.strengthRow}>
              <View
                style={[
                  styles.strengthBar,
                  {
                    backgroundColor: strengthColor,
                    width: passwordStrength === 'strong' ? '100%' : passwordStrength === 'medium' ? '66%' : '33%',
                  },
                ]}
              />
              <Text variant="labelSmall" style={{ color: strengthColor, marginLeft: 8 }}>
                {passwordStrength}
              </Text>
            </View>
          )}

          <TextInput
            label="Confirm Password"
            value={confirmPassword}
            onChangeText={(text) => {
              setConfirmPassword(text);
              setError('');
            }}
            mode="outlined"
            secureTextEntry={!showPassword}
            left={<TextInput.Icon icon="lock-check-outline" />}
            style={styles.input}
          />

          {error ? (
            <HelperText type="error" visible>
              {error}
            </HelperText>
          ) : null}

          <Button
            mode="contained"
            onPress={handleRegister}
            loading={loading}
            disabled={loading}
            style={styles.registerButton}
            contentStyle={styles.buttonContent}
          >
            Create Account
          </Button>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 24,
  },
  form: {
    width: '100%',
  },
  title: {
    fontFamily: 'Outfit-SemiBold',
    marginBottom: 4,
  },
  subtitle: {
    marginBottom: 24,
  },
  input: {
    marginBottom: 12,
  },
  strengthRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    marginTop: -4,
  },
  strengthBar: {
    height: 4,
    borderRadius: 2,
    flex: 1,
    maxWidth: 120,
  },
  registerButton: {
    marginTop: 8,
    borderRadius: 12,
  },
  buttonContent: {
    paddingVertical: 6,
  },
});
