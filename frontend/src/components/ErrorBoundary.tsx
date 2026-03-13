import React from "react";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[ErrorBoundary] Caught error:", error, info.componentStack);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            background: "#0a0a0a",
            color: "#e0e0e0",
            fontFamily: "monospace",
            gap: "16px",
            zIndex: 9999,
          }}
        >
          <div style={{ fontSize: "1.1rem" }}>Rendering error</div>
          <div style={{ fontSize: "0.8rem", color: "#888", maxWidth: 400, textAlign: "center" }}>
            {this.state.error?.message ?? "An unexpected error occurred."}
          </div>
          <button
            onClick={this.handleRetry}
            style={{
              marginTop: "8px",
              padding: "8px 20px",
              background: "transparent",
              border: "1px solid #555",
              color: "#e0e0e0",
              borderRadius: "4px",
              cursor: "pointer",
              fontFamily: "monospace",
              fontSize: "0.85rem",
            }}
          >
            Click to retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
