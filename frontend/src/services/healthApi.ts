/**
 * Milestone 1's only API call. Later milestones add authApi.ts,
 * conversationApi.ts and chatApi.ts alongside this file, all built on api.ts.
 */

import { apiGet } from './api';

export interface HealthResponse {
  status: string;
  database: string;
  version: string;
}

export const getHealth = () => apiGet<HealthResponse>('/api/health');
