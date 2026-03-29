let currentUser = null;

async function handleRequestOTP() {
  const name = document.getElementById('authName').value;
  const mobile = document.getElementById('authMobile').value;

  if (!name || !mobile) {
    alert("Please enter Name and Mobile");
    return;
  }

  const res = await fetch('/api/auth/request-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, mobile })
  });

  if (res.ok) {
    document.getElementById('loginStep1').style.display = 'none';
    document.getElementById('loginStep2').style.display = 'block';
  }
}

async function handleVerifyOTP() {
  const mobile = document.getElementById('authMobile').value;
  const otp = document.getElementById('authOTP').value;

  const res = await fetch('/api/auth/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mobile, otp })
  });

  if (res.ok) {
    const data = await res.json();
    currentUser = data.user;
    
    document.getElementById('profileNameDisplay').textContent = currentUser.name;
    document.getElementById('profileNameInput').value = currentUser.name;
    document.getElementById('profileMobileInput').value = currentUser.mobile;

    document.getElementById('authOverlay').style.display = 'none';
    boot();
  } else {
    alert("Invalid OTP Code.");
  }
}

let ALL_PROJECTS = [];
let ALL_SCHEMES = [];

const dom = {
  loadingOverlay: document.getElementById('loadingOverlay'),
  fiscalTag: document.getElementById('fiscalTag'),
  kpiGrid: document.getElementById('kpiGrid'),
  projTableBody: document.querySelector('#projTable tbody'),
  resultCount: document.getElementById('resultCount'),
  searchInput: document.getElementById('searchInput'),
  statusFilter: document.getElementById('statusFilter'),
  
  dashboardView: document.getElementById('dashboardView'),
  schemesView: document.getElementById('schemesView'),
  reportView: document.getElementById('reportView'),
  profileView: document.getElementById('profileView'), 
  analyticsView: document.getElementById('analyticsView'), 
  
  btnDashboard: document.getElementById('btnDashboard'),
  btnSchemes: document.getElementById('btnSchemes'),
  btnReport: document.getElementById('btnReport'),
  btnProfile: document.getElementById('btnProfile'), 
  btnAnalytics: document.getElementById('btnAnalytics'), 

  schemesGrid: document.getElementById('schemesGrid'),
  yearFilter: document.getElementById('yearFilter'),
  schemeSearchInput: document.getElementById('schemeSearchInput'),
  schemeCount: document.getElementById('schemeCount')
};

function escapeHTML(str) {
  if (typeof str !== 'string') return str;
  return str.replace(/[&<>'\"]/g, tag => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[tag]));
}

function debounce(func, wait) {
  let timeout;
  return function(...args) { clearTimeout(timeout); timeout = setTimeout(() => func.apply(this, args), wait); };
}

window.switchView = function(viewName) {
  dom.dashboardView.style.display = viewName === 'dashboard' ? 'flex' : 'none';
  dom.schemesView.style.display = viewName === 'schemes' ? 'flex' : 'none';
  dom.reportView.style.display = viewName === 'report' ? 'block' : 'none';
  dom.profileView.style.display = viewName === 'profile' ? 'block' : 'none'; 
  dom.analyticsView.style.display = viewName === 'analytics' ? 'block' : 'none'; 
  
  dom.btnDashboard.classList.toggle('active', viewName === 'dashboard');
  dom.btnSchemes.classList.toggle('active', viewName === 'schemes');
  dom.btnReport.classList.toggle('active', viewName === 'report');
  if(dom.btnProfile) dom.btnProfile.classList.toggle('active', viewName === 'profile'); 
  if(dom.btnAnalytics) dom.btnAnalytics.classList.toggle('active', viewName === 'analytics'); 
  
  if(viewName === 'analytics') {
      window.dispatchEvent(new Event('resize')); 
  }
};

async function boot() {
  try {
    const res1 = await fetch('/api/summary'); 
    const data1 = await res1.json();
    renderKPIs(data1.data.kpis); 
    ALL_PROJECTS = data1.data.projects;
    renderProjects(ALL_PROJECTS);
    if (dom.fiscalTag) dom.fiscalTag.textContent = `${escapeHTML(data1.data.kpis.fiscal_year)} · ${escapeHTML(data1.data.kpis.quarter)}`;

    drawMinistryChart(ALL_PROJECTS);
    drawScatterChart(ALL_PROJECTS);
    drawStateChart(ALL_PROJECTS);
    drawTimelineChart(ALL_PROJECTS);

    const res2 = await fetch('/api/schemes');
    const data2 = await res2.json();
    ALL_SCHEMES = data2.data;
    renderSchemes(ALL_SCHEMES);

    dom.loadingOverlay.style.opacity = '0'; 
    setTimeout(() => dom.loadingOverlay.style.display = 'none', 400);
  } catch (e) {
    document.querySelector('.load-text').textContent = '⚠️ Could not reach Flask backend.';
    console.error(e);
  }
}

function renderKPIs(k) {
  dom.kpiGrid.innerHTML = `
    <div class="kpi-card blue"><div class="kpi-icon">💰</div><div class="kpi-label">Total Budget</div><div class="kpi-value">₹<span id="c1">0</span> Cr</div></div>
    <div class="kpi-card gold"><div class="kpi-icon">📤</div><div class="kpi-label">Total Expenditure</div><div class="kpi-value">₹<span id="c2">0</span> Cr</div></div>
    <div class="kpi-card green"><div class="kpi-icon">✅</div><div class="kpi-label">Projects Completed</div><div class="kpi-value"><span id="c3">0</span> / ${escapeHTML(String(k.projects_total))}</div></div>
    <div class="kpi-card red"><div class="kpi-icon">⚠️</div><div class="kpi-label">Funds Unspent</div><div class="kpi-value">₹<span id="c4">0</span> Cr</div></div>`;
  counter('c1', k.total_budget_cr); counter('c2', k.total_spent_cr); counter('c3', k.projects_completed); counter('c4', k.unspent_cr);
}

function counter(id, target) {
  const el = document.getElementById(id); if (!el) return;
  const inc = target / (1400 / 16); let cur = 0;
  const t = setInterval(() => { cur = Math.min(cur + inc, target); el.textContent = Math.round(cur).toLocaleString('en-IN'); if (cur >= target) clearInterval(t); }, 16);
}

function renderProjects(data) {
  dom.resultCount.textContent = data.length + ' active results';
  if (!data.length) { dom.projTableBody.innerHTML = '<tr><td colspan="8" style="text-align:center;">No results.</td></tr>'; return; }
  
  dom.projTableBody.innerHTML = data.map(p => {
    return `<tr id="row-${p.id}">
      <td style="font-family:'DM Mono';font-size:.7rem;color:var(--text3)">${escapeHTML(p.id)}</td>
      <td class="proj-name">${escapeHTML(p.name)}</td>
      <td style="color:var(--text2)">${escapeHTML(p.sector)}</td>
      <td style="font-family:'DM Mono';color:var(--gold)">₹${escapeHTML(String(p.alloc))}</td>
      <td style="font-family:'DM Mono';color:var(--teal)">₹${escapeHTML(String(p.spent))}</td>
      <td style="font-size:.7rem;color:var(--text3)">${escapeHTML(p.start_date)} - ${escapeHTML(p.end_date)}</td>
      <td><span class="status-pill ${escapeHTML(p.status)}">${escapeHTML(p.status.toUpperCase())}</span></td>
      <td style="color:var(--text2);font-size:.72rem">${escapeHTML(p.state)}</td>
    </tr>`;
  }).join('');
}

window.searchProjects = debounce(() => {
  const q = dom.searchInput.value.toLowerCase(); const s = dom.statusFilter.value;
  let filtered = ALL_PROJECTS;
  if (q) filtered = filtered.filter(p => [p.name, p.state, p.ministry].some(v => v.toLowerCase().includes(q)));
  if (s) filtered = filtered.filter(p => p.status === s);
  renderProjects(filtered);
}, 300);

function renderSchemes(data) {
  dom.schemeCount.textContent = data.length + ' schemes found';
  if (!data.length) { dom.schemesGrid.innerHTML = '<p style="color:var(--text3)">No schemes match your criteria.</p>'; return; }

  dom.schemesGrid.innerHTML = data.map(s => {
    const uc = s.pct >= 80 ? '#00e676' : s.pct >= 60 ? '#3882ff' : '#f5c542';
    const statusClass = s.status.toLowerCase().includes('complete') ? 'complete' : s.status.toLowerCase().includes('delayed') ? 'delayed' : 'active';
    
    return `
      <div class="scheme-card">
        <div class="sc-head">
          <div class="sc-title">${escapeHTML(s.name)}</div>
          <div class="sc-year">${escapeHTML(String(s.launch_year))}</div>
        </div>
        <div class="sc-tags">
          <span class="sc-tag">${escapeHTML(s.id)}</span>
          <span class="sc-tag">${escapeHTML(s.sector)}</span>
          <span class="status-pill ${statusClass}" style="margin-left:auto">${escapeHTML(s.status)}</span>
        </div>
        <div class="sc-finance">
          <span style="color:var(--text2)">Allocated: <span style="color:var(--gold)">₹${escapeHTML(String(s.alloc))} Cr</span></span>
          <span style="color:var(--text2)">Spent: <span style="color:var(--teal)">₹${escapeHTML(String(s.spent))} Cr</span></span>
        </div>
        <div class="sc-bar-bg"><div class="sc-bar-fill" style="width:${s.pct}%;background:${uc}"></div></div>
        <div class="sc-footer" style="flex-direction: column; gap: 12px;">
          <div style="display: flex; justify-content: space-between; width: 100%;">
            <span>Utilised: <strong style="color:var(--text)">${s.pct}%</strong></span>
            <span>Timeline: <strong>${escapeHTML(s.time_taken)}</strong></span>
          </div>
          <a href="${escapeHTML(s.website_url)}" target="_blank" class="scheme-link">🔗 Visit Official Website ↗</a>
        </div>
      </div>
    `;
  }).join('');
}

window.filterSchemes = debounce(() => {
  const y = dom.yearFilter.value;
  const q = dom.schemeSearchInput.value.toLowerCase();
  let filtered = ALL_SCHEMES;
  
  if (y) filtered = filtered.filter(s => String(s.launch_year) === y);
  if (q) filtered = filtered.filter(s => s.name.toLowerCase().includes(q) || s.sector.toLowerCase().includes(q));
  
  renderSchemes(filtered);
}, 300);

window.toggleCustomIssue = function() {
  const type = document.getElementById('issueType').value;
  const customInput = document.getElementById('customIssue');
  if (type === 'custom') { customInput.style.display = 'block'; customInput.required = true; } 
  else { customInput.style.display = 'none'; customInput.required = false; }
};

window.submitReport = async function(e) {
  e.preventDefault();
  const btn = document.getElementById('submitBtn'); const msg = document.getElementById('formMessage');
  btn.textContent = 'Submitting...'; btn.disabled = true; msg.textContent = ''; 

  let finalIssueType = document.getElementById('issueType').value;
  if (finalIssueType === 'custom') finalIssueType = document.getElementById('customIssue').value;

  const payload = {
    project_id: document.getElementById('projectId').value, 
    issue_type: finalIssueType,
    description: document.getElementById('description').value
  };

  try {
    const response = await fetch('/api/report', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    if (response.ok) {
      msg.style.color = 'var(--green)'; msg.textContent = '✅ Report submitted successfully.'; 
      document.getElementById('reportForm').reset(); toggleCustomIssue(); 
    } else throw new Error('Failed to submit.');
  } catch (error) {
    msg.style.color = 'var(--red)'; msg.textContent = '❌ Error: ' + error.message;
  } finally { btn.textContent = 'Submit Report Securely'; btn.disabled = false; }
};

window.runAIAudit = async function() {
    const badge = document.getElementById('aiBadgeBtn');
    badge.textContent = '✦ Auditing Database...';
    
    try {
        const res = await fetch('/api/ai/audit');
        const audit = await res.json();
        
        document.querySelectorAll('tr').forEach(tr => tr.classList.remove('ai-flagged'));
        
        audit.anomalies.forEach(anomaly => {
            const row = document.getElementById(`row-${anomaly.id}`);
            if (row) {
                row.classList.add('ai-flagged');
                row.title = `AI Flag: ${anomaly.reason}`;
            }
        });

        badge.textContent = `✦ Trust Score: ${audit.trust_score}%`;
        
        const toast = document.getElementById('auditToast');
        toast.innerHTML = `⚠️ AI Audit Complete: <strong>${audit.anomalies_found} Anomalies Detected.</strong>`;
        toast.className = 'toast-visible';
        setTimeout(() => { toast.className = 'toast-hidden'; }, 5000);

    } catch(err) {
        badge.textContent = '✦ Audit Failed';
        console.error(err);
    }
}

window.downloadReport = function() {
    window.location.href = '/api/export/csv';
}

window.toggleChat = function() {
  const widget = document.getElementById('chatWidget');
  if (widget.classList.contains('chat-hidden')) {
    widget.classList.remove('chat-hidden');
    widget.classList.add('chat-visible');
  } else {
    widget.classList.remove('chat-visible');
    widget.classList.add('chat-hidden');
  }
}

window.handleChatEnter = function(e) {
  if (e.key === 'Enter') sendChatMessage();
}

window.sendChatMessage = async function() {
  const input = document.getElementById('chatInput');
  const msg = input.value.trim();
  if (!msg) return;

  const chatBody = document.getElementById('chatBody');
  chatBody.innerHTML += `<div class="user-msg">${escapeHTML(msg)}</div>`;
  input.value = '';
  chatBody.scrollTop = chatBody.scrollHeight;

  try {
    const res = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });
    
    const data = await res.json();
    
    chatBody.innerHTML += `<div class="bot-msg">${data.response}</div>`;
    chatBody.scrollTop = chatBody.scrollHeight;

    if (data.action === "NAVIGATE_ANALYTICS") {
        setTimeout(() => { switchView('analytics'); }, 1500);
    } else if (data.action === "NAVIGATE_REPORT") {
        setTimeout(() => { switchView('report'); }, 1500);
    }

  } catch (e) {
    chatBody.innerHTML += `<div class="bot-msg" style="color:var(--red);">Error connecting to AI Server.</div>`;
  }
}

let ministryChart, scatterChart, stateChart, timelineChart;

function drawMinistryChart(projects) {
  const minData = {};
  projects.forEach(p => {
    if(!minData[p.ministry]) minData[p.ministry] = {active:0, complete:0, delayed:0};
    if(p.status in minData[p.ministry]) minData[p.ministry][p.status]++;
  });

  const sortedMins = Object.keys(minData).sort((a,b) => 
    (minData[b].active+minData[b].complete+minData[b].delayed) - (minData[a].active+minData[a].complete+minData[a].delayed)
  ).slice(0, 6);

  const ctx = document.getElementById('ministryChart');
  if(!ctx) return;
  if (ministryChart) ministryChart.destroy();
  
  ministryChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sortedMins,
      datasets: [
        { label: 'Completed', data: sortedMins.map(m => minData[m].complete), backgroundColor: '#16a34a' },
        { label: 'Active', data: sortedMins.map(m => minData[m].active), backgroundColor: '#2563eb' },
        { label: 'Delayed', data: sortedMins.map(m => minData[m].delayed), backgroundColor: '#dc2626' }
      ]
    },
    options: { 
      responsive: true, 
      maintainAspectRatio: false, 
      scales: { x: { stacked: true }, y: { stacked: true } },
      plugins: { legend: { labels: { color: '#475569' } } }
    }
  });
}

function drawScatterChart(projects) {
  const datasets = [
    { label: 'Complete', data: [], backgroundColor: '#16a34a' },
    { label: 'Active', data: [], backgroundColor: '#2563eb' },
    { label: 'Delayed', data: [], backgroundColor: '#dc2626' },
    { label: 'Review', data: [], backgroundColor: '#d97706' }
  ];

  projects.forEach(p => {
    const point = { x: p.pct, y: p.spent, name: p.name };
    if(p.status === 'complete') datasets[0].data.push(point);
    else if(p.status === 'active') datasets[1].data.push(point);
    else if(p.status === 'delayed') datasets[2].data.push(point);
    else datasets[3].data.push(point);
  });

  const ctx = document.getElementById('scatterChart');
  if(!ctx) return;
  if (scatterChart) scatterChart.destroy();

  scatterChart = new Chart(ctx, {
    type: 'scatter',
    data: { datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        x: { title: { display: true, text: 'Completion %', color: '#475569' }, max: 100, grid: { color: '#e2e8f0' } },
        y: { title: { display: true, text: 'Budget Spent (Cr)', color: '#475569' }, grid: { color: '#e2e8f0' } }
      },
      plugins: {
        tooltip: { callbacks: { label: (ctx) => `${ctx.raw.name}: ${ctx.raw.x}% done, ₹${ctx.raw.y} Cr spent` } },
        legend: { labels: { color: '#475569' } }
      }
    }
  });
}

function drawStateChart(projects) {
  const stateData = {};
  projects.forEach(p => {
    if(p.state === 'Multi-State' || p.state === 'National') return;
    if(!stateData[p.state]) stateData[p.state] = 0;
    stateData[p.state] += p.alloc;
  });

  const sortedStates = Object.keys(stateData).sort((a,b) => stateData[b] - stateData[a]).slice(0, 5);
  const data = sortedStates.map(s => stateData[s]);

  const ctx = document.getElementById('stateChart');
  if(!ctx) return;
  if (stateChart) stateChart.destroy();

  stateChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sortedStates,
      datasets: [{ label: 'Total Allocated Budget (Cr)', data: data, backgroundColor: '#0d9488', borderRadius: 4 }]
    },
    options: { 
      indexAxis: 'y', 
      responsive: true, 
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#475569' } } }
    }
  });
}

function drawTimelineChart(projects) {
  const yearData = {};
  projects.forEach(p => {
    if(!p.end_date) return;
    const yearMatch = p.end_date.match(/\d{4}/);
    if(yearMatch) {
      const year = yearMatch[0];
      if(!yearData[year]) yearData[year] = 0;
      yearData[year]++;
    }
  });

  const sortedYears = Object.keys(yearData).sort();
  const data = sortedYears.map(y => yearData[y]);

  const ctx = document.getElementById('timelineChart');
  if(!ctx) return;
  if (timelineChart) timelineChart.destroy();

  timelineChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: sortedYears,
      datasets: [{
        label: 'Projects Targeted for Completion',
        data: data, borderColor: '#2563eb', backgroundColor: 'rgba(37, 99, 235, 0.1)',
        fill: true, tension: 0.3, pointBackgroundColor: '#2563eb'
      }]
    },
    options: { 
      responsive: true, 
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#475569' } } }
    }
  });
}