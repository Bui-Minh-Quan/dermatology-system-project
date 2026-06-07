import { useState } from 'react';
import Auth from './components/Auth';
import Register from './components/Register';
import Diagnosis from './components/Diagnosis';
import Chatbot from './components/Chatbot';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('access_token'));
  const [isRegistering, setIsRegistering] = useState(false);
  const [showRegisterPrompt, setShowRegisterPrompt] = useState(true);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setIsAuthenticated(false);
    setIsRegistering(false);
  };

  /*Make this button "No account yet" closable*/
  if (!isAuthenticated) {
    return isRegistering ? (
      <Register onSwitchToLogin={() => setIsRegistering(false)} />
    ) : (
      <div className="auth-shell">
        <Auth onLoginSuccess={() => setIsAuthenticated(true)} />
        {showRegisterPrompt ? (
          <div className="auth-switch-panel" role="status" aria-live="polite">
            <p className="auth-switch-text">No account yet?</p>
            <button
              type="button"
              className="auth-switch-btn"
              onClick={() => setIsRegistering(true)}
            >
              Create an account
            </button>
            <button
              type="button"
              className="auth-switch-close"
              aria-label="Close register prompt"
              onClick={() => setShowRegisterPrompt(false)}
            >
              x
            </button>
          </div>
        ) : (
          <button
            type="button"
            className="auth-switch-reopen"
            onClick={() => setShowRegisterPrompt(true)}
          >
            Need an account?
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="app-badge">Dermatology AI</p>
          <h1 className="app-title">Clinical Workspace</h1>
          <p className="app-subtitle">Analyze skin images, compare heatmaps, and support patient decisions with AI.</p>
        </div>

        <button type="button" className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </header>

      <main className="workspace-grid">
        <section className="workspace-panel diagnosis-panel" aria-label="Diagnosis tool">
          <Diagnosis />
        </section>

        <section className="workspace-panel chatbot-panel" aria-label="Chat assistant">
          <div className="panel-header">
            <h2>AI Chat Assistant</h2>
            <p>Clinical Q&A and guidance based on patient context.</p>
          </div>
          <Chatbot />
        </section>
      </main>
    </div>
  );
}

export default App;