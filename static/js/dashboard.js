/**
 * Keshveda Founder Dashboard & WhatsApp Simulator Client
 */

let currentFilter = 'last_month';
let currentSimOrder = null;
let currentSimLang = 'hinglish';
let allOrdersData = [];
let bucketsChartInstance = null;
let statesChartInstance = null;
let financeChartInstance = null;
let currentThresholdsData = {};

document.addEventListener('DOMContentLoaded', () => {
  loadDashboardData();
});

function setTimeFilter(filter) {
  currentFilter = filter;
  ['yesterday', 'last_month', 'all'].forEach(f => {
    const btn = document.getElementById(`btn-${f}`);
    if (f === filter) {
      btn.className = "px-3 py-1.5 text-xs font-medium rounded-md transition-all bg-white text-slate-900 shadow-sm";
    } else {
      btn.className = "px-3 py-1.5 text-xs font-medium rounded-md transition-all text-slate-600 hover:text-slate-900";
    }
  });

  const labels = {
    'yesterday': 'Latest Date (Yesterday)',
    'last_month': 'September 2026 (Last Month)',
    'all': 'All 2,018 Historical COD Orders'
  };
  document.getElementById('current-filter-label').innerText = labels[filter] || filter;
  loadDashboardData();
}

async function loadDashboardData() {
  try {
    const res = await fetch(`/api/summary?time_filter=${currentFilter}`);
    const data = await res.json();
    currentThresholdsData = data.current_thresholds;

    updateKPIs(data);
    renderCharts(data);
    renderOrdersTable(data.sample_orders);

    // Initialize simulator with first order if not already selected
    if (!currentSimOrder && data.sample_orders && data.sample_orders.length > 0) {
      startWhatsAppSimulation(data.sample_orders[0].order_id);
    }
  } catch (err) {
    console.error("Failed to load dashboard data:", err);
  }
}

function updateKPIs(data) {
  const sim = data.simulation || {};
  const buckets = sim.buckets || {};
  const fin = sim.financial_impact_rupees || {};
  const metrics = sim.intervention_metrics || {};
  const base = sim.baseline || {};

  document.getElementById('kpi-total-orders').innerText = Number(data.total_evaluated || 0).toLocaleString();
  document.getElementById('kpi-ship-as-is').innerText = Number(buckets['Ship as-is'] || 0).toLocaleString();
  document.getElementById('kpi-confirm').innerText = Number(buckets['Ship after confirmation'] || 0).toLocaleString();
  document.getElementById('kpi-nudge').innerText = Number(buckets['Nudge to prepaid'] || 0).toLocaleString();
  document.getElementById('kpi-cancel').innerText = Number(buckets['Hold / cancel'] || 0).toLocaleString();

  document.getElementById('kpi-savings').innerText = `₹${Math.round(fin.gross_rto_savings || 0).toLocaleString()}`;
  document.getElementById('kpi-avoided-count').innerText = Math.round(metrics.avoided_rto_count || 0);
  document.getElementById('kpi-new-rto-rate').innerText = `${metrics.new_projected_rto_rate_pct || 0}%`;
  document.getElementById('kpi-base-rto-rate').innerText = `${base.rto_rate_pct || 0}%`;

  document.getElementById('kpi-lost-margin').innerText = `₹${Math.round(fin.lost_margin_from_false_cancellations_and_dropoffs || 0).toLocaleString()}`;
  document.getElementById('kpi-false-cancels').innerText = Math.round(metrics.false_cancellations || 0);

  document.getElementById('kpi-prepaid-conversions').innerText = Math.round(metrics.prepaid_conversions || 0);
  document.getElementById('kpi-discounts-incurred').innerText = `₹${Math.round(fin.prepaid_discounts_incurred || 0).toLocaleString()}`;

  const netGain = Math.round(fin.net_rupee_gain || 0);
  const netEl = document.getElementById('kpi-net-gain');
  if (netGain >= 0) {
    netEl.innerText = `+₹${netGain.toLocaleString()}`;
    netEl.className = "text-3xl font-extrabold text-emerald-400 mt-1";
  } else {
    netEl.innerText = `-₹${Math.abs(netGain).toLocaleString()}`;
    netEl.className = "text-3xl font-extrabold text-rose-400 mt-1";
  }
  document.getElementById('kpi-rto-reduction').innerText = `${metrics.rto_reduction_pct || 0}%`;
}

function renderCharts(data) {
  const buckets = data.simulation?.buckets || {};
  const fin = data.simulation?.financial_impact_rupees || {};
  const states = data.state_breakdown || [];

  // 1. Buckets Chart
  const ctxBuckets = document.getElementById('bucketsChart').getContext('2d');
  if (bucketsChartInstance) bucketsChartInstance.destroy();
  bucketsChartInstance = new Chart(ctxBuckets, {
    type: 'doughnut',
    data: {
      labels: ['Ship As-Is', 'Confirm (WhatsApp)', 'Nudge Prepaid', 'Hold / Cancel'],
      datasets: [{
        data: [
          buckets['Ship as-is'] || 0,
          buckets['Ship after confirmation'] || 0,
          buckets['Nudge to prepaid'] || 0,
          buckets['Hold / cancel'] || 0
        ],
        backgroundColor: ['#10b981', '#f59e0b', '#8b5cf6', '#f43f5e'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } }
      },
      cutout: '68%'
    }
  });

  // 2. States Chart
  const ctxStates = document.getElementById('statesChart').getContext('2d');
  if (statesChartInstance) statesChartInstance.destroy();
  statesChartInstance = new Chart(ctxStates, {
    type: 'bar',
    data: {
      labels: states.map(s => s.state),
      datasets: [{
        label: 'Historical RTO %',
        data: states.map(s => s.rto_rate),
        backgroundColor: states.map(s => s.rto_rate >= 40 ? '#f43f5e' : (s.rto_rate >= 25 ? '#f59e0b' : '#10b981')),
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      scales: {
        x: { beginAtZero: true, max: 70, ticks: { callback: v => `${v}%`, font: { size: 9 } } },
        y: { ticks: { font: { size: 10 } } }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });

  // 3. Finance Waterfall Chart
  const ctxFinance = document.getElementById('financeChart').getContext('2d');
  if (financeChartInstance) financeChartInstance.destroy();
  financeChartInstance = new Chart(ctxFinance, {
    type: 'bar',
    data: {
      labels: ['Logistics Saved', 'Margin Lost', 'Discounts Given', 'Net ₹ Gain'],
      datasets: [{
        data: [
          fin.gross_rto_savings || 0,
          -(fin.lost_margin_from_false_cancellations_and_dropoffs || 0),
          -(fin.prepaid_discounts_incurred || 0),
          fin.net_rupee_gain || 0
        ],
        backgroundColor: ['#10b981', '#f43f5e', '#a855f7', '#059669'],
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { ticks: { callback: v => `₹${v.toLocaleString()}`, font: { size: 9 } } },
        x: { ticks: { font: { size: 9 } } }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

function renderOrdersTable(orders) {
  allOrdersData = orders || [];
  filterOrdersTable();
}

function filterOrdersTable() {
  const search = (document.getElementById('order-search').value || '').toLowerCase();
  const actionFilter = document.getElementById('action-filter').value;
  const tbody = document.getElementById('orders-tbody');
  tbody.innerHTML = '';

  const filtered = allOrdersData.filter(o => {
    const matchesSearch = !search ||
      (o.order_id && o.order_id.toLowerCase().includes(search)) ||
      (o.customer_name && o.customer_name.toLowerCase().includes(search)) ||
      (o.phone && o.phone.includes(search)) ||
      (o.city && o.city.toLowerCase().includes(search)) ||
      (o.state && o.state.toLowerCase().includes(search));

    const matchesAction = actionFilter === 'ALL' || o.action === actionFilter;
    return matchesSearch && matchesAction;
  });

  filtered.slice(0, 100).forEach(order => {
    const tr = document.createElement('tr');
    tr.className = "hover:bg-slate-50 transition cursor-pointer";
    tr.onclick = (e) => {
      if (!e.target.closest('button')) {
        startWhatsAppSimulation(order.order_id);
      }
    };

    let actionBadge = '';
    if (order.action === 'Ship as-is') {
      actionBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">Ship As-Is</span>';
    } else if (order.action === 'Ship after confirmation') {
      actionBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">Confirm First</span>';
    } else if (order.action === 'Nudge to prepaid') {
      actionBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800">Nudge Prepaid</span>';
    } else {
      actionBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">Hold / Cancel</span>';
    }

    let riskBadge = '';
    if (order.risk_score >= 70) {
      riskBadge = `<span class="font-bold text-rose-600">${order.risk_score}</span>/100`;
    } else if (order.risk_score >= 40) {
      riskBadge = `<span class="font-bold text-amber-600">${order.risk_score}</span>/100`;
    } else {
      riskBadge = `<span class="font-bold text-emerald-600">${order.risk_score}</span>/100`;
    }

    tr.innerHTML = `
      <td class="p-3 font-semibold text-slate-800">
        <div>${order.order_id}</div>
        <div class="text-[10px] text-slate-400 font-normal">${order.order_datetime?.slice(0, 10) || ''}</div>
      </td>
      <td class="p-3">
        <div class="font-medium text-slate-900">${order.customer_name} · <span class="text-slate-400 font-normal">${order.phone}</span></div>
        <div class="text-[11px] text-slate-500 truncate max-w-xs" title="${order.address}, ${order.city}">${order.address}, ${order.city}</div>
        <div class="text-[10px] text-slate-400 italic mt-0.5">${order.reason}</div>
      </td>
      <td class="p-3 font-bold text-slate-800">₹${order.order_value}</td>
      <td class="p-3">${actionBadge}</td>
      <td class="p-3 text-[11px]">${riskBadge}</td>
      <td class="p-3 text-right">
        <button onclick="startWhatsAppSimulation('${order.order_id}')" class="px-2 py-1 bg-whatsapp-green text-white rounded text-[10px] font-semibold hover:bg-emerald-700 transition">
          <i class="fa-brands fa-whatsapp mr-1"></i> Sim
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// WhatsApp Simulator
async function startWhatsAppSimulation(orderId) {
  currentSimOrder = orderId;
  const orderObj = allOrdersData.find(o => o.order_id === orderId) || {};
  document.getElementById('sim-order-info').innerText = `Selected: ${orderId} · ${orderObj.customer_name || 'Customer'} (₹${orderObj.order_value || 649})`;

  try {
    const res = await fetch('/api/whatsapp/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: orderId, lang: currentSimLang })
    });
    const data = await res.json();
    renderChatMessages(data.session);
  } catch (err) {
    console.error("Failed to start WhatsApp simulation:", err);
  }
}

function renderChatMessages(session) {
  const container = document.getElementById('chat-messages');
  container.innerHTML = '';
  document.getElementById('sim-session-state').innerText = session.state || 'AWAITING_REPLY';

  const messages = session.messages || [];
  messages.forEach(msg => {
    const bubble = document.createElement('div');
    const isBot = msg.sender === 'bot';

    if (isBot) {
      bubble.className = "flex justify-start";
      bubble.innerHTML = `
        <div class="bg-whatsapp-bubble-in text-slate-800 max-w-[85%] rounded-lg p-2.5 shadow-sm text-xs border border-slate-200">
          <div class="text-[10px] font-bold text-emerald-800 mb-0.5">Keshveda Official</div>
          <div class="whitespace-pre-line leading-relaxed">${escapeHtml(msg.text)}</div>
          <div class="text-[9px] text-slate-400 text-right mt-1">${msg.timestamp || ''}</div>
        </div>
      `;
    } else {
      bubble.className = "flex justify-end";
      bubble.innerHTML = `
        <div class="bg-whatsapp-bubble-out text-slate-900 max-w-[80%] rounded-lg p-2.5 shadow-sm text-xs border border-emerald-200">
          <div class="whitespace-pre-line leading-relaxed font-medium">${escapeHtml(msg.text)}</div>
          <div class="text-[9px] text-emerald-700 text-right mt-1 flex items-center justify-end space-x-1">
            <span>${msg.timestamp || ''}</span>
            <i class="fa-solid fa-check-double text-[10px] text-emerald-600"></i>
          </div>
        </div>
      `;
    }
    container.appendChild(bubble);
  });

  // Scroll to bottom
  container.scrollTop = container.scrollHeight;
}

async function sendSimMessage(text) {
  if (!currentSimOrder) return;
  try {
    const res = await fetch('/api/whatsapp/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: currentSimOrder, text: text })
    });
    const data = await res.json();
    renderChatMessages(data.session);
  } catch (err) {
    console.error("Failed to send WhatsApp message:", err);
  }
}

function sendCustomMessage() {
  const input = document.getElementById('sim-custom-input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  sendSimMessage(text);
}

async function triggerSimTimer(eventType) {
  if (!currentSimOrder) return;
  try {
    const res = await fetch('/api/whatsapp/timer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: currentSimOrder, event: eventType })
    });
    const data = await res.json();
    renderChatMessages(data.session);
  } catch (err) {
    console.error("Failed to trigger simulator timer:", err);
  }
}

function setSimulatorLang(lang) {
  currentSimLang = lang;
  if (lang === 'hinglish') {
    document.getElementById('sim-lang-hinglish').className = "px-2 py-0.5 rounded bg-white text-emerald-800 font-bold text-[10px]";
    document.getElementById('sim-lang-english').className = "px-2 py-0.5 rounded bg-emerald-700 text-emerald-100 font-medium text-[10px]";
  } else {
    document.getElementById('sim-lang-english').className = "px-2 py-0.5 rounded bg-white text-emerald-800 font-bold text-[10px]";
    document.getElementById('sim-lang-hinglish').className = "px-2 py-0.5 rounded bg-emerald-700 text-emerald-100 font-medium text-[10px]";
  }
  if (currentSimOrder) {
    startWhatsAppSimulation(currentSimOrder);
  }
}

// Modal & Threshold Configuration
function toggleConfigModal() {
  const modal = document.getElementById('config-modal');
  modal.classList.toggle('hidden');

  if (!modal.classList.contains('hidden') && currentThresholdsData.operational_thresholds) {
    const ops = currentThresholdsData.operational_thresholds;
    const fin = currentThresholdsData.financial_assumptions;
    document.getElementById('cfg-nudge-state-val').value = ops.nudge_high_risk_state_min_order_value || 800;
    document.getElementById('cfg-nudge-general-val').value = ops.nudge_general_min_order_value || 1500;
    document.getElementById('cfg-cancel-prior-rto').value = ops.cancel_min_prior_rto || 2;
    document.getElementById('cfg-short-addr-len').value = ops.confirm_short_address_length || 25;
    document.getElementById('cfg-prepaid-discount').value = fin?.prepaid_discount_amount || 50;
  }
}

async function saveThresholds() {
  const updated = JSON.parse(JSON.stringify(currentThresholdsData));
  updated.operational_thresholds.nudge_high_risk_state_min_order_value = Number(document.getElementById('cfg-nudge-state-val').value);
  updated.operational_thresholds.nudge_general_min_order_value = Number(document.getElementById('cfg-nudge-general-val').value);
  updated.operational_thresholds.cancel_min_prior_rto = Number(document.getElementById('cfg-cancel-prior-rto').value);
  updated.operational_thresholds.confirm_short_address_length = Number(document.getElementById('cfg-short-addr-len').value);
  updated.financial_assumptions.prepaid_discount_amount = Number(document.getElementById('cfg-prepaid-discount').value);

  try {
    const res = await fetch('/api/update_thresholds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updated)
    });
    if (res.ok) {
      toggleConfigModal();
      loadDashboardData();
    }
  } catch (err) {
    console.error("Failed to save thresholds:", err);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

