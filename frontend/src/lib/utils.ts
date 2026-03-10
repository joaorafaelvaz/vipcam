import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import { EMOTION_COLORS, EMOTION_LABELS, type EmotionName } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatEmotion(emotion: string): string {
  return EMOTION_LABELS[emotion as EmotionName] || emotion;
}

export function emotionColor(emotion: string): string {
  return EMOTION_COLORS[emotion as EmotionName] || "#6b7280";
}

export function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return "agora";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}min atrás`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h atrás`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d atrás`;
  return date.toLocaleDateString("pt-BR");
}

export function satisfactionLevel(score: number | null): {
  label: string;
  color: string;
} {
  if (score === null) return { label: "N/A", color: "#6b7280" };
  if (score >= 7) return { label: "Boa", color: "#22c55e" };
  if (score >= 4) return { label: "Regular", color: "#eab308" };
  return { label: "Baixa", color: "#ef4444" };
}

export function occupancyLevel(count: number): string {
  if (count <= 2) return "low";
  if (count <= 5) return "moderate";
  return "high";
}
