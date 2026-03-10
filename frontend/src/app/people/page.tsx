"use client";

import { useEffect, useState } from "react";
import { Search } from "lucide-react";

import { Header } from "@/components/layout/Header";
import { PersonCard } from "@/components/people/PersonCard";
import { usePersonStore } from "@/stores/usePersonStore";

export default function PeoplePage() {
  const { persons, loading, fetchPersons, search, setSearch } = usePersonStore();
  const [inputValue, setInputValue] = useState(search);

  useEffect(() => {
    fetchPersons(search || undefined);
  }, [fetchPersons, search]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(inputValue);
  };

  return (
    <div>
      <Header
        title="Pessoas"
        subtitle={`${persons.length} pessoas reconhecidas`}
      />

      <div className="p-6 space-y-6">
        {/* Search */}
        <form onSubmit={handleSearch} className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Buscar por nome..."
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 pl-10 pr-4 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-amber-500 focus:outline-none"
          />
        </form>

        {/* Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-amber-400 border-t-transparent" />
          </div>
        ) : persons.length === 0 ? (
          <div className="flex items-center justify-center rounded-xl border border-dashed border-zinc-800 py-20">
            <p className="text-sm text-zinc-500">
              {search ? "Nenhuma pessoa encontrada" : "Nenhuma pessoa reconhecida ainda"}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {persons.map((person) => (
              <PersonCard key={person.id} person={person} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
