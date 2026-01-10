// Minimal working App without module loader
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Layout/Navbar';

// Simple placeholder component
function Placeholder({ title }) {
  return (
    <div style={{ padding: '40px', textAlign: 'center' }}>
      <h2>{title}</h2>
      <p>Questa pagina è temporanea per testare il routing.</p>
      <p style={{ color: 'green' }}>✅ Se vedi questo, il frontend funziona!</p>
    </div>
  );
}

function AppMinimal() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <div className="container" style={{ paddingTop: '20px' }}>
          <Routes>
            <Route path="/" element={<Placeholder title="Home" />} />
            <Route path="/unita-immobiliari" element={<Placeholder title="Unità Immobiliari" />} />
            <Route path="/affittuari" element={<Placeholder title="Affittuari" />} />
            <Route path="/contratti" element={<Placeholder title="Contratti" />} />
            <Route path="*" element={<Placeholder title="Pagina non trovata" />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default AppMinimal;
