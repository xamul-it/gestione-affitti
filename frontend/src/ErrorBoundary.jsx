import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '40px',
          margin: '20px',
          border: '3px solid red',
          backgroundColor: '#ffe6e6',
          fontFamily: 'monospace'
        }}>
          <h1 style={{ color: 'red' }}>❌ Errore Applicazione</h1>
          <h2>Qualcosa è andato storto!</h2>

          <div style={{
            marginTop: '20px',
            padding: '15px',
            backgroundColor: '#ffcccc',
            borderRadius: '5px'
          }}>
            <h3>Errore:</h3>
            <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {this.state.error && this.state.error.toString()}
            </pre>
          </div>

          <div style={{
            marginTop: '20px',
            padding: '15px',
            backgroundColor: '#ffcccc',
            borderRadius: '5px'
          }}>
            <h3>Stack Trace:</h3>
            <pre style={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontSize: '12px',
              maxHeight: '400px',
              overflow: 'auto'
            }}>
              {this.state.errorInfo && this.state.errorInfo.componentStack}
            </pre>
          </div>

          <div style={{ marginTop: '20px' }}>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '10px 20px',
                fontSize: '16px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer'
              }}
            >
              🔄 Ricarica Pagina
            </button>
          </div>

          <div style={{
            marginTop: '30px',
            padding: '15px',
            backgroundColor: '#fff3cd',
            borderRadius: '5px'
          }}>
            <h3>Debug Info:</h3>
            <ul>
              <li><strong>Browser:</strong> {navigator.userAgent}</li>
              <li><strong>URL:</strong> {window.location.href}</li>
              <li><strong>Timestamp:</strong> {new Date().toISOString()}</li>
            </ul>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
