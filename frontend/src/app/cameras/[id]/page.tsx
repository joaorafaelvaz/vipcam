"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useRealtimeStore } from "@/stores/useRealtimeStore";
import { api } from "@/lib/api";
import { formatEmotion, emotionColor } from "@/lib/utils";
import type { Camera } from "@/types";

export default function CameraDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [camera, setCamera] = useState<Camera | null>(null);
  const occupancy = useRealtimeStore((s) => s.occupancy[id] ?? 0);
  const persons = useRealtimeStore((s) => s.latestPersons[id] ?? []);

  useEffect(() => {
    api.get<Camera>(`/cameras/${id}`).then(setCamera);
  }, [id]);

  if (!camera) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-amber-400 border-t-transparent" />
      </div>
    );
  }

  return (
    <div>
      <Header title={camera.name} subtitle={camera.location || undefined} />

      <div className="p-6 space-y-6">
        <Link
          href="/cameras"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar
        </Link>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Snapshot */}
          <Card className="lg:col-span-2">
            <div className="aspect-video bg-zinc-900 rounded-t-xl overflow-hidden">
              <img
                src={`/api/cameras/${id}/snapshot`}
                alt={camera.name}
                className="h-full w-full object-cover"
              />
            </div>
            <CardContent>
              <div className="flex items-center justify-between">
                <Badge variant={camera.is_active ? "success" : "default"}>
                  {camera.is_active ? "Online" : "Offline"}
                </Badge>
                <span className="text-sm text-zinc-400 tabular-nums">
                  {occupancy} pessoas detectadas
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Live persons */}
          <Card>
            <CardHeader>
              <h3 className="text-sm font-medium text-zinc-300">
                Pessoas Visiveis ({persons.length})
              </h3>
            </CardHeader>
            <CardContent className="space-y-3">
              {persons.length === 0 ? (
                <p className="text-xs text-zinc-600">Nenhuma pessoa detectada</p>
              ) : (
                persons.map((person, i) => (
                  <div
                    key={person.person_id || i}
                    className="flex items-center justify-between py-2 border-b border-zinc-800/30 last:border-0"
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="h-3 w-3 rounded-full"
                        style={{
                          backgroundColor: emotionColor(person.dominant_emotion),
                        }}
                      />
                      <div>
                        <p className="text-sm text-zinc-200">
                          {person.display_name || `Pessoa ${i + 1}`}
                        </p>
                        <p className="text-[10px] text-zinc-500">
                          {formatEmotion(person.dominant_emotion)} ·{" "}
                          {person.age ? `${person.age} anos` : ""}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium tabular-nums text-zinc-200">
                        {person.satisfaction_score?.toFixed(1) ?? "—"}
                      </p>
                      <p className="text-[10px] text-zinc-600">satisfacao</p>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
