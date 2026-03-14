import React, { useCallback, useRef, useState } from 'react';
import { View, StyleSheet, FlatList, Pressable, Animated, Alert } from 'react-native';
import { Text, useTheme, ActivityIndicator } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Swipeable } from 'react-native-gesture-handler';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { useStrategies, useDeleteStrategy } from '../../src/hooks/useBooking';
import type { BookingStrategyListItem } from '../../src/types/booking';

const STATUS_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  ready: { icon: 'check-circle', color: '#16A34A', label: 'Ready' },
  processing: { icon: 'progress-clock', color: '#D97706', label: 'Analyzing...' },
  failed: { icon: 'alert-circle', color: '#DC2626', label: 'Failed' },
};

export default function BookingHistoryScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { data, isLoading, isError, refetch } = useStrategies(true);
  const deleteMutation = useDeleteStrategy();
  const strategies = data?.strategies ?? [];
  const hasProcessing = strategies.some((s) => s.status === 'processing');
  const swipeableRefs = useRef<Map<string, Swipeable>>(new Map());
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = useCallback((id: string) => {
    Alert.alert(
      'Delete Strategy',
      'Are you sure you want to delete this strategy?',
      [
        { text: 'Cancel', style: 'cancel', onPress: () => swipeableRefs.current.get(id)?.close() },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            setDeletingId(id);
            deleteMutation.mutate(id, {
              onSettled: () => setDeletingId(null),
            });
          },
        },
      ]
    );
  }, [deleteMutation]);

  const renderRightActions = useCallback((id: string) => {
    return (
      <Pressable
        onPress={() => handleDelete(id)}
        style={styles.deleteAction}
      >
        <MaterialCommunityIcons name="trash-can-outline" size={22} color="#FFFFFF" />
        <Text style={styles.deleteText}>Delete</Text>
      </Pressable>
    );
  }, [handleDelete]);

  if (isLoading) {
    return <LoadingState message="Loading strategies..." />;
  }

  if (isError) {
    return (
      <EmptyState
        icon="alert-circle-outline"
        title="Something went wrong"
        message="Could not load your booking history."
        actionLabel="Retry"
        onAction={() => refetch()}
      />
    );
  }

  if (strategies.length === 0) {
    return (
      <EmptyState
        icon="bed-outline"
        title="No strategies yet"
        message="Search for hotels and analyze booking strategies to see them here."
        actionLabel="Start Searching"
        onAction={() => router.push('/stacks/booking-optimizer' as any)}
      />
    );
  }

  const renderItem = ({ item }: { item: BookingStrategyListItem }) => {
    const config = STATUS_CONFIG[item.status] || STATUS_CONFIG.failed;
    const isProcessing = item.status === 'processing';
    const isDeleting = deletingId === item.id;

    return (
      <Swipeable
        ref={(ref) => { if (ref) swipeableRefs.current.set(item.id, ref); }}
        renderRightActions={() => renderRightActions(item.id)}
        overshootRight={false}
        enabled={!isProcessing && !isDeleting}
      >
        <Pressable
          onPress={() => {
            if (!isProcessing && !isDeleting) {
              router.push(`/stacks/booking-strategy/${item.id}` as any);
            }
          }}
          style={[styles.card, isProcessing && styles.cardProcessing, isDeleting && styles.cardDeleting]}
        >
          {isProcessing && <View style={styles.processingBar} />}

          {isDeleting && (
            <View style={styles.deletingOverlay}>
              <ActivityIndicator size={20} color="#DC2626" />
              <Text style={styles.deletingText}>Deleting...</Text>
            </View>
          )}

          <View style={isDeleting ? { opacity: 0.3 } : undefined}>
            <View style={styles.cardHeader}>
              <View style={{ flex: 1 }}>
                <Text style={styles.location}>{item.location_text || 'Unknown Location'}</Text>
                <Text style={styles.dates}>
                  {item.check_in} → {item.check_out} · {item.guests} guest{item.guests !== '1' ? 's' : ''}
                </Text>
              </View>
              <View style={[styles.statusBadge, { backgroundColor: config.color + '15' }]}>
                {isProcessing ? (
                  <ActivityIndicator size={10} color={config.color} />
                ) : (
                  <MaterialCommunityIcons name={config.icon as any} size={12} color={config.color} />
                )}
                <Text style={[styles.statusText, { color: config.color }]}>{config.label}</Text>
              </View>
            </View>

            <View style={styles.cardFooter}>
              <Text style={styles.hotelCount}>
                {item.hotel_count} hotel{item.hotel_count !== 1 ? 's' : ''}
              </Text>
              {isProcessing ? (
                <Text style={styles.processingHint}>AI is analyzing...</Text>
              ) : (
                <MaterialCommunityIcons name="chevron-right" size={18} color="#94A3B8" />
              )}
            </View>
          </View>
        </Pressable>
      </Swipeable>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {hasProcessing && (
        <View style={styles.pollingBanner}>
          <ActivityIndicator size={14} color="#6366F1" />
          <Text style={styles.pollingText}>
            Strategies are being analyzed. This page updates automatically.
          </Text>
        </View>
      )}
      <FlatList
        data={strategies}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  pollingBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  pollingText: {
    fontSize: 12,
    fontFamily: 'Outfit-Medium',
    color: '#6366F1',
    flex: 1,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 40,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    overflow: 'hidden',
  },
  cardProcessing: {
    borderColor: '#D97706',
    borderWidth: 1.5,
  },
  cardDeleting: {
    opacity: 1,
  },
  deletingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255,255,255,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
    borderRadius: 14,
    flexDirection: 'row',
    gap: 8,
  },
  deletingText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    color: '#DC2626',
  },
  processingBar: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
    backgroundColor: '#D97706',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  location: {
    fontSize: 15,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  dates: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#64748B',
    marginTop: 2,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  statusText: {
    fontSize: 10,
    fontFamily: 'Outfit-Bold',
    letterSpacing: 0.3,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingTop: 10,
  },
  hotelCount: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#94A3B8',
  },
  processingHint: {
    fontSize: 11,
    fontFamily: 'Outfit',
    color: '#D97706',
    fontStyle: 'italic',
  },
  deleteAction: {
    backgroundColor: '#DC2626',
    justifyContent: 'center',
    alignItems: 'center',
    width: 80,
    borderRadius: 14,
    marginBottom: 12,
    marginLeft: 8,
  },
  deleteText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontFamily: 'Outfit-Medium',
    marginTop: 4,
  },
});
