import { create } from "zustand";

import { api } from "@/lib/api";
import type { Person } from "@/types";

interface PersonState {
  persons: Person[];
  loading: boolean;
  error: string | null;
  search: string;
  fetchPersons: (search?: string) => Promise<void>;
  updatePerson: (id: string, data: Partial<Person>) => Promise<void>;
  mergePersons: (sourceId: string, targetId: string) => Promise<Person>;
  deletePerson: (id: string) => Promise<void>;
  setSearch: (search: string) => void;
}

export const usePersonStore = create<PersonState>((set, get) => ({
  persons: [],
  loading: false,
  error: null,
  search: "",

  fetchPersons: async (search) => {
    set({ loading: true, error: null });
    try {
      const query = search ? `?search=${encodeURIComponent(search)}` : "";
      const persons = await api.get<Person[]>(`/persons${query}`);
      set({ persons, loading: false });
    } catch (err) {
      set({ error: (err as Error).message, loading: false });
    }
  },

  updatePerson: async (id, data) => {
    const updated = await api.patch<Person>(`/persons/${id}`, data);
    set({
      persons: get().persons.map((p) => (p.id === id ? updated : p)),
    });
  },

  mergePersons: async (sourceId, targetId) => {
    const merged = await api.post<Person>("/persons/merge", {
      source_id: sourceId,
      target_id: targetId,
    });
    // Remove source, update target in list
    set({
      persons: get()
        .persons.filter((p) => p.id !== sourceId)
        .map((p) => (p.id === targetId ? merged : p)),
    });
    return merged;
  },

  deletePerson: async (id) => {
    await api.del(`/persons/${id}`);
    set({ persons: get().persons.filter((p) => p.id !== id) });
  },

  setSearch: (search) => set({ search }),
}));
