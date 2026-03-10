export interface Camera {
  id: string;
  name: string;
  location: string | null;
  rtsp_url: string;
  franchise_unit_id: number | null;
  is_active: boolean;
  resolution: string;
  fps_target: number;
  created_at: string;
  updated_at: string;
}

export interface Person {
  id: string;
  display_name: string | null;
  person_type: "client" | "employee" | "unknown";
  first_seen_at: string;
  last_seen_at: string;
  total_visits: number;
  avg_satisfaction: number | null;
  estimated_age: number | null;
  estimated_gender: string | null;
  thumbnail_path: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmotionScores {
  anger: number;
  contempt: number;
  disgust: number;
  fear: number;
  happiness: number;
  neutral: number;
  sadness: number;
  surprise: number;
}

export interface EmotionRecord extends EmotionScores {
  id: string;
  person_id: string;
  camera_id: string;
  dominant_emotion: string;
  valence: number | null;
  arousal: number | null;
  satisfaction_score: number | null;
  face_confidence: number | null;
  captured_at: string;
}

export interface WSPersonData {
  person_id: string;
  display_name: string | null;
  person_type: string;
  dominant_emotion: string;
  satisfaction_score: number | null;
  valence: number | null;
  emotions: EmotionScores;
  bbox: number[];
  age: number | null;
  gender: string | null;
  is_new: boolean;
  visit_count: number;
}

export interface WSAnalysisUpdate {
  type: "analysis_update";
  camera_id: string;
  camera_name: string;
  timestamp: string;
  person_count: number;
  faces_detected: number;
  persons: WSPersonData[];
  processing_time_ms: number;
}

export interface EmotionTimelinePoint {
  timestamp: string;
  anger: number;
  contempt: number;
  disgust: number;
  fear: number;
  happiness: number;
  neutral: number;
  sadness: number;
  surprise: number;
  avg_satisfaction: number | null;
}

export interface OccupancyPoint {
  timestamp: string;
  avg_count: number;
  max_count: number;
  min_count: number;
}

export type EmotionName = keyof EmotionScores;

export const EMOTION_NAMES: EmotionName[] = [
  "anger",
  "contempt",
  "disgust",
  "fear",
  "happiness",
  "neutral",
  "sadness",
  "surprise",
];

export const EMOTION_LABELS: Record<EmotionName, string> = {
  anger: "Raiva",
  contempt: "Desprezo",
  disgust: "Nojo",
  fear: "Medo",
  happiness: "Felicidade",
  neutral: "Neutro",
  sadness: "Tristeza",
  surprise: "Surpresa",
};

export const EMOTION_COLORS: Record<EmotionName, string> = {
  anger: "#ef4444",
  contempt: "#a855f7",
  disgust: "#84cc16",
  fear: "#f97316",
  happiness: "#22c55e",
  neutral: "#6b7280",
  sadness: "#3b82f6",
  surprise: "#eab308",
};
