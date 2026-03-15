export const formatCurrency = (value: number | null | undefined) =>
  (value ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

export function shortMonth(ym: string): string {
  const [, m] = ym.split('-').map(Number);
  const names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
  return names[m - 1] ?? ym;
}

export const chartTickFormatter = (value: number): string =>
  Math.abs(value) >= 1000
    ? `R$${(value / 1000).toFixed(0)}k`
    : `R$${value}`;
