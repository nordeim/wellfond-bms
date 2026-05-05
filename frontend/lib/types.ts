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
  firstName: string;
  lastName: string;
  role: Role;
  entityId: string | null;
  pdpaConsent: boolean;
  isActive: boolean;
  createdAt: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  csrfToken: string;
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
  isActive: boolean;
  isHolding: boolean;
  gstRate: number;
  avsLicenseNumber: string | null;
  avsLicenseExpiry: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  createdAt: string;
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
  entityId: string;
  status: DogStatus;
  damId: string | null;
  sireId: string | null;
  unit: string;
  dnaStatus: DNAStatus;
  notes: string;
  imageUrl: string | null;
  // Extended properties
  ageYears?: number;
  ageDisplay?: string;
  damName?: string;
  sireName?: string;
}

// =============================================================================
// Breeding Types (Preview)
// =============================================================================

export type MatingStatus = 'PLANNED' | 'CONFIRMED' | 'PREGNANT' | 'WHELPED';

export interface Mating {
  id: string;
  sireId: string;
  damId: string;
  matingDate: string;
  dueDate: string;
  status: MatingStatus;
  entityId: string;
}

// =============================================================================
// Sales Types (Preview)
// =============================================================================

export type SaleStage = 'INQUIRY' | 'RESERVED' | 'CONTRACT' | 'AVS_SUBMITTED' | 'DELIVERED';

export interface Sale {
  id: string;
  puppyId: string;
  customerId: string;
  stage: SaleStage;
  price: number;
  depositAmount: number;
  entityId: string;
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
  requiredRoles: Role[];
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
  resourceType: string;
  resourceId: string;
  payload: Record<string, unknown>;
  ipAddress: string | null;
  createdAt: string;
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
  entityId: string;
  unit?: string;
  damId?: string | null;
  sireId?: string | null;
}

export interface DogUpdate extends Partial<DogCreate> {}

export interface DogListResponse {
  count: number;
  results: Dog[];
}

export interface DogDetailResponse {
  dog: Dog;
  healthRecords?: HealthRecord[];
  vaccinations?: Vaccination[];
}



// =============================================================================
// Health Types
// =============================================================================

export interface HealthRecord {
  id: string;
  dogId: string;
  type: string;
  description: string;
  date: string;
  vetName?: string;
}

export interface HealthRecordCreate {
  dogId: string;
  type: string;
  description: string;
  date: string;
  vetName?: string;
}

export interface Vaccination {
  id: string;
  dogId: string;
  name: string;
  date: string;
  dueDate: string;
  status: 'GIVEN' | 'DUE' | 'OVERDUE';
}

export interface VaccinationCreate {
  dogId: string;
  name: string;
  date: string;
  dueDate: string;
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
  dogId?: string;
  dogName?: string;
  createdAt?: string;
  actionUrl?: string;
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
  dogId: string;
  draminskiReading: number;
  matingWindow: 'EARLY' | 'RISING' | 'FAST' | 'PEAK' | 'MATE_NOW';
  notes?: string;
  createdAt: string;
  createdByName?: string;
}

export interface MatedLog {
  id: string;
  dogId: string;
  sireId: string;
  sireName: string;
  method: 'natural' | 'ai' | 'surgical';
  sire2Id?: string;
  sire2Name?: string;
  notes?: string;
  createdAt: string;
  createdByName?: string;
}

export interface WhelpedLog {
  id: string;
  dogId: string;
  method: 'natural' | 'c_section' | 'assisted';
  aliveCount: number;
  stillbornCount: number;
  pups: WhelpedPup[];
  notes?: string;
  createdAt: string;
  createdByName?: string;
}

export interface WhelpedPup {
  id: string;
  gender: 'male' | 'female';
  colour: string;
  birthWeight: number;
}

export interface HealthObsLog {
  id: string;
  dogId: string;
  category: string;
  description: string;
  temperature?: number;
  weight?: number;
  photos?: string[];
  createdAt: string;
  createdByName?: string;
}

export interface WeightLog {
  id: string;
  dogId: string;
  weight: number;
  createdAt: string;
  createdByName?: string;
}

export interface NursingFlagLog {
  id: string;
  dogId: string;
  section: string;
  pupNumber?: number;
  flagType: string;
  photos?: string[];
  severity: 'info' | 'warning' | 'serious';
  createdAt: string;
  createdByName?: string;
}

export interface NotReadyLog {
  id: string;
  dogId: string;
  notes?: string;
  expectedDate?: string;
  createdAt: string;
  createdByName?: string;
}

export type SortField = 'name' | 'created_at' | 'breed' | 'status' | 'unit' | 'microchip' | 'dob' | 'gender' | 'entity' | 'updated_at' | 'id';
