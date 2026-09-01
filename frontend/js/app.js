// Core Application Engine & Universal Event Bus

const getApiBaseUrl = () => {
  if (window.location.port && window.location.port !== '8000' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    return `http://${window.location.hostname}:8000/api`;
  }
  return '/api';
};
const API_BASE = getApiBaseUrl();

const APP = {
  currentTab: 'dashboard',
  reports: [],
  isAnalyzing: false,
  isUploading: false
};

function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  const tabContent = document.getElementById(`tab-${tabId}`);
  if (tabContent) tabContent.classList.remove('hidden');
  
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  const tabBtn = document.getElementById(`tab-btn-${tabId}`);
  if (tabBtn) tabBtn.classList.add('active');
  
  APP.currentTab = tabId;
  
  if (tabId === 'dashboard') refreshDashboard();
  if (tabId === 'reports') loadReportsTable(1);
  if (tabId === 'reviews') loadReviewQueue();
  if (tabId === 'analysis') renderAnalysisSection();
  
  if (window.lucide) lucide.createIcons();
}

function showNotification(message, type = 'info', duration = 4000) {
  // Simple toast or alert notification
  const container = document.getElementById('notification-container');
  if (!container) return;
  
  const toast = document.createElement('div');
  toast.className = `p-4 rounded-xl border bg-white shadow-lg text-xs font-semibold text-slate-800 flex items-center space-x-2 transition-all`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

// Universal Refresh: Refreshes all sections across the entire platform
async function refreshAllData() {
  const btn = document.getElementById('universal-refresh-btn');
  const icon = btn?.querySelector('[data-lucide="refresh-cw"]') || btn?.querySelector('svg');
  if (icon) icon.classList.add('animate-spin');
  
  try {
    await Promise.all([
      refreshDashboard(),
      typeof loadReportsTable === 'function' ? loadReportsTable(typeof currentReportsPage !== 'undefined' ? currentReportsPage : 1) : Promise.resolve(),
      typeof loadReviewQueue === 'function' ? loadReviewQueue() : Promise.resolve(),
      typeof renderAnalysisSection === 'function' ? renderAnalysisSection() : Promise.resolve()
    ]);
  } catch (err) {
    console.error('Error in universal refresh:', err);
  } finally {
    if (icon) icon.classList.remove('animate-spin');
    if (window.lucide) lucide.createIcons();
  }
}

document.addEventListener('DOMContentLoaded', function() {
  if (window.lucide) lucide.createIcons();
  
  refreshDashboard();
  if (typeof loadReportsTable === 'function') loadReportsTable(1);
  if (typeof initUploadHandlers === 'function') initUploadHandlers();
  
  // Universal keyboard shortcut: Ctrl+R / Cmd+R to trigger universal refresh
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
      e.preventDefault();
      refreshAllData();
    }
    if (e.key === 'Escape') closeReportModal();
  });
});