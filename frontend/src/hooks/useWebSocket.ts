"use client";

import { useEffect } from "react";

import { useRealtimeStore } from "@/stores/useRealtimeStore";

export function useWebSocket() {
  const { connected, occupancy, latestPersons, processingTime, connect, disconnect } =
    useRealtimeStore();

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { connected, occupancy, latestPersons, processingTime };
}
