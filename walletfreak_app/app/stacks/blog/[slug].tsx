import React, { useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Text, Button, TextInput, Divider, IconButton, useTheme } from 'react-native-paper';
import { useLocalSearchParams } from 'expo-router';
import { LoadingState } from '../../../src/components/layout/LoadingState';
import { useBlogPost, useVoteBlog, useCommentBlog, useSaveBlog } from '../../../src/hooks/useBlog';
import { formatRelativeTime } from '../../../src/utils/formatters';
import type { Comment } from '../../../src/types/blog';

export default function BlogDetailScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { data: post, isLoading } = useBlogPost(slug);
  const voteBlog = useVoteBlog();
  const commentBlog = useCommentBlog();
  const saveBlog = useSaveBlog();
  const [commentText, setCommentText] = useState('');
  const theme = useTheme();

  if (isLoading || !post) {
    return <LoadingState message="Loading post..." />;
  }

  const netVotes = (post.upvotes ?? 0) - (post.downvotes ?? 0);

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

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.content}
    >
      {/* Header */}
      <Text variant="headlineSmall" style={styles.title}>
        {post.title}
      </Text>
      <View style={styles.meta}>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {post.author_name} · {formatRelativeTime(post.created_at)}
        </Text>
        <Text variant="labelSmall" style={{ color: theme.colors.primary }}>
          {post.category}
        </Text>
      </View>

      {/* Content */}
      <Text variant="bodyMedium" style={styles.body}>
        {post.content}
      </Text>

      {/* Voting & Save */}
      <View style={styles.actionBar}>
        <View style={styles.voteRow}>
          <IconButton
            icon={post.user_vote === 'up' ? 'arrow-up-bold' : 'arrow-up-bold-outline'}
            size={22}
            onPress={() => handleVote('upvote')}
            iconColor={post.user_vote === 'up' ? theme.colors.primary : undefined}
          />
          <Text variant="labelLarge">{netVotes}</Text>
          <IconButton
            icon={post.user_vote === 'down' ? 'arrow-down-bold' : 'arrow-down-bold-outline'}
            size={22}
            onPress={() => handleVote('downvote')}
            iconColor={post.user_vote === 'down' ? theme.colors.error : undefined}
          />
        </View>
        <IconButton
          icon={post.is_saved ? 'bookmark' : 'bookmark-outline'}
          size={22}
          onPress={handleSave}
          iconColor={post.is_saved ? theme.colors.primary : undefined}
        />
      </View>

      <Divider style={{ marginVertical: 16 }} />

      {/* Comments Section */}
      <Text variant="titleMedium" style={{ fontFamily: 'Outfit-Medium', marginBottom: 12 }}>
        Comments ({post.comments?.length ?? 0})
      </Text>

      {post.comments?.map((comment: Comment) => (
        <View key={comment.id} style={styles.commentItem}>
          <View style={styles.commentHeader}>
            <Text variant="labelMedium">{comment.author_name}</Text>
            <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
              {formatRelativeTime(comment.created_at)}
            </Text>
          </View>
          <Text variant="bodySmall">
            {comment.is_deleted ? '[deleted]' : comment.content}
          </Text>
        </View>
      ))}

      {/* Add Comment */}
      <View style={styles.commentInput}>
        <TextInput
          placeholder="Add a comment..."
          value={commentText}
          onChangeText={setCommentText}
          mode="outlined"
          style={{ flex: 1 }}
          multiline
        />
        <Button
          mode="contained-tonal"
          onPress={handleComment}
          loading={commentBlog.isPending}
          disabled={!commentText.trim()}
          compact
          style={{ marginLeft: 8, alignSelf: 'flex-end' }}
        >
          Post
        </Button>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  title: {
    fontFamily: 'Outfit-SemiBold',
    marginBottom: 8,
  },
  meta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  body: {
    lineHeight: 24,
  },
  actionBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
  },
  voteRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  commentItem: {
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#e0e0e0',
  },
  commentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  commentInput: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: 16,
  },
});
