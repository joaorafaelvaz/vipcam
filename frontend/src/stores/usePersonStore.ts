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

  setSearch: (search) => set({ search }),
}));
