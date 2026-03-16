import { Tabs, useRouter } from 'expo-router';
import { useTheme, Badge } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Platform, Pressable, View } from 'react-native';
import { useUnreadCount } from '../../src/hooks/useNotifications';

type TabIconName = React.ComponentProps<typeof MaterialCommunityIcons>['name'];

function NotificationBell() {
  const theme = useTheme();
  const router = useRouter();
  const { data: count } = useUnreadCount();

  return (
    <Pressable onPress={() => router.push('/stacks/notification-center' as any)} style={{ marginRight: 12, padding: 4 }}>
      <View>
        <MaterialCommunityIcons name="bell-outline" size={22} color={theme.colors.onSurface} />
        {(count ?? 0) > 0 && (
          <Badge size={16} style={{ position: 'absolute', top: -4, right: -6 }}>
            {count! > 99 ? '99+' : count}
          </Badge>
        )}
      </View>
    </Pressable>
  );
}

export default function TabLayout() {
  const theme = useTheme();
  const router = useRouter();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: '#B0BEC5',
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.outlineVariant,
          borderTopWidth: 0.5,
          paddingBottom: Platform.OS === 'ios' ? 0 : 8,
          height: Platform.OS === 'ios' ? 88 : 64,
          elevation: 0,
          shadowOpacity: 0,
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
        headerRight: () => <NotificationBell />,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Wallet',
          headerShown: false,
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons
              name={'credit-card-outline' as TabIconName}
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
              name={'view-grid-outline' as TabIconName}
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
              name={'earth' as TabIconName}
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
