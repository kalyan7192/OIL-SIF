// Data Analysis & Statistical Analytics Engine (Human-Friendly & Robust Chart Rendering)

let chartAnalysisRules = null;
let chartAnalysisSites = null;
let chartAnalysisBarriers = null;
let chartAnalysisTrends = null;

async function renderAnalysisSection() {
  // Allow DOM layout to compute container dimensions after tab switch
  setTimeout(async () => {
    try {
      const summaryData = await renderAnalysisSummaryKPIs();
      const hasData = summaryData && summaryData.total_reports > 0;

      await Promise.all([
        renderAnalysisRules(hasData),
        renderAnalysisSites(hasData),
        renderAnalysisBarriers(hasData),
        renderAnalysisTrends(hasData)
      ]);
    } catch (err) {
      console.error('Error rendering analysis section:', err);
    }
    if (window.lucide) lucide.createIcons();
  }, 80);
}

// Top KPI summary in the Analysis tab
async function renderAnalysisSummaryKPIs() {
  try {
    const res = await fetch(`${API_BASE}/dashboard/summary`);
    if (!res.ok) return null;
    const data = await res.json();

    const elTotal = document.getElementById('analysis-kpi-total');
    if (elTotal) elTotal.textContent = (data.total_reports || 0).toLocaleString();

    const elSif = document.getElementById('analysis-kpi-sif');
    if (elSif) elSif.textContent = (data.sif_reports || 0).toLocaleString();

    const elDensity = document.getElementById('analysis-kpi-density');
    if (elDensity) elDensity.textContent = (data.overall_sif_density || 0.0).toFixed(1) + '%';

    const elPending = document.getElementById('analysis-kpi-pending');
    if (elPending) elPending.textContent = (data.pending_reviews || 0).toLocaleString();

    return data;
  } catch (e) {
    console.error('Error loading analysis summary KPIs:', e);
    return null;
  }
}

// Helper to show empty state placeholder
function showChartEmptyState(containerId, iconName, title, subtitle) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = `
    <div class="w-full h-72 flex flex-col items-center justify-center text-center p-6 bg-slate-50/70 rounded-2xl border border-dashed border-slate-200 text-slate-400">
      <div class="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-slate-400 shadow-sm mb-2.5">
        <i data-lucide="${iconName}" class="w-5 h-5"></i>
      </div>
      <p class="text-xs font-bold text-slate-700">${title}</p>
      <p class="text-[11px] text-slate-500 mt-1 max-w-xs">${subtitle}</p>
      <button onclick="switchTab('upload')" class="mt-3.5 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white text-xs font-bold px-3.5 py-1.5 rounded-xl transition shadow-sm flex items-center space-x-1.5">
        <i data-lucide="upload-cloud" class="w-3.5 h-3.5"></i>
        <span>Upload Sample Data</span>
      </button>
    </div>
  `;
}

// 1. Life-Saving Rules Pie & Donut Distribution
async function renderAnalysisRules(hasData) {
  const container = document.getElementById('container-analysis-rules');
  if (!container) return;

  if (!hasData) {
    showChartEmptyState('container-analysis-rules', 'pie-chart', 'No Safety Rules Logged Yet', 'Upload safety observation records to see the Life-Saving Rules breakdown.');
    return;
  }

  container.innerHTML = `<canvas id="chart-analysis-rules"></canvas>`;
  const canvas = document.getElementById('chart-analysis-rules');
  if (!canvas) return;

  const existingChart = Chart.getChart(canvas);
  if (existingChart) existingChart.destroy();

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  try {
    const res = await fetch(`${API_BASE}/dashboard/rules`);
    if (!res.ok) return;
    const rules = await res.json();

    if (!rules || rules.length === 0) {
      showChartEmptyState('container-analysis-rules', 'pie-chart', 'No Safety Rules Logged Yet', 'Upload safety observation records to see the Life-Saving Rules breakdown.');
      return;
    }

    const labels = rules.map(r => r.rule_name);
    const counts = rules.map(r => r.count);
    const colors = rules.map(r => r.color || '#0284c7');

    chartAnalysisRules = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: counts,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: '#ffffff',
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: '#334155', font: { size: 11, weight: '600' }, boxWidth: 12, padding: 8 }
          },
          tooltip: {
            backgroundColor: '#0f172a',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.raw} observations (${((ctx.raw / counts.reduce((a, b) => a + b, 0)) * 100).toFixed(1)}%)`
            }
          }
        },
        cutout: '60%'
      }
    });
  } catch (err) {
    console.error('Error in renderAnalysisRules:', err);
  }
}

// 2. Site SIF Precursor Density Comparison Bar Chart
async function renderAnalysisSites(hasData) {
  const container = document.getElementById('container-analysis-sites');
  if (!container) return;

  if (!hasData) {
    showChartEmptyState('container-analysis-sites', 'map-pin', 'No Facility Data Logged Yet', 'Upload safety observations to compare danger rates across Indian installations.');
    return;
  }

  container.innerHTML = `<canvas id="chart-analysis-sites"></canvas>`;
  const canvas = document.getElementById('chart-analysis-sites');
  if (!canvas) return;

  const existingChart = Chart.getChart(canvas);
  if (existingChart) existingChart.destroy();

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  try {
    const res = await fetch(`${API_BASE}/dashboard/sites?min_reports=1`);
    if (!res.ok) return;
    const sites = (await res.json()).slice(0, 8);

    if (!sites || sites.length === 0) {
      showChartEmptyState('container-analysis-sites', 'map-pin', 'No Facility Data Logged Yet', 'Upload safety observations to compare danger rates across Indian installations.');
      return;
    }

    const labels = sites.map(s => s.site.length > 22 ? s.site.substring(0, 20) + '...' : s.site);
    const densities = sites.map(s => s.sif_density);
    const colors = sites.map(s => s.sif_density >= 50 ? '#ef4444' : (s.sif_density >= 35 ? '#f97316' : '#0284c7'));

    chartAnalysisSites = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Critical Danger Rate (%)',
          data: densities,
          backgroundColor: colors,
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0f172a',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => ` Critical Risk: ${ctx.raw}% (${sites[ctx.dataIndex].sif_reports} critical / ${sites[ctx.dataIndex].total_reports} total)`
            }
          }
        },
        scales: {
          x: {
            max: 100,
            grid: { color: '#f1f5f9' },
            ticks: { color: '#64748b', font: { weight: '600', size: 11 }, callback: v => v + '%' }
          },
          y: {
            grid: { display: false },
            ticks: { color: '#1e293b', font: { weight: '600', size: 11 } }
          }
        }
      }
    });
  } catch (err) {
    console.error('Error in renderAnalysisSites:', err);
  }
}

// 3. Barrier Failure Pareto Chart
async function renderAnalysisBarriers(hasData) {
  const container = document.getElementById('container-analysis-barriers');
  if (!container) return;

  if (!hasData) {
    showChartEmptyState('container-analysis-barriers', 'shield-alert', 'No Barrier Failures Logged Yet', 'Upload safety logs to identify the top safety controls requiring intervention.');
    return;
  }

  container.innerHTML = `<canvas id="chart-analysis-barriers"></canvas>`;
  const canvas = document.getElementById('chart-analysis-barriers');
  if (!canvas) return;

  const existingChart = Chart.getChart(canvas);
  if (existingChart) existingChart.destroy();

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  try {
    const res = await fetch(`${API_BASE}/dashboard/barriers`);
    if (!res.ok) return;
    const barriers = (await res.json()).slice(0, 6);

    if (!barriers || barriers.length === 0) {
      showChartEmptyState('container-analysis-barriers', 'shield-alert', 'No Barrier Failures Logged Yet', 'Upload safety logs to identify the top safety controls requiring intervention.');
      return;
    }

    const labels = barriers.map(b => b.barrier_failure.length > 24 ? b.barrier_failure.substring(0, 22) + '...' : b.barrier_failure);
    const counts = barriers.map(b => b.count);

    chartAnalysisBarriers = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Failed Safety Barrier Count',
          data: counts,
          backgroundColor: '#0284c7',
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0f172a',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => ` Occurrences: ${ctx.raw} (${barriers[ctx.dataIndex].percentage}% of all failures)`
            }
          }
        },
        scales: {
          y: {
            grid: { color: '#f1f5f9' },
            ticks: { color: '#64748b', font: { weight: '600' } }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#1e293b', font: { weight: '600', size: 10 } }
          }
        }
      }
    });
  } catch (err) {
    console.error('Error in renderAnalysisBarriers:', err);
  }
}

// 4. Monthly Temporal Trend Chart
async function renderAnalysisTrends(hasData) {
  const container = document.getElementById('container-analysis-trends');
  if (!container) return;

  if (!hasData) {
    showChartEmptyState('container-analysis-trends', 'trending-up', 'No Safety Timeline Logged Yet', 'Upload safety logs to see the month-over-month danger trajectory curve.');
    return;
  }

  container.innerHTML = `<canvas id="chart-analysis-trends"></canvas>`;
  const canvas = document.getElementById('chart-analysis-trends');
  if (!canvas) return;

  const existingChart = Chart.getChart(canvas);
  if (existingChart) existingChart.destroy();

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  try {
    const res = await fetch(`${API_BASE}/dashboard/trends`);
    if (!res.ok) return;
    const trends = await res.json();

    if (!trends || trends.length === 0) {
      showChartEmptyState('container-analysis-trends', 'trending-up', 'No Safety Timeline Logged Yet', 'Upload safety logs to see the month-over-month danger trajectory curve.');
      return;
    }

    const periods = trends.map(t => t.period);
    const sifCounts = trends.map(t => t.sif_reports);
    const totalCounts = trends.map(t => t.total_reports);

    chartAnalysisTrends = new Chart(ctx, {
      type: 'line',
      data: {
        labels: periods,
        datasets: [
          {
            label: 'Life-Threatening / Critical Precursors',
            data: sifCounts,
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.12)',
            fill: true,
            tension: 0.35,
            borderWidth: 2.5,
            pointRadius: 4,
            pointBackgroundColor: '#ef4444'
          },
          {
            label: 'Total Safety Observations',
            data: totalCounts,
            borderColor: '#0284c7',
            borderDash: [5, 5],
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 3,
            pointBackgroundColor: '#0284c7'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: '#334155', font: { size: 11, weight: '600' } }
          },
          tooltip: {
            backgroundColor: '#0f172a',
            padding: 10,
            cornerRadius: 8
          }
        },
        scales: {
          x: {
            grid: { color: '#f1f5f9' },
            ticks: { color: '#64748b', font: { weight: '600' } }
          },
          y: {
            grid: { color: '#f1f5f9' },
            ticks: { color: '#64748b', font: { weight: '600' } }
          }
        }
      }
    });
  } catch (err) {
    console.error('Error in renderAnalysisTrends:', err);
  }
}

window.renderAnalysisSection = renderAnalysisSection;
