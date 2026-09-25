import { z } from "zod";

/**
 * Foundational schema validators for common queries and utility data.
 */
export const PaginationQuerySchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  pageSize: z.coerce.number().int().min(1).max(100).default(20),
  search: z.string().optional(),
  sortBy: z.string().optional(),
  sortOrder: z.enum(["asc", "desc"]).default("asc")
});

export type PaginationQuery = z.infer<typeof PaginationQuerySchema>;

export const IdParamSchema = z.object({
  id: z.string().uuid({ message: "Invalid UUID format" })
});

export type IdParam = z.infer<typeof IdParamSchema>;

export const SystemHealthSchema = z.object({
  status: z.enum(["healthy", "unhealthy", "degraded"]),
  version: z.string(),
  database: z.enum(["connected", "disconnected"]),
  uptimeSeconds: z.number().optional()
});

export type SystemHealthData = z.infer<typeof SystemHealthSchema>;
