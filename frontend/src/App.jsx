import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './Layout';
import Dashboard from './pages/Dashboard';
import VoiceReport from './pages/VoiceReport';
import History from './pages/History';
import Handover from './pages/Handover';
import Eval from './pages/Eval';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/report" element={<VoiceReport />} />
          <Route path="/history" element={<History />} />
          <Route path="/handover" element={<Handover />} />
          <Route path="/eval" element={<Eval />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
