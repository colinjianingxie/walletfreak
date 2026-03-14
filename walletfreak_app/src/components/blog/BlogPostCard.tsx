import React from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text, Chip, Surface, useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { formatRelativeTime } from '../../utils/formatters';
import type { BlogPost } from '../../types/blog';

interface BlogPostCardProps {
  post: BlogPost;
  onPress: (post: BlogPost) => void;
}

export const BlogPostCard: React.FC<BlogPostCardProps> = ({ post, onPress }) => {
  const theme = useTheme();

  return (
    <Surface style={[styles.container, { backgroundColor: theme.colors.elevation.level1 }]} elevation={1}>
      <Pressable onPress={() => onPress(post)} style={styles.pressable}>
        <View style={styles.header}>
          <Chip compact style={styles.categoryChip} textStyle={{ fontSize: 10 }}>
            {post.category}
          </Chip>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {formatRelativeTime(post.created_at)}
          </Text>
        </View>

        <Text variant="titleSmall" numberOfLines={2} style={styles.title}>
          {post.title}
        </Text>

        {post.excerpt && (
          <Text
            variant="bodySmall"
            numberOfLines={2}
            style={{ color: theme.colors.onSurfaceVariant, marginBottom: 8 }}
          >
            {post.excerpt}
          </Text>
        )}

        <View style={styles.footer}>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {post.author_name}
          </Text>
          <View style={styles.stats}>
            <View style={styles.statItem}>
              <MaterialCommunityIcons
                name="arrow-up"
                size={14}
                color={theme.colors.onSurfaceVariant}
              />
              <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
                {post.upvotes - post.downvotes}
              </Text>
            </View>
            <View style={styles.statItem}>
              <MaterialCommunityIcons
                name="comment-outline"
                size={14}
                color={theme.colors.onSurfaceVariant}
              />
              <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
                {post.comment_count}
              </Text>
            </View>
          </View>
        </View>
      </Pressable>
    </Surface>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    marginBottom: 8,
  },
  pressable: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  categoryChip: {
    height: 24,
  },
  title: {
    fontFamily: 'Outfit-Medium',
    marginBottom: 4,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  stats: {
    flexDirection: 'row',
    gap: 12,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
});
