import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Catches render-time errors in its subtree and displays a safe fallback.
 * Does not catch async errors — those are handled by callers via toasts.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  override state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  override render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }

    if (this.props.fallback) {
      return this.props.fallback;
    }

    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-muted p-6">
        <div className="w-full max-w-lg rounded-lg border border-surface-border bg-white p-6 shadow-sm">
          <h1 className="mb-2 text-lg font-semibold text-danger">
            Something went wrong
          </h1>
          <p className="mb-4 text-sm text-slate-600">
            The interface encountered an unexpected error. You can try to
            recover, or reload the page.
          </p>
          {this.state.error ? (
            <pre className="mb-4 max-h-40 overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
              {this.state.error.message}
            </pre>
          ) : null}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={this.handleReset}
              className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
            >
              Try again
            </button>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="rounded border border-surface-border px-4 py-2 text-sm font-medium text-slate-700 hover:bg-surface-muted"
            >
              Reload page
            </button>
          </div>
        </div>
      </div>
    );
  }
}