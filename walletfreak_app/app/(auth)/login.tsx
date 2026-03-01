import React, { useState, useEffect } from 'react';
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
import {
  useAuthRequest,
  exchangeCodeAsync,
} from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';
import {
  loginWithEmail,
  loginWithGoogleCredential,
  GOOGLE_IOS_CLIENT_ID,
} from '../../src/firebase/auth';
import { isValidEmail } from '../../src/utils/validators';

WebBrowser.maybeCompleteAuthSession();

const googleDiscovery = {
  authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
  tokenEndpoint: 'https://oauth2.googleapis.com/token',
  revocationEndpoint: 'https://oauth2.googleapis.com/revoke',
};

// iOS client redirect URI: reverse-DNS of the client ID
const IOS_REDIRECT_URI =
  `com.googleusercontent.apps.${GOOGLE_IOS_CLIENT_ID.split('.apps.googleusercontent.com')[0]}:/oauthredirect`;

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();
  const theme = useTheme();

  const [request, response, promptAsync] = useAuthRequest(
    {
      clientId: GOOGLE_IOS_CLIENT_ID,
      redirectUri: IOS_REDIRECT_URI,
      scopes: ['openid', 'profile', 'email'],
    },
    googleDiscovery,
  );

  useEffect(() => {
    if (response?.type === 'success' && request?.codeVerifier) {
      const { code } = response.params;
      setGoogleLoading(true);
      setError('');

      exchangeCodeAsync(
        {
          clientId: GOOGLE_IOS_CLIENT_ID,
          code,
          redirectUri: IOS_REDIRECT_URI,
          extraParams: { code_verifier: request.codeVerifier },
        },
        googleDiscovery,
      )
        .then((tokenResponse) => {
          if (tokenResponse.idToken) {
            return loginWithGoogleCredential(tokenResponse.idToken);
          }
          throw new Error('No ID token received from Google.');
        })
        .catch((err: any) => {
          setError(err?.message || 'Google sign-in failed. Please try again.');
        })
        .finally(() => setGoogleLoading(false));
    } else if (response?.type === 'error') {
      setError(response.error?.message || 'Google sign-in failed.');
    }
  }, [response]);

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

  const handleGoogleSignIn = () => {
    setError('');
    promptAsync();
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
              onPress={handleGoogleSignIn}
              loading={googleLoading}
              disabled={!request || googleLoading || loading}
              style={styles.socialButton}
              contentStyle={styles.buttonContent}
            >
              Continue with Google
            </Button>

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
