import type { ReactNode } from "react";
import { Outlet } from "react-router-dom";
import { RootLayout } from "@/components/layout/root-layout";

interface SafetyLayoutProps {
  breadcrumbs?: ReactNode;
  vesselSlot?: ReactNode;
}

function DefaultBreadcrumbs() {
  return (
    <nav aria-label="Breadcrumb" className="text-sm text-slate-500">
      <ol className="flex items-center gap-2">
        <li>Home</li>
        <li>/</li>
        <li className="font-medium text-slate-700">Safety</li>
      </ol>
    </nav>
  );
}

export function SafetyLayout({
  breadcrumbs,
  vesselSlot,
}: SafetyLayoutProps) {
  return (
    <RootLayout>
      <div
        className="mx-auto flex w-full max-w-6xl flex-col gap-6 py-2"
        data-testid="safety-layout"
      >
        <header className="flex flex-col gap-3 border-b border-slate-200 pb-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            {breadcrumbs ?? <DefaultBreadcrumbs />}
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">Safety</h1>
            </div>
          </div>
          {vesselSlot ? <div>{vesselSlot}</div> : null}
        </header>

        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </RootLayout>
  );
}

export default SafetyLayout;
