import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowLeft, ArrowRight, Check, ChevronRight, CircleDot, FlaskConical, Play, RotateCcw, Sparkles } from 'lucide-react';
import RetrosynthesisGraph from './components/RetrosynthesisGraph';
import { aspirinPaths } from './data/aspirinRetrosynthesis';
import './styles.css';
import spectrumOriginStyle from '../Images/spectrum_origin_style.png';
import spectrumComparison from '../Images/spec-compare.png';
import bertranditeImage from '../Images/Bertrandite.png';
import clinoptiloliteCaImage from '../Images/Clinoptilolite-Ca.png';
import diopsideImage from '../Images/Diopside.png';
import proteinEvolutionImage from '../Images/Protein-Envolve.png';

const TOTAL = 7;

function Typewriter({ text, active, speed = 26 }) {
  const [visible, setVisible] = useState('');
  useEffect(() => {
    if (!active) return;
    setVisible('');
    let index = 0;
    const timer = window.setInterval(() => {
      index += 1;
      setVisible(text.slice(0, index));
      if (index >= text.length) window.clearInterval(timer);
    }, speed);
    return () => window.clearInterval(timer);
  }, [text, active, speed]);
  return <>{visible}<span className="caret" /></>;
}

function SectionFrame({ children, index, onNext, onPrev, nextLabel = '下一步', restart }) {
  return <main className="screen">
    <div className="topline"><span>OPENAI4S / SCIENTIFIC WORKFLOWS</span><span>DEMO 2026</span></div>
    {children}
    <div className="progress"><span>{String(index + 1).padStart(2, '0')} / {String(TOTAL).padStart(2, '0')}</span><div className="progress-track"><i style={{ width: `${((index + 1) / TOTAL) * 100}%` }} /></div></div>
    <div className="navigation">
      {index > 0 ? <button className="icon-button" onClick={onPrev} aria-label="上一页"><ArrowLeft size={19} /></button> : <span />}
      {restart ? <button className="next-button" onClick={restart}>重新播放 <RotateCcw size={17} /></button> : <button className="next-button" onClick={onNext}>{nextLabel} {index === TOTAL - 1 ? <RotateCcw size={17} /> : <ArrowRight size={18} />}</button>}
    </div>
  </main>;
}

function Molecule({ small = false }) {
  return <svg className={small ? 'molecule small' : 'molecule'} viewBox="0 0 350 220" aria-hidden="true"><g className="molecule-core" fill="none" stroke="currentColor" strokeWidth="2"><path d="M54 148 79 105h50l25 43-25 43H79z"/></g><g className="molecule-core" fill="currentColor"><circle cx="54" cy="148" r="8"/><circle cx="79" cy="105" r="8"/><circle cx="129" cy="105" r="8"/><circle cx="154" cy="148" r="8"/><circle cx="129" cy="191" r="8"/><circle cx="79" cy="191" r="8"/></g><g className="molecule-tail" fill="none" stroke="currentColor" strokeWidth="2"><path d="M154 148h48"/><path d="M202 148 227 105h50l25 43-25 43h-50z"/><path d="m228 142 22-37m43 6 0 74m-43 6-22-37" strokeOpacity=".7" strokeWidth="1.5"/></g><g className="molecule-tail" fill="currentColor"><circle cx="202" cy="148" r="8"/><circle cx="227" cy="105" r="8"/><circle cx="277" cy="105" r="8"/><circle cx="302" cy="148" r="8"/><circle cx="277" cy="191" r="8"/><circle cx="227" cy="191" r="8"/></g></svg>;
}

function DNA() { return <svg className="dna" viewBox="0 0 190 320" aria-hidden="true"><path d="M30 0c130 38 0 72 130 110S30 183 160 220 30 282 160 320M160 0C30 38 160 72 30 110s130 73 0 110 130 62 0 100" fill="none" stroke="currentColor" strokeWidth="5"/><g stroke="currentColor" strokeWidth="2" opacity=".65"><path d="M48 30h94M56 73h78M68 145h56M60 190h69M58 262h74M76 300h39"/></g></svg>; }

function Cover({ next }) { return <SectionFrame index={0} onNext={next} nextLabel="Explore"><div className="cover-art"><DNA /><Molecule /><div className="spectrum-lines" /></div><div className="cover-content"><div className="eyebrow"><Sparkles size={15} /> SCIENTIFIC AI, ORCHESTRATED</div><h1>OpenAI4S</h1><p>一个面向科学问题求解的<br /><strong>AI harness</strong></p><div className="domains"><span>有机化学</span><span>生命科学</span><span>新材料</span></div></div></SectionFrame>; }

const chemistryTasks = [{ n: '01', name: '类药性优化', detail: 'ADMET / molecular design' }, { n: '02', name: '合成路径预测', detail: 'retrosynthesis planning', active: true, target: 'retrosynthesis' }, { n: '03', name: '混合物成分分析', detail: 'Raman spectra / NNLS', active: true }];
const lifeTasks = [{ n: '01', name: '蛋白-分子靶点', detail: 'structural reasoning / docking' }, { n: '02', name: '蛋白定向进化', detail: 'ESM scoring / structure ranking', active: true }];
function Overview({ index, title, label, tasks, next, prev, onTaskSelect }) { return <SectionFrame index={index} onNext={next} onPrev={prev}><div className="overview"><div className="overview-copy"><div className="eyebrow"><CircleDot size={15} /> DOMAIN / {label}</div><h2>{title}</h2><p>{index === 1 ? '让模型阅读科学数据，以可追溯的工具链完成从谱图到结论的分析。' : '将语言模型、序列模型与结构预测组合为可检查的设计闭环。'}</p><div className="scope-line">03 READY-TO-RUN SKILLS</div></div><div className="task-stack">{tasks.map((task, i) => <motion.div key={task.name} initial={{ opacity: 0, x: 44 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.18 + i * .12 }}>{task.target ? <button className={`task-card task-card-button ${task.active ? 'active' : ''}`} onClick={() => onTaskSelect(task.target)}><span className="task-number">{task.n}</span><div><h3>{task.name}</h3><p>{task.detail}</p></div><ChevronRight size={20} /></button> : <div className={`task-card ${task.active ? 'active' : ''}`}><span className="task-number">{task.n}</span><div><h3>{task.name}</h3><p>{task.detail}</p></div><ChevronRight size={20} /></div>}</motion.div>)}</div></div></SectionFrame>; }

function Spectrum() { return <img className="spectrum" src={spectrumOriginStyle} alt="未知混合物的拉曼光谱" />; }

const mineralCode = ["spectrum = load_spectrum_csv('case1/spectrum.csv')", 'clean = preprocess_once(spectrum, despike=True, baseline="asls")', 'matches = iterative_residual_match(clean, library="RRUFF")', 'result = nnls_unmix(clean, matches)', 'report = summarize(result, confidence="high")'];
const proteinCode = ["library = enumerate_mutants(wt, positions=active_sites, max_order=1)", 'esm_scores = score_sequence_effect(library, model="fair-esm2")', 'folds = predict_structures(top(esm_scores, 32), model="esmfold2")', 'ranked = merge_and_rank(esm_scores, folds, weights=DEFAULT)', 'accepted = apply_thresholds(ranked, plddt=75, composite=0.72)'];
function CodePanel({ kind }) { const code = kind === 'mineral' ? mineralCode : proteinCode; const logs = kind === 'mineral' ? ['Loaded 626 spectral points', '28 peaks retained after preprocessing', 'Residual loop complete: 3 components', 'NNLS fit correlation: 0.983'] : ['Round 1 library: 228 variants', 'ESM sequence scores merged', 'Structure metrics received: 32 candidates', '3 variants passed acceptance gates']; return <div className="agent-panel"><div className="agent-head"><div><span className="live-dot" /> AGENT WORKSPACE</div><span>{kind === 'mineral' ? 'mineral_spectra_analysis' : 'protein-mutation-enhancement'}</span></div><div className="agent-grid"><section><small>TASK DESCRIPTION</small><p>{kind === 'mineral' ? 'Blind identification and NNLS unmixing of an unknown Raman mineral mixture.' : 'Build and score a directed protein-mutation library, then rank valid candidates.'}</p></section><section className="code"><small>GENERATED CODE</small>{code.map((line, i) => <div key={line} className="code-line"><b>{String(i + 1).padStart(2, '0')}</b><span>{line}</span></div>)}</section><section className="logs"><small>EXECUTION LOG</small>{logs.map((line, i) => <div key={line} className="log-line" style={{ animationDelay: `${i * .5}s` }}><Check size={13}/>{line}</div>)}</section></div></div>; }

function MineralResult() { const data = [['Diopside', '45.7%', '180 · 232 · 324 · 1012 cm⁻¹', 'aqua', diopsideImage], ['Bertrandite', '29.6%', '182 · 202 · 710 · 926 cm⁻¹', 'cobalt', bertranditeImage], ['Clinoptilolite-Ca', '24.7%', '220 · 260 · 482 · 614 cm⁻¹', 'violet', clinoptiloliteCaImage]]; return <div className="results"><div className="result-head"><div><span className="eyebrow"><Check size={14}/> BLIND ANALYSIS COMPLETE</span><h3>3 mineral phases identified</h3></div><div className="confidence">HIGH CONFIDENCE<br/><strong>r = 0.983</strong></div></div><div className="mineral-result-body"><div className="mineral-list">{data.map(([name, fraction, peaks, color, image]) => <div className="mineral-row" key={name}><span className={`color-dot ${color}`} /><img className="mineral-structure" src={image} alt={`${name} crystal structure`} /><div className="mineral-name"><strong>{name}</strong><small>{peaks}</small></div><div className="mineral-composition"><span>COMPOSITION</span><b>{fraction}</b><div className="bar"><i className={color} style={{ width: fraction }} /></div></div></div>)}</div><figure className="spectrum-comparison"><figcaption>INPUT CLEANED SPECTRUM / PREDICTED RECONSTRUCTION</figcaption><img src={spectrumComparison} alt="输入清洗光谱与预测组分重建光谱的对比" /></figure></div><p className="result-note">28 clean peaks · 0 residual peaks · NNLS unmixing · RRUFF reference library</p></div>; }

const retrosynthesisCode = [
  'target = parse_smiles("CC(=O)Oc1ccccc1C(=O)O")',
  'templates = load_retrosynthesis_templates("uspto")',
  'graph = expand_precursors(target, templates, max_depth=2)',
  'ranked = score_routes(graph, stock_catalog=True)',
  'valid = filter_solved_routes(ranked, limit=3)',
];
const retrosynthesisLogs = ['Loaded aspirin target molecule', 'Parsed aromatic ester and carboxylic acid groups', 'Searched retrosynthetic reaction templates', 'Expanded purchasable precursor branches', 'Built merged AND-OR search graph', 'Evaluated route feasibility and step count', 'Ranked solved candidate routes'];
function RetrosynthesisCode({ compact, complete }) { const lines = complete ? retrosynthesisLogs : retrosynthesisLogs.slice(0, 5); return <div className={`retro-code-panel ${compact ? 'compact' : ''}`}><div className="agent-head"><div><span className="live-dot" /> AGENT WORKSPACE</div><span>retrosynthesis_planning</span></div><div className="retro-code-body"><section className="code"><small>GENERATED CODE</small>{retrosynthesisCode.map((line, i) => <div className="code-line" key={line}><b>{String(i + 1).padStart(2, '0')}</b><span>{line}</span></div>)}</section><section className="logs"><small>EXECUTION LOG</small>{lines.map((line, i) => <div className="log-line" key={line} style={{ animationDelay: `${i * .32}s` }}><Check size={13}/>{line}</div>)}</section></div></div>; }
function RetrosynthesisResults() { return <div className="retro-results"><div className="result-head"><div><span className="eyebrow"><Check size={14}/> ROUTE SEARCH COMPLETE</span><h3>3 valid synthesis pathways found</h3></div><div className="confidence">TOP SCORE<br/><strong>0.998</strong></div></div><div className="retro-path-grid">{aspirinPaths.map((path, i) => <motion.article className="retro-path-card" key={path.id} initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: .18 + i * .14 }}><header><span>PATH 0{path.id}</span><b>{path.recommendation}</b></header><div className="retro-flow"><strong>{path.donor}</strong><i>+</i><strong>{path.precursor}</strong><i>→</i><strong className="target-product">Aspirin</strong></div><p>{path.reaction}</p><footer><span>{path.steps} STEP</span><span>SCORE {path.score}</span></footer></motion.article>)}</div><p className="result-note">Source: aspirin_retrosynthesis.html · predicted routes require expert chemical review before execution</p></div>; }
function RetrosynthesisDemo({ index, next, prev }) {
  const [phase, setPhase] = useState(0);
  const [run, setRun] = useState(0);
  useEffect(() => {
    const timings = [[2700, 1], [5900, 2], [9700, 3]];
    const timers = timings.map(([delay, value]) => window.setTimeout(() => setPhase(value), delay));
    return () => timers.forEach(window.clearTimeout);
  }, [run]);
  const replay = () => { setPhase(0); setRun(value => value + 1); };
  return <SectionFrame index={index} onNext={next} onPrev={prev} nextLabel="生命科学">
    <div className="demo-title"><span className="eyebrow"><FlaskConical size={15}/> LIVE SCIENTIFIC WORKFLOW</span><h2>合成路径预测</h2></div>
    <div className="retro-stage">
      <AnimatePresence mode="wait">{phase === 0 && <motion.div className="prompt-box retro-prompt" initial={{ opacity: 0, y: 40, scale: .88 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, scale: .82, y: -30 }} transition={{ duration: .5 }}><div className="retro-prompt-mark">C₉H₈O₄</div><div className="prompt-text"><small>OPENAI4S TASK</small><p><Typewriter active text="帮我预测目标产物阿司匹林的合成路径" /></p></div><button aria-label="运行任务"><Play size={17} fill="currentColor" /></button></motion.div>}</AnimatePresence>
      <AnimatePresence mode="wait">{phase === 1 && <motion.div className="retro-code-central" initial={{ opacity: 0, scale: .92 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, x: -280, scale: .82 }} transition={{ duration: .6 }}><RetrosynthesisCode /></motion.div>}</AnimatePresence>
      <AnimatePresence mode="wait">{phase === 2 && <motion.div className="retro-workspace" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, x: -35 }} transition={{ duration: .45 }}><motion.div className="retro-code-column" initial={{ x: 120, scale: .88 }} animate={{ x: 0, scale: 1 }} transition={{ duration: .6 }}><RetrosynthesisCode compact /></motion.div><motion.div className="retro-graph-column" initial={{ opacity: 0, x: 80 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: .6 }}><RetrosynthesisGraph /></motion.div></motion.div>}</AnimatePresence>
      <AnimatePresence mode="wait">{phase === 3 && <motion.div className="retro-workspace retro-final-workspace" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: .5 }}><motion.div className="retro-code-column" initial={{ x: 60 }} animate={{ x: 0 }} transition={{ duration: .5 }}><RetrosynthesisCode compact complete /></motion.div><motion.div className="retro-results-fade" initial={{ opacity: 0, x: 60 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: .55 }}><RetrosynthesisResults /></motion.div></motion.div>}</AnimatePresence>
    </div>
    <button className="replay" onClick={replay}><RotateCcw size={14}/> replay workflow</button>
  </SectionFrame>;
}

function ProteinVisual() { return <img className="protein-visual" src={proteinEvolutionImage} alt="蛋白质定向进化位点与对接口袋示意图" />; }

function ProteinResult() { const rows = [['T3L+Y5V', '0.89', '88.4', '0.72'], ['A12V', '0.81', '86.0', '0.78'], ['G47D+S50T', '0.76', '82.7', '0.74']]; return <div className="protein-results"><div className="result-head"><div><span className="eyebrow"><Check size={14}/> DESIGN ROUND 01</span><h3>Prioritized variants</h3></div><div className="confidence">ACCEPTANCE<br/><strong>3 / 228</strong></div></div><div className="protein-table"><div className="table-head"><span>VARIANT</span><span>COMPOSITE</span><span>pLDDT</span><span>PROPERTY</span></div>{rows.map(([id, score, plddt, property], i) => <div className="protein-row" key={id}><span className="rank">0{i + 1}</span><strong>{id}</strong><span>{score}</span><span>{plddt}</span><span>{property}</span></div>)}</div><p className="result-note">Weighted ranking: ESM sequence effect · structural confidence · RMSD · local property heuristic</p></div>; }

function Demo({ kind, index, next, prev }) { const [phase, setPhase] = useState(0); const mineral = kind === 'mineral'; useEffect(() => { setPhase(0); const timings = [1200, 3400, 6900]; const timers = timings.map((time, i) => window.setTimeout(() => setPhase(i + 1), time)); return () => timers.forEach(window.clearTimeout); }, [kind]); const prompt = mineral ? '请针对提供的未知混合物拉曼光谱开展一次盲测成分鉴定与解混分析' : '针对目标蛋白的关键活性位点，构建突变库并筛选具有更优综合得分的候选变体'; return <SectionFrame index={index} onNext={next} onPrev={prev} nextLabel={mineral ? '合成路径预测' : '完成'}><div className="demo-title"><span className="eyebrow"><FlaskConical size={15}/> LIVE SCIENTIFIC WORKFLOW</span><h2>{mineral ? '混合物成分分析' : '蛋白定向进化'}</h2></div><div className="demo-stage"><AnimatePresence mode="wait">{phase < 1 && <motion.div key="source" className={`source-visual ${mineral ? 'spectral-card' : 'protein-card'}`} initial={{ opacity: 0, scale: .9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: .45, y: 84 }} transition={{ duration: .65 }}><div className="visual-label">{mineral ? 'UNKNOWN RAMAN SPECTRUM / CASE 1' : 'TARGET PROTEIN / ACTIVE-SITE REGION'}</div>{mineral ? <Spectrum /> : <ProteinVisual />}</motion.div>}</AnimatePresence><AnimatePresence>{phase >= 1 && phase < 3 && <motion.div className="prompt-box" initial={{ opacity: 0, y: 40, scale: .88 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, x: -90 }} transition={{ duration: .5 }}><div className="prompt-attachment">{mineral ? <Spectrum /> : <ProteinVisual />}</div><div className="prompt-text"><small>OPENAI4S TASK</small><p><Typewriter active={phase >= 1} text={prompt} /></p></div><button aria-label="运行任务"><Play size={17} fill="currentColor" /></button></motion.div>}</AnimatePresence><AnimatePresence>{phase === 2 && <motion.div className="agent-fade" initial={{ opacity: 0 }} animate={{ opacity: 1 }}><CodePanel kind={kind} /></motion.div>}{phase === 3 && <motion.div className={`result-fade ${mineral ? 'mineral-result-fade' : ''}`} initial={{ opacity: 0, y: 35 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .6 }}>{mineral ? <MineralResult /> : <ProteinResult />}</motion.div>}</AnimatePresence></div><button className="replay" onClick={() => setPhase(0)}><RotateCcw size={14}/> replay workflow</button></SectionFrame>; }

function End({ prev, restart }) { return <SectionFrame index={6} onPrev={prev} restart={restart}><div className="end"><div className="eyebrow"><Sparkles size={15}/> ONE HARNESS, MANY SCIENTIFIC WORKFLOWS</div><h1>OpenAI4S</h1><p>将自然语言、科学实体、推理与工具执行连接成统一的<br />AI 驱动科学问题求解系统。</p><div className="capabilities"><span>natural language prompting</span><span>scientific entity grounding</span><span>agentic reasoning and coding</span><span>automated scientific analysis</span></div><a href="https://github.com/OpenAI4S/openai4s" target="_blank" rel="noreferrer">github.com/OpenAI4S/openai4s <ArrowRight size={16}/></a></div></SectionFrame>; }

function App() { const [page, setPage] = useState(0); const next = () => setPage(p => Math.min(TOTAL - 1, p + 1)); const prev = () => setPage(p => Math.max(0, p - 1)); const goTo = target => { if (target === 'retrosynthesis') setPage(3); }; const screens = useMemo(() => [<Cover next={next}/>, <Overview index={1} title="有机化学" label="CHEMISTRY" tasks={chemistryTasks} next={next} prev={prev} onTaskSelect={goTo}/>, <Demo kind="mineral" index={2} next={next} prev={prev}/>, <RetrosynthesisDemo index={3} next={next} prev={prev}/>, <Overview index={4} title="生命科学" label="LIFE SCIENCE" tasks={lifeTasks} next={next} prev={prev} onTaskSelect={goTo}/>, <Demo kind="protein" index={5} next={next} prev={prev}/>, <End prev={prev} restart={() => setPage(0)}/>], []); useEffect(() => { const key = e => { if (e.key === 'ArrowRight' || e.key === ' ') next(); if (e.key === 'ArrowLeft') prev(); }; window.addEventListener('keydown', key); return () => window.removeEventListener('keydown', key); }); return <div className="app"><AnimatePresence mode="wait">{React.cloneElement(screens[page], { key: page })}</AnimatePresence></div>; }

createRoot(document.getElementById('root')).render(<App />);
