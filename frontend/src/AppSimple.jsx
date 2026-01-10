// Simple test version of App without module loader
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

function AppSimple() {
  return (
    <Router>
      <div style={{ padding: '20px', fontFamily: 'Arial' }}>
        <h1 style={{ color: 'green' }}>✅ Frontend Funziona!</h1>
        <p>Se vedi questo messaggio, React sta funzionando correttamente.</p>
        <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f0f0f0', borderRadius: '5px' }}>
          <h2>Test Sistema</h2>
          <ul>
            <li>✅ React montato</li>
            <li>✅ React Router caricato</li>
            <li>✅ JSX compilato correttamente</li>
            <li>✅ Vite HMR attivo</li>
          </ul>
        </div>
        <div style={{ marginTop: '20px' }}>
          <h3>Prossimi passi:</h3>
          <p>Il frontend base funziona. Ora torna ad App.jsx normale.</p>
        </div>
      </div>
    </Router>
  );
}

export default AppSimple;
