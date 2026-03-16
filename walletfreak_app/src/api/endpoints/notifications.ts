import apiClient from '../client';

export interface Notification {
  id: string;
  uid: string;
  type: 'blog_published' | 'benefit_expiration' | 'system';
  title: string;
  body: string;
  read: boolean;
  created_at: any;
  metadata: Record<string, any>;
  action_url: string | null;
  action_route: string | null;
}

export const getNotifications = async (limit = 20, cursor?: string) => {
  const params: Record<string, any> = { limit };
  if (cursor) params.cursor = cursor;
  const { data } = await apiClient.get('/notifications/', { params });
  return data as { notifications: Notification[] };
};

export const getUnreadCount = async () => {
  const { data } = await apiClient.get('/notifications/unread-count/');
  return data as { count: number };
};

export const markRead = async (id: string) => {
  const { data } = await apiClient.post(`/notifications/${id}/read/`);
  return data;
};

export const markAllRead = async () => {
  const { data } = await apiClient.post('/notifications/read-all/');
  return data;
};

export const deleteNotification = async (id: string) => {
  const { data } = await apiClient.delete(`/notifications/${id}/`);
  return data;
};
