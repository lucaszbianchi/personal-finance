import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@/components/Layout/Layout';
import { Dashboard } from '@/pages/Dashboard';
import { Transactions } from '@/pages/Transactions';
import { Categories } from '@/pages/Categories';
import { Investments } from '@/pages/Investments';
import { Summary } from '@/pages/Summary';

// Páginas placeholder para rotas futuras
const SyncPage = () => (
  <div className="text-center py-12">
    <h2 className="text-xl font-semibold mb-2">Sincronização de Dados</h2>
    <p className="text-gray-600">Funcionalidade de sincronização em desenvolvimento</p>
  </div>
);

const SettingsPage = () => (
  <div className="text-center py-12">
    <h2 className="text-xl font-semibold mb-2">Configurações</h2>
    <p className="text-gray-600">Página de configurações em desenvolvimento</p>
  </div>
);

const NotFoundPage = () => (
  <div className="text-center py-12">
    <h2 className="text-xl font-semibold mb-2">Página não encontrada</h2>
    <p className="text-gray-600">A página que você está procurando não existe.</p>
  </div>
);

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="transactions" element={<Transactions />} />
        <Route path="categories" element={<Categories />} />
        <Route path="investments" element={<Investments />} />
        <Route path="summary" element={<Summary />} />
        <Route path="sync" element={<SyncPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  );
}

export default App;