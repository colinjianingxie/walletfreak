import { Stack, useRouter } from 'expo-router';
import { Pressable } from 'react-native';
import { useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';

export default function StacksLayout() {
  const theme = useTheme();
  const router = useRouter();

  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: theme.colors.surface },
        headerTintColor: theme.colors.onSurface,
        headerTitleStyle: { fontFamily: 'Outfit-Medium' },
        headerShadowVisible: false,
        headerLeft: ({ tintColor }) => (
          <Pressable onPress={() => router.back()} style={{ marginLeft: 8, padding: 4 }}>
            <MaterialCommunityIcons name="arrow-left" size={24} color={tintColor ?? theme.colors.onSurface} />
          </Pressable>
        ),
      }}
    >
      <Stack.Screen name="card-detail/[slug]" options={{ title: 'Card Details' }} />
      <Stack.Screen name="personality/[slug]" options={{ title: 'Personality' }} />
      <Stack.Screen name="personality-list" options={{ title: 'Personalities' }} />
      <Stack.Screen name="blog/[slug]" options={{ title: 'Blog Post', headerShown: false }} />
      <Stack.Screen name="datapoint-submit" options={{ title: 'Submit Data Point' }} />
      <Stack.Screen name="worth-it/[slug]" options={{ title: 'Worth It?' }} />
      <Stack.Screen name="worth-it-list" options={{ title: 'Worth It? Calculator' }} />
      <Stack.Screen name="worth-it-audit" options={{ title: 'Worth It? Audit' }} />
      <Stack.Screen name="spend-optimizer" options={{ title: 'Spend Optimizer' }} />
      <Stack.Screen name="spend-optimizer-step2" options={{ title: 'Spend Optimizer' }} />
      <Stack.Screen name="spend-optimizer-results" options={{ title: 'Results' }} />
      <Stack.Screen
        name="sub-optimizer"
        options={{
          title: 'SUB Optimizer',
          headerStyle: { backgroundColor: '#0F0F1A' },
          headerTintColor: '#FFFFFF',
        }}
      />
      <Stack.Screen name="sub-optimizer-results" options={{ title: 'Results' }} />
      <Stack.Screen
        name="booking-optimizer"
        options={{
          title: 'Booking Optimizer',
          headerRight: () => (
            <Pressable
              onPress={() => router.push('/stacks/booking-history' as any)}
              style={{ marginRight: 8, padding: 4 }}
            >
              <MaterialCommunityIcons name="clipboard-text-clock-outline" size={22} color={theme.colors.primary} />
            </Pressable>
          ),
        }}
      />
      <Stack.Screen name="booking-strategy/[id]" options={{ title: 'Strategy Report' }} />
      <Stack.Screen name="booking-history" options={{ title: 'Booking History' }} />
      <Stack.Screen name="award-scout" options={{ title: 'Award Scout' }} />
      <Stack.Screen name="subscription" options={{ title: 'Premium' }} />
      <Stack.Screen name="points-collection" options={{ title: 'Points Collection' }} />
      <Stack.Screen name="compare-cards" options={{ title: 'Compare Cards' }} />
      <Stack.Screen name="settings" options={{ title: 'Settings' }} />
      <Stack.Screen name="notifications" options={{ title: 'Notifications' }} />
      <Stack.Screen name="personality-quiz" options={{ title: 'Freak Quiz' }} />
      <Stack.Screen name="wallet-card/[userCardId]" options={{ title: 'Card Benefits', headerShown: false }} />
      <Stack.Screen name="privacy-policy" options={{ title: 'Privacy Policy' }} />
      <Stack.Screen name="terms-of-service" options={{ title: 'Terms of Service' }} />
    </Stack>
  );
}
