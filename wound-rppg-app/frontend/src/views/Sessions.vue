<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title gradient-text">Sessions</h1>
        <p class="page-sub">{{ store.sessions.length }} session{{ store.sessions.length !== 1 ? 's' : '' }}</p>
      </div>
      <div class="header-right">
        <div class="search-box">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="color:var(--muted);flex-shrink:0">
            <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.4"/>
            <path d="M11 11l3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
          </svg>
          <input v-model="search" placeholder="Rechercher une session…" class="search-input" />
          <button v-if="search" class="search-clear" @click="search = ''">×</button>
        </div>
        <div class="view-toggle">
          <button class="toggle-btn" :class="{ active: view === 'grid' }" @click="view = 'grid'" title="Grille">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="1" y="1" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/><rect x="8" y="1" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/><rect x="1" y="8" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/><rect x="8" y="8" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/></svg>
          </button>
          <button class="toggle-btn" :class="{ active: view === 'timeline' }" @click="switchTimeline" title="Évolution temporelle">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 11L4 7l3 2 3-5 3 2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <button class="btn-ghost btn-ghost--accent" @click="showBatch = !showBatch">
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none"><path d="M2 7h10M7 2v10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
          Batch
        </button>
      </div>
    </div>

    <!-- Batch panel -->
    <Transition name="slide-up">
      <div v-if="showBatch" class="card-block mb-5">
        <div class="card-head">
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none" style="color:var(--accent)"><path d="M3 2l9 5-9 5V2z" fill="currentColor"/></svg>
          Analyse en lot
          <span class="badge-count">{{ batchSelected.length }} sélectionnée{{ batchSelected.length > 1 ? 's' : '' }}</span>
          <div class="card-head-actions">
            <button class="btn-ghost btn-ghost--sm" @click="selectAllUnananalyzed">
              Non analysées
            </button>
            <button class="btn-accent" style="padding:5px 14px;font-size:0.78rem" @click="runBatch" :disabled="batchLoading || batchSelected.length===0">
              <v-progress-circular v-if="batchLoading" indeterminate size="12" width="2" color="white" />
              <span v-else>Lancer</span>
            </button>
          </div>
        </div>
        <div class="batch-list">
          <div v-for="s in store.sessions" :key="s.name" class="batch-row">
            <input type="checkbox" :value="s.name" v-model="batchSelected" class="batch-check" />
            <span class="batch-name">{{ s.name }}</span>
            <span class="batch-status" :class="s.has_results ? 'status-done' : 'status-pending'">
              {{ s.has_results ? '✓ Analysée' : 'En attente' }}
            </span>
            <span v-if="batchJobs[s.name]" class="job-badge" :class="`job-${batchJobs[s.name]}`">
              {{ batchJobs[s.name] }}
            </span>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Grid view -->
    <template v-if="view === 'grid'">
      <div v-if="store.loading" class="state-loading">
        <v-progress-circular indeterminate color="var(--accent)" size="28" width="2" />
        <span>Chargement des sessions…</span>
      </div>

      <div v-else-if="filteredSessions.length === 0" class="state-empty">
        <div class="empty-icon-wrap">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" stroke-width="1.3" stroke-linecap="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            <line x1="12" y1="10" x2="12" y2="16"/><line x1="9" y1="13" x2="15" y2="13"/>
          </svg>
        </div>
        <p class="empty-title">{{ search ? 'Aucun résultat' : 'Aucune session' }}</p>
        <p class="empty-sub">{{ search ? `Aucune session ne correspond à « ${search} »` : 'Commencez par une acquisition ou importez un ZIP' }}</p>
      </div>

      <div v-else class="session-grid">
        <router-link
          v-for="(s, i) in filteredSessions"
          :key="s.name"
          :to="`/analysis/${s.name}`"
          class="session-card"
          :style="{ animationDelay: `${i * 35}ms` }"
        >
          <div class="sc-accent-bar" :style="{ background: s.has_results ? 'var(--green)' : 'var(--warn)' }" />
          <div class="sc-body">
            <div class="sc-name">{{ s.name }}</div>
            <div class="sc-date">{{ formatDate(s.date) }}</div>
            <div class="sc-chips">
              <span class="chip chip--fps">{{ s.fps?.toFixed(0) }} FPS</span>
              <span class="chip chip--frames">{{ s.nb_frames }} frames</span>
              <span class="chip chip--dur">{{ s.duration_s }}s</span>
            </div>
            <div v-if="s.scenario?.label" class="sc-scenario">
              <svg width="9" height="9" viewBox="0 0 10 10" fill="none"><path d="M1 5h8M5 1l4 4-4 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
              {{ s.scenario.label }}
            </div>
          </div>
          <div class="sc-footer">
            <div class="sc-status-dot" :style="{ background: s.has_results ? 'var(--green)' : 'var(--warn)' }" />
            <span class="sc-status-text" :style="{ color: s.has_results ? 'var(--green)' : 'var(--muted)' }">
              {{ s.has_results ? "Analysée" : "Non analysée" }}
            </span>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" class="sc-arrow"><path d="M4 2l4 4-4 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
        </router-link>
      </div>
    </template>

    <!-- Timeline view -->
    <template v-else>
      <div class="card-block mb-5">
        <div class="card-head">
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none" style="color:#06b6d4"><path d="M1 11L4 7l3 2 3-5 3 2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          Évolution temporelle
          <div class="tl-filters">
            <input v-model="tlZone"    placeholder="Zone anatomique" class="tl-input" />
            <input v-model="tlLabel"   placeholder="Label tissu"     class="tl-input" />
            <input v-model="tlWoundId" placeholder="wound_id"        class="tl-input" />
            <button class="btn-accent" style="padding:5px 12px;font-size:0.78rem" @click="fetchTimeline">
              Filtrer
            </button>
          </div>
        </div>

        <div v-if="tlLoading" class="state-loading">
          <v-progress-circular indeterminate size="20" width="2" color="#06b6d4" />
          <span>Chargement…</span>
        </div>

        <div v-else-if="tlPoints.length === 0" class="state-empty" style="padding:40px">
          <p class="empty-title">Aucun point de données</p>
          <p class="empty-sub">Filtrez par zone anatomique ou label de tissu</p>
        </div>

        <div v-else>
          <v-chart :option="timelineChartOption" autoresize style="height:320px;padding:8px" />
          <div class="tl-table-wrap">
            <table class="tl-table">
              <thead>
                <tr>
                  <th>Date</th><th>Session</th><th>SNR (dB)</th><th>FC (bpm)</th><th>TMS (%)</th><th>Respi</th><th>Zone (%)</th><th>Score</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in tlPoints" :key="p.name">
                  <td>{{ formatDate(p.date) }}</td>
                  <td><router-link :to="`/analysis/${p.name}`" class="tl-link">{{ p.name }}</router-link></td>
                  <td>{{ p.snr_db }}</td>
                  <td>{{ p.hr_bpm }}</td>
                  <td>{{ (p.tms * 100).toFixed(1) }}</td>
                  <td>{{ p.rr_bpm || '—' }}</td>
                  <td>{{ p.wound_pct ? p.wound_pct + '%' : '—' }}</td>
                  <td><span class="score-chip" :style="scoreChipStyle(p.score)">{{ p.score }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import axios from "axios";
import { useSessionStore } from "../stores/session.js";
import { apiUrl } from "../lib/api.js";

const store  = useSessionStore();
const search = ref("");
const view   = ref("grid");

onMounted(() => store.fetchSessions());

const filteredSessions = computed(() =>
  store.sessions.filter(s =>
    s.name.toLowerCase().includes(search.value.toLowerCase()) ||
    s.scenario?.label?.toLowerCase().includes(search.value.toLowerCase())
  )
);

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

// ── Batch ─────────────────────────────────────────────────────────────────────
const showBatch     = ref(false);
const batchSelected = ref([]);
const batchLoading  = ref(false);
const batchJobs     = ref({});

function selectAllUnananalyzed() {
  batchSelected.value = store.sessions.filter(s => !s.has_results).map(s => s.name);
}

async function runBatch() {
  if (!batchSelected.value.length) return;
  batchLoading.value = true;
  try {
    const { data } = await axios.post(apiUrl("/analysis/batch"), {
      sessions: batchSelected.value, force: false,
    });
    for (const job of data.jobs || []) {
      batchJobs.value[job.session] = job.error ? "error" : "pending";
    }
    for (const job of data.jobs || []) {
      if (!job.job_id) continue;
      pollBatchJob(job.session, job.job_id);
    }
  } finally {
    batchLoading.value = false;
  }
}

async function pollBatchJob(sessionName, jobId) {
  while (true) {
    await new Promise(r => setTimeout(r, 3000));
    try {
      const { data } = await axios.get(apiUrl(`/analysis/${sessionName}/status/${jobId}`));
      if (data.status === "done") { batchJobs.value[sessionName] = "done"; store.fetchSessions(); return; }
      if (data.status === "error") { batchJobs.value[sessionName] = "error"; return; }
      batchJobs.value[sessionName] = "running";
    } catch { return; }
  }
}

// ── Timeline ──────────────────────────────────────────────────────────────────
const tlZone    = ref("");
const tlLabel   = ref("");
const tlWoundId = ref("");
const tlPoints  = ref([]);
const tlLoading = ref(false);

async function fetchTimeline() {
  tlLoading.value = true;
  tlPoints.value  = [];
  try {
    const params = {};
    if (tlWoundId.value) params.wound_id = tlWoundId.value;
    else {
      if (tlZone.value)  params.zone  = tlZone.value;
      if (tlLabel.value) params.label = tlLabel.value;
    }
    const { data } = await axios.get(apiUrl("/analysis/timeline"), { params });
    tlPoints.value = data.points || [];
  } finally {
    tlLoading.value = false;
  }
}

function switchTimeline() {
  view.value = "timeline";
  if (tlPoints.value.length === 0) fetchTimeline();
}

function scoreChipStyle(score) {
  if (score >= 80) return { background: "rgba(34,212,126,0.12)",  color: "var(--green)",  border: "1px solid rgba(34,212,126,0.25)" };
  if (score >= 50) return { background: "rgba(245,158,11,0.10)",  color: "var(--warn)",   border: "1px solid rgba(245,158,11,0.25)" };
  return             { background: "rgba(239,68,68,0.10)", color: "var(--danger)", border: "1px solid rgba(239,68,68,0.25)" };
}

const C = { border: "var(--border)", muted: "var(--muted)" };

const timelineChartOption = computed(() => {
  const pts   = tlPoints.value;
  const dates = pts.map(p => p.date ? new Date(p.date).toLocaleDateString("fr-FR") : p.name);
  return {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      formatter: params =>
        `<b>${params[0].axisValue}</b><br/>` +
        params.map(p => `<span style="color:${p.color}">●</span> ${p.seriesName}: ${p.value}`).join("<br/>"),
    },
    legend: { data: ["SNR (dB)", "FC (bpm)", "Score", "Zone plaie (%)"], textStyle: { color: "#55556a", fontSize: 11 }, top: 4 },
    grid: { left: 48, right: 24, top: 36, bottom: 48 },
    xAxis: { type: "category", data: dates, axisLabel: { color: "#55556a", fontSize: 10, rotate: 30 }, axisLine: { lineStyle: { color: "#1a1a2e" } } },
    yAxis: [
      { type: "value", name: "dB / bpm", nameTextStyle: { color: "#55556a", fontSize: 10 }, axisLabel: { color: "#55556a", fontSize: 10 }, splitLine: { lineStyle: { color: "#1a1a2e" } } },
      { type: "value", name: "Score", min: 0, max: 100, nameTextStyle: { color: "#55556a", fontSize: 10 }, axisLabel: { color: "#55556a", fontSize: 10 }, splitLine: { show: false } },
    ],
    series: [
      { name: "SNR (dB)",     type: "line", yAxisIndex: 0, smooth: true, symbol: "circle", data: pts.map(p => p.snr_db),    lineStyle: { color: "#06b6d4", width: 2 }, itemStyle: { color: "#06b6d4" }, areaStyle: { color: "rgba(6,182,212,0.07)" } },
      { name: "FC (bpm)",     type: "line", yAxisIndex: 0, smooth: true, symbol: "circle", data: pts.map(p => p.hr_bpm),    lineStyle: { color: "#e8622a", width: 2 }, itemStyle: { color: "#e8622a" } },
      { name: "Score",        type: "bar",  yAxisIndex: 1,                                 data: pts.map(p => p.score),     itemStyle: { color: "rgba(168,139,250,0.35)", borderRadius: [3,3,0,0] }, barMaxWidth: 28 },
      { name: "Zone plaie (%)", type: "line", yAxisIndex: 1, smooth: true, symbol: "diamond", data: pts.map(p => p.wound_pct || null), lineStyle: { color: "#f43f5e", width: 2, type: "dashed" }, itemStyle: { color: "#f43f5e" } },
    ],
  };
});
</script>

<style scoped>
.header-right { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

/* Search */
.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: 7px 12px;
  min-width: 220px;
  transition: border-color 0.15s, background 0.3s;
}
.search-box:focus-within { border-color: var(--border2); }
.search-input  { background: none; border: none; outline: none; color: var(--text); font-size: 0.82rem; width: 100%; font-family: inherit; }
.search-input::placeholder { color: var(--muted); }
.search-clear  { background: none; border: none; color: var(--muted); cursor: pointer; font-size: 1rem; padding: 0; line-height: 1; transition: color 0.15s; }
.search-clear:hover { color: var(--text2); }

/* View toggle */
.view-toggle  { display: flex; background: var(--surface); border: 1px solid var(--border); border-radius: 9px; overflow: hidden; }
.toggle-btn   { padding: 7px 10px; background: none; border: none; cursor: pointer; color: var(--muted); display: flex; align-items: center; transition: all 0.15s; }
.toggle-btn.active { background: var(--surface2); color: var(--accent); }

/* Session grid */
.session-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
@media (max-width: 1200px) { .session-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 880px)  { .session-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 480px)  { .session-grid { grid-template-columns: 1fr; } }

.session-card {
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  text-decoration: none;
  overflow: hidden;
  transition: border-color 0.2s, transform 0.18s, box-shadow 0.2s, background 0.3s;
  animation: fadeInUp 0.4s ease both;
}
.session-card:hover {
  border-color: var(--border2);
  transform: translateY(-3px);
  box-shadow: 0 8px 24px var(--shadow);
}
.session-card:hover .sc-arrow { color: var(--accent); transform: translateX(2px); }

.sc-accent-bar { height: 2px; width: 100%; flex-shrink: 0; }
.sc-body   { padding: 14px 14px 10px; flex: 1; }
.sc-name   { font-size: 0.82rem; font-weight: 700; color: var(--text); word-break: break-all; margin-bottom: 3px; line-height: 1.3; }
.sc-date   { font-size: 0.69rem; color: var(--muted); margin-bottom: 10px; }
.sc-chips  { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 8px; }
.chip { font-size: 0.67rem; font-weight: 600; padding: 2px 7px; border-radius: 4px; }
.chip--fps    { background: rgba(2,132,199,0.10); color: #38bdf8; border: 1px solid rgba(2,132,199,0.2); }
.chip--frames { background: rgba(6,182,212,0.09); color: #22d3ee; border: 1px solid rgba(6,182,212,0.2); }
.chip--dur    { background: var(--surface2); color: var(--muted); border: 1px solid var(--border); }
.sc-scenario  { display: flex; align-items: center; gap: 4px; font-size: 0.7rem; color: var(--accent); font-weight: 500; }
.sc-footer    { display: flex; align-items: center; gap: 6px; padding: 9px 14px; border-top: 1px solid var(--border); }
.sc-status-dot  { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.sc-status-text { flex: 1; font-size: 0.7rem; font-weight: 600; }
.sc-arrow { color: var(--border2); transition: color 0.15s, transform 0.15s; flex-shrink: 0; }

/* States */
.state-loading { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 60px 20px; color: var(--muted); font-size: 0.83rem; }
.state-empty   { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 80px 20px; text-align: center; }
.empty-icon-wrap { width: 52px; height: 52px; border-radius: 14px; background: var(--surface2); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; margin-bottom: 6px; }
.empty-title { font-size: 0.9rem; font-weight: 700; color: var(--text2); margin: 0; }
.empty-sub   { font-size: 0.75rem; color: var(--muted); margin: 0; }

/* Batch */
.badge-count { font-size: 0.67rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; background: var(--surface3); color: var(--muted); border: 1px solid var(--border); margin-left: 4px; }
.card-head-actions { display: flex; align-items: center; gap: 6px; margin-left: auto; }
.batch-list { max-height: 240px; overflow-y: auto; padding: 8px 14px; }
.batch-row  { display: flex; align-items: center; gap: 10px; padding: 7px 0; border-bottom: 1px solid var(--border); font-size: 0.8rem; }
.batch-row:last-child { border-bottom: none; }
.batch-check { accent-color: var(--accent); }
.batch-name  { flex: 1; color: var(--text2); font-weight: 500; font-size: 0.8rem; }
.batch-status  { font-size: 0.7rem; font-weight: 600; }
.status-done   { color: var(--green); }
.status-pending { color: var(--muted); }
.job-badge { font-size: 0.67rem; font-weight: 700; padding: 1px 8px; border-radius: 4px; }
.job-running { background: rgba(232,98,42,0.1); color: var(--accent); border: 1px solid rgba(232,98,42,0.3); }
.job-done    { background: rgba(34,212,126,0.1); color: var(--green); border: 1px solid rgba(34,212,126,0.3); }
.job-error   { background: rgba(239,68,68,0.1); color: var(--danger); border: 1px solid rgba(239,68,68,0.3); }

/* Timeline */
.tl-filters { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-left: auto; }
.tl-input {
  background: var(--surface2); border: 1px solid var(--border); border-radius: 6px;
  color: var(--text); font-size: 0.78rem; padding: 5px 10px; outline: none;
  width: 130px; font-family: inherit; transition: border-color 0.15s;
}
.tl-input::placeholder { color: var(--muted); }
.tl-input:focus { border-color: var(--border2); }
.tl-table-wrap { overflow-x: auto; padding: 0 14px 14px; }
.tl-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
.tl-table th { text-align: left; color: var(--muted); font-weight: 600; font-size: 0.67rem; text-transform: uppercase; letter-spacing: 0.5px; padding: 8px 10px; border-bottom: 1px solid var(--border); }
.tl-table td { padding: 8px 10px; border-bottom: 1px solid var(--border); color: var(--text2); }
.tl-table tr:last-child td { border-bottom: none; }
.tl-table tr:hover td { background: var(--surface2); }
.tl-link  { color: var(--accent); text-decoration: none; font-weight: 600; }
.tl-link:hover { text-decoration: underline; }
.score-chip { font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; }
</style>
