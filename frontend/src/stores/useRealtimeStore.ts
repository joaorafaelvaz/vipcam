import { create } from "zustand";

import { createWSConnection } from "@/lib/ws";
import type { WSAnalysisUpdate, WSPersonData } from "@/types";

interface RealtimeState {
  connected: boolean;
  occupancy: Record<string, number>;
  latestPersons: Record<string, WSPersonData[]>;
  processingTime: Record<string, number>;
  connect: () => void;
  disconnect: () => void;
}

let wsConnection: ReturnType<typeof createWSConnection> | null = null;

export const useRealtimeStore = create<RealtimeState>((set) => ({
  connected: false,
  occupancy: {},
  latestPersons: {},
  processingTime: {},

  connect: () => {
    if (wsConnection) return;

    const wsUrl =
      process.env.NEXT_PUBLIC_WS_URL || `ws://${window.location.hostname}:8000`;

    wsConnection = createWSConnection(
      `${wsUrl}/ws/live`,
      (data) => {
        const msg = data as WSAnalysisUpdate;
        if (msg.type === "analysis_update") {
          set((state) => ({
            occupancy: { ...state.occupancy, [msg.camera_id]: msg.person_count },
            latestPersons: {
              ...state.latestPersons,
              [msg.camera_id]: msg.persons,
            },
            processingTime: {
              ...state.processingTime,
              [msg.camera_id]: msg.processing_time_ms,
            },
          }));
        }
      },
      (connected) => set({ connected }),
    );
  },

  disconnect: () => {
    wsConnection?.close();
    wsConnection = null;
    set({ connected: false });
  },
}));
