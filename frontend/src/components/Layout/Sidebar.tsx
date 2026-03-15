import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  LayoutDashboard,
  CreditCard,
  Tag,
  TrendingUp,
  PieChart,
  Settings,
  RefreshCw,
  Repeat,
} from 'lucide-react';
import clsx from 'clsx';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Visão Geral', href: '/overview', icon: LayoutDashboard },
  { name: 'Transações', href: '/transactions', icon: CreditCard },
  { name: 'Categorias', href: '/categories', icon: Tag },
  { name: 'Investimentos', href: '/investments', icon: TrendingUp },
  { name: 'Resumo', href: '/summary', icon: PieChart },
  { name: 'Recorrencias', href: '/recurrences', icon: Repeat },
];

const actions = [
  { name: 'Sincronizar Dados', href: '/sync', icon: RefreshCw },
  { name: 'Configurações', href: '/settings', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();

  const NavItem = ({ item }: { item: typeof navigation[0] }) => {
    const isActive = location.pathname === item.href;

    return (
      <Link
        to={item.href}
        onClick={onClose}
        className={clsx(
          'flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors',
          isActive
            ? 'bg-primary-100 text-primary-700 border-r-2 border-primary-600'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        )}
      >
        <item.icon className="mr-3 h-5 w-5" />
        {item.name}
      </Link>
    );
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          onClick={onClose}
        >
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" />
        </div>
      )}

      {/* Sidebar */}
      <div
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-16 px-4 bg-primary-600">
            <h2 className="text-xl font-bold text-white">Personal Finance</h2>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            <div>
              <h3 className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Navegação
              </h3>
              <div className="space-y-1">
                {navigation.map((item) => (
                  <NavItem key={item.name} item={item} />
                ))}
              </div>
            </div>

            <div className="pt-6">
              <h3 className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Ações
              </h3>
              <div className="space-y-1">
                {actions.map((item) => (
                  <NavItem key={item.name} item={item} />
                ))}
              </div>
            </div>
          </nav>
        </div>
      </div>
    </>
  );
};