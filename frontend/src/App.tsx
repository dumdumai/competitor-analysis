import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import IntroPage from './pages/IntroPage';
import HomePage from './pages/HomePage';
import AnalysisPage from './pages/AnalysisPage';
import ReportsPage from './pages/ReportsPage';
import ResultsPageV2 from './pages/ResultsPageV2';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<IntroPage />} />
            <Route path="/home" element={<HomePage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/results/:requestId" element={<ResultsPageV2 />} />
            <Route path="/analysis/:requestId" element={<ResultsPageV2 />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;