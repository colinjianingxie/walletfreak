import React, { useState, useRef, useCallback, useMemo } from 'react';
import { View, StyleSheet, Pressable, Image, ScrollView, RefreshControl, ActivityIndicator } from 'react-native';
import { Text, Searchbar, useTheme } from 'react-native-paper';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  useAnimatedScrollHandler,
  interpolate,
  Extrapolation,
} from 'react-native-reanimated';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import BottomSheet, { BottomSheetScrollView } from '@gorhom/bottom-sheet';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { CardImage } from '../../src/components/ui/CardImage';
import { useBlogPosts } from '../../src/hooks/useBlog';
import { useDatapoints, useVoteDatapoint, useMarkOutdated } from '../../src/hooks/useDatapoints';
import { formatDate, formatRelativeTime } from '../../src/utils/formatters';
import type { BlogPost } from '../../src/types/blog';

const COLLAPSE_DISTANCE = 100;

const estimateReadTime = (content?: string): number => {
  if (!content) return 3;
  const words = content.split(/\s+/).length;
  return Math.max(1, Math.ceil(words / 200));
};

// Quick filter categories shown as pills below search
const QUICK_FILTERS = ['All', 'Reviews', 'Guides', 'News', 'Strategy', 'Travel'];

// Blog tag taxonomy groups (for advanced filter sheet)
const TAG_GROUPS = [
  { label: 'Ecosystem', tags: ['American Express', 'Chase', 'Citi'] },
  { label: 'Content Type', tags: ['guide', 'review', 'lounges', 'savings', 'strategy', 'tips'] },
  { label: 'Experience Level', tags: ['Beginner', 'Intermediate', 'Advanced'] },
  { label: 'Read Time', tags: ['Short (< 3m)', 'Medium (3-7m)', 'Long (7m+)', 'Video Only'] },
];

// Quick filter categories for datapoints
const DP_QUICK_FILTERS = ['All', 'Amex', 'Chase', 'Citi', 'Hyatt', 'Credits', 'Retention'];

// Datapoint sort options
const DP_SORT_OPTIONS = [
  { label: 'Newest', value: 'newest' },
  { label: 'Most Helpful', value: 'votes' },
];

export default function CommunityScreen() {
  const [segment, setSegment] = useState<'blog' | 'datapoints'>('blog');
  const [search, setSearch] = useState('');
  const [quickFilter, setQuickFilter] = useState('All');
  const [category, setCategory] = useState('');
  const [selectedTag, setSelectedTag] = useState('');
  const [showSaved, setShowSaved] = useState(false);
  // Datapoint filters
  const [dpQuickFilter, setDpQuickFilter] = useState('All');
  const [dpSort, setDpSort] = useState('newest');
  const [dpCard, setDpCard] = useState('');
  const [dpBenefit, setDpBenefit] = useState('');
  const filterSheetRef = useRef<BottomSheet>(null);
  const router = useRouter();
  const theme = useTheme();
  const insets = useSafeAreaInsets();

  const scrollY = useSharedValue(0);
  const scrollHandler = useAnimatedScrollHandler({
    onScroll: (event) => {
      scrollY.value = event.contentOffset.y;
    },
  });

  const effectiveCategory = quickFilter !== 'All' ? quickFilter : (category || undefined);
  const { data: blogData, isLoading: blogLoading, isFetching: blogFetching, refetch: refetchBlogs } = useBlogPosts({
    search: search || undefined,
    category: effectiveCategory,
    tag: selectedTag || undefined,
    saved: showSaved || undefined,
  });
  const { data: dpData, isLoading: dpLoading } = useDatapoints({
    sort: dpSort || undefined,
    card: dpCard || undefined,
    benefit: dpBenefit || undefined,
  });
  const voteDatapoint = useVoteDatapoint();
  const markOutdated = useMarkOutdated();

  const availableCategories = useMemo(() => {
    return blogData?.categories ?? [];
  }, [blogData]);

  // Collect unique card names & benefit types from datapoints for filter chips
  const dpFilterOptions = useMemo(() => {
    const cards = new Set<string>();
    const benefits = new Set<string>();
    (dpData?.datapoints ?? []).forEach((dp: any) => {
      if (dp.card_name) cards.add(dp.card_name);
      if (dp.benefit) benefits.add(dp.benefit);
    });
    return { cards: Array.from(cards).sort(), benefits: Array.from(benefits).sort() };
  }, [dpData]);

  // Client-side filtering for datapoint quick filters
  const filteredDatapoints = useMemo(() => {
    const all = dpData?.datapoints ?? [];
    if (dpQuickFilter === 'All') return all;
    const q = dpQuickFilter.toLowerCase();
    return all.filter((dp: any) => {
      const name = (dp.card_name || '').toLowerCase();
      const benefit = (dp.benefit || '').toLowerCase();
      return name.includes(q) || benefit.includes(q);
    });
  }, [dpData, dpQuickFilter]);

  const activeFilterCount = segment === 'blog'
    ? (selectedTag ? 1 : 0) + (showSaved ? 1 : 0)
    : (dpCard ? 1 : 0) + (dpBenefit ? 1 : 0) + (dpSort !== 'newest' ? 1 : 0);

  const handleBlogPress = (post: BlogPost) => {
    router.push(`/stacks/blog/${post.slug}` as any);
  };

  const handleOpenFilters = useCallback(() => {
    filterSheetRef.current?.snapToIndex(0);
  }, []);

  const handleClearFilters = useCallback(() => {
    setQuickFilter('All');
    setCategory('');
    setSelectedTag('');
    setShowSaved(false);
    setDpQuickFilter('All');
    setDpSort('newest');
    setDpCard('');
    setDpBenefit('');
    filterSheetRef.current?.close();
  }, []);

  const handleSegmentSwitch = useCallback((seg: 'blog' | 'datapoints') => {
    setSegment(seg);
    scrollY.value = 0;
  }, [scrollY]);

  // --- Animated Styles ---
  const animatedTitle = useAnimatedStyle(() => ({
    fontSize: interpolate(scrollY.value, [0, COLLAPSE_DISTANCE], [28, 20], Extrapolation.CLAMP),
  }));

  const animatedSearchRow = useAnimatedStyle(() => ({
    height: interpolate(scrollY.value, [0, 60], [56, 0], Extrapolation.CLAMP),
    opacity: interpolate(scrollY.value, [0, 60], [1, 0], Extrapolation.CLAMP),
    overflow: 'hidden' as const,
  }));

  const animatedFilterChips = useAnimatedStyle(() => ({
    height: interpolate(scrollY.value, [0, 60], [44, 0], Extrapolation.CLAMP),
    opacity: interpolate(scrollY.value, [0, 60], [1, 0], Extrapolation.CLAMP),
    overflow: 'hidden' as const,
  }));

  const renderBlogItem = ({ item }: { item: BlogPost }) => {
    const readTime = estimateReadTime(item.content || item.excerpt);
    const netVotes = (item.upvotes ?? 0) - (item.downvotes ?? 0);
    const tagLabel = (() => {
      const tags: any = item.tags;
      if (Array.isArray(tags) && tags.length > 0) return String(tags[0]).toUpperCase();
      if (typeof tags === 'string' && tags.trim()) return tags.split(',')[0].trim().toUpperCase();
      return (item.category || '').toUpperCase();
    })();

    return (
      <Pressable
        style={[styles.articleCard, { backgroundColor: theme.colors.surface }]}
        onPress={() => handleBlogPress(item)}
      >
        {item.image_url ? (
          <Image
            source={{ uri: item.image_url }}
            style={styles.articleImage}
            resizeMode="cover"
          />
        ) : (
          <View style={[styles.articleImage, styles.thumbnailPlaceholder, { backgroundColor: theme.colors.surfaceVariant }]}>
            <MaterialCommunityIcons name="newspaper-variant-outline" size={40} color={theme.colors.onSurfaceVariant} />
          </View>
        )}

        <View style={styles.articleContent}>
          <View style={styles.articleMeta}>
            <View style={[styles.categoryBadge, { backgroundColor: '#3B5998' }]}>
              <Text style={styles.categoryBadgeText}>{tagLabel}</Text>
            </View>
            <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
              {formatDate(item.created_at)}
            </Text>
          </View>
          <Text variant="titleMedium" numberOfLines={3} style={styles.articleTitle}>
            {item.title}
          </Text>
          {item.excerpt && (
            <Text variant="bodySmall" numberOfLines={2} style={{ color: theme.colors.onSurfaceVariant, marginBottom: 10 }}>
              {item.excerpt}
            </Text>
          )}
          <View style={styles.articleFooter}>
            <View style={styles.articleStats}>
              <View style={styles.statItem}>
                <MaterialCommunityIcons name="thumb-up-outline" size={14} color={theme.colors.onSurfaceVariant} />
                <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>{netVotes}</Text>
              </View>
              <View style={styles.statItem}>
                <MaterialCommunityIcons name="comment-outline" size={14} color={theme.colors.onSurfaceVariant} />
                <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>{item.comment_count ?? 0}</Text>
              </View>
            </View>
            <View style={styles.statItem}>
              <MaterialCommunityIcons name="clock-outline" size={14} color={theme.colors.onSurfaceVariant} />
              <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
                {readTime} min read
              </Text>
            </View>
          </View>
        </View>
      </Pressable>
    );
  };

  const renderDatapointItem = ({ item }: { item: any }) => {
    return (
      <View style={[styles.dpCard, { backgroundColor: theme.colors.surface }]}>
        {/* Header: User + Date */}
        <View style={styles.dpHeader}>
          <Text style={styles.dpUsername}>@{item.author_name || 'Anonymous'}</Text>
          <Text style={styles.dpTimestamp}>{formatDate(item.created_at)}</Text>
        </View>

        {/* Content / title */}
        {item.data ? (
          <Text style={styles.dpContent}>{item.data}</Text>
        ) : null}

        {/* Card info box */}
        <View style={[styles.dpInfoBox, { backgroundColor: theme.colors.background }]}>
          <View style={styles.dpInfoRow}>
            <View style={styles.dpCardRow}>
              {item.card_slug ? (
                <CardImage slug={item.card_slug} size="small" />
              ) : null}
              <Text style={[styles.dpCardName, { color: theme.colors.onSurface }]} numberOfLines={1} ellipsizeMode="tail">
                {item.card_name || 'Unknown Card'}
              </Text>
            </View>
            <View style={[
              styles.dpStatusBadge,
              { backgroundColor: item.status === 'Success' ? '#ECFDF5' : '#FEF2F2' },
            ]}>
              <MaterialCommunityIcons
                name={item.status === 'Success' ? 'check-circle-outline' : 'close-circle-outline'}
                size={14}
                color={item.status === 'Success' ? '#16A34A' : '#DC2626'}
              />
              <Text style={[
                styles.dpStatusText,
                { color: item.status === 'Success' ? '#16A34A' : '#DC2626' },
              ]}>
                {item.status || 'Success'}
              </Text>
            </View>
          </View>
          {item.benefit ? (
            <View style={styles.dpBenefitTag}>
              <MaterialCommunityIcons name="lightning-bolt" size={12} color="#4361EE" />
              <Text style={styles.dpBenefitTagText}>{item.benefit.toUpperCase()}</Text>
            </View>
          ) : null}
        </View>

        {/* Footer: Works / Outdated pill buttons */}
        <View style={styles.dpFooter}>
          <Pressable
            style={[
              styles.dpFooterPill,
              item.user_voted && styles.dpFooterPillActiveGreen,
            ]}
            onPress={() => voteDatapoint.mutate(item.id)}
            disabled={voteDatapoint.isPending && voteDatapoint.variables === item.id}
          >
            {voteDatapoint.isPending && voteDatapoint.variables === item.id ? (
              <ActivityIndicator size={14} color="#16A34A" />
            ) : (
              <MaterialCommunityIcons
                name={item.user_voted ? 'thumb-up' : 'thumb-up-outline'}
                size={16}
                color={item.user_voted ? '#16A34A' : '#94A3B8'}
              />
            )}
            <Text style={[styles.dpFooterPillText, item.user_voted && { color: '#16A34A' }]}>
              Works
            </Text>
          </Pressable>
          <Pressable
            style={[
              styles.dpFooterPill,
              item.user_outdated && styles.dpFooterPillActiveRed,
            ]}
            onPress={() => markOutdated.mutate(item.id)}
            disabled={markOutdated.isPending && markOutdated.variables === item.id}
          >
            {markOutdated.isPending && markOutdated.variables === item.id ? (
              <ActivityIndicator size={14} color="#F59E0B" />
            ) : (
              <MaterialCommunityIcons
                name="alert-circle-outline"
                size={16}
                color={item.user_outdated ? '#F59E0B' : '#94A3B8'}
              />
            )}
            <Text style={[styles.dpFooterPillText, item.user_outdated && { color: '#F59E0B' }]}>
              Outdated
            </Text>
          </Pressable>
        </View>
      </View>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Collapsible Header */}
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <View style={styles.headerTitleRow}>
          <Animated.Text style={[styles.headerTitle, animatedTitle]}>Community</Animated.Text>
          <View style={styles.headerIcons}>
            <Pressable
              style={[styles.toggleIcon, segment === 'blog' && styles.toggleIconActive]}
              onPress={() => handleSegmentSwitch('blog')}
            >
              <MaterialCommunityIcons
                name="book-open-variant"
                size={22}
                color={segment === 'blog' ? theme.colors.primary : theme.colors.onSurfaceVariant}
              />
            </Pressable>
            <Pressable
              style={[styles.toggleIcon, segment === 'datapoints' && styles.toggleIconActive]}
              onPress={() => handleSegmentSwitch('datapoints')}
            >
              <MaterialCommunityIcons
                name="chart-bar"
                size={22}
                color={segment === 'datapoints' ? theme.colors.primary : theme.colors.onSurfaceVariant}
              />
            </Pressable>
          </View>
        </View>
      </View>

      {/* Search + Filter */}
      <View style={styles.searchRow}>
        <Searchbar
          placeholder={segment === 'blog' ? 'Search articles...' : 'Search data points...'}
          onChangeText={setSearch}
          value={search}
          style={styles.searchbar}
          inputStyle={{ fontFamily: 'Outfit' }}
        />
        <Pressable
          style={[
            styles.filterButton,
            { borderColor: activeFilterCount > 0 ? theme.colors.primary : theme.colors.outlineVariant },
            activeFilterCount > 0 && { backgroundColor: 'rgba(103, 80, 164, 0.08)' },
          ]}
          onPress={handleOpenFilters}
        >
          <MaterialCommunityIcons
            name="filter-variant"
            size={20}
            color={activeFilterCount > 0 ? theme.colors.primary : theme.colors.onSurfaceVariant}
          />
          {activeFilterCount > 0 && (
            <View style={styles.filterBadge}>
              <Text style={styles.filterBadgeText}>{activeFilterCount}</Text>
            </View>
          )}
        </Pressable>
      </View>

      {/* Quick filter pills */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.quickFilterRow}
        contentContainerStyle={styles.quickFilterContent}
      >
        {(segment === 'blog' ? QUICK_FILTERS : DP_QUICK_FILTERS).map((filter) => {
          const isActive = segment === 'blog' ? quickFilter === filter : dpQuickFilter === filter;
          return (
            <Pressable
              key={filter}
              style={[
                styles.quickFilterChip,
                isActive
                  ? styles.quickFilterChipActive
                  : { borderColor: theme.colors.outlineVariant },
              ]}
              onPress={() => segment === 'blog' ? setQuickFilter(filter) : setDpQuickFilter(filter)}
            >
              <Text
                style={[
                  styles.quickFilterText,
                  { color: isActive ? '#FFFFFF' : theme.colors.onSurfaceVariant },
                ]}
              >
                {filter}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>

      {/* Active advanced filter chips */}
      {activeFilterCount > 0 && (
        <View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.activeFiltersRow} contentContainerStyle={styles.activeFiltersContent}>
            {segment === 'blog' ? (
              <>
                {showSaved && (
                  <Pressable
                    style={[styles.activeChip, { backgroundColor: theme.colors.primaryContainer }]}
                    onPress={() => setShowSaved(false)}
                  >
                    <Text style={[styles.activeChipText, { color: theme.colors.onPrimaryContainer }]}>Saved</Text>
                    <MaterialCommunityIcons name="close" size={14} color={theme.colors.onPrimaryContainer} />
                  </Pressable>
                )}
                {selectedTag ? (
                  <Pressable
                    style={[styles.activeChip, { backgroundColor: theme.colors.primaryContainer }]}
                    onPress={() => setSelectedTag('')}
                  >
                    <Text style={[styles.activeChipText, { color: theme.colors.onPrimaryContainer }]}>{selectedTag}</Text>
                    <MaterialCommunityIcons name="close" size={14} color={theme.colors.onPrimaryContainer} />
                  </Pressable>
                ) : null}
              </>
            ) : (
              <>
                {dpCard ? (
                  <Pressable
                    style={[styles.activeChip, { backgroundColor: theme.colors.primaryContainer }]}
                    onPress={() => setDpCard('')}
                  >
                    <Text style={[styles.activeChipText, { color: theme.colors.onPrimaryContainer }]}>{dpCard}</Text>
                    <MaterialCommunityIcons name="close" size={14} color={theme.colors.onPrimaryContainer} />
                  </Pressable>
                ) : null}
                {dpBenefit ? (
                  <Pressable
                    style={[styles.activeChip, { backgroundColor: theme.colors.primaryContainer }]}
                    onPress={() => setDpBenefit('')}
                  >
                    <Text style={[styles.activeChipText, { color: theme.colors.onPrimaryContainer }]}>{dpBenefit}</Text>
                    <MaterialCommunityIcons name="close" size={14} color={theme.colors.onPrimaryContainer} />
                  </Pressable>
                ) : null}
                {dpSort !== 'newest' ? (
                  <Pressable
                    style={[styles.activeChip, { backgroundColor: theme.colors.primaryContainer }]}
                    onPress={() => setDpSort('newest')}
                  >
                    <Text style={[styles.activeChipText, { color: theme.colors.onPrimaryContainer }]}>Most Helpful</Text>
                    <MaterialCommunityIcons name="close" size={14} color={theme.colors.onPrimaryContainer} />
                  </Pressable>
                ) : null}
              </>
            )}
            <Pressable style={styles.clearAllChip} onPress={handleClearFilters}>
              <Text style={styles.clearAllText}>Clear all</Text>
            </Pressable>
          </ScrollView>
        </View>
      )}

      {segment === 'blog' ? (
        <>
          {blogLoading ? (
            <View style={styles.centeredLoader}>
              <ActivityIndicator size="large" color={theme.colors.primary} />
            </View>
          ) : !blogData?.posts?.length ? (
            <EmptyState
              icon="post-outline"
              title="No posts found"
              message="Check back later for new community content."
            />
          ) : (
            <Animated.FlatList
              data={blogData.posts}
              renderItem={renderBlogItem}
              keyExtractor={(item) => item.id || item.slug}
              contentContainerStyle={styles.listContent}
              showsVerticalScrollIndicator={false}
              onScroll={scrollHandler}
              scrollEventThrottle={16}
              refreshControl={
                <RefreshControl
                  refreshing={blogFetching && !blogLoading}
                  onRefresh={refetchBlogs}
                  tintColor={theme.colors.primary}
                  colors={[theme.colors.primary]}
                />
              }
            />
          )}
        </>
      ) : (
        <>
          {dpLoading ? (
            <View style={styles.centeredLoader}>
              <ActivityIndicator size="large" color={theme.colors.primary} />
            </View>
          ) : !dpData?.datapoints?.length ? (
            <EmptyState
              icon="chart-bubble"
              title="No data points yet"
              message="Be the first to share a data point!"
              actionLabel="Submit Data Point"
              onAction={() => router.push('/stacks/datapoint-submit' as any)}
            />
          ) : (
            <Animated.FlatList
              data={filteredDatapoints}
              renderItem={renderDatapointItem}
              keyExtractor={(item) => item.id}
              contentContainerStyle={styles.listContent}
              showsVerticalScrollIndicator={false}
              onScroll={scrollHandler}
              scrollEventThrottle={16}
            />
          )}
          {/* FAB for submitting data points */}
          <Pressable
            style={[styles.fab, { backgroundColor: '#1E293B' }]}
            onPress={() => router.push('/stacks/datapoint-submit' as any)}
          >
            <MaterialCommunityIcons name="plus" size={28} color="#FFFFFF" />
          </Pressable>
        </>
      )}

      {/* Filter Bottom Sheet */}
      <BottomSheet
        ref={filterSheetRef}
        index={-1}
        snapPoints={['65%']}
        enablePanDownToClose
        backgroundStyle={{ backgroundColor: theme.colors.surface }}
        handleIndicatorStyle={{ backgroundColor: theme.colors.outlineVariant }}
      >
        <BottomSheetScrollView contentContainerStyle={styles.filterSheetContent}>
          <View style={styles.filterSheetHeader}>
            <Text style={styles.filterSheetTitle}>Filters</Text>
            <Pressable onPress={handleClearFilters}>
              <Text style={[styles.filterClearText, { color: theme.colors.primary }]}>Clear All</Text>
            </Pressable>
          </View>

          {segment === 'blog' ? (
            <>
              {/* Saved Toggle */}
              <View style={styles.filterSection}>
                <Pressable
                  style={[
                    styles.filterChip,
                    showSaved && { backgroundColor: theme.colors.primaryContainer, borderColor: theme.colors.primary },
                    { borderColor: theme.colors.outlineVariant },
                  ]}
                  onPress={() => setShowSaved(!showSaved)}
                >
                  <Text
                    style={[
                      styles.filterChipText,
                      { color: showSaved ? theme.colors.onPrimaryContainer : theme.colors.onSurface },
                    ]}
                  >
                    Saved Posts
                  </Text>
                </Pressable>
              </View>

              {/* Tag Groups */}
              {TAG_GROUPS.map((group) => (
                <View key={group.label} style={styles.filterSection}>
                  <Text style={styles.filterSectionTitle}>{group.label}</Text>
                  <View style={styles.chipGrid}>
                    {group.tags.map((tag) => (
                      <Pressable
                        key={tag}
                        style={[
                          styles.filterChip,
                          selectedTag === tag && { backgroundColor: theme.colors.primaryContainer, borderColor: theme.colors.primary },
                          { borderColor: theme.colors.outlineVariant },
                        ]}
                        onPress={() => setSelectedTag(selectedTag === tag ? '' : tag)}
                      >
                        <Text
                          style={[
                            styles.filterChipText,
                            { color: selectedTag === tag ? theme.colors.onPrimaryContainer : theme.colors.onSurface },
                          ]}
                        >
                          {tag}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </View>
              ))}
            </>
          ) : (
            <>
              {/* Datapoint Filters */}
              <View style={styles.filterSection}>
                <Text style={styles.filterSectionTitle}>Sort By</Text>
                <View style={styles.chipGrid}>
                  {DP_SORT_OPTIONS.map((opt) => (
                    <Pressable
                      key={opt.value}
                      style={[
                        styles.filterChip,
                        dpSort === opt.value && { backgroundColor: theme.colors.primaryContainer, borderColor: theme.colors.primary },
                        { borderColor: theme.colors.outlineVariant },
                      ]}
                      onPress={() => setDpSort(opt.value)}
                    >
                      <Text
                        style={[
                          styles.filterChipText,
                          { color: dpSort === opt.value ? theme.colors.onPrimaryContainer : theme.colors.onSurface },
                        ]}
                      >
                        {opt.label}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </View>

              {dpFilterOptions.cards.length > 0 && (
                <View style={styles.filterSection}>
                  <Text style={styles.filterSectionTitle}>Card</Text>
                  <View style={styles.chipGrid}>
                    {dpFilterOptions.cards.map((card) => (
                      <Pressable
                        key={card}
                        style={[
                          styles.filterChip,
                          dpCard === card && { backgroundColor: theme.colors.primaryContainer, borderColor: theme.colors.primary },
                          { borderColor: theme.colors.outlineVariant },
                        ]}
                        onPress={() => setDpCard(dpCard === card ? '' : card)}
                      >
                        <Text
                          style={[
                            styles.filterChipText,
                            { color: dpCard === card ? theme.colors.onPrimaryContainer : theme.colors.onSurface },
                          ]}
                          numberOfLines={1}
                        >
                          {card}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </View>
              )}

              {dpFilterOptions.benefits.length > 0 && (
                <View style={styles.filterSection}>
                  <Text style={styles.filterSectionTitle}>Benefit Type</Text>
                  <View style={styles.chipGrid}>
                    {dpFilterOptions.benefits.map((b) => (
                      <Pressable
                        key={b}
                        style={[
                          styles.filterChip,
                          dpBenefit === b && { backgroundColor: theme.colors.primaryContainer, borderColor: theme.colors.primary },
                          { borderColor: theme.colors.outlineVariant },
                        ]}
                        onPress={() => setDpBenefit(dpBenefit === b ? '' : b)}
                      >
                        <Text
                          style={[
                            styles.filterChipText,
                            { color: dpBenefit === b ? theme.colors.onPrimaryContainer : theme.colors.onSurface },
                          ]}
                          numberOfLines={1}
                        >
                          {b}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </View>
              )}
            </>
          )}
        </BottomSheetScrollView>
      </BottomSheet>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingBottom: 12,
  },
  headerTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
  },
  headerIcons: {
    flexDirection: 'row',
    gap: 4,
  },
  toggleIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  toggleIconActive: {
    backgroundColor: 'rgba(67, 97, 238, 0.08)',
  },
  searchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginBottom: 8,
    gap: 8,
  },
  searchbar: {
    flex: 1,
    borderRadius: 12,
    elevation: 0,
    backgroundColor: '#F5F5F5',
  },
  filterButton: {
    width: 44,
    height: 44,
    borderRadius: 12,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  filterBadge: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: '#4361EE',
    justifyContent: 'center',
    alignItems: 'center',
  },
  filterBadgeText: {
    fontSize: 9,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
  },
  activeFiltersRow: {
    maxHeight: 44,
    marginBottom: 4,
  },
  activeFiltersContent: {
    paddingHorizontal: 16,
    gap: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  activeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 4,
  },
  activeChipText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
  },
  clearAllChip: {
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  clearAllText: {
    fontSize: 13,
    fontFamily: 'Outfit',
    color: '#94A3B8',
    textDecorationLine: 'underline',
  },
  centeredLoader: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    paddingTop: 4,
  },
  // Quick filter pills
  quickFilterRow: {
    marginBottom: 10,
  },
  quickFilterContent: {
    paddingHorizontal: 16,
    gap: 10,
    flexDirection: 'row',
    alignItems: 'center',
  },
  quickFilterChip: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 22,
    borderWidth: 1,
  },
  quickFilterChipActive: {
    backgroundColor: '#1E293B',
    borderColor: '#1E293B',
  },
  quickFilterText: {
    fontSize: 15,
    fontFamily: 'Outfit-Medium',
  },
  // Blog article card — vertical layout
  articleCard: {
    borderRadius: 14,
    marginBottom: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  articleImage: {
    width: '100%',
    height: 200,
  },
  thumbnailPlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  articleContent: {
    padding: 14,
  },
  articleMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  categoryBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  categoryBadgeText: {
    fontSize: 10,
    fontFamily: 'Outfit-Bold',
    letterSpacing: 0.5,
    color: '#FFFFFF',
  },
  articleTitle: {
    fontFamily: 'Outfit-Bold',
    marginBottom: 6,
    lineHeight: 24,
  },
  articleFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  articleStats: {
    flexDirection: 'row',
    gap: 14,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  // Datapoint card
  dpCard: {
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  dpHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  dpUsername: {
    fontSize: 15,
    fontFamily: 'Outfit-Bold',
    color: '#1E293B',
  },
  dpTimestamp: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#94A3B8',
  },
  dpContent: {
    fontSize: 17,
    fontFamily: 'Outfit-SemiBold',
    color: '#1E293B',
    lineHeight: 24,
    marginBottom: 12,
  },
  dpInfoBox: {
    borderRadius: 12,
    padding: 12,
    marginBottom: 14,
  },
  dpInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  dpCardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  dpCardName: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    flex: 1,
  },
  dpStatusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  dpStatusText: {
    fontSize: 12,
    fontFamily: 'Outfit-SemiBold',
  },
  dpBenefitTag: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 4,
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  dpBenefitTagText: {
    fontSize: 11,
    fontFamily: 'Outfit-Bold',
    color: '#4361EE',
    letterSpacing: 0.3,
  },
  dpFooter: {
    flexDirection: 'row',
    gap: 10,
  },
  dpFooterPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F1F5F9',
  },
  dpFooterPillActiveGreen: {
    backgroundColor: '#ECFDF5',
  },
  dpFooterPillActiveRed: {
    backgroundColor: '#FEF3C7',
  },
  dpFooterPillText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    color: '#64748B',
  },
  fab: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
  // Filter Bottom Sheet
  filterSheetContent: {
    padding: 20,
    paddingBottom: 40,
  },
  filterSheetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  filterSheetTitle: {
    fontSize: 20,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
  },
  filterClearText: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
  },
  filterSection: {
    marginBottom: 20,
  },
  filterSectionTitle: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    color: '#64748B',
    marginBottom: 10,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  chipGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  filterChip: {
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  filterChipText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
  },
});
