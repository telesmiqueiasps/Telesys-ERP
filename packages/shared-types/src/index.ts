/**
 * Foundation shared types for Telesys ERP
 * General communication and structure contracts without business logic.
 */

export interface ApiResponse<T = unknown> {
  success: boolean;
  message?: string;
  data: T;
  timestamp: string;
}

export interface PaginationMeta {
  page: number;
  pageSize: number;
  totalRecords: number;
  totalPages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationMeta;
}

export interface SystemHealth {
  status: "healthy" | "unhealthy" | "degraded";
  version: string;
  database: "connected" | "disconnected";
  uptimeSeconds?: number;
}

export type CommonStatus = "active" | "inactive" | "pending" | "archived";
