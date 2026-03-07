export type AnalysisStatus = "idle" | "running" | "complete";

export interface AnalysisState {
  name: string;
  riskScore: number;
  flagged: boolean;
  inDegree: number;
  outDegree: number;
  selfLoop: boolean;
  resetDistance: number;
  fix?: string;
}

export interface RewardHistoryPoint {
  episode: number;
  reward: number;
}

export interface AnalysisResults {
  totalStates: number;
  flaggedCount: number;
  securityScore: number;
  patchVerified: boolean;
  states: AnalysisState[];
  rewardHistory: RewardHistoryPoint[];
}