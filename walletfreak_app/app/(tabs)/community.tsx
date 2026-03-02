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

// Blog tag taxonomy groups
const TAG_GROUPS = [
  { label: 'Ecosystem', tags: ['American Express', 'Chase', 'Citi'] },
  { label: 'Content Type', tags: ['guide', 'review', 'lounges', 'savings', 'strategy', 'tips'] },
  { label: 'Experience Level', tags: ['Beginner', 'Intermediate', 'Advanced'] },
  { label: 'Read Time', tags: ['Short (< 3m)', 'Medium (3-7m)', 'Long (7m+)', 'Video Only'] },
];

// Datapoint sort options
const DP_SORT_OPTIONS = [
  { label: 'Newest', value: 'newest' },
  { label: 'Most Helpful', value: 'votes' },
];

export default function CommunityScreen() {
  const [segment, setSegment] = useState<'blog' | 'datapoints'>('blog');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [selectedTag, setSelectedTag] = useState('');
  const [showSaved, setShowSaved] = useState(false);
  // Datapoint filters
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

  const { data: blogData, isLoading: blogLoading, isFetching: blogFetching, refetch: refetchBlogs } = useBlogPosts({
    search: search || undefined,
    category: category || undefined,
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

  const activeFilterCount = segment === 'blog'
    ? (category ? 1 : 0) + (selectedTag ? 1 : 0) + (showSaved ? 1 : 0)
    : (dpCard ? 1 : 0) + (dpBenefit ? 1 : 0) + (dpSort !== 'newest' ? 1 : 0);

  const handleBlogPress = (post: BlogPost) => {
    router.push(`/stacks/blog/${post.slug}` as any);
  };

  const handleOpenFilters = useCallback(() => {
    filterSheetRef.current?.snapToIndex(0);
  }, []);

  const handleClearFilters = useCallback(() => {
    setCategory('');
    setSelectedTag('');
    setShowSaved(false);
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

    return (
      <Pressable
        style={[styles.articleCard, { backgroundColor: theme.colors.elevation.level1 }]}
        onPress={() => handleBlogPress(item)}
      >
        {item.image_url ? (
          <Image
            source={{ uri: item.image_url }}
            style={styles.articleThumbnail}
            resizeMode="cover"
          />
        ) : (
          <View style={[styles.articleThumbnail, styles.thumbnailPlaceholder, { backgroundColor: theme.colors.surfaceVariant }]}>
            <MaterialCommunityIcons name="newspaper-variant-outline" size={28} color={theme.colors.onSurfaceVariant} />
          </View>
        )}

        <View style={styles.articleContent}>
          <View style={styles.articleMeta}>
            <View style={[styles.categoryBadge, { backgroundColor: '#4338CA' }]}>
              <Text style={[styles.categoryBadgeText, { color: '#FFFFFF' }]}>
                {(() => {
                  const tags: any = item.tags;
                  if (Array.isArray(tags) && tags.length > 0) return String(tags[0]).toUpperCase();
                  if (typeof tags === 'string' && tags.trim()) return tags.split(',')[0].trim().toUpperCase();
                  return (item.category || '').toUpperCase();
                })()}
              </Text>
            </View>
            <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
              {formatDate(item.created_at)}
            </Text>
          </View>
          <Text variant="titleSmall" numberOfLines={2} style={styles.articleTitle}>
            {item.title}
          </Text>
          {item.excerpt && (
            <Text variant="bodySmall" numberOfLines={2} style={{ color: theme.colors.onSurfaceVariant, marginBottom: 8 }}>
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
      <View style={[styles.dpCard, { backgroundColor: theme.colors.elevation.level1 }]}>
        {/* Header: User + Date */}
        <View style={styles.dpHeader}>
          <Text style={styles.dpUsername}>@{item.author_name || 'Anonymous'}</Text>
          <Text style={styles.dpTimestamp}>{formatRelativeTime(item.created_at)}</Text>
        </View>

        {/* Card row */}
        <View style={styles.dpCardBenefitRow}>
          {item.card_slug ? (
            <CardImage slug={item.card_slug} size="small" />
          ) : null}
          <Text style={styles.dpCardName} numberOfLines={1} ellipsizeMode="tail">
            {item.card_name || 'Unknown Card'}
          </Text>
        </View>

        {/* Benefit tag + Status badge on same row */}
        <View style={styles.dpBenefitStatusRow}>
          {item.benefit ? (
            <View style={styles.dpBenefitTag}>
              <MaterialCommunityIcons name="lightning-bolt" size={12} color="#4F46E5" />
              <Text style={styles.dpBenefitTagText}>{item.benefit.toUpperCase()}</Text>
            </View>
          ) : <View />}
          <View style={[
            styles.dpStatusBadge,
            { backgroundColor: item.status === 'Success' ? '#ECFDF5' : '#FEF2F2' },
          ]}>
            <MaterialCommunityIcons
              name={item.status === 'Success' ? 'check-circle' : 'close-circle'}
              size={12}
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

        {/* Full content text on its own line */}
        {item.data ? (
          <Text style={styles.dpContent}>{item.data}</Text>
        ) : null}

        {/* Footer: Votes */}
        <View style={styles.dpFooter}>
          <Pressable
            style={styles.dpFooterItem}
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
            <Text style={[styles.dpFooterText, { color: item.user_voted ? '#16A34A' : '#94A3B8' }]}>
              Works {item.upvotes ?? 0}
            </Text>
          </Pressable>
          <Pressable
            style={styles.dpFooterItem}
            onPress={() => markOutdated.mutate(item.id)}
            disabled={markOutdated.isPending && markOutdated.variables === item.id}
          >
            {markOutdated.isPending && markOutdated.variables === item.id ? (
              <ActivityIndicator size={14} color="#DC2626" />
            ) : (
              <MaterialCommunityIcons
                name={item.user_outdated ? 'thumb-down' : 'thumb-down-outline'}
                size={16}
                color={item.user_outdated ? '#DC2626' : '#94A3B8'}
              />
            )}
            <Text style={[styles.dpFooterText, { color: item.user_outdated ? '#DC2626' : '#94A3B8' }]}>
              Outdated {item.outdated_count ?? 0}
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

      {/* Search + Filter — collapses on scroll */}
      <Animated.View style={[styles.searchRow, animatedSearchRow]}>
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
      </Animated.View>

      {/* Active filter chips — collapses on scroll */}
      {activeFilterCount > 0 && (
        <Animated.View style={animatedFilterChips}>
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
                {category ? (
                  <Pressable
                    style={[styles.activeChip, { backgroundColor: theme.colors.primaryContainer }]}
                    onPress={() => setCategory('')}
                  >
                    <Text style={[styles.activeChipText, { color: theme.colors.onPrimaryContainer }]}>{category}</Text>
                    <MaterialCommunityIcons name="close" size={14} color={theme.colors.onPrimaryContainer} />
                  </Pressable>
                ) : null}
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
        </Animated.View>
      )}

      {segment === 'blog' ? (
        <>
          {blogLoading ? (
            <LoadingState message="Loading posts..." />
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
            <LoadingState message="Loading data points..." />
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
              data={dpData.datapoints}
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
            style={[styles.fab, { backgroundColor: theme.colors.primary }]}
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

              {/* Category */}
              {availableCategories.length > 0 && (
                <View style={styles.filterSection}>
                  <Text style={styles.filterSectionTitle}>Category</Text>
                  <View style={styles.chipGrid}>
                    {availableCategories.map((cat: string) => (
                      <Pressable
                        key={cat}
                        style={[
                          styles.filterChip,
                          category === cat && { backgroundColor: theme.colors.primaryContainer, borderColor: theme.colors.primary },
                          { borderColor: theme.colors.outlineVariant },
                        ]}
                        onPress={() => setCategory(category === cat ? '' : cat)}
                      >
                        <Text
                          style={[
                            styles.filterChipText,
                            { color: category === cat ? theme.colors.onPrimaryContainer : theme.colors.onSurface },
                          ]}
                        >
                          {cat}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </View>
              )}

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
    backgroundColor: 'rgba(103, 80, 164, 0.08)',
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
    backgroundColor: '#4F46E5',
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
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    paddingTop: 4,
  },
  // Blog article card
  articleCard: {
    flexDirection: 'row',
    borderRadius: 12,
    marginBottom: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  articleThumbnail: {
    width: 110,
    minHeight: 120,
  },
  thumbnailPlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  articleContent: {
    flex: 1,
    padding: 12,
  },
  articleMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  categoryBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  categoryBadgeText: {
    fontSize: 9,
    fontFamily: 'Outfit-Bold',
    letterSpacing: 0.5,
  },
  articleTitle: {
    fontFamily: 'Outfit-SemiBold',
    marginBottom: 4,
  },
  articleFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  articleStats: {
    flexDirection: 'row',
    gap: 12,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  // Datapoint card
  dpCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  dpHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  dpUsername: {
    fontSize: 14,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
  },
  dpTimestamp: {
    fontSize: 11,
    fontFamily: 'Outfit',
    color: '#94A3B8',
  },
  dpCardBenefitRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  dpCardName: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    color: '#64748B',
  },
  dpStatusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  dpStatusText: {
    fontSize: 11,
    fontFamily: 'Outfit-SemiBold',
    letterSpacing: 0.3,
  },
  dpBenefitStatusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  dpBenefitTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  dpBenefitTagText: {
    fontSize: 10,
    fontFamily: 'Outfit-Bold',
    color: '#4F46E5',
    letterSpacing: 0.3,
  },
  dpContent: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: '#1C1B1F',
    lineHeight: 20,
    marginBottom: 12,
  },
  dpFooter: {
    flexDirection: 'row',
    gap: 20,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingTop: 12,
  },
  dpFooterItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dpFooterText: {
    fontSize: 13,
    fontFamily: 'Outfit-Medium',
    color: '#94A3B8',
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
