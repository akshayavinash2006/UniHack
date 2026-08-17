import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { SingleProduct } from './pages/SingleProduct';
import { BatchProcessing } from './pages/BatchProcessing';
import { ResultsPage } from './pages/ResultsPage';
import { ReviewQueue } from './pages/ReviewQueue';
import { Analytics } from './pages/Analytics';
import { Exports } from './pages/Exports';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="enrich/single" element={<SingleProduct />} />
          <Route path="enrich/batch" element={<BatchProcessing />} />
          <Route path="results/:jobId" element={<ResultsPage />} />
          <Route path="review" element={<ReviewQueue />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="exports" element={<Exports />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
