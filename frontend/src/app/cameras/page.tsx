"use client";

import { useEffect, useState } from "react";
import { Plus, Trash2, Edit2 } from "lucide-react";

import { Header } from "@/components/layout/Header";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { useCameraStore } from "@/stores/useCameraStore";
import { useRealtimeStore } from "@/stores/useRealtimeStore";

export default function CamerasPage() {
  const { cameras, fetchCameras, createCamera, deleteCamera } =
    useCameraStore();
  const occupancy = useRealtimeStore((s) => s.occupancy);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [rtspUrl, setRtspUrl] = useState("");
  const [fpsTarget, setFpsTarget] = useState(5);

  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    try {
      await createCamera({
        name,
        location: location || null,
        rtsp_url: rtspUrl,
        fps_target: fpsTarget,
      });
      setShowForm(false);
      setName("");
      setLocation("");
      setRtspUrl("");
      setFpsTarget(5);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro ao salvar camera");
    }
  };

  return (
    <div>
      <Header title="Cameras" subtitle={`${cameras.length} cameras configuradas`} />

      <div className="p-6 space-y-6">
        {/* Actions */}
        <div className="flex justify-end">
          <Button onClick={() => setShowForm(!showForm)}>
            <Plus className="h-4 w-4" />
            Adicionar Camera
          </Button>
        </div>

        {/* Add form */}
        {showForm && (
          <Card>
            <CardHeader>
              <h3 className="text-sm font-medium">Nova Camera</h3>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">Nome</label>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 px-3 py-2 text-sm text-zinc-200 focus:border-amber-500 focus:outline-none"
                    placeholder="Salao Principal"
                  />
                </div>
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">Localizacao</label>
                  <input
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 px-3 py-2 text-sm text-zinc-200 focus:border-amber-500 focus:outline-none"
                    placeholder="Unidade Centro"
                  />
                </div>
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">URL RTSP</label>
                  <input
                    value={rtspUrl}
                    onChange={(e) => setRtspUrl(e.target.value)}
                    required
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 px-3 py-2 text-sm text-zinc-200 focus:border-amber-500 focus:outline-none"
                    placeholder="rtsp://admin:senha@192.168.0.101:554/onvif1"
                  />
                </div>
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">FPS Target</label>
                  <input
                    type="number"
                    value={fpsTarget}
                    onChange={(e) => setFpsTarget(Number(e.target.value))}
                    min={1}
                    max={30}
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 px-3 py-2 text-sm text-zinc-200 focus:border-amber-500 focus:outline-none"
                  />
                </div>
                {formError && (
                  <div className="col-span-2 rounded-lg bg-red-500/10 border border-red-500/30 px-3 py-2 text-sm text-red-400">
                    {formError}
                  </div>
                )}
                <div className="col-span-2 flex gap-2 justify-end">
                  <Button variant="secondary" type="button" onClick={() => setShowForm(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit">Salvar</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Camera list */}
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-800/50">
                  <th className="px-5 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">
                    Camera
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">
                    Localizacao
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">
                    Ocupacao
                  </th>
                  <th className="px-5 py-3 text-right text-xs font-medium text-zinc-500 uppercase tracking-wider">
                    Acoes
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/30">
                {cameras.map((camera) => (
                  <tr key={camera.id} className="hover:bg-zinc-900/50 transition-colors">
                    <td className="px-5 py-3">
                      <div className="font-medium text-zinc-200">{camera.name}</div>
                      <div className="text-[11px] text-zinc-600 truncate max-w-[200px]">
                        {camera.rtsp_url}
                      </div>
                    </td>
                    <td className="px-5 py-3 text-zinc-400">
                      {camera.location || "—"}
                    </td>
                    <td className="px-5 py-3">
                      <Badge variant={camera.is_active ? "success" : "default"}>
                        {camera.is_active ? "Ativa" : "Inativa"}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 tabular-nums text-zinc-300">
                      {occupancy[camera.id] ?? 0} pessoas
                    </td>
                    <td className="px-5 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="sm">
                          <Edit2 className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteCamera(camera.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5 text-red-400" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
