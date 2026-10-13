import { RouterProvider } from "react-router-dom";

import { ErrorBoundary } from "@/components/feedback/ErrorBoundary";
import { router } from "@/router";

export function App(): JSX.Element {
  return (
    <ErrorBoundary>
      <RouterProvider router={router} />
    </ErrorBoundary>
  );
}