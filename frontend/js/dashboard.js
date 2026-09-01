// Executive HSE Dashboard Engine (100% Dynamic Real-Time)

async function populateFilterDropdowns() {
  try {
    const res = await fetch(`${API_BASE}/dashboard/filters`);
    if (!res.ok) return;
    const data = await res.json();
    
    const dashSite = document.getElementById('filter-dash-site');
    if (dashSite) {
      const currentVal = dashSite.value;
      dashSite.innerHTML = '<option value="all">All OIL Sites & Facilities</option>';
      (data.sites || []).forEach(s => {
        const opt = document.createElement('option');
        opt.value = s;
        opt.textContent = s;
        dashSite.appendChild(opt);
      });
      dashSite.value = currentVal || 'all';
    }
    
    const dashAct = document.getElementById('filter-dash-activity');
    if (dashAct) {
      const currentVal = dashAct.value;
      dashAct.innerHTML = '<option value="all">All Operational Activities</option>';
      (data.activities || []).forEach(a => {
        const opt = document.createElement('option');
        opt.value = a;
        opt.textContent = a;
        dashAct.appendChild(opt);
      });
      dashAct.value = currentVal || 'all';
    }

    const repSite = document.getElementById('reports-filter-site');
    if (repSite) {
      const currentVal = repSite.value;
      repSite.innerHTML = '<option value="all">All Sites</option>';
      (data.sites || []).forEach(s => {
        const opt = document.createElement('option');
        opt.value = s;
        opt.textContent = s;
        repSite.appendChild(opt);
      });
      repSite.value = currentVal || 'all';
    }

    const repRule = document.getElementById('reports-filter-rule');
    if (repRule) {
      const currentVal = repRule.value;
      repRule.innerHTML = '<option value="all">All Life-Saving Rules</option>';
      (data.rules || []).forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.id;
        opt.textContent = r.name;
        repRule.appendChild(opt);
      });
      repRule.value = currentVal || 'all';
    }
  } catch (err) {
    console.error('Error populating filters:', err);
  }
}

async function refreshDashboard() {
  await populateFilterDropdowns();
  const site = document.getElementById('filter-dash-site')?.value || 'all';
  const activity = document.getElementById('filter-dash-activity')?.value || 'all';
  
  try {
    const res = await fetch(`${API_BASE}/dashboard/summary?site=${encodeURIComponent(site)}&activity=${encodeURIComponent(activity)}`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById('kpi-total-reports').textContent = data.total_reports.toLocaleString();
      document.getElementById('kpi-sif-reports').textContent = data.sif_reports.toLocaleString();
      document.getElementById('kpi-non-sif').textContent = data.non_sif_reports.toLocaleString();
      document.getElementById('kpi-sif-density').textContent = (data.overall_sif_density || 0.0).toFixed(1) + '%';
      document.getElementById('kpi-high-risk-sites').textContent = data.high_risk_sites_count;
      document.getElementById('kpi-pending-reviews').textContent = data.pending_reviews;
      document.getElementById('kpi-approved-reviews').textContent = data.approved_reviews;
      
      const badge = document.getElementById('review-badge');
      if (badge) {
        if (data.pending_reviews > 0) { 
          badge.textContent = data.pending_reviews; 
          badge.classList.remove('hidden'); 
        } else { 
          badge.classList.add('hidden'); 
        }
      }
    }
    
    await Promise.all([
      renderExecutiveSites(site, activity),
      renderExecutiveActivities(site, activity),
      renderExecutiveAlerts(site, activity),
      renderExecutiveBarriers(site, activity)
    ]);
  } catch (err) {
    console.error('Error fetching dashboard summary:', err);
  } finally {
    if (window.lucide) lucide.createIcons();
  }
}

// Executive Component 1: Top High-Risk Sites Progress List
async function renderExecutiveSites(site = 'all', activity = 'all') {
  const container = document.getElementById('dash-top-sites-container');
  if (!container) return;
  
  try {
    let url = `${API_BASE}/dashboard/sites?min_reports=1`;
    if (site && site !== 'all') url += `&site=${encodeURIComponent(site)}`;
    if (activity && activity !== 'all') url += `&activity=${encodeURIComponent(activity)}`;
    const res = await fetch(url);
    if (!res.ok) return;
    const sites = await res.json();

    const label = document.getElementById('dash-sites-count-label');
    if (label) label.textContent = `${sites.length} Sites Monitored`;

    if (sites.length === 0) {
      container.innerHTML = `
        <div class="text-center py-8 text-slate-400 text-xs font-semibold">
          <i data-lucide="map-pin-off" class="w-8 h-8 mx-auto mb-2 text-slate-300"></i>
          No site data logged yet. Submit observations to track high-risk sites.
        </div>
      `;
      return;
    }

    container.innerHTML = sites.slice(0, 5).map(s => {
      const isCritical = s.sif_density >= 45;
      const isModerate = s.sif_density >= 30;
      const barColor = isCritical ? 'bg-red-500' : (isModerate ? 'bg-amber-500' : 'bg-blue-500');
      const badgeClass = isCritical ? 'bg-red-100 text-red-700 border-red-200' : (isModerate ? 'bg-amber-100 text-amber-700 border-amber-200' : 'bg-blue-100 text-blue-700 border-blue-200');
      const statusText = isCritical ? 'Critical Focus' : (isModerate ? 'Elevated Risk' : 'Standard');

      return `
        <div class="p-3 bg-slate-50 hover:bg-slate-100/80 rounded-xl border border-slate-200 transition">
          <div class="flex items-center justify-between text-xs mb-1.5">
            <span class="font-bold text-slate-900 truncate max-w-[220px]" title="${s.site}">${s.site}</span>
            <div class="flex items-center space-x-2">
              <span class="font-mono font-black text-slate-900">${s.sif_density}% SIF</span>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded-full border ${badgeClass}">${statusText}</span>
            </div>
          </div>
          <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
            <div class="${barColor} h-full rounded-full transition-all duration-500" style="width: ${Math.min(s.sif_density, 100)}%"></div>
          </div>
          <div class="flex items-center justify-between text-[11px] text-slate-500 mt-1.5">
            <span>${s.sif_reports} SIF precursors detected</span>
            <span>${s.total_reports} total observations</span>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error rendering executive sites:', err);
  }
}

// Executive Component 2: High-Risk Operational Activities
async function renderExecutiveActivities(site = 'all', activity = 'all') {
  const container = document.getElementById('dash-top-activities-container');
  if (!container) return;

  try {
    let url = `${API_BASE}/dashboard/activities?min_reports=1`;
    if (site && site !== 'all') url += `&site=${encodeURIComponent(site)}`;
    if (activity && activity !== 'all') url += `&activity=${encodeURIComponent(activity)}`;
    const res = await fetch(url);
    if (!res.ok) return;
    const activities = await res.json();

    const label = document.getElementById('dash-activities-count-label');
    if (label) label.textContent = `${activities.length} Activities Monitored`;

    if (activities.length === 0) {
      container.innerHTML = `
        <div class="text-center py-8 text-slate-400 text-xs font-semibold">
          <i data-lucide="activity" class="w-8 h-8 mx-auto mb-2 text-slate-300"></i>
          No operational activity data logged yet.
        </div>
      `;
      return;
    }

    container.innerHTML = activities.slice(0, 5).map(a => {
      const isCritical = a.sif_density >= 45;
      const barColor = isCritical ? 'bg-red-500' : 'bg-amber-500';

      return `
        <div class="p-3 bg-slate-50 hover:bg-slate-100/80 rounded-xl border border-slate-200 transition">
          <div class="flex items-center justify-between text-xs mb-1.5">
            <span class="font-bold text-slate-900 truncate max-w-[220px]" title="${a.activity}">${a.activity}</span>
            <span class="font-mono font-black text-amber-700">${a.sif_density}% Density</span>
          </div>
          <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
            <div class="${barColor} h-full rounded-full transition-all duration-500" style="width: ${Math.min(a.sif_density, 100)}%"></div>
          </div>
          <div class="flex items-center justify-between text-[11px] text-slate-500 mt-1.5">
            <span>${a.sif_reports} SIF precursors</span>
            <span>${a.total_reports} reports</span>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error rendering executive activities:', err);
  }
}

// Executive Component 3: Live Critical SIF Alerts Feed
async function renderExecutiveAlerts(site = 'all', activity = 'all') {
  const container = document.getElementById('dash-critical-alerts-container');
  if (!container) return;

  try {
    let url = `${API_BASE}/reports?page=1&page_size=4&sif_potential=true`;
    if (site && site !== 'all') url += `&site=${encodeURIComponent(site)}`;
    if (activity && activity !== 'all') url += `&activity=${encodeURIComponent(activity)}`;
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();
    const items = data.items || [];

    if (items.length === 0) {
      container.innerHTML = `
        <div class="text-center py-8 text-slate-400 text-xs font-semibold">
          <i data-lucide="shield-check" class="w-8 h-8 mx-auto mb-2 text-emerald-500"></i>
          No high-potential SIF alerts recorded yet.
        </div>
      `;
      return;
    }

    container.innerHTML = items.map(r => {
      const confPct = `${(r.ai.sif_confidence * 100).toFixed(0)}%`;

      return `
        <div onclick="openReportModal('${r.report_id}')" class="p-3.5 bg-red-50/40 hover:bg-red-50/80 rounded-xl border border-red-200 transition cursor-pointer flex flex-wrap items-start justify-between gap-3">
          <div class="flex-1 min-w-[200px]">
            <div class="flex items-center space-x-2">
              <span class="font-mono font-bold text-xs text-amber-700">${r.report_id}</span>
              <span class="bg-red-100 text-red-800 text-[10px] px-2 py-0.5 rounded-full font-black border border-red-200">SIF POTENTIAL</span>
              <span class="text-xs text-slate-500 font-medium">${r.site} • ${r.date}</span>
            </div>
            <p class="text-xs text-slate-800 font-medium mt-1 line-clamp-2">${r.description}</p>
            <div class="mt-2 flex flex-wrap items-center gap-2 text-[11px]">
              <span class="bg-white text-slate-700 border border-slate-200 px-2 py-0.5 rounded font-bold">${r.ai.life_saving_rule_name}</span>
              <span class="text-slate-500">Barrier: <strong class="text-slate-700">${r.ai.precursor.barrier_failure}</strong></span>
            </div>
          </div>
          <div class="text-right flex-shrink-0">
            <span class="text-[10px] text-slate-500 uppercase font-bold block">Confidence</span>
            <span class="font-mono font-black text-red-600 text-sm">${confPct}</span>
            <button class="mt-1 text-[11px] font-bold text-amber-700 hover:text-amber-800 block">Inspect &rarr;</button>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error rendering executive alerts:', err);
  }
}

// Executive Component 4: Top Barrier Failures
async function renderExecutiveBarriers(site = 'all', activity = 'all') {
  const container = document.getElementById('dash-top-barriers-container');
  if (!container) return;

  try {
    let url = `${API_BASE}/dashboard/barriers`;
    if (site && site !== 'all') url += `?site=${encodeURIComponent(site)}&activity=${encodeURIComponent(activity)}`;
    const res = await fetch(url);
    if (!res.ok) return;
    const barriers = (await res.json()).slice(0, 3);

    if (barriers.length === 0) {
      container.innerHTML = `
        <div class="text-center py-6 text-slate-400 text-xs font-semibold">
          No barrier failures identified.
        </div>
      `;
      return;
    }

    container.innerHTML = barriers.map((b, i) => {
      return `
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200">
          <div class="flex items-center justify-between text-xs">
            <span class="font-bold text-slate-800 truncate max-w-[170px]" title="${b.barrier_failure}">${b.barrier_failure}</span>
            <span class="bg-blue-100 text-blue-800 font-bold px-2 py-0.5 rounded-full text-[10px]">${b.count} events</span>
          </div>
          <div class="mt-1 flex items-center justify-between text-[11px] text-slate-500">
            <span>Failure Frequency</span>
            <span class="font-bold text-slate-700">${b.percentage}% of all failures</span>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error rendering executive barriers:', err);
  }
}