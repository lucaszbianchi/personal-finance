import React from 'react';

interface SyncCountCardProps {
  title: string;
  inserted: number;
  updated: number;
  colorScheme: 'emerald' | 'sky' | 'amber' | 'violet';
}

const colorSchemes = {
  emerald: {
    bg: 'from-emerald-50 to-emerald-100',
    border: 'border-emerald-200',
    title: 'text-emerald-900',
    text: 'text-emerald-800',
  },
  sky: {
    bg: 'from-sky-50 to-sky-100',
    border: 'border-sky-200',
    title: 'text-sky-900',
    text: 'text-sky-800',
  },
  amber: {
    bg: 'from-amber-50 to-amber-100',
    border: 'border-amber-200',
    title: 'text-amber-900',
    text: 'text-amber-800',
  },
  violet: {
    bg: 'from-violet-50 to-violet-100',
    border: 'border-violet-200',
    title: 'text-violet-900',
    text: 'text-violet-800',
  },
};

export const SyncCountCard: React.FC<SyncCountCardProps> = ({
  title,
  inserted,
  updated,
  colorScheme,
}) => {
  const colors = colorSchemes[colorScheme];

  return (
    <div
      className={`bg-gradient-to-br ${colors.bg} rounded-lg p-4 border ${colors.border}`}
    >
      <h4 className={`font-semibold ${colors.title} mb-2`}>{title}</h4>
      <div className={`space-y-1 text-sm ${colors.text}`}>
        <p>
          <span className="font-medium">Novas:</span> {inserted}
        </p>
        <p>
          <span className="font-medium">Atualizadas:</span> {updated}
        </p>
      </div>
    </div>
  );
};
