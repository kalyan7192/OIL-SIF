// Safety Reports Table & Management (Instant Deletion Update & UI Sync)

let currentReportsPage = 1;
let reportsPageSize = 12;
let searchTimeout = null;
let selectedUploadFile = null;
let selectedReportIds = new Set();

function debounceReportsSearch() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    loadReportsTable(1);
  }, 300);
}

async function loadReportsTable(page = 1) {
  currentReportsPage = page;
  const search = document.getElementById('reports-search-input')?.value.trim() || '';
  const sifVal = document.getElementById('reports-filter-sif')?.value || 'all';
  const ruleVal = document.getElementById('reports-filter-rule')?.value || 'all';
  const siteVal = document.getElementById('reports-filter-site')?.value || 'all';
  const reviewVal = document.getElementById('reports-filter-review')?.value || 'all';

  let url = `${API_BASE}/reports?page=${page}&page_size=${reportsPageSize}`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (sifVal !== 'all') url += `&sif_potential=${sifVal === 'true'}`;
  if (ruleVal !== 'all') url += `&rule_id=${encodeURIComponent(ruleVal)}`;
  if (siteVal !== 'all') url += `&site=${encodeURIComponent(siteVal)}`;
  if (reviewVal !== 'all') url += `&review_status=${encodeURIComponent(reviewVal)}`;

  try {
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();
    
    // Auto-adjust page if current page became empty after deletions
    if ((!data.items || data.items.length === 0) && data.total > 0 && page > 1) {
      return loadReportsTable(data.total_pages);
    }

    renderReportsTable(data);
  } catch (err) {
    console.error('Error loading reports:', err);
  }
}

function renderReportsTable(data) {
  const tbody = document.getElementById('reports-table-body');
  if (!tbody) return;
  tbody.innerHTML = '';

  // Reset select all checkbox
  const selectAllCb = document.getElementById('reports-select-all');
  if (selectAllCb) selectAllCb.checked = false;

  updateBatchActionBar();

  if (!data.items || data.items.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" class="px-4 py-12 text-center text-slate-400 text-xs font-semibold">
          <i data-lucide="folder-open" class="w-8 h-8 mx-auto mb-2 text-slate-300"></i>
          No safety observations match the current search or filters.
        </td>
      </tr>
    `;
    document.getElementById('reports-pagination-info').textContent = 'Showing 0 to 0 of 0 observations';
    document.getElementById('reports-pagination-buttons').innerHTML = '';
    if (window.lucide) lucide.createIcons();
    return;
  }

  data.items.forEach(r => {
    const effectiveSif = r.review?.is_override && r.review?.expert_sif_label !== null ? r.review.expert_sif_label : r.ai.sif_potential;
    const sifBadgeClass = effectiveSif ? 'badge-sif-yes' : 'badge-sif-no';
    const sifText = effectiveSif ? 'Critical / Life-Threatening' : 'Minor / Routine';
    const confPct = `${(r.ai.sif_confidence * 100).toFixed(0)}%`;
    const isChecked = selectedReportIds.has(r.report_id);

    const row = document.createElement('tr');
    row.className = `hover:bg-slate-50 transition cursor-pointer border-b border-slate-100 ${isChecked ? 'bg-amber-50/40' : ''}`;
    row.id = `report-row-${r.report_id}`;
    row.onclick = (e) => {
      // Don't open modal if clicked on checkbox or action buttons
      if (e.target.tagName === 'INPUT' || e.target.closest('button') || e.target.closest('a')) return;
      openReportModal(r.report_id);
    };

    row.innerHTML = `
      <td class="px-4 py-3.5 text-center" onclick="event.stopPropagation();">
        <input type="checkbox" value="${r.report_id}" ${isChecked ? 'checked' : ''} onchange="toggleReportSelection('${r.report_id}', this.checked)" class="w-4 h-4 rounded text-amber-600 focus:ring-amber-500 border-slate-300 cursor-pointer">
      </td>
      <td class="px-3 py-3.5 font-mono font-bold text-amber-700 text-xs">${r.report_id}</td>
      <td class="px-3 py-3.5 text-slate-500 whitespace-nowrap text-xs font-medium">${r.date}</td>
      <td class="px-3 py-3.5">
        <div class="font-bold text-slate-900 text-xs">${r.site}</div>
        <div class="text-[11px] text-slate-500 font-medium">${r.location || r.ai.precursor.location}</div>
      </td>
      <td class="px-3 py-3.5 max-w-xs truncate text-slate-800 font-medium text-xs" title="${r.description}">${r.description}</td>
      <td class="px-3 py-3.5 text-center">
        <span class="px-2.5 py-1 rounded-full text-[10px] font-extrabold tracking-wide ${sifBadgeClass}">${sifText}</span>
      </td>
      <td class="px-3 py-3.5 font-mono font-bold text-xs ${r.ai.sif_confidence >= 0.80 ? 'text-emerald-700' : (r.ai.sif_confidence >= 0.65 ? 'text-amber-600' : 'text-purple-600')}">${confPct}</td>
      <td class="px-3 py-3.5">
        <span class="bg-slate-100 text-slate-800 px-2.5 py-1 rounded-lg text-[11px] font-bold border border-slate-200">${r.ai.life_saving_rule_name}</span>
      </td>
      <td class="px-3 py-3.5 text-slate-600 text-[11px] font-medium">${r.ai.precursor.barrier_failure}</td>
      <td class="px-3 py-3.5 text-center whitespace-nowrap" onclick="event.stopPropagation();">
        <div class="flex items-center justify-center space-x-1.5">
          <button onclick="openReportModal('${r.report_id}')" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 font-bold px-2.5 py-1.5 rounded-lg transition shadow-sm" title="Inspect details">
            Inspect
          </button>
          <button onclick="deleteSingleReport('${r.report_id}')" class="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition border border-transparent hover:border-red-200" title="Delete observation">
            <i data-lucide="trash-2" class="w-4 h-4"></i>
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(row);
  });

  const start = (data.page - 1) * data.page_size + 1;
  const end = Math.min(start + data.items.length - 1, data.total);
  document.getElementById('reports-pagination-info').textContent = `Showing ${start} to ${end} of ${data.total} observations`;

  const btnContainer = document.getElementById('reports-pagination-buttons');
  btnContainer.innerHTML = '';

  if (data.page > 1) {
    btnContainer.innerHTML += `<button onclick="loadReportsTable(${data.page - 1})" class="bg-white hover:bg-slate-100 border border-slate-300 text-xs font-bold px-3 py-1.5 rounded-lg text-slate-700 shadow-sm">Previous</button>`;
  }
  btnContainer.innerHTML += `<span class="text-xs font-bold text-slate-600 px-2">Page ${data.page} of ${data.total_pages}</span>`;
  if (data.page < data.total_pages) {
    btnContainer.innerHTML += `<button onclick="loadReportsTable(${data.page + 1})" class="bg-white hover:bg-slate-100 border border-slate-300 text-xs font-bold px-3 py-1.5 rounded-lg text-slate-700 shadow-sm">Next</button>`;
  }

  if (window.lucide) lucide.createIcons();
}

// Multi-Selection Logic
function toggleReportSelection(reportId, isChecked) {
  if (isChecked) {
    selectedReportIds.add(reportId);
  } else {
    selectedReportIds.delete(reportId);
  }
  const row = document.getElementById(`report-row-${reportId}`);
  if (row) {
    if (isChecked) row.classList.add('bg-amber-50/40');
    else row.classList.remove('bg-amber-50/40');
  }
  updateBatchActionBar();
}

function toggleSelectAll(isChecked) {
  const checkboxes = document.querySelectorAll('#reports-table-body input[type="checkbox"]');
  checkboxes.forEach(cb => {
    cb.checked = isChecked;
    const repId = cb.value;
    if (isChecked) selectedReportIds.add(repId);
    else selectedReportIds.delete(repId);
    
    const row = document.getElementById(`report-row-${repId}`);
    if (row) {
      if (isChecked) row.classList.add('bg-amber-50/40');
      else row.classList.remove('bg-amber-50/40');
    }
  });
  updateBatchActionBar();
}

function clearSelection() {
  selectedReportIds.clear();
  const selectAllCb = document.getElementById('reports-select-all');
  if (selectAllCb) selectAllCb.checked = false;
  const checkboxes = document.querySelectorAll('#reports-table-body input[type="checkbox"]');
  checkboxes.forEach(cb => {
    cb.checked = false;
    const row = document.getElementById(`report-row-${cb.value}`);
    if (row) row.classList.remove('bg-amber-50/40');
  });
  updateBatchActionBar();
}

function updateBatchActionBar() {
  const bar = document.getElementById('reports-batch-action-bar');
  const countLabel = document.getElementById('reports-selected-count');
  if (!bar || !countLabel) return;

  if (selectedReportIds.size > 0) {
    bar.classList.remove('hidden');
    countLabel.textContent = `${selectedReportIds.size} observation${selectedReportIds.size > 1 ? 's' : ''} selected`;
  } else {
    bar.classList.add('hidden');
  }
}

// Deletion Handlers - Direct & Instantaneous UI Updates
async function deleteSingleReport(reportId) {
  if (!confirm(`Are you sure you want to permanently delete observation ${reportId}?`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/reports/${encodeURIComponent(reportId)}`, {
      method: 'DELETE'
    });

    if (res.ok) {
      selectedReportIds.delete(reportId);
      closeReportModal();
      
      // Instant row removal from DOM
      const row = document.getElementById(`report-row-${reportId}`);
      if (row) row.remove();

      // Immediate refresh of table and dashboard
      await loadReportsTable(currentReportsPage);
      refreshDashboard();
      if (typeof renderAnalysisSection === 'function') renderAnalysisSection();
    } else {
      alert('Failed to delete report.');
    }
  } catch (err) {
    console.error('Error deleting report:', err);
    alert('Error connecting to server.');
  }
}

async function deleteSelectedReports() {
  const count = selectedReportIds.size;
  if (count === 0) return;

  if (!confirm(`Are you sure you want to permanently delete all ${count} selected safety observations?`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/reports/delete-batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_ids: Array.from(selectedReportIds) })
    });

    if (res.ok) {
      selectedReportIds.clear();
      updateBatchActionBar();
      
      // Immediate refresh of table and dashboard
      await loadReportsTable(currentReportsPage);
      refreshDashboard();
      if (typeof renderAnalysisSection === 'function') renderAnalysisSection();
    } else {
      alert('Failed to delete selected reports.');
    }
  } catch (err) {
    console.error('Error deleting selected reports:', err);
    alert('Error connecting to server.');
  }
}

// Modal Inspector
async function openReportModal(reportId) {
  try {
    const res = await fetch(`${API_BASE}/reports/${encodeURIComponent(reportId)}`);
    if (!res.ok) return;
    const r = await res.json();

    document.getElementById('modal-report-id').textContent = r.report_id;
    document.getElementById('modal-report-type').textContent = r.report_type;
    document.getElementById('modal-report-meta').textContent = `${r.site} • ${r.date}`;
    document.getElementById('modal-description').textContent = r.description;

    const effectiveSif = r.review?.is_override && r.review?.expert_sif_label !== null ? r.review.expert_sif_label : r.ai.sif_potential;
    const badge = document.getElementById('modal-sif-badge');
    badge.textContent = effectiveSif ? 'CRITICAL DANGER / SIF RISK' : 'MINOR / ROUTINE HAZARD';
    badge.className = effectiveSif ? 'px-3 py-0.5 rounded-full text-xs font-black badge-sif-yes' : 'px-3 py-0.5 rounded-full text-xs font-black badge-sif-no';

    document.getElementById('modal-confidence').textContent = `${(r.ai.sif_confidence * 100).toFixed(1)}% Confidence`;
    document.getElementById('modal-rule-name').textContent = r.ai.life_saving_rule_name;
    document.getElementById('modal-barrier').textContent = r.ai.precursor.barrier_failure;

    const modalDeleteBtn = document.getElementById('modal-btn-delete');
    if (modalDeleteBtn) {
      modalDeleteBtn.onclick = () => deleteSingleReport(r.report_id);
    }

    const evContainer = document.getElementById('modal-evidence-tags');
    evContainer.innerHTML = '';
    if (r.ai.precursor.evidence_snippets && r.ai.precursor.evidence_snippets.length > 0) {
      r.ai.precursor.evidence_snippets.forEach(phrase => {
        evContainer.innerHTML += `<span class="evidence-chip">${phrase}</span>`;
      });
    } else {
      evContainer.innerHTML = '<span class="text-xs text-slate-400 font-medium">No specific trigger keywords extracted</span>';
    }

    const modal = document.getElementById('report-modal');
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error('Error fetching modal report:', err);
  }
}

function closeReportModal() {
  const modal = document.getElementById('report-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
}

// Drag & Drop / Batch File Upload Handlers
function initUploadHandlers() {
  const dropZone = document.getElementById('drop-zone');
  if (!dropZone) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('border-amber-500', 'bg-amber-50/50');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('border-amber-500', 'bg-amber-50/50');
    }, false);
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      handleFileSelected(files[0]);
    }
  });
}

function handleFileSelect(e) {
  const files = e.target.files;
  if (files.length > 0) {
    handleFileSelected(files[0]);
  }
}

function handleFileSelected(file) {
  selectedUploadFile = file;
  document.getElementById('upload-status-box').classList.remove('hidden');
  document.getElementById('upload-file-name').textContent = file.name;
  document.getElementById('upload-file-size').textContent = `${(file.size / 1024).toFixed(1)} KB`;
  document.getElementById('upload-result-summary').classList.add('hidden');
}

function resetUploadForm() {
  selectedUploadFile = null;
  const fileInput = document.getElementById('csv-file-input');
  if (fileInput) fileInput.value = '';
  const statusBox = document.getElementById('upload-status-box');
  if (statusBox) statusBox.classList.add('hidden');
  const summaryBox = document.getElementById('upload-result-summary');
  if (summaryBox) summaryBox.classList.add('hidden');
  const dropZone = document.getElementById('drop-zone');
  if (dropZone) dropZone.classList.remove('border-amber-500', 'bg-amber-50/50');
}
window.resetUploadForm = resetUploadForm;

async function executeUpload() {
  if (!selectedUploadFile) {
    alert('Please choose a CSV file to upload.');
    return;
  }

  const formData = new FormData();
  formData.append('file', selectedUploadFile);

  const btn = document.getElementById('btn-start-upload');
  btn.disabled = true;
  btn.textContent = 'Processing & Writing Records...';

  try {
    const res = await fetch(`${API_BASE}/reports/upload`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      alert('Upload failed.');
      return;
    }

    const data = await res.json();
    
    // Clear selection state and hide upload action box
    const fileInput = document.getElementById('csv-file-input');
    if (fileInput) fileInput.value = '';
    selectedUploadFile = null;
    document.getElementById('upload-status-box').classList.add('hidden');

    // Show summary with option to upload another
    document.getElementById('upload-result-summary').classList.remove('hidden');
    document.getElementById('upload-summary-text').innerHTML = 
      `Successfully processed <strong>${data.processed_records}</strong> safety observations.<br>Identified <strong>${data.sif_detected}</strong> critical life-threatening risks and queued <strong>${data.pending_reviews}</strong> cases for safety officer review.`;

    // Refresh all views
    refreshAllData();
  } catch (err) {
    console.error('Error executing upload:', err);
    alert('Error connecting to backend.');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Process & Save Records';
  }
}