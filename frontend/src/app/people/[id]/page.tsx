"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, User } from "lucide-react";

import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";
import { formatEmotion, emotionColor, formatTimeAgo } from "@/lib/utils";
import type { Person, EmotionRecord } from "@/types";

export default function PersonDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [person, setPerson] = useState<Person | null>(null);
  const [emotions, setEmotions] = useState<EmotionRecord[]>([]);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");

  useEffect(() => {
    api.get<Person>(`/persons/${id}`).then((p) => {
      setPerson(p);
      setName(p.display_name || "");
    });
    api.get<EmotionRecord[]>(`/persons/${id}/emotions?limit=20`).then(setEmotions);
  }, [id]);

  const handleSave = async () => {
    const updated = await api.patch<Person>(`/persons/${id}`, {
      display_name: name || null,
    });
    setPerson(updated);
    setEditing(false);
  };

  if (!person) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-amber-400 border-t-transparent" />
      </div>
    );
  }

  return (
    <div>
      <Header
        title={person.display_name || `Pessoa #${person.id.slice(0, 6)}`}
        subtitle={`${person.total_visits} visitas`}
      />

      <div className="p-6 space-y-6">
        <Link
          href="/people"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar
        </Link>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Profile */}
          <Card>
            <CardContent className="flex flex-col items-center text-center py-6">
              <div className="h-24 w-24 rounded-full bg-zinc-800 flex items-center justify-center overflow-hidden mb-4">
                {person.thumbnail_path ? (
                  <img
                    src={`/api/persons/${id}/thumbnail`}
                    alt=""
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <User className="h-10 w-10 text-zinc-600" />
                )}
              </div>

              {editing ? (
                <div className="w-full space-y-2">
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 px-3 py-2 text-sm text-center text-zinc-200 focus:border-amber-500 focus:outline-none"
                    placeholder="Nome da pessoa"
                  />
                  <div className="flex gap-2 justify-center">
                    <Button size="sm" onClick={handleSave}>Salvar</Button>
                    <Button size="sm" variant="secondary" onClick={() => setEditing(false)}>
                      Cancelar
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <h3 className="text-lg font-semibold text-zinc-100">
                    {person.display_name || "Sem nome"}
                  </h3>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="mt-1"
                    onClick={() => setEditing(true)}
                  >
                    Editar nome
                  </Button>
                </>
              )}

              <div className="mt-4 space-y-2 w-full text-sm">
                <div className="flex justify-between text-zinc-400">
                  <span>Tipo</span>
                  <Badge variant={person.person_type === "employee" ? "success" : "info"}>
                    {person.person_type}
                  </Badge>
                </div>
                <div className="flex justify-between text-zinc-400">
                  <span>Idade est.</span>
                  <span className="text-zinc-200">{person.estimated_age ?? "—"}</span>
                </div>
                <div className="flex justify-between text-zinc-400">
                  <span>Genero est.</span>
                  <span className="text-zinc-200">{person.estimated_gender ?? "—"}</span>
                </div>
                <div className="flex justify-between text-zinc-400">
                  <span>Primeira vez</span>
                  <span className="text-zinc-200">{formatTimeAgo(person.first_seen_at)}</span>
                </div>
                <div className="flex justify-between text-zinc-400">
                  <span>Ultima vez</span>
                  <span className="text-zinc-200">{formatTimeAgo(person.last_seen_at)}</span>
                </div>
                <div className="flex justify-between text-zinc-400">
                  <span>Satisfacao media</span>
                  <span className="text-zinc-200">
                    {person.avg_satisfaction?.toFixed(1) ?? "—"}/10
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Emotion history */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <h3 className="text-sm font-medium text-zinc-300">
                Historico de Emocoes ({emotions.length})
              </h3>
            </CardHeader>
            <CardContent>
              {emotions.length === 0 ? (
                <p className="text-sm text-zinc-600 text-center py-8">
                  Sem registros de emocao ainda
                </p>
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {emotions.map((rec) => (
                    <div
                      key={rec.id}
                      className="flex items-center justify-between py-2 border-b border-zinc-800/30 last:border-0"
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className="h-3 w-3 rounded-full"
                          style={{ backgroundColor: emotionColor(rec.dominant_emotion) }}
                        />
                        <span className="text-sm text-zinc-200">
                          {formatEmotion(rec.dominant_emotion)}
                        </span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm tabular-nums text-zinc-300">
                          {rec.satisfaction_score?.toFixed(1) ?? "—"}
                        </span>
                        <span className="text-xs text-zinc-600">
                          {new Date(rec.captured_at).toLocaleTimeString("pt-BR")}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
