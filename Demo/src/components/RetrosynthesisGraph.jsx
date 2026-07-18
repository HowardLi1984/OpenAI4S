import React, { useMemo, useRef, useState } from 'react';
import { graphEdges, graphNodes } from '../data/aspirinRetrosynthesis';

const nodeById = Object.fromEntries(graphNodes.map(node => [node.id, node]));

export default function RetrosynthesisGraph() {
  const [selected, setSelected] = useState(graphNodes[0]);
  const [collapsed, setCollapsed] = useState(new Set());
  const [view, setView] = useState({ x: 0, y: 0, scale: 1 });
  const drag = useRef(null);

  const visibleNodes = useMemo(() => graphNodes.filter(node => !node.parent || !collapsed.has(node.parent)), [collapsed]);
  const visibleIds = new Set(visibleNodes.map(node => node.id));
  const related = new Set(graphEdges.filter(([from, to]) => from === selected.id || to === selected.id).flat());

  const reset = () => {
    setSelected(graphNodes[0]);
    setCollapsed(new Set());
    setView({ x: 0, y: 0, scale: 1 });
  };
  const toggleReactions = () => setCollapsed(current => current.size ? new Set() : new Set(['rxn-1', 'rxn-2', 'rxn-3']));
  const beginDrag = event => { drag.current = { x: event.clientX, y: event.clientY, view }; event.currentTarget.setPointerCapture(event.pointerId); };
  const dragGraph = event => {
    if (!drag.current) return;
    setView({ ...drag.current.view, x: drag.current.view.x + event.clientX - drag.current.x, y: drag.current.view.y + event.clientY - drag.current.y });
  };
  const endDrag = () => { drag.current = null; };
  const zoom = event => {
    event.preventDefault();
    setView(current => ({ ...current, scale: Math.max(.55, Math.min(1.75, current.scale + (event.deltaY < 0 ? .1 : -.1))) }));
  };

  return <section className="retro-graph-card">
    <header className="retro-graph-head"><div><span className="eyebrow">SEARCH GRAPH</span><h3>Interactive Retrosynthesis Knowledge Graph</h3></div><div className="retro-graph-actions"><button onClick={() => setCollapsed(new Set())}>Expand</button><button onClick={toggleReactions}>Collapse</button><button onClick={reset}>Reset</button></div></header>
    <div className="retro-graph-layout">
      <div className="retro-graph-canvas" onWheel={zoom}>
        <svg viewBox="0 0 1000 450" role="img" aria-label="Interactive aspirin retrosynthesis knowledge graph" onPointerDown={beginDrag} onPointerMove={dragGraph} onPointerUp={endDrag} onPointerCancel={endDrag}>
          <defs><marker id="retro-arrow" markerWidth="8" markerHeight="8" refX="7" refY="3.5" orient="auto"><path d="M0,0 L0,7 L7,3.5 z" /></marker></defs>
          <g transform={`translate(${view.x} ${view.y}) scale(${view.scale})`}>
            {graphEdges.filter(([from, to]) => visibleIds.has(from) && visibleIds.has(to)).map(([from, to]) => {
              const start = nodeById[from]; const end = nodeById[to];
              return <path className={`retro-edge ${related.has(from) && related.has(to) ? 'active' : ''}`} key={`${from}-${to}`} d={`M${start.x + 105} ${start.y + 68} C${start.x + 105} ${start.y + 115}, ${end.x + 105} ${end.y - 36}, ${end.x + 105} ${end.y}`} />;
            })}
            {visibleNodes.map(node => <g key={node.id} className={`retro-node ${node.kind} ${selected.id === node.id ? 'selected' : ''} ${related.has(node.id) ? 'neighbor' : ''}`} transform={`translate(${node.x} ${node.y})`} onClick={event => { event.stopPropagation(); setSelected(node); }} onDoubleClick={() => node.kind === 'reaction' && setCollapsed(current => { const next = new Set(current); next.has(node.id) ? next.delete(node.id) : next.add(node.id); return next; })}>
              <rect width="210" height="68" rx="7" /><text x="105" y="27" textAnchor="middle">{node.title}</text><text className="retro-node-meta" x="105" y="47" textAnchor="middle">{node.meta.length > 28 ? `${node.meta.slice(0, 28)}…` : node.meta}</text>{node.kind === 'reaction' && <text className="retro-node-toggle" x="190" y="57">{collapsed.has(node.id) ? '+' : '−'}</text>}
            </g>)}
          </g>
        </svg>
      </div>
      <aside className="retro-node-detail"><span className="eyebrow">NODE DETAILS</span><h4>{selected.title}</h4><p>{selected.detail}</p><dl><dt>Type</dt><dd>{selected.kind}</dd><dt>Source</dt><dd>aspirin_retrosynthesis.html</dd></dl><small>Click a node for details. Double-click a reaction to fold/unfold its precursor branch. Drag to pan; scroll to zoom.</small></aside>
    </div>
  </section>;
}
