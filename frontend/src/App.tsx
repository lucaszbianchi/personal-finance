import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
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
import { Projection } from '@/pages/Projection';
import { OnboardingPage } from '@/pages/onboarding/OnboardingPage';
import { useOnboardingStatus } from '@/hooks/useOnboarding';

const NotFoundPage = () => (
  <div className="text-center py-12">
    <h2 className="text-xl font-semibold mb-2">Pagina nao encontrada</h2>
    <p className="text-gray-600">A pagina que voce esta procurando nao existe.</p>
  </div>
);

function OnboardingGuard() {
  const { data: status, isLoading } = useOnboardingStatus();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <p className="text-gray-500">Carregando...</p>
      </div>
    );
  }

  if (status && !status.is_complete) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}

function App() {
  return (
    <Routes>
      <Route path="/onboarding" element={<OnboardingPage />} />
      <Route element={<OnboardingGuard />}>
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
          <Route path="projection" element={<Projection />} />
          <Route path="404" element={<NotFoundPage />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
