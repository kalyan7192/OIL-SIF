// Live AI / NLP Analyzer Sandbox

const SAMPLES = {
  loto: { 
    text: "During scheduled maintenance on crude oil booster pump P-102B at Moran GGS-1, technician opened the 4\" flange connection without verifying the 415V breaker lock-out tag-out. No energy isolation verification was performed and circuit remained energized.",
    site: "Moran Gas Gathering Station (GGS-1)", 
    type: "Near Miss" 
  },
  height: { 
    text: "Contractor crew working at height on drilling rig derrick at Naharkatiya Rig D-14 observed using worn-out full body harness with unhooked lifeline lanyard. Fall arrest system not anchored at 28 meters elevation.", 
    site: "Naharkatiya Drilling Rig D-14", 
    type: "Unsafe Act" 
  },
  gas: { 
    text: "Wireline logging crew opened wellhead swab valve on sour gas well B-02 without wearing personal multi-gas detectors or staging 30-minute positive-pressure SCBA units. H2S concentration registered 18 ppm.", 
    site: "Baghjan Well Area B-02", 
    type: "Near Miss" 
  },
  routine: { 
    text: "A small puddle of rainwater and spilled cleaning detergent was noticed near the entrance walkway of Duliajan Central Workshop admin building, posing a minor slip hazard for office staff.", 
    site: "Duliajan Central Workshop", 
    type: "Unsafe Condition" 
  }
};

function loadSampleReport(sampleKey) {
  const sample = SAMPLES[sampleKey];
  if (!sample) return;

  document.getElementById('analyzer-text').value = sample.text;
  document.getElementById('analyzer-site').value = sample.site;
  document.getElementById('analyzer-type').value = sample.type;

  runLiveAnalysis();
}

async function runLiveAnalysis() {
  const text = document.getElementById('analyzer-text').value.trim();
  const site = document.getElementById('analyzer-site').value.trim();
  const reportType = document.getElementById('analyzer-type').value;

  if (!text) {
    alert('Please enter a safety observation text to analyze.');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        site: site || null,
        report_type: reportType
      })
    });

    if (!res.ok) {
      alert('Error running AI analysis.');
      return;
    }

    const data = await res.json();
    window.lastAnalysisResult = { ...data, text, site, reportType };
    renderAnalysisResult(data);

  } catch (err) {
    console.error('Error during analysis:', err);
    alert('Failed to connect to backend AI service.');
  }
}

function renderAnalysisResult(result) {
  document.getElementById('analyzer-placeholder').classList.add('hidden');
  const card = document.getElementById('analyzer-result-card');
  card.classList.remove('hidden');

  // SIF Badge
  const sifBadge = document.getElementById('res-sif-badge');
  if (result.sif_potential) {
    sifBadge.textContent = 'YES — SIF POTENTIAL';
    sifBadge.className = 'px-3.5 py-1 rounded-full text-xs font-black tracking-wide badge-sif-yes';
  } else {
    sifBadge.textContent = 'NO — ROUTINE HAZARD';
    sifBadge.className = 'px-3.5 py-1 rounded-full text-xs font-black tracking-wide badge-sif-no';
  }

  // Uncertain badge
  const uncertainBadge = document.getElementById('res-uncertain-badge');
  if (result.is_uncertain) {
    uncertainBadge.classList.remove('hidden');
  } else {
    uncertainBadge.classList.add('hidden');
  }

  // Confidence
  document.getElementById('res-confidence').textContent = `${(result.sif_confidence * 100).toFixed(1)}%`;

  // Rule
  document.getElementById('res-rule-name').textContent = result.life_saving_rule_name;

  // Secondary rules
  const secContainer = document.getElementById('res-secondary-rules');
  secContainer.innerHTML = '';
  if (result.secondary_rules && result.secondary_rules.length > 0) {
    result.secondary_rules.forEach(ruleName => {
      secContainer.innerHTML += `<span class="bg-slate-100 text-slate-700 border border-slate-200 px-2.5 py-0.5 rounded-lg text-xs font-semibold">${ruleName}</span>`;
    });
  }

  // Precursor Details
  document.getElementById('res-activity').textContent = result.precursor.activity;
  document.getElementById('res-location').textContent = result.precursor.location;
  document.getElementById('res-barrier').textContent = result.precursor.barrier_failure;

  // Evidence Snippets
  const evContainer = document.getElementById('res-evidence-tags');
  evContainer.innerHTML = '';
  if (result.precursor.evidence_snippets && result.precursor.evidence_snippets.length > 0) {
    result.precursor.evidence_snippets.forEach(phrase => {
      evContainer.innerHTML += `<span class="evidence-chip">${phrase}</span>`;
    });
  } else {
    evContainer.innerHTML = '<span class="text-xs text-slate-400 font-medium">No specific trigger keywords identified</span>';
  }

  // Show Save Button
  document.getElementById('btn-save-analyzed').classList.remove('hidden');

  if (window.lucide) lucide.createIcons();
}

async function saveAnalyzedReport() {
  if (!window.lastAnalysisResult) return;

  const payload = {
    description: window.lastAnalysisResult.text,
    site: window.lastAnalysisResult.site || 'General Field Operations',
    report_type: window.lastAnalysisResult.reportType || 'Near Miss',
    activity: window.lastAnalysisResult.precursor?.activity,
    location: window.lastAnalysisResult.precursor?.location
  };

  try {
    const res = await fetch(`${API_BASE}/reports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const saved = await res.json();
      alert(`Observation ${saved.report_id} successfully saved to safety records!`);
      document.getElementById('btn-save-analyzed').classList.add('hidden');
      refreshAllData();
    }
  } catch (err) {
    console.error('Error saving report:', err);
    alert('Failed to save report to database.');
  }
}