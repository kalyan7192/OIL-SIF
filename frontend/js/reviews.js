// HSE Expert Review Queue (Human-in-the-Loop)

async function loadReviewQueue() {
  const container = document.getElementById('reviews-queue-container');
  if (container) {
    container.innerHTML = '<div class="text-center py-8 text-slate-400 text-xs font-semibold">Fetching pending reviews from safety records...</div>';
  }
  
  try {
    const res = await fetch(`${API_BASE}/reviews/queue`);
    if (!res.ok) throw new Error('Failed to load queue');
    const items = await res.json();
    renderReviewQueue(items);
  } catch (err) {
    console.error('Error loading review queue:', err);
    if (container) {
      container.innerHTML = '<div class="text-center py-8 text-red-600 text-xs font-bold">Failed to connect to review queue</div>';
    }
  } finally {
    if (window.lucide) lucide.createIcons();
  }
}

function renderReviewQueue(items) {
  const container = document.getElementById('reviews-queue-container');
  if (!container) return;
  container.innerHTML = '';
  
  if (!items || items.length === 0) {
    container.innerHTML = `
      <div class="bg-white p-12 rounded-2xl border border-slate-200 text-center shadow-sm">
        <div class="w-14 h-14 bg-emerald-50 text-emerald-600 rounded-2xl mx-auto flex items-center justify-center border border-emerald-200 mb-3 shadow-sm">
          <i data-lucide="check-circle" class="w-8 h-8"></i>
        </div>
        <h3 class="text-base font-bold text-slate-900">Review Queue is Clear!</h3>
        <p class="text-xs text-slate-500 mt-1">All safety observations have high model confidence or have been validated by HSE experts.</p>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }
  
  items.forEach(r => {
    const card = document.createElement('div');
    card.className = 'bg-white p-5 sm:p-6 rounded-2xl border border-purple-200 hover:border-purple-300 transition-all shadow-sm space-y-4';
    card.id = `review-card-${r.report_id}`;
    
    const confPct = `${(r.ai.sif_confidence * 100).toFixed(1)}%`;
    const isSif = r.ai.sif_potential;

    card.innerHTML = `
      <div class="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
        <div class="flex items-center space-x-3">
          <span class="font-mono font-bold text-amber-600 text-sm">${r.report_id}</span>
          <span class="bg-slate-100 text-slate-700 text-xs px-2.5 py-0.5 rounded-full font-bold border border-slate-200">${r.site}</span>
          <span class="text-xs text-slate-400 font-medium">${r.date}</span>
        </div>
        <span class="bg-purple-50 text-purple-700 border border-purple-200 text-xs font-bold px-3 py-1 rounded-full shadow-sm">
          Low Confidence: ${confPct}
        </span>
      </div>

      <div>
        <p class="text-sm text-slate-800 leading-relaxed font-sans bg-slate-50 p-4 rounded-xl border border-slate-200">
          ${r.description}
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs bg-slate-50 p-3.5 rounded-xl border border-slate-200">
        <div>
          <span class="text-slate-400 block uppercase text-[10px] font-bold">AI SIF Prediction</span>
          <span class="font-black ${isSif ? 'text-red-600' : 'text-emerald-700'} text-xs">
            ${isSif ? 'YES — SIF Potential' : 'NO — Routine Hazard'}
          </span>
        </div>
        <div>
          <span class="text-slate-400 block uppercase text-[10px] font-bold">AI Life-Saving Rule</span>
          <span class="font-bold text-amber-700 text-xs">${r.ai.life_saving_rule_name}</span>
        </div>
        <div>
          <span class="text-slate-400 block uppercase text-[10px] font-bold">Failed Barrier</span>
          <span class="font-bold text-slate-800 text-xs">${r.ai.precursor.barrier_failure}</span>
        </div>
      </div>

      <div class="pt-2 flex flex-wrap items-center justify-between gap-3">
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center space-x-2">
            <label class="text-xs font-bold text-slate-700">Expert Decision:</label>
            <select id="select-sif-${r.report_id}" class="bg-white border border-slate-300 text-xs font-semibold rounded-xl px-3 py-1.5 text-slate-800 focus:ring-2 focus:ring-amber-500">
              <option value="true" ${isSif ? 'selected' : ''}>Confirm SIF (YES)</option>
              <option value="false" ${!isSif ? 'selected' : ''}>Classify as Non-SIF (NO)</option>
            </select>
          </div>

          <div class="flex items-center space-x-2">
            <label class="text-xs font-bold text-slate-700">Notes:</label>
            <input id="notes-${r.report_id}" type="text" placeholder="Reviewer comments / justification..." class="bg-white border border-slate-300 text-xs rounded-xl px-3 py-1.5 text-slate-800 w-56 focus:ring-2 focus:ring-amber-500">
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <button onclick="submitReviewCard('${r.report_id}')" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition shadow-sm flex items-center space-x-1.5">
            <i data-lucide="check" class="w-3.5 h-3.5"></i>
            <span>Validate & Save Decision</span>
          </button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
  
  if (window.lucide) lucide.createIcons();
}

async function submitReviewCard(reportId) {
  const sifSelect = document.getElementById(`select-sif-${reportId}`);
  const notesInput = document.getElementById(`notes-${reportId}`);

  const expertSif = sifSelect ? sifSelect.value === 'true' : true;
  const notes = notesInput ? notesInput.value.trim() : '';

  try {
    const res = await fetch(`${API_BASE}/reviews/${encodeURIComponent(reportId)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: 'APPROVED',
        reviewer_name: 'Lead HSE Specialist',
        expert_sif_label: expertSif,
        expert_notes: notes || 'Verified and updated in database by HSE reviewer.'
      })
    });
    if (res.ok) {
      const card = document.getElementById(`review-card-${reportId}`);
      if (card) { 
        card.style.opacity = '0.3'; 
        setTimeout(() => {
          card.remove();
          const remaining = document.querySelectorAll('[id^="review-card-"]').length;
          if (remaining === 0) loadReviewQueue();
        }, 300); 
      }
      refreshAllData();
    }
  } catch (err) { 
    console.error('Error submitting review:', err); 
    alert('Failed to submit review to database.');
  }
}

window.submitReviewCard = submitReviewCard;
window.submitReview = (id) => submitReviewCard(id);