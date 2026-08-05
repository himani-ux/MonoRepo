import { Outlet } from "react-router-dom";
import { RootLayout } from "@/components/layout/root-layout";

export function SafetyLayout() {
  return (
    <RootLayout>
      <div
        className="mx-auto flex w-full max-w-6xl flex-col gap-6 py-2"
        data-testid="safety-layout"
      >
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </RootLayout>
  );
}

export default SafetyLayout;
