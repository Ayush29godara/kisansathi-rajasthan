import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error in React component tree:', error, errorInfo);
  }

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          role="alert"
          className="min-h-screen bg-gray-50 flex flex-col justify-center items-center px-4 py-12"
        >
          <div className="bg-white p-8 rounded-2xl shadow-lg border border-red-100 max-w-md w-full text-center">
            <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-8 h-8" aria-hidden="true" />
            </div>
            <h1 className="text-xl font-bold text-gray-900 mb-2">
              कुछ तकनीकी समस्या आई / Something went wrong
            </h1>
            <p className="text-sm text-gray-600 mb-6">
              एप्लिकेशन में त्रुटि हुई है। कृपया पृष्ठ को पुनः लोड करें या कुछ समय बाद प्रयास करें।
              <br />
              <span className="text-xs text-gray-500 mt-1 block">
                An unexpected application error occurred. Please refresh or retry shortly.
              </span>
            </p>
            {this.state.error && (
              <div className="bg-gray-100 text-left p-3 rounded text-xs font-mono text-gray-700 mb-6 max-h-24 overflow-y-auto">
                {this.state.error.message}
              </div>
            )}
            <button
              onClick={this.handleReload}
              className="w-full bg-primary-600 text-white font-medium py-2.5 px-4 rounded-xl flex items-center justify-center space-x-2 hover:bg-primary-700 transition focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <RefreshCw className="w-4 h-4" aria-hidden="true" />
              <span>पुनः लोड करें / Reload App</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
