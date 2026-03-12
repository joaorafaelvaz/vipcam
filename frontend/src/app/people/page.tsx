"use client";

import { useCallback, useEffect, useState } from "react";
import { GitMerge, Search, X, Check, User } from "lucide-react";

import { Header } from "@/components/layout/Header";
import { PersonCard } from "@/components/people/PersonCard";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { usePersonStore } from "@/stores/usePersonStore";
import type { Person } from "@/types";

export default function PeoplePage() {
  const { persons, loading, fetchPersons, search, setSearch, mergePersons } =
    usePersonStore();
  const [inputValue, setInputValue] = useState(search);
  const [mergeMode, setMergeMode] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [merging, setMerging] = useState(false);
  const [mergeError, setMergeError] = useState<string | null>(null);

  useEffect(() => {
    fetchPersons(search || undefined);
  }, [fetchPersons, search]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(inputValue);
  };

  const toggleSelect = useCallback((id: string) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
  }, []);

  const cancelMerge = () => {
    setMergeMode(false);
    setSelected([]);
    setMergeError(null);
  };

  const handleMerge = async () => {
    if (selected.length !== 2) return;
    setMerging(true);
    setMergeError(null);
    try {
      await mergePersons(selected[0], selected[1]);
      setSelected([]);
      setMergeMode(false);
    } catch (err) {
      setMergeError((err as Error).message);
    } finally {
      setMerging(false);
    }
  };

  const selectedPersons = selected
    .map((id) => persons.find((p) => p.id === id))
    .filter(Boolean) as Person[];

  return (
    <div>
      <Header
        title="Pessoas"
        subtitle={`${persons.length} pessoas reconhecidas`}
      />

      <div className="p-6 space-y-6">
        {/* Toolbar */}
        <div className="flex items-center gap-3 flex-wrap">
          <form
            onSubmit={handleSearch}
            className="relative flex-1 min-w-[200px] max-w-md"
          >
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
            <input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Buscar por nome..."
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 pl-10 pr-4 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-amber-500 focus:outline-none"
            />
          </form>

          {!mergeMode ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setMergeMode(true)}
              disabled={persons.length < 2}
            >
              <GitMerge className="h-4 w-4" />
              Mesclar Pessoas
            </Button>
          ) : (
            <Button variant="ghost" size="sm" onClick={cancelMerge}>
              <X className="h-4 w-4" />
              Cancelar
            </Button>
          )}
        </div>

        {/* Merge bar */}
        {mergeMode && (
          <Card className="border-amber-500/30 bg-amber-500/5">
            <div className="p-4 space-y-3">
              <p className="text-sm text-amber-400 font-medium">
                Selecione 2 pessoas para mesclar. A primeira (origem) sera
                absorvida pela segunda (destino).
              </p>

              {selectedPersons.length > 0 && (
                <div className="flex items-center gap-3 flex-wrap">
                  {selectedPersons.map((p, idx) => (
                    <div key={p.id} className="flex items-center gap-2">
                      <div className="flex items-center gap-2 rounded-lg bg-zinc-800 px-3 py-2 border border-zinc-700">
                        <div className="h-8 w-8 rounded-full bg-zinc-700 flex items-center justify-center overflow-hidden shrink-0">
                          {p.thumbnail_path ? (
                            <img
                              src={`/api/persons/${p.id}/thumbnail`}
                              alt=""
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <User className="h-4 w-4 text-zinc-500" />
                          )}
                        </div>
                        <div>
                          <span className="text-sm text-zinc-200">
                            {p.display_name || `#${p.id.slice(0, 6)}`}
                          </span>
                          <span className="block text-[10px] text-zinc-500">
                            {p.total_visits} visitas
                          </span>
                        </div>
                        <Badge variant={idx === 0 ? "warning" : "success"}>
                          {idx === 0 ? "Origem" : "Destino"}
                        </Badge>
                      </div>
                      {idx === 0 && selectedPersons.length === 2 && (
                        <span className="text-zinc-600 text-lg">→</span>
                      )}
                    </div>
                  ))}

                  {selectedPersons.length === 2 && (
                    <Button size="sm" onClick={handleMerge} disabled={merging}>
                      <Check className="h-4 w-4" />
                      {merging ? "Mesclando..." : "Confirmar"}
                    </Button>
                  )}
                </div>
              )}

              {mergeError && (
                <p className="text-sm text-red-400">{mergeError}</p>
              )}
            </div>
          </Card>
        )}

        {/* Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-amber-400 border-t-transparent" />
          </div>
        ) : persons.length === 0 ? (
          <div className="flex items-center justify-center rounded-xl border border-dashed border-zinc-800 py-20">
            <p className="text-sm text-zinc-500">
              {search
                ? "Nenhuma pessoa encontrada"
                : "Nenhuma pessoa reconhecida ainda"}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {persons.map((person) =>
              mergeMode ? (
                <div
                  key={person.id}
                  onClick={() => toggleSelect(person.id)}
                  className="cursor-pointer relative"
                >
                  <div
                    className={`rounded-xl transition-all duration-200 ${
                      selected.includes(person.id)
                        ? "ring-2 ring-amber-500 ring-offset-2 ring-offset-zinc-900"
                        : "hover:ring-1 hover:ring-zinc-700"
                    }`}
                  >
                    <PersonCard person={person} disableLink />
                  </div>
                  {selected.includes(person.id) && (
                    <div className="absolute top-3 right-3 h-6 w-6 rounded-full bg-amber-500 flex items-center justify-center z-10">
                      <span className="text-xs font-bold text-zinc-900">
                        {selected.indexOf(person.id) + 1}
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <PersonCard key={person.id} person={person} />
              ),
            )}
          </div>
        )}
      </div>
    </div>
  );
}
