export interface BlogPost {
  id: string;
  slug: string;
  title: string;
  excerpt: string;
  content: string;
  author: string;
  author_name: string;
  category: string;
  image_url?: string;
  tags?: string[];
  vendor?: string;
  created_at: string;
  updated_at: string;
  upvotes: number;
  downvotes: number;
  comment_count: number;
  user_vote: 'up' | 'down' | null;
  is_saved: boolean;
}

export interface Comment {
  id: string;
  content: string;
  author: string;
  author_name: string;
  created_at: string;
  upvotes: number;
  downvotes: number;
  user_vote: 'up' | 'down' | null;
  is_deleted: boolean;
}
