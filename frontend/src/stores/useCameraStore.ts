import { create } from "zustand";

import { api } from "@/lib/api";
import type { Camera } from "@/types";

interface CameraState {
  cameras: Camera[];
  loading: boolean;
  error: string | null;
  fetchCameras: () => Promise<void>;
  createCamera: (data: Partial<Camera>) => Promise<Camera>;
  updateCamera: (id: string, data: Partial<Camera>) => Promise<void>;
  deleteCamera: (id: string) => Promise<void>;
}

export const useCameraStore = create<CameraState>((set, get) => ({
  cameras: [],
  loading: false,
  error: null,

  fetchCameras: async () => {
    set({ loading: true, error: null });
    try {
      const cameras = await api.get<Camera[]>("/cameras");
      set({ cameras, loading: false });
    } catch (err) {
      set({ error: (err as Error).message, loading: false });
    }
  },

  createCamera: async (data) => {
    const camera = await api.post<Camera>("/cameras", data);
    set({ cameras: [...get().cameras, camera] });
    return camera;
  },

  updateCamera: async (id, data) => {
    const updated = await api.patch<Camera>(`/cameras/${id}`, data);
    set({
      cameras: get().cameras.map((c) => (c.id === id ? updated : c)),
    });
  },

  deleteCamera: async (id) => {
    await api.del(`/cameras/${id}`);
    set({ cameras: get().cameras.filter((c) => c.id !== id) });
  },
}));
