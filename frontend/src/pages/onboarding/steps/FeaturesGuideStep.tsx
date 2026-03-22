import React, { useState } from 'react';
import {
  Compass,
  Languages,
  Tags,
  Zap,
  Repeat,
  TrendingUp,
  CreditCard,
  BarChart3,
  LineChart,
  RefreshCw,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';

type FeatureCard = {
  icon: React.ReactNode;
  title: string;
  description: string;
  tip: string;
  route: string;
};

const FEATURES: FeatureCard[] = [
  {
    icon: <Languages size={20} />,
    title: 'Idioma das Categorias',
    description:
      'As categorias importadas da Pluggy vem em ingles. Voce pode alternar para exibicao em portugues.',
    tip: 'Va em Configuracoes e escolha o idioma de exibicao das categorias.',
    route: '/settings',
  },
  {
    icon: <Zap size={20} />,
    title: 'Automacoes de Categoria',
    description:
      'Crie regras para categorizar transacoes automaticamente. Ex: toda transacao com "UBER" vai para "Transporte".',
    tip: 'Acesse a aba Automacoes dentro de Categorias para criar regras com condicoes (descricao, valor) e acoes (definir categoria, excluir).',
    route: '/categories',
  },
  {
    icon: <Tags size={20} />,
    title: 'Categorias',
    description:
      'Organize suas transacoes em categorias e grupos. Voce pode criar, editar, agrupar e unificar categorias duplicadas.',
    tip: 'Revise as categorias importadas, adicione traducoes e agrupe-as para melhor organizacao.',
    route: '/categories',
  },
  {
    icon: <Repeat size={20} />,
    title: 'Recorrencias (Despesas Fixas)',
    description:
      'Registre suas contas fixas mensais como aluguel, internet, academia. O sistema tambem detecta recorrencias automaticamente.',
    tip: 'Adicione manualmente suas despesas fixas ou revise as detectadas automaticamente.',
    route: '/recurrences',
  },
  {
    icon: <TrendingUp size={20} />,
    title: 'Receitas',
    description:
      'Cadastre suas fontes de renda recorrentes como salario, freelance, investimentos. Usado para projecoes financeiras.',
    tip: 'Adicione suas fontes de renda com valor e frequencia para projecoes mais precisas.',
    route: '/income',
  },
  {
    icon: <CreditCard size={20} />,
    title: 'Faturas',
    description:
      'Acompanhe suas faturas de cartao de credito com classificacao automatica: parcelas, recorrentes e avulsas.',
    tip: 'As faturas sao importadas automaticamente. Revise a classificacao de cada despesa.',
    route: '/bills',
  },
  {
    icon: <CreditCard size={20} />,
    title: 'Transacoes',
    description:
      'Visualize, filtre e organize suas transacoes bancarias e de cartao. Altere categorias, exclua transacoes irrelevantes e use filtros por periodo, categoria ou descricao.',
    tip: 'Revise suas transacoes apos cada sincronizacao para manter a categorizacao em dia.',
    route: '/transactions',
  },
  {
    icon: <TrendingUp size={20} />,
    title: 'Investimentos',
    description:
      'Acompanhe seu portfolio de investimentos importado automaticamente, agrupado por tipo (renda fixa, acoes, fundos, etc.).',
    tip: 'Seus investimentos sao atualizados a cada sincronizacao com a Pluggy.',
    route: '/investments',
  },
  {
    icon: <BarChart3 size={20} />,
    title: 'Visao Geral',
    description:
      'Patrimonio liquido, resultado parcial do mes e ritmo de gastos comparado ao mes anterior.',
    tip: 'Acompanhe diariamente seu ritmo de gastos para nao estourar o orcamento.',
    route: '/',
  },
  {
    icon: <BarChart3 size={20} />,
    title: 'Fluxo de Caixa',
    description:
      'Compare receitas e gastos entre periodos (3 ou 6 meses) com detalhamento por categoria e variacao percentual.',
    tip: 'Use para identificar tendencias de gastos e ajustar seu orcamento.',
    route: '/cash-flow',
  },
  {
    icon: <LineChart size={20} />,
    title: 'Projecao Patrimonial',
    description:
      'Projecao de 12 meses do seu patrimonio baseada em receitas, despesas fixas e parcelas.',
    tip: 'Cadastre receitas e recorrencias para ter projecoes mais precisas.',
    route: '/projection',
  },
  {
    icon: <RefreshCw size={20} />,
    title: 'Sincronizacao',
    description:
      'Importe dados recentes (ultimos 7 dias) ou historicos (ate 365 dias). Dados historicos tem limite de 4 syncs/mes.',
    tip: 'Sincronize regularmente para manter seus dados atualizados.',
    route: '/sync',
  },
];

type Props = { onNext: () => void };

export const FeaturesGuideStep: React.FC<Props> = ({ onNext }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
          <Compass size={20} className="text-blue-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-800">Conheca as ferramentas</h2>
          <p className="text-sm text-gray-500">
            Veja o que voce pode configurar para aproveitar ao maximo
          </p>
        </div>
      </div>

      <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
        {FEATURES.map((feature, index) => {
          const isExpanded = expandedIndex === index;
          return (
            <button
              key={feature.title}
              onClick={() => setExpandedIndex(isExpanded ? null : index)}
              className="w-full text-left rounded-lg border border-gray-200 hover:border-blue-200 transition-colors"
            >
              <div className="flex items-center gap-3 px-4 py-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gray-100 text-gray-600 flex-shrink-0">
                  {feature.icon}
                </div>
                <span className="text-sm font-medium text-gray-800 flex-1">
                  {feature.title}
                </span>
                <ChevronRight
                  size={16}
                  className={`text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                />
              </div>
              {isExpanded && (
                <div className="px-4 pb-3 space-y-2">
                  <p className="text-sm text-gray-600">{feature.description}</p>
                  <div className="rounded-md bg-amber-50 border border-amber-100 px-3 py-2">
                    <p className="text-xs text-amber-800">
                      <span className="font-semibold">Dica:</span> {feature.tip}
                    </p>
                  </div>
                  <a
                    href={feature.route}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    Abrir {feature.title}
                    <ExternalLink size={12} />
                  </a>
                </div>
              )}
            </button>
          );
        })}
      </div>

      <button
        onClick={onNext}
        className="mt-6 w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700 transition-colors"
      >
        Tudo certo, vamos comecar!
      </button>
    </div>
  );
};
