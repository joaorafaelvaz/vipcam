"use client";

import { useEffect } from "react";

import { Header } from "@/components/layout/Header";
import { CameraGrid } from "@/components/dashboard/CameraGrid";
import { useCameraStore } from "@/stores/useCameraStore";

export default function DashboardPage() {
  const cameras = useCameraStore((s) => s.cameras);
  const fetchCameras = useCameraStore((s) => s.fetchCameras);

  useEffect(() => {
    fetchCameras();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <Header title="Dashboard" subtitle={`${cameras.length} cameras`} />
      <div className="p-6">
        <CameraGrid cameras={cameras} />
      </div>
    </div>
  );
}
