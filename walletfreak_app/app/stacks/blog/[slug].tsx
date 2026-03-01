import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Image, Dimensions, TextInput, Pressable } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { MarkdownRenderer } from '../../../src/components/ui/MarkdownRenderer';
import { LoadingState } from '../../../src/components/layout/LoadingState';
import { useBlogPost, useVoteBlog, useCommentBlog, useSaveBlog } from '../../../src/hooks/useBlog';
import { formatDate, formatRelativeTime } from '../../../src/utils/formatters';
import type { Comment } from '../../../src/types/blog';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const HERO_HEIGHT = 220;

const estimateReadTime = (content?: string): number => {
  if (!content) return 3;
  const words = content.split(/\s+/).length;
  return Math.max(1, Math.ceil(words / 200));
};

export default function BlogDetailScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { data: post, isLoading } = useBlogPost(slug);
  const voteBlog = useVoteBlog();
  const commentBlog = useCommentBlog();
  const saveBlog = useSaveBlog();
  const [commentText, setCommentText] = useState('');
  const theme = useTheme();
  const router = useRouter();
  const insets = useSafeAreaInsets();

  if (isLoading || !post) {
    return <LoadingState message="Loading post..." />;
  }

  const netVotes = (post.upvotes ?? 0) - (post.downvotes ?? 0);
  const readTime = estimateReadTime(post.content);

  const handleVote = (voteType: 'upvote' | 'downvote') => {
    voteBlog.mutate({ slug, voteType });
  };

  const handleComment = () => {
    if (!commentText.trim()) return;
    commentBlog.mutate(
      { slug, content: commentText.trim() },
      { onSuccess: () => setCommentText('') }
    );
  };

  const handleSave = () => {
    saveBlog.mutate({ slug, save: !post.is_saved });
  };

  const getInitial = (name: string) => {
    return (name || '?').charAt(0).toUpperCase();
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Hero Image (shorter, just image + gradient) */}
        <View style={styles.heroContainer}>
          {post.image_url ? (
            <Image
              source={{ uri: post.image_url }}
              style={styles.heroImage}
              resizeMode="cover"
            />
          ) : (
            <View style={[styles.heroImage, { backgroundColor: '#374151' }]} />
          )}
        </View>

        {/* Title + Metadata below hero */}
        <View style={styles.titleSection}>
          <Text style={styles.title}>{post.title}</Text>
          <View style={styles.metaRow}>
            <View style={styles.categoryBadge}>
              <Text style={styles.categoryText}>
                {(post.category || '').toUpperCase()}
              </Text>
            </View>
            <Text style={styles.metaDot}>·</Text>
            <Text style={styles.metaText}>{post.author_name}</Text>
            <Text style={styles.metaDot}>·</Text>
            <Text style={styles.metaText}>{formatDate(post.created_at)}</Text>
            <Text style={styles.metaDot}>·</Text>
            <View style={styles.readTimeRow}>
              <MaterialCommunityIcons name="clock-outline" size={13} color="#94A3B8" />
              <Text style={styles.metaText}>{readTime} min</Text>
            </View>
          </View>
        </View>

        {/* Action Bar */}
        <View style={[styles.actionBar, { borderBottomColor: theme.colors.outlineVariant }]}>
          <View style={styles.actionGroup}>
            <Pressable style={styles.actionButton} onPress={() => handleVote('upvote')}>
              <MaterialCommunityIcons
                name={post.user_vote === 'up' ? 'thumb-up' : 'thumb-up-outline'}
                size={22}
                color={post.user_vote === 'up' ? theme.colors.primary : '#94A3B8'}
              />
            </Pressable>
            <Text style={styles.actionCount}>{netVotes}</Text>
            <Pressable style={styles.actionButton} onPress={() => handleVote('downvote')}>
              <MaterialCommunityIcons
                name={post.user_vote === 'down' ? 'thumb-down' : 'thumb-down-outline'}
                size={22}
                color={post.user_vote === 'down' ? theme.colors.error : '#94A3B8'}
              />
            </Pressable>
            <View style={styles.actionDivider} />
            <MaterialCommunityIcons name="comment-outline" size={20} color="#94A3B8" />
            <Text style={styles.actionCount}>{post.comments?.length ?? 0}</Text>
          </View>
          <Pressable style={styles.actionButton} onPress={handleSave}>
            <MaterialCommunityIcons
              name={post.is_saved ? 'bookmark' : 'bookmark-outline'}
              size={22}
              color="#94A3B8"
            />
          </Pressable>
        </View>

        {/* Article Body - Markdown */}
        <View style={styles.bodyContainer}>
          <MarkdownRenderer>{post.content || ''}</MarkdownRenderer>
        </View>

        {/* Comments Section */}
        <View style={styles.commentsSection}>
          <Text variant="titleMedium" style={styles.commentsTitle}>
            Comments ({post.comments?.length ?? 0})
          </Text>

          {/* Comment Input */}
          <View style={styles.commentInputRow}>
            <View style={[styles.commentAvatar, { backgroundColor: theme.colors.surfaceVariant }]}>
              <Text style={[styles.commentAvatarText, { color: theme.colors.onSurfaceVariant }]}>
                Y
              </Text>
            </View>
            <View style={styles.commentInputContainer}>
              <TextInput
                placeholder="Add to the discussion..."
                placeholderTextColor="#94A3B8"
                value={commentText}
                onChangeText={setCommentText}
                style={[styles.commentInput, { borderColor: theme.colors.outlineVariant }]}
                multiline
              />
              <Pressable
                style={[
                  styles.postButton,
                  { backgroundColor: commentText.trim() ? '#818CF8' : '#C7D2FE' },
                ]}
                onPress={handleComment}
                disabled={!commentText.trim()}
              >
                <MaterialCommunityIcons name="send" size={16} color="#FFFFFF" />
                <Text style={styles.postButtonText}>Post</Text>
              </Pressable>
            </View>
          </View>

          {/* Comment Items */}
          {post.comments?.map((comment: Comment) => (
            <View key={comment.id} style={styles.commentItem}>
              <View style={[styles.commentAvatar, { backgroundColor: theme.colors.surfaceVariant }]}>
                <Text style={[styles.commentAvatarText, { color: theme.colors.onSurfaceVariant }]}>
                  {getInitial(comment.author_name)}
                </Text>
              </View>
              <View style={styles.commentContent}>
                <View style={styles.commentHeader}>
                  <Text style={styles.commentAuthor}>{comment.author_name}</Text>
                  <Text style={styles.commentTime}> · {formatRelativeTime(comment.created_at)}</Text>
                </View>
                <Text variant="bodyMedium" style={{ color: theme.colors.onSurface }}>
                  {comment.is_deleted ? '[deleted]' : comment.content}
                </Text>
                {!comment.is_deleted && (
                  <View style={styles.commentLikes}>
                    <MaterialCommunityIcons name="thumb-up-outline" size={14} color="#818CF8" />
                    <Text style={styles.commentLikesText}>
                      {comment.upvotes ?? 0} Likes
                    </Text>
                  </View>
                )}
              </View>
            </View>
          ))}
        </View>
      </ScrollView>

      {/* Sticky Back Button - always visible over scroll content */}
      <Pressable
        style={[styles.backButton, { top: insets.top + 8 }]}
        onPress={() => router.back()}
      >
        <MaterialCommunityIcons name="arrow-left" size={24} color="#FFFFFF" />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 40,
  },
  // Hero
  heroContainer: {
    width: SCREEN_WIDTH,
    height: HERO_HEIGHT,
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  // Sticky back button (outside ScrollView)
  backButton: {
    position: 'absolute',
    left: 16,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  // Title & metadata below hero
  titleSection: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 12,
  },
  title: {
    fontSize: 26,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
    lineHeight: 34,
    marginBottom: 12,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 6,
  },
  categoryBadge: {
    backgroundColor: '#4338CA',
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 6,
  },
  categoryText: {
    fontSize: 10,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
    letterSpacing: 0.5,
  },
  metaDot: {
    fontSize: 12,
    color: '#94A3B8',
  },
  metaText: {
    fontSize: 13,
    fontFamily: 'Outfit',
    color: '#64748B',
  },
  readTimeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  // Action Bar
  actionBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  actionGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  actionButton: {
    padding: 6,
  },
  actionCount: {
    fontSize: 15,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
    marginHorizontal: 2,
  },
  actionDivider: {
    width: 1,
    height: 20,
    backgroundColor: '#E5E7EB',
    marginHorizontal: 8,
  },
  // Body
  bodyContainer: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 16,
  },
  // Comments
  commentsSection: {
    paddingHorizontal: 20,
    paddingTop: 8,
  },
  commentsTitle: {
    fontFamily: 'Outfit-SemiBold',
    marginBottom: 16,
  },
  commentInputRow: {
    flexDirection: 'row',
    marginBottom: 24,
    gap: 12,
  },
  commentAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  commentAvatarText: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
  },
  commentInputContainer: {
    flex: 1,
  },
  commentInput: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    minHeight: 80,
    textAlignVertical: 'top',
    fontFamily: 'Outfit',
    fontSize: 14,
    color: '#1C1B1F',
  },
  postButton: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    marginTop: 8,
    gap: 6,
  },
  postButtonText: {
    fontSize: 14,
    fontFamily: 'Outfit-Medium',
    color: '#FFFFFF',
  },
  commentItem: {
    flexDirection: 'row',
    marginBottom: 20,
    gap: 12,
  },
  commentContent: {
    flex: 1,
  },
  commentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  commentAuthor: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
  },
  commentTime: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#94A3B8',
  },
  commentLikes: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 8,
  },
  commentLikesText: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#818CF8',
  },
});
