import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { IndexPage } from './pages/Index';

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-neutral-50">
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<IndexPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
