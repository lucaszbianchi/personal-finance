import React, { useState } from 'react';
import { useCategoryDistribution } from '@/hooks/useCategoryVisualization';
import { formatCurrency } from '@/utils/format';
import type { CategoryDistribution } from '@/types';

// ── Layout constants ────────────────────────────────────────────────────────
const NODE_W = 14;
const NODE_PAD = 10;   // vertical gap between sibling nodes

// Column x positions (SVG coordinates)
const SRC_X = 100;
const GRP_X = 320;
const CAT_X = 560;
const SVG_W = 754;

const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6b7280',
  '#14b8a6', '#a855f7', '#fb923c', '#4ade80', '#f43f5e',
];

function trunc(s: string, n = 22) {
  return s.length > n ? s.slice(0, n - 1) + '…' : s;
}

function currentMonth() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

// ── Data types ──────────────────────────────────────────────────────────────
interface SNode {
  id: string; name: string; total: number;
  x: number; y: number; h: number; color: string;
}

interface SLink {
  id: string;
  sx: number; sy0: number; sy1: number;   // source attachment (right edge)
  tx: number; ty0: number; ty1: number;   // target attachment (left edge)
  color: string;
}

// ── Layout builder ──────────────────────────────────────────────────────────
// Guarantees no crossings:
//   - Src → groups links are stacked in the same top-to-bottom order as groups
//   - Group → cat links are stacked so cats follow their parent group's vertical order
function buildLayout(
  dist: CategoryDistribution,
  svgH: number,
): { src: SNode; groups: SNode[]; leafs: SNode[]; links: SLink[] } | null {
  const G = dist.total;
  if (!G) return null;

  // ── Middle column: group nodes ────────────────────────────────────────────
  const numG = dist.groups.length;
  const gAvailH = svgH - NODE_PAD * (numG - 1);
  const groupNodes: SNode[] = [];
  let gy = 0;
  for (let i = 0; i < numG; i++) {
    const g = dist.groups[i];
    const h = Math.max(4, (g.total / G) * gAvailH);
    groupNodes.push({
      id: g.id, name: g.name, total: g.total,
      x: GRP_X, y: gy, h, color: COLORS[i % COLORS.length],
    });
    gy += h + NODE_PAD;
  }

  // ── Right column: leaf nodes in parent-ordered sequence ──────────────────
  // All cats of group[0] come first, then group[1], etc.
  // Standalone groups (no children) are themselves a leaf.
  const leafItems: Array<{ id: string; name: string; total: number; gi: number }> = [];
  for (let i = 0; i < numG; i++) {
    const g = dist.groups[i];
    if (g.categories.length === 0) {
      leafItems.push({ id: g.id + '__L', name: g.name, total: g.total, gi: i });
    } else {
      for (const c of g.categories) {
        leafItems.push({ id: c.id, name: c.name, total: c.total, gi: i });
      }
    }
  }
  const numL = leafItems.length;
  const lAvailH = svgH - NODE_PAD * (numL - 1);
  const leafNodes: SNode[] = [];
  let ly = 0;
  for (const item of leafItems) {
    const h = Math.max(4, (item.total / G) * lAvailH);
    leafNodes.push({
      id: item.id, name: item.name, total: item.total,
      x: CAT_X, y: ly, h, color: COLORS[item.gi % COLORS.length],
    });
    ly += h + NODE_PAD;
  }

  // ── Source node (Despesas): spans full height ─────────────────────────────
  const src: SNode = {
    id: 'root', name: 'Despesas', total: G,
    x: SRC_X, y: 0, h: svgH, color: '#ef4444',
  };

  // ── Links ─────────────────────────────────────────────────────────────────
  const links: SLink[] = [];

  // Source → Groups
  // At source: no padding → cumulative proportion of svgH
  // At target: actual group node y/h
  let srcOff = 0;
  for (let i = 0; i < numG; i++) {
    const g = dist.groups[i];
    const gn = groupNodes[i];
    const lh = (g.total / G) * svgH;
    links.push({
      id: 's_' + g.id,
      sx: SRC_X + NODE_W, sy0: srcOff, sy1: srcOff + lh,
      tx: GRP_X, ty0: gn.y, ty1: gn.y + gn.h,
      color: COLORS[i % COLORS.length],
    });
    srcOff += lh;
  }

  // Groups → Leafs
  // Within a group, links are stacked top-to-bottom in the same order as leaf nodes
  for (let i = 0; i < numG; i++) {
    const g = dist.groups[i];
    const gn = groupNodes[i];

    if (g.categories.length === 0) {
      const ln = leafNodes.find(n => n.id === g.id + '__L')!;
      links.push({
        id: 'g_' + g.id,
        sx: GRP_X + NODE_W, sy0: gn.y, sy1: gn.y + gn.h,
        tx: CAT_X, ty0: ln.y, ty1: ln.y + ln.h,
        color: COLORS[i % COLORS.length],
      });
    } else {
      let grpOff = 0;
      for (const cat of g.categories) {
        const ln = leafNodes.find(n => n.id === cat.id)!;
        // link height within the group is proportional to cat's share of the group
        const lh = gn.h * (cat.total / g.total);
        links.push({
          id: `g_${g.id}_${cat.id}`,
          sx: GRP_X + NODE_W, sy0: gn.y + grpOff, sy1: gn.y + grpOff + lh,
          tx: CAT_X, ty0: ln.y, ty1: ln.y + ln.h,
          color: COLORS[i % COLORS.length],
        });
        grpOff += lh;
      }
    }
  }

  return { src, groups: groupNodes, leafs: leafNodes, links };
}

// ── Bezier band path ────────────────────────────────────────────────────────
function bandPath(l: SLink): string {
  const cx = (l.sx + l.tx) / 2;
  return [
    `M ${l.sx} ${l.sy0}`,
    `C ${cx} ${l.sy0} ${cx} ${l.ty0} ${l.tx} ${l.ty0}`,
    `L ${l.tx} ${l.ty1}`,
    `C ${cx} ${l.ty1} ${cx} ${l.sy1} ${l.sx} ${l.sy1}`,
    'Z',
  ].join(' ');
}

// ── Node label (outside the bar) ─────────────────────────────────────────────
interface LabelProps {
  x: number; y: number; h: number;
  name: string; total: number;
  align: 'left' | 'right';
}

const NodeLabel: React.FC<LabelProps> = ({ x, y, h, name, total, align }) => {
  const lx = align === 'right' ? x + NODE_W + 6 : x - 6;
  const anchor = align === 'right' ? 'start' : 'end';
  const midY = y + h / 2;
  const twoLines = h >= 26;

  return (
    <g>
      <text
        x={lx}
        y={twoLines ? midY - 6 : midY}
        textAnchor={anchor}
        dominantBaseline="middle"
        fontSize={11}
        fill="#374151"
      >
        {trunc(name)}
      </text>
      {twoLines && (
        <text
          x={lx}
          y={midY + 8}
          textAnchor={anchor}
          dominantBaseline="middle"
          fontSize={10}
          fill="#6b7280"
        >
          {formatCurrency(total)}
        </text>
      )}
    </g>
  );
};

// ── Chart component ──────────────────────────────────────────────────────────
export const CategorySankeyChart: React.FC = () => {
  const [month, setMonth] = useState(currentMonth);
  const { data, isLoading } = useCategoryDistribution(month);

  const hasData = !!data && data.groups.length > 0;

  const numLeafs = hasData
    ? data.groups.reduce((s, g) => s + Math.max(1, g.categories.length), 0)
    : 0;

  // Height grows with number of leaf nodes so small categories stay readable
  const svgH = Math.max(400, numLeafs * 42);

  const layout = hasData ? buildLayout(data, svgH) : null;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Distribuição de Despesas</h3>
        <input
          type="month"
          value={month}
          onChange={e => setMonth(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-primary-500 focus:border-primary-500"
        />
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
        </div>
      ) : !layout ? (
        <p className="text-gray-500 text-center py-12">Sem dados de despesas para este mês.</p>
      ) : (
        <div className="overflow-x-auto">
          <svg
            width={SVG_W}
            height={svgH}
            style={{ fontFamily: 'system-ui, -apple-system, sans-serif', display: 'block' }}
          >
            {/* Links drawn first so nodes sit on top */}
            {layout.links.map(l => (
              <path
                key={l.id}
                d={bandPath(l)}
                fill={l.color}
                fillOpacity={0.2}
                stroke={l.color}
                strokeOpacity={0.35}
                strokeWidth={0.5}
              />
            ))}

            {/* Source node */}
            <rect
              x={layout.src.x} y={layout.src.y}
              width={NODE_W} height={layout.src.h}
              fill={layout.src.color} rx={2}
            />
            <NodeLabel
              x={SRC_X} y={0} h={svgH}
              name="Despesas" total={layout.src.total}
              align="left"
            />

            {/* Group nodes */}
            {layout.groups.map(gn => (
              <g key={gn.id}>
                <rect x={gn.x} y={gn.y} width={NODE_W} height={gn.h} fill={gn.color} rx={2} />
                <NodeLabel x={GRP_X} y={gn.y} h={gn.h} name={gn.name} total={gn.total} align="left" />
              </g>
            ))}

            {/* Leaf (category) nodes */}
            {layout.leafs.map(ln => (
              <g key={ln.id}>
                <rect x={ln.x} y={ln.y} width={NODE_W} height={ln.h} fill={ln.color} rx={2} />
                <NodeLabel x={CAT_X} y={ln.y} h={ln.h} name={ln.name} total={ln.total} align="right" />
              </g>
            ))}
          </svg>
        </div>
      )}
    </div>
  );
};
