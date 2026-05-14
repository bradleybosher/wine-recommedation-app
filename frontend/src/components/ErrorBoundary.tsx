import { Component, ReactNode } from "react";
import { AlertTriangle } from "lucide-react";
import { INK, INK_SOFT, PAPER, RULE, OXBLOOD } from "@/design/tokens";

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
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 32,
            background: PAPER,
            minHeight: '100vh',
          }}
        >
          <div
            style={{
              maxWidth: 400,
              width: '100%',
              border: `1px solid ${RULE}`,
              padding: '36px 32px',
              textAlign: 'center',
            }}
          >
            <AlertTriangle
              style={{ margin: '0 auto 16px', color: OXBLOOD, display: 'block' }}
              size={32}
              strokeWidth={1.5}
            />
            <div
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 20,
                color: INK,
                marginBottom: 8,
              }}
            >
              Something went wrong
            </div>
            <div
              style={{
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: 14,
                color: INK_SOFT,
                marginBottom: 24,
                lineHeight: 1.5,
              }}
            >
              An unexpected error occurred. Please refresh the page to try again.
            </div>
            <button
              onClick={() => window.location.reload()}
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 12,
                letterSpacing: 2,
                textTransform: 'uppercase',
                padding: '8px 18px',
                background: 'transparent',
                color: INK,
                border: `1px solid ${RULE}`,
                cursor: 'pointer',
              }}
            >
              Refresh page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
