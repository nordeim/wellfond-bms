/**
 * Wellfond BMS - TypeScript Types
 * =================================
 * Core type definitions for Phase 1: Auth, BFF Proxy & RBAC
 */

// =============================================================================
// User & RBAC Types
// =============================================================================

export type Role = 'management' | 'admin' | 'sales' | 'ground' | 'vet';

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  entity_id: string | null;
  pdpa_consent: boolean;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  csrf_token: string;
}

// =============================================================================
// Entity Types
// =============================================================================

export type EntityCode = 'HOLDINGS' | 'KATONG' | 'THOMSON';

export interface Entity {
  id: string;
  name: string;
  code: EntityCode;
  slug: string;
  is_active: boolean;
  is_holding: boolean;
  gst_rate: number;
  avs_license_number: string | null;
  avs_license_expiry: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  created_at: string;
}

// =============================================================================
// Dog Types (Preview for Phase 2+)
// =============================================================================

export type DogStatus = 'ACTIVE' | 'RETIRED' | 'REHOMED' | 'DECEASED';
export type DNAStatus = 'PENDING' | 'SUBMITTED' | 'RESULTS_RECEIVED' | 'EXCLUDED';

export interface Dog {
  id: string;
  microchip: string;
  name: string;
  breed: string;
  dob: string;
  gender: 'M' | 'F';
  colour: string;
  entity_id: string;
  status: DogStatus;
  dam_id: string | null;
  sire_id: string | null;
  unit: string;
  dna_status: DNAStatus;
  notes: string;
  image_url: string | null;
  // Extended properties
  age_years?: number;
  age_display?: string;
  dam_name?: string;
  sire_name?: string;
}

// =============================================================================
// Breeding Types (Preview)
// =============================================================================

export type MatingStatus = 'PLANNED' | 'CONFIRMED' | 'PREGNANT' | 'WHELPED';

export interface Mating {
  id: string;
  sire_id: string;
  dam_id: string;
  mating_date: string;
  due_date: string;
  status: MatingStatus;
  entity_id: string;
}

// =============================================================================
// Sales Types (Preview)
// =============================================================================

export type SaleStage = 'INQUIRY' | 'RESERVED' | 'CONTRACT' | 'AVS_SUBMITTED' | 'DELIVERED';

export interface Sale {
  id: string;
  puppy_id: string;
  customer_id: string;
  stage: SaleStage;
  price: number;
  deposit_amount: number;
  entity_id: string;
}

// =============================================================================
// API Response Types
// =============================================================================

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  error: string;
  details?: string;
  reference?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  results: T[];
}

// =============================================================================
// Navigation Types
// =============================================================================

export interface NavItem {
  label: string;
  href: string;
  icon: string;
  required_roles: Role[];
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

// =============================================================================
// Audit Log Types
// =============================================================================

export type AuditAction = 'create' | 'update' | 'delete' | 'login' | 'logout' | 'view' | 'export';

export interface AuditLog {
  uuid: string;
  actor: User | null;
  action: AuditAction;
  resource_type: string;
  resource_id: string;
  payload: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

// =============================================================================
// Dog Filter Types
// =============================================================================

export interface DogFilterParams {
  status?: DogStatus | undefined;
  entity?: string | undefined;
  breed?: string | undefined;
  gender?: 'M' | 'F' | undefined;
  search?: string | undefined;
  unit?: string | undefined;
  page?: number | undefined;
  limit?: number | undefined;
}

// =============================================================================
// Dog API Types
// =============================================================================

export interface DogCreate {
  microchip: string;
  name: string;
  breed: string;
  dob: string;
  gender: 'M' | 'F';
  colour: string;
  entity_id: string;
  unit?: string;
  dam_id?: string | null;
  sire_id?: string | null;
}

export interface DogUpdate extends Partial<DogCreate> {}

export interface DogListResponse {
  count: number;
  results: Dog[];
}

export interface DogDetailResponse {
  dog: Dog;
  health_records?: HealthRecord[];
  vaccinations?: Vaccination[];
}



// =============================================================================
// Health Types
// =============================================================================

export interface HealthRecord {
  id: string;
  dog_id: string;
  type: string;
  description: string;
  date: string;
  vet_name?: string;
}

export interface HealthRecordCreate {
  dog_id: string;
  type: string;
  description: string;
  date: string;
  vet_name?: string;
}

export interface Vaccination {
  id: string;
  dog_id: string;
  name: string;
  date: string;
  due_date: string;
  status: 'GIVEN' | 'DUE' | 'OVERDUE';
}

export interface VaccinationCreate {
  dog_id: string;
  name: string;
  date: string;
  due_date: string;
}

// =============================================================================
// Alert Types
// =============================================================================

export interface AlertCard {
  id: string;
  type: 'in_heat' | 'mating' | 'whelping' | 'health' | 'vaccine' | 'rehome' | 'vaccine_overdue' | 'vaccine_due_soon' | 'rehome_overdue' | 'nursing_flags' | 'nparks_countdown' | '8week_litters';
  title: string;
  message?: string;
  severity?: 'info' | 'warning' | 'critical';
  dog_id?: string;
  dog_name?: string;
  created_at?: string;
  action_url?: string;
  // Dashboard card display properties
  color?: string;
  trend?: 'up' | 'down' | 'flat';
  count?: number;
}

// =============================================================================
// Dashboard Types (Phase 8)
// =============================================================================

export interface DashboardStats {
  total_dogs: number;
  active_litters: number;
  pending_agreements: number;
  overdue_vaccinations: number;
}

export interface NParksCountdown {
  days: number;
  deadline_date: string;
  status: 'upcoming' | 'due_soon' | 'overdue';
}

export interface ActivityFeedItem {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  actor_name: string;
  timestamp: string;
}

export interface RevenueMonthlyData {
  month: string;
  month_label: string;
  total_sales: number;
  gst_collected: number;
}

export interface RevenueSummary {
  period_months: number;
  monthly_data: RevenueMonthlyData[];
  total_revenue: number;
  total_gst: number;
}

export interface SalesPipeline {
  draft_count: number;
  signed_count: number;
}

export interface HealthAlerts {
  overdue_vaccines: number;
  nursing_flags: number;
}

export interface DashboardMetrics {
  role: string;
  entity_id: string | null;
  stats: DashboardStats;
  alerts: AlertCard[];
  nparks_countdown: NParksCountdown;
  recent_activity: ActivityFeedItem[];
  revenue_summary?: RevenueSummary;
  health_alerts?: HealthAlerts;
  sales_pipeline?: SalesPipeline;
}

// =============================================================================
// Ground Log Types (Phase 3)
// =============================================================================

export interface InHeatLog {
  id: string;
  dog_id: string;
  draminski_reading: number;
  mating_window: 'EARLY' | 'RISING' | 'FAST' | 'PEAK' | 'MATE_NOW';
  notes?: string;
  created_at: string;
  created_by_name?: string;
}

export interface MatedLog {
  id: string;
  dog_id: string;
  sire_id: string;
  sire_name: string;
  method: 'natural' | 'ai' | 'surgical';
  sire2_id?: string;
  sire2_name?: string;
  notes?: string;
  created_at: string;
  created_by_name?: string;
}

export interface WhelpedLog {
  id: string;
  dog_id: string;
  method: 'natural' | 'c_section' | 'assisted';
  alive_count: number;
  stillborn_count: number;
  pups: WhelpedPup[];
  notes?: string;
  created_at: string;
  created_by_name?: string;
}

export interface WhelpedPup {
  id: string;
  gender: 'male' | 'female';
  colour: string;
  birth_weight: number;
}

export interface HealthObsLog {
  id: string;
  dog_id: string;
  category: string;
  description: string;
  temperature?: number;
  weight?: number;
  photos?: string[];
  created_at: string;
  created_by_name?: string;
}

export interface WeightLog {
  id: string;
  dog_id: string;
  weight: number;
  created_at: string;
  created_by_name?: string;
}

export interface NursingFlagLog {
  id: string;
  dog_id: string;
  section: string;
  pup_number?: number;
  flag_type: string;
  photos?: string[];
  severity: 'info' | 'warning' | 'serious';
  created_at: string;
  created_by_name?: string;
}

export interface NotReadyLog {
  id: string;
  dog_id: string;
  notes?: string;
  expected_date?: string;
  created_at: string;
  created_by_name?: string;
}

export type SortField = 'name' | 'created_at' | 'breed' | 'status' | 'unit' | 'microchip' | 'dob' | 'gender' | 'entity' | 'updated_at' | 'id';
