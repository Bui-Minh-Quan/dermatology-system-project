import { useState } from 'react';
import Auth from './components/Auth';
import Register from './components/Register';
import Diagnosis from './components/Diagnosis';
import Chatbot from './components/Chatbot';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('access_token'));
  const [isRegistering, setIsRegistering] = useState(false);

  if (!isAuthenticated) {
    return isRegistering ? 
      <Register onSwitchToLogin={() => setIsRegistering(false)} /> : 
      <div>
        <Auth onLoginSuccess={() => setIsAuthenticated(true)} />
        <button onClick={() => setIsRegistering(true)}>Go to Register</button>
      </div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1>Dermatology AI System</h1>
      <button onClick={() => { localStorage.removeItem('access_token'); setIsAuthenticated(false); }}>
        Logout
      </button>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
        <Diagnosis />
        <Chatbot />
      </div>
    </div>
  );
}
export default App;