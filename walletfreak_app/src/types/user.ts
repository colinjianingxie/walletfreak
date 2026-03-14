export interface UserProfile {
  uid: string;
  email: string;
  first_name: string;
  last_name: string;
  username: string;
  is_premium: boolean;
  assigned_personality: string | null;
  photo_url: string | null;
}

export interface NotificationPreferences {
  benefit_expiration?: {
    enabled: boolean;
    repeat_frequency: number;
  };
  annual_fee_reminder?: {
    enabled: boolean;
  };
  blog_updates?: {
    enabled: boolean;
    frequency: string;
  };
}
