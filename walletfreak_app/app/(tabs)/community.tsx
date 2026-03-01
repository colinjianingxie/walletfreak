import React, { useState } from 'react';
import { View, StyleSheet, FlatList } from 'react-native';
import { Text, SegmentedButtons, Searchbar, Chip, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { EmptyState } from '../../src/components/layout/EmptyState';
import { LoadingState } from '../../src/components/layout/LoadingState';
import { BlogPostCard } from '../../src/components/blog/BlogPostCard';
import { DatapointCard } from '../../src/components/community/DatapointCard';
import { useBlogPosts } from '../../src/hooks/useBlog';
import { useDatapoints, useVoteDatapoint } from '../../src/hooks/useDatapoints';
import type { BlogPost } from '../../src/types/blog';

const BLOG_CATEGORIES = ['All', 'News', 'Guides', 'Reviews', 'Deals', 'Tips'];

export default function CommunityScreen() {
  const [segment, setSegment] = useState('blog');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const router = useRouter();
  const theme = useTheme();

  const { data: blogData, isLoading: blogLoading } = useBlogPosts({
    search: search || undefined,
    category: category || undefined,
  });
  const { data: dpData, isLoading: dpLoading } = useDatapoints();
  const voteDatapoint = useVoteDatapoint();

  const handleBlogPress = (post: BlogPost) => {
    router.push(`/stacks/blog/${post.slug}` as any);
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <SegmentedButtons
        value={segment}
        onValueChange={setSegment}
        buttons={[
          { value: 'blog', label: 'Blog' },
          { value: 'datapoints', label: 'Data Points' },
        ]}
        style={styles.segments}
      />

      {segment === 'blog' ? (
        <>
          <Searchbar
            placeholder="Search posts..."
            onChangeText={setSearch}
            value={search}
            style={styles.searchbar}
            inputStyle={{ fontFamily: 'Outfit' }}
          />
          <FlatList
            data={BLOG_CATEGORIES}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.filterRow}
            renderItem={({ item }) => (
              <Chip
                selected={item === 'All' ? !category : category === item}
                onPress={() => setCategory(item === 'All' ? '' : item)}
                style={styles.filterChip}
                compact
              >
                {item}
              </Chip>
            )}
            keyExtractor={(item) => item}
          />
          {blogLoading ? (
            <LoadingState message="Loading posts..." />
          ) : !blogData?.posts?.length ? (
            <EmptyState
              icon="post-outline"
              title="No posts found"
              message="Check back later for new community content."
            />
          ) : (
            <FlatList
              data={blogData.posts}
              renderItem={({ item }) => (
                <BlogPostCard post={item} onPress={handleBlogPress} />
              )}
              keyExtractor={(item) => item.id || item.slug}
              contentContainerStyle={styles.listContent}
              showsVerticalScrollIndicator={false}
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
            <FlatList
              data={dpData.datapoints}
              renderItem={({ item }) => (
                <DatapointCard
                  datapoint={item}
                  onVote={(id) => voteDatapoint.mutate(id)}
                />
              )}
              keyExtractor={(item) => item.id}
              contentContainerStyle={styles.listContent}
              showsVerticalScrollIndicator={false}
            />
          )}
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  segments: {
    marginBottom: 8,
  },
  searchbar: {
    marginBottom: 8,
    borderRadius: 12,
  },
  filterRow: {
    paddingVertical: 4,
    gap: 8,
  },
  filterChip: {
    marginRight: 4,
  },
  listContent: {
    paddingBottom: 16,
    paddingTop: 8,
  },
});
