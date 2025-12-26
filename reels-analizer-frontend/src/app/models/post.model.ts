export interface Post {
  instagram_id: string;
  permalink?: string;
  username: string;
  caption: string | null;
  media_type: string;
  media_url: string;
  post_timestamp: string;
  ai_category: string | null;
  ai_summary: string | null;
  drink_category: string | null;
}

export interface AnalysisRequest {
  instagram_url: string;
}

export interface DrinkStats {
  username: string;
  total_posts: number;
  categories: CategoryCount[];
}

export interface CategoryCount {
  drink_category: string;
  count: number;
}