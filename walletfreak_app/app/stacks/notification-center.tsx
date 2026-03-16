import React, { useCallback } from 'react';
import { View, FlatList, StyleSheet, Pressable } from 'react-native';
import { Text, useTheme, Divider, ActivityIndicator } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useRouter, Stack } from 'expo-router';
import { useNotifications, useUnreadCount, useMarkRead, useMarkAllRead } from '../../src/hooks/useNotifications';
import type { Notification } from '../../src/api/endpoints/notifications';

function formatTimeAgo(timestamp: any): string {
  if (!timestamp) return '';
  const date = timestamp._seconds
    ? new Date(timestamp._seconds * 1000)
    : new Date(timestamp);
  const now = new Date();
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return date.toLocaleDateString();
}

function notificationIcon(type: string): React.ComponentProps<typeof MaterialCommunityIcons>['name'] {
  switch (type) {
    case 'blog_published':
      return 'newspaper-variant-outline';
    case 'benefit_expiration':
      return 'clock-alert-outline';
    default:
      return 'bell-outline';
  }
}

export default function NotificationCenterScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading, refetch } = useNotifications();
  const { data: unreadCount } = useUnreadCount();
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();

  const notifications = data?.pages.flatMap((p) => p.notifications) ?? [];

  const handlePress = useCallback(
    (item: Notification) => {
      if (!item.read) {
        markRead.mutate(item.id);
      }
      if (item.action_route) {
        router.push(item.action_route as any);
      }
    },
    [markRead, router]
  );

  const renderItem = ({ item }: { item: Notification }) => (
    <Pressable
      onPress={() => handlePress(item)}
      style={[
        styles.item,
        { backgroundColor: item.read ? theme.colors.surface : theme.colors.secondaryContainer + '30' },
      ]}
    >
      <View style={[styles.iconCircle, { backgroundColor: theme.colors.primaryContainer }]}>
        <MaterialCommunityIcons name={notificationIcon(item.type)} size={20} color={theme.colors.primary} />
      </View>
      <View style={styles.itemContent}>
        <Text
          variant="bodyMedium"
          style={{ fontFamily: item.read ? 'Outfit-Regular' : 'Outfit-SemiBold', color: theme.colors.onSurface }}
          numberOfLines={1}
        >
          {item.title}
        </Text>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }} numberOfLines={2}>
          {item.body}
        </Text>
        <Text variant="labelSmall" style={{ color: theme.colors.outline, marginTop: 2 }}>
          {formatTimeAgo(item.created_at)}
        </Text>
      </View>
      {!item.read && <View style={[styles.unreadDot, { backgroundColor: theme.colors.primary }]} />}
    </Pressable>
  );

  return (
    <>
      <Stack.Screen
        options={{
          title: 'Notifications',
          headerRight: () =>
            (unreadCount ?? 0) > 0 ? (
              <Pressable onPress={() => markAllRead.mutate()} style={{ marginRight: 8, padding: 4 }}>
                <MaterialCommunityIcons name="check-all" size={22} color={theme.colors.primary} />
              </Pressable>
            ) : null,
        }}
      />
      <FlatList
        data={notifications}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        ItemSeparatorComponent={() => <Divider />}
        contentContainerStyle={notifications.length === 0 ? styles.emptyContainer : undefined}
        ListEmptyComponent={
          isLoading ? (
            <ActivityIndicator style={{ marginTop: 40 }} />
          ) : (
            <View style={styles.empty}>
              <MaterialCommunityIcons name="bell-off-outline" size={48} color={theme.colors.outline} />
              <Text variant="bodyLarge" style={{ color: theme.colors.onSurfaceVariant, marginTop: 12 }}>
                No notifications yet
              </Text>
            </View>
          )
        }
        onEndReached={() => {
          if (hasNextPage && !isFetchingNextPage) fetchNextPage();
        }}
        onEndReachedThreshold={0.5}
        onRefresh={refetch}
        refreshing={false}
        ListFooterComponent={isFetchingNextPage ? <ActivityIndicator style={{ padding: 16 }} /> : null}
        style={{ backgroundColor: theme.colors.background }}
      />
    </>
  );
}

const styles = StyleSheet.create({
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    gap: 12,
  },
  iconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  itemContent: {
    flex: 1,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  empty: {
    alignItems: 'center',
    paddingTop: 80,
  },
});
