import { useState } from "react";
import { Outlet } from "react-router-dom";

import { Sidebar } from "@/layout/Sidebar";
import { TopNav } from "@/layout/TopNav";
import { useHealth } from "@/hooks/useHealth";
import { useAppSettings } from "@/hooks/useAppSettings";

export function Layout(): JSX.Element {
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);

  // Poll health and load settings once at the layout level so the TopNav
  // and any page can read the latest snapshot from the store.
  useHealth();
  useAppSettings();

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Sidebar — desktop */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {/* Sidebar — mobile overlay */}
      {sidebarOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-slate-900/40"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
          <div className="relative h-full w-64 bg-white">
            <Sidebar />
          </div>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <TopNav onToggleSidebar={() => setSidebarOpen((v) => !v)} />
        <main className="min-h-0 flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}