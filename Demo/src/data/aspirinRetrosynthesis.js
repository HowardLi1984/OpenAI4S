// Derived from skills/retrosynthesis_planning/examples/aspirin_routes.json,
// aspirin_annotations.json, and aspirin_retrosynthesis.html.
export const aspirinPaths = [
  {
    id: 1,
    score: '0.998',
    steps: 1,
    donor: 'Acetic anhydride',
    donorSmiles: 'CC(=O)OC(C)=O',
    precursor: 'Salicylic acid',
    precursorSmiles: 'O=C(O)c1ccccc1O',
    reaction: 'phenolic O-acylation / aryl acetate formation',
    recommendation: 'GO WITH VERIFICATION',
  },
  {
    id: 2,
    score: '0.998',
    steps: 1,
    donor: 'Acetyl chloride',
    donorSmiles: 'CC(=O)Cl',
    precursor: 'Salicylic acid',
    precursorSmiles: 'O=C(O)c1ccccc1O',
    reaction: 'phenolic O-acylation / aryl acetate formation',
    recommendation: 'GO WITH VERIFICATION',
  },
  {
    id: 3,
    score: '0.998',
    steps: 1,
    donor: 'Acetic acid (activation required)',
    donorSmiles: 'CC(=O)O',
    precursor: 'Salicylic acid',
    precursorSmiles: 'O=C(O)c1ccccc1O',
    reaction: 'phenolic O-acylation / aryl acetate formation',
    recommendation: 'LOWER-CONFIDENCE ACTIVATION',
  },
];

export const graphNodes = [
  { id: 'aspirin', x: 435, y: 42, kind: 'target', title: 'Aspirin', meta: 'CC(=O)Oc1ccccc1C(=O)O', detail: 'Target molecule. The source graph merges five solved retrosynthesis routes at this root.' },
  { id: 'rxn-1', x: 110, y: 180, kind: 'reaction', title: 'Route 1 · O-acylation', meta: 'US PTO p=0.726', detail: 'Phenolic O-acylation using acetic anhydride and salicylic acid. Score 0.998; one reaction.' },
  { id: 'rxn-2', x: 435, y: 180, kind: 'reaction', title: 'Route 2 · O-acylation', meta: 'US PTO p=0.726', detail: 'Phenolic O-acylation using acetyl chloride and salicylic acid. Score 0.998; one reaction.' },
  { id: 'rxn-3', x: 760, y: 180, kind: 'reaction', title: 'Route 3 · O-acylation', meta: 'US PTO p=0.726', detail: 'Phenolic O-acylation using acetic acid with activation/dehydrating conditions. Score 0.998; one reaction.' },
  { id: 'anhydride', x: 40, y: 330, kind: 'stock', parent: 'rxn-1', title: 'Acetic anhydride', meta: 'CC(=O)OC(C)=O', detail: 'Terminal stock precursor in route 1.' },
  { id: 'salicylic-1', x: 195, y: 330, kind: 'stock', parent: 'rxn-1', title: 'Salicylic acid', meta: 'O=C(O)c1ccccc1O', detail: 'Terminal stock precursor shared by routes 1–3.' },
  { id: 'acetyl-chloride', x: 365, y: 330, kind: 'stock', parent: 'rxn-2', title: 'Acetyl chloride', meta: 'CC(=O)Cl', detail: 'Terminal stock precursor in route 2.' },
  { id: 'salicylic-2', x: 520, y: 330, kind: 'stock', parent: 'rxn-2', title: 'Salicylic acid', meta: 'O=C(O)c1ccccc1O', detail: 'Terminal stock precursor shared by routes 1–3.' },
  { id: 'acetic-acid', x: 690, y: 330, kind: 'stock', parent: 'rxn-3', title: 'Acetic acid', meta: 'CC(=O)O', detail: 'Terminal stock precursor in route 3; source annotations flag activation as lower confidence.' },
  { id: 'salicylic-3', x: 845, y: 330, kind: 'stock', parent: 'rxn-3', title: 'Salicylic acid', meta: 'O=C(O)c1ccccc1O', detail: 'Terminal stock precursor shared by routes 1–3.' },
];

export const graphEdges = [
  ['aspirin', 'rxn-1'], ['aspirin', 'rxn-2'], ['aspirin', 'rxn-3'],
  ['rxn-1', 'anhydride'], ['rxn-1', 'salicylic-1'],
  ['rxn-2', 'acetyl-chloride'], ['rxn-2', 'salicylic-2'],
  ['rxn-3', 'acetic-acid'], ['rxn-3', 'salicylic-3'],
];
