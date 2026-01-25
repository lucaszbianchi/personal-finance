import React from 'react';
import { useLocation } from 'react-router-dom';
import { DollarSign, Menu, X } from 'lucide-react';

interface HeaderProps {
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ isSidebarOpen, toggleSidebar }) => {
  const location = useLocation();

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/':
        return 'Dashboard';
      case '/transactions':
        return 'Transações';
      case '/categories':
        return 'Categorias';
      case '/investments':
        return 'Investimentos';
      case '/summary':
        return 'Resumo Financeiro';
      default:
        return 'Personal Finance';
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100"
          >
            {isSidebarOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>

          <div className="flex items-center space-x-3">
            <DollarSign className="w-8 h-8 text-primary-600" />
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                {getPageTitle()}
              </h1>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500">
            Última sincronização: {new Date().toLocaleDateString('pt-BR')}
          </div>
        </div>
      </div>
    </header>
  );
};