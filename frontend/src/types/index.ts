// Common types for the application

export interface CompetitorData {
  name: string;
  website?: string;
  description: string;
  business_model: string;
  target_market: string;
  founding_year?: number;
  headquarters?: string;
  employee_count?: string;
  funding_info?: {
    total_funding?: string;
    last_round?: string;
    investors?: string[];
  };
  key_products: string[];
  pricing_strategy?: string;
  market_position?: string;
  strengths: string[];
  weaknesses: string[];
  recent_news: Array<{
    title: string;
    date: string;
    summary: string;
  }>;
  technology_stack: string[];
  partnerships: string[];
  competitive_advantages: string[];
  market_share?: number;
  growth_trajectory?: string;
  threat_level?: string;
}

export interface AnalysisRequest {
  client_company: string;
  industry: string;
  target_market: string;
  business_model: string;
  specific_requirements?: string;
  max_competitors: number;
  demo_mode?: boolean;
  
  // Product comparison fields
  comparison_type?: 'company' | 'product';
  client_product?: string;
  product_category?: string;
  comparison_criteria?: string[];
}

export interface ProductData {
  id?: string;
  name: string;
  company: string;
  category: string;
  sub_category?: string;
  description: string;
  target_audience: string;
  launch_date?: string;
  version?: string;
  website_url?: string;
  documentation_url?: string;
  
  // Features
  core_features: ProductFeature[];
  unique_features: string[];
  integrations: string[];
  supported_platforms: string[];
  
  // Pricing
  pricing_model: string;
  pricing_tiers: PricingTier[];
  free_trial: boolean;
  free_trial_duration?: number;
  
  // Performance & Technical
  performance_metrics: Record<string, any>;
  technology_stack: string[];
  api_availability: boolean;
  mobile_app: boolean;
  
  // Market Position
  market_share?: number;
  user_base_size?: string;
  customer_segments: string[];
  geographic_availability: string[];
  
  // Reviews & Ratings
  average_rating?: number;
  total_reviews?: number;
  review_sources: Record<string, number>;
  customer_satisfaction_score?: number;
  
  // Competitive Analysis
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
  competitive_advantages: string[];
  
  // Metadata
  created_at: string;
  updated_at: string;
  data_sources: string[];
}

export interface ProductFeature {
  name: string;
  description: string;
  category: string;
  availability: string;
}

export interface PricingTier {
  name: string;
  price?: number;
  billing_cycle?: string;
  features: string[];
  limitations: Record<string, any>;
  target_audience: string;
}

export interface ProductComparisonRequest {
  client_product: string;
  client_company: string;
  product_category: string;
  comparison_criteria?: string[];
  target_market: string;
  specific_requirements?: string;
  max_products?: number;
  include_indirect_competitors?: boolean;
  demo_mode?: boolean;
}

export interface ProductComparison {
  product_a: ProductData;
  product_b: ProductData;
  common_features: string[];
  unique_to_a: string[];
  unique_to_b: string[];
  feature_advantage: string;
  price_comparison: Record<string, any>;
  value_for_money: string;
  performance_comparison: Record<string, any>;
  performance_winner: string;
  market_position_analysis: string;
  growth_trajectory_comparison: string;
  overall_winner: string;
  recommendation: string;
  key_differentiators: string[];
  comparison_date: string;
  confidence_score: number;
}

export interface AnalysisResult {
  request_id: string;
  client_company: string;
  industry: string;
  competitors: CompetitorData[];
  market_analysis: any;
  competitive_landscape: any;
  threats_opportunities: any;
  recommendations: string[];
  status: string;
  progress: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface AnalysisStatus {
  request_id: string;
  status: string;
  progress: number;
  current_stage: string;
  completed_stages: string[];
  errors: string[];
  warnings: string[];
}

export interface Report {
  id: string;
  analysis_id: string;
  title: string;
  executive_summary: string;
  client_company: string;
  industry: string;
  analysis_date: string;
  total_competitors_analyzed: number;
  confidence_level: string;
  created_at: string;
}

export interface WebSocketMessage {
  type: string;
  request_id?: string;
  progress?: number;
  stage?: string;
  status?: string;
  timestamp?: string;
  message?: string;
  completed_stages?: string[];
  errors?: string[];
  warnings?: string[];
}