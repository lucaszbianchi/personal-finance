import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@/components/Layout/Layout';
import { Dashboard } from '@/pages/Dashboard';
import { Overview } from '@/pages/Overview';
import { Transactions } from '@/pages/Transactions';
import { Categories } from '@/pages/Categories';
import { Investments } from '@/pages/Investments';
import { Summary } from '@/pages/Summary';
import { SyncPage } from '@/pages/SyncPage';
import { Settings } from '@/pages/Settings';
import { Recurrences } from '@/pages/Recurrences';
import { Income } from '@/pages/Income';
import { CashFlow } from '@/pages/CashFlow';
import { Bills } from '@/pages/Bills';

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
        <Route path="overview" element={<Overview />} />
        <Route path="transactions" element={<Transactions />} />
        <Route path="categories" element={<Categories />} />
        <Route path="investments" element={<Investments />} />
        <Route path="summary" element={<Summary />} />
        <Route path="sync" element={<SyncPage />} />
        <Route path="settings" element={<Settings />} />
        <Route path="recurrences" element={<Recurrences />} />
        <Route path="income" element={<Income />} />
        <Route path="cash-flow" element={<CashFlow />} />
        <Route path="bills" element={<Bills />} />
        <Route path="404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  );
}

export default App;