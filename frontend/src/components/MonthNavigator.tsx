import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface Props {
  month: string; // YYYY-MM
  onChange: (month: string) => void;
  maxMonth?: string; // YYYY-MM — disables "next" if current == maxMonth
}

const MONTH_NAMES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
];

function addMonths(ym: string, delta: number): string {
  const [y, m] = ym.split('-').map(Number);
  const date = new Date(y, m - 1 + delta, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

export const MonthNavigator: React.FC<Props> = ({ month, onChange, maxMonth }) => {
  const [year, mon] = month.split('-').map(Number);
  const label = `${MONTH_NAMES[mon - 1]} ${year}`;
  const disableNext = maxMonth ? month >= maxMonth : false;

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={() => onChange(addMonths(month, -1))}
        className="p-1.5 rounded-full hover:bg-gray-100 transition-colors"
        aria-label="Mês anterior"
      >
        <ChevronLeft className="w-5 h-5 text-gray-600" />
      </button>
      <span className="font-semibold text-gray-900 min-w-[160px] text-center">{label}</span>
      <button
        onClick={() => onChange(addMonths(month, 1))}
        disabled={disableNext}
        className="p-1.5 rounded-full hover:bg-gray-100 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        aria-label="Próximo mês"
      >
        <ChevronRight className="w-5 h-5 text-gray-600" />
      </button>
    </div>
  );
};
