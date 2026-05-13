import { Component, ReactNode } from "react";
import { AlertTriangle } from "lucide-react";
import GlassCard from "@/components/ui/GlassCard";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="flex items-center justify-center p-8">
          <GlassCard className="max-w-md w-full p-8 text-center">
            <AlertTriangle className="mx-auto mb-4 text-white/70" size={40} strokeWidth={1.5} />
            <h2 className="text-xl font-semibold text-white mb-2">Something went wrong</h2>
            <p className="text-white/60 mb-6">
              An unexpected error occurred. Please refresh the page to try again.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm transition-colors"
            >
              Refresh page
            </button>
          </GlassCard>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
