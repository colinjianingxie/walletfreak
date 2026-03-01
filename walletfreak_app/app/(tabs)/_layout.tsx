import { Tabs, useRouter } from 'expo-router';
import { useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Platform, Pressable } from 'react-native';

type TabIconName = React.ComponentProps<typeof MaterialCommunityIcons>['name'];

export default function TabLayout() {
  const theme = useTheme();
  const router = useRouter();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.onSurfaceVariant,
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.outlineVariant,
          paddingBottom: Platform.OS === 'ios' ? 0 : 8,
          height: Platform.OS === 'ios' ? 88 : 64,
        },
        tabBarLabelStyle: {
          fontFamily: 'Outfit-Medium',
          fontSize: 11,
        },
        headerStyle: {
          backgroundColor: theme.colors.surface,
        },
        headerTintColor: theme.colors.onSurface,
        headerTitleStyle: {
          fontFamily: 'Outfit-SemiBold',
        },
        headerShadowVisible: false,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Wallet',
          headerShown: false,
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons
              name={'wallet-outline' as TabIconName}
              size={size}
              color={color}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="tools"
        options={{
          title: 'Tools',
          headerTitle: 'Tools',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons
              name={'calculator-variant-outline' as TabIconName}
              size={size}
              color={color}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="community"
        options={{
          title: 'Community',
          headerShown: false,
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons
              name={'account-group-outline' as TabIconName}
              size={size}
              color={color}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: 'Explore',
          headerShown: false,
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons
              name={'compass-outline' as TabIconName}
              size={size}
              color={color}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          headerTitle: 'Profile',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons
              name={'account-outline' as TabIconName}
              size={size}
              color={color}
            />
          ),
        }}
      />
    </Tabs>
  );
}
