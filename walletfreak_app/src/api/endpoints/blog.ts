import apiClient from '../client';

export interface BlogListParams {
  page?: number;
  page_size?: number;
  search?: string;
  category?: string;
  tag?: string;
  saved?: boolean;
}

export const getBlogPosts = async (params?: BlogListParams) => {
  const { data } = await apiClient.get('/blog/', { params });
  return data;
};

export const getBlogPostDetail = async (slug: string) => {
  const { data } = await apiClient.get(`/blog/${slug}/`);
  return data;
};

export const voteBlogPost = async (slug: string, voteType: 'upvote' | 'downvote') => {
  const { data } = await apiClient.post(`/blog/${slug}/vote/`, { vote_type: voteType });
  return data;
};

export const commentOnBlogPost = async (slug: string, content: string) => {
  const { data } = await apiClient.post(`/blog/${slug}/comment/`, { content });
  return data;
};

export const saveBlogPost = async (slug: string) => {
  const { data } = await apiClient.post(`/blog/${slug}/save/`);
  return data;
};

export const unsaveBlogPost = async (slug: string) => {
  const { data } = await apiClient.delete(`/blog/${slug}/save/`);
  return data;
};
