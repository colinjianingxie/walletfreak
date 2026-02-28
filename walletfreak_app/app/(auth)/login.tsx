import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import {
  Text,
  TextInput,
  Button,
  Divider,
  useTheme,
  HelperText,
} from 'react-native-paper';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { loginWithEmail } from '../../src/firebase/auth';
import { isValidEmail } from '../../src/utils/validators';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();
  const theme = useTheme();

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Please enter your email and password.');
      return;
    }
    if (!isValidEmail(email)) {
      setError('Please enter a valid email address.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const credential = await loginWithEmail(email, password);

      if (!credential.user.emailVerified) {
        router.replace('/verify-email' as any);
        return;
      }
      // Auth state listener in useAuth will handle navigation
    } catch (err: any) {
      const code = err?.code;
      if (code === 'auth/user-not-found' || code === 'auth/wrong-password') {
        setError('Invalid email or password.');
      } else if (code === 'auth/invalid-credential') {
        setError('Invalid email or password.');
      } else if (code === 'auth/too-many-requests') {
        setError('Too many attempts. Please try again later.');
      } else {
        setError(err?.message || 'An error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <Text variant="displaySmall" style={[styles.logo, { color: theme.colors.primary }]}>
              WalletFreak
            </Text>
            <Text
              variant="bodyLarge"
              style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}
            >
              Your credit card companion
            </Text>
          </View>

          <View style={styles.form}>
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

            {error ? (
              <HelperText type="error" visible>
                {error}
              </HelperText>
            ) : null}

            <Button
              mode="contained"
              onPress={handleLogin}
              loading={loading}
              disabled={loading}
              style={styles.loginButton}
              contentStyle={styles.buttonContent}
            >
              Sign In
            </Button>

            <Button
              mode="text"
              onPress={() => router.push('/forgot-password' as any)}
              style={styles.forgotButton}
            >
              Forgot Password?
            </Button>

            <Divider style={styles.divider} />

            <Button
              mode="outlined"
              icon="google"
              onPress={() => {
                // Google Sign-In will be implemented with expo-auth-session
              }}
              style={styles.socialButton}
              contentStyle={styles.buttonContent}
            >
              Continue with Google
            </Button>

            {Platform.OS === 'ios' && (
              <Button
                mode="outlined"
                icon="apple"
                onPress={() => {
                  // Apple Sign-In will be implemented with expo-apple-authentication
                }}
                style={styles.socialButton}
                contentStyle={styles.buttonContent}
              >
                Continue with Apple
              </Button>
            )}

            <View style={styles.registerRow}>
              <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
                Don't have an account?
              </Text>
              <Button
                mode="text"
                compact
                onPress={() => router.push('/register' as any)}
              >
                Sign Up
              </Button>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logo: {
    fontFamily: 'Outfit-Bold',
    fontWeight: '700',
  },
  subtitle: {
    marginTop: 8,
  },
  form: {
    width: '100%',
  },
  input: {
    marginBottom: 12,
  },
  loginButton: {
    marginTop: 8,
    borderRadius: 12,
  },
  buttonContent: {
    paddingVertical: 6,
  },
  forgotButton: {
    marginTop: 8,
  },
  divider: {
    marginVertical: 24,
  },
  socialButton: {
    marginBottom: 12,
    borderRadius: 12,
  },
  registerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
  },
});
