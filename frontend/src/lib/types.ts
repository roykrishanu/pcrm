export type User = {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  job_title: string | null;
  role_id: string | null;
  role_name: string | null;
  team_id: string | null;
  is_active: boolean;
  is_email_verified: boolean;
  last_login_at: string | null;
  created_at: string;
};

export type Lead = {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  whatsapp_number: string | null;
  source: string | null;
  campaign: string | null;
  assigned_user_id: string | null;
  team_id: string | null;
  status_key: string;
  budget_min: string | null;
  budget_max: string | null;
  preferred_location: string | null;
  property_type: string | null;
  bedrooms: number | null;
  bathrooms: number | null;
  purpose: string | null;
  timeline: string | null;
  financing_status: string | null;
  notes: string | null;
  tags: string[] | null;
  score: number;
  temperature: "cold" | "warm" | "hot" | "very_hot";
  next_follow_up_at: string | null;
  last_activity_at: string | null;
  created_at: string;
  updated_at: string;
};

export type LeadActivity = {
  id: string;
  lead_id: string;
  actor_user_id: string | null;
  type: string;
  payload: Record<string, unknown> | null;
  created_at: string;
};

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};
