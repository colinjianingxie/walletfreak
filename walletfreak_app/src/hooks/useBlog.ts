import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getBlogPosts,
  getBlogPostDetail,
  voteBlogPost,
  commentOnBlogPost,
  saveBlogPost,
  unsaveBlogPost,
  BlogListParams,
} from '../api/endpoints/blog';

export const useBlogPosts = (params?: BlogListParams) => {
  return useQuery({
    queryKey: ['blog', params],
    queryFn: () => getBlogPosts(params),
  });
};

export const useBlogPost = (slug: string) => {
  return useQuery({
    queryKey: ['blog', slug],
    queryFn: () => getBlogPostDetail(slug),
    enabled: !!slug,
  });
};

export const useVoteBlog = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ slug, voteType }: { slug: string; voteType: 'upvote' | 'downvote' }) =>
      voteBlogPost(slug, voteType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blog'] });
    },
  });
};

export const useCommentBlog = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ slug, content }: { slug: string; content: string }) =>
      commentOnBlogPost(slug, content),
    onSuccess: (_, { slug }) => {
      queryClient.invalidateQueries({ queryKey: ['blog', slug] });
    },
  });
};

export const useSaveBlog = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ slug, save }: { slug: string; save: boolean }) =>
      save ? saveBlogPost(slug) : unsaveBlogPost(slug),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blog'] });
    },
  });
};
