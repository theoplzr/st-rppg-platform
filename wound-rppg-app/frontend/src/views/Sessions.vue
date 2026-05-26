<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title gradient-text">Sessions</h1>
        <p class="page-sub">{{ store.sessions.length }} session{{ store.sessions.length !== 1 ? 's' : '' }}</p>
      </div>
      <div class="header-right">
        <div class="search-box">
          <v-icon size="15" style="color: var(--muted)">mdi-magnify</v-icon>
          <input v-model="search" placeholder="Rechercher..." class="search-input" />
        </div>
        <div class="view-toggle">
          <button class="toggle-btn" :class="{ active: view === 'grid' }" @click="view = 'grid'" title="Grille">
            <v-icon size="15">mdi-view-grid-outline</v-icon>
          </button>
          <button class="toggle-btn" :class="{ active: view === 'timeline' }" @click="switchTimeline" title="Évolution temporelle">
            <v-icon size="15">mdi-chart-timeline-variant</v-icon>
          </button>
        </div>
        <button class="btn-batch" @click="showBatch = !showBatch" title="Analyse en lot">
          <v-icon size="14">mdi-play-box-multiple-outline</v-icon> Batch
        </button>
      </div>
    </div>

    <!-- Batch analysis panel -->
    <div v-if="showBatch" class="card-block mb-5">
      <div class="card-head">
        <v-icon size="13" color="#e8622a">mdi-play-box-multiple-outline</v-icon>
        Analyse en lot
        <span class="mask-badge mask-badge--off" style="margin-left:4px">{{ batchSelected.length }} sessions</span>
        <div style="display:flex;gap:6px;margin-left:auto">
          <button class="btn-tl" style="background:var(--surface2);color:var(--muted);border:1px solid var(--border)" @click="selectAllUnananalyzed">
            <v-icon size="12">mdi-checkbox-multiple-marked-outline</v-icon> Non analysées
          </button>
          <button class="btn-tl" @click="runBatch" :disabled="batchLoading || batchSelected.length===0">
            <v-icon size="12">mdi-play</v-icon> {{ batchLoading ? 'En cours…' : 'Lancer' }}
          </button>
        </div>
      </div>
      <div style="padding:12px 14px;max-height:220px;overflow-y:auto">
        <div v-for="s in store.sessions" :key="s.name" class="batch-row">
          <input type="checkbox" :value="s.name" v-model="batchSelected" class="batch-check" />
          <span class="batch-name">{{ s.name }}</span>
          <span class="batch-status" :class="s.has_results ? 'batch-done' : 'batch-pending'">
            {{ s.has_results ? 'Analysée' : 'En attente' }}
          </span>
          <span v-if="batchJobs[s.name]" class="batch-job-status" :class="`job-${batchJobs[s.name]}`">
            {{ batchJobs[s.name] }}
          </span>
        </div>
      </div>
    </div>

    <!-- Grid view -->
    <template v-if="view === 'grid'">
      <div v-if="store.loading" class="loading-block">
        <v-progress-circular indeterminate color="#e8622a" size="32" />
      </div>
      <div v-else-if="filteredSessions.length === 0" class="empty-block">
        <v-icon size="44" style="color: var(--border2)">mdi-folder-search-outline</v-icon>
        <p>Aucune session trouvée.</p>
      </div>
      <v-row v-else>
        <v-col v-for="s in filteredSessions" :key="s.name" cols="12" sm="6" md="4" lg="3">
          <router-link :to="`/analysis/${s.name}`" class="session-card">
            <div class="card-accent" :style="{ background: s.has_results ? 'var(--green)' : 'var(--warn)' }" />
            <div class="card-body">
              <div class="s-name">{{ s.name }}</div>
              <div class="s-date">{{ formatDate(s.date) }}</div>
              <div class="s-chips">
                <span class="chip chip--blue">{{ s.fps?.toFixed(0) }} FPS</span>
                <span class="chip chip--teal">{{ s.nb_frames }} frames</span>
                <span class="chip chip--gray">{{ s.duration_s }}s</span>
              </div>
              <div v-if="s.scenario?.label" class="s-tag">
                <v-icon size="10" color="#e8622a">mdi-tag-outline</v-icon>
                {{ s.scenario.label }}
              </div>
              <div class="s-status">
                <div class="status-dot" :style="{ background: s.has_results ? 'var(--green)' : 'var(--warn)' }" />
                <span>{{ s.has_results ? "Analysée" : "Non analysée" }}</span>
              </div>
            </div>
          </router-link>
        </v-col>
      </v-row>
    </template>

    <!-- Timeline view -->
    <template v-else>
      <div class="card-block mb-5">
        <div class="card-head">
          <v-icon size="13" color="#06b6d4">mdi-chart-timeline-variant</v-icon>
          Évolution temporelle
          <div class="tl-filters">
            <input v-model="tlZone" placeholder="Zone anatomique" class="tl-input" />
            <input v-model="tlLabel" placeholder="Label de tissu" class="tl-input" />
            <input v-model="tlWoundId" placeholder="wound_id" class="tl-input" />
            <button class="btn-tl" @click="fetchTimeline">
              <v-icon size="12">mdi-magnify</v-icon> Filtrer
            </button>
          </div>
        </div>

        <div v-if="tlLoading" style="display:flex;align-items:center;justify-content:center;height:280px;gap:10px">
          <v-progress-circular indeterminate size="22" width="2" color="#06b6d4" />
          <span style="font-size:0.83rem;color:var(--muted)">Chargement de la timeline…</span>
        </div>

        <div v-else-if="tlPoints.length === 0" class="empty-block" style="height:200px;padding:40px">
          <v-icon size="32" style="color:var(--border2)">mdi-chart-timeline-variant</v-icon>
          <p>Aucun point de données. Filtrez par zone ou label.</p>
        </div>

        <div v-else>
          <v-chart :option="timelineChartOption" autoresize style="height:320px;padding:8px" />
          <div class="tl-table-wrap">
            <table class="tl-table">
              <thead>
                <tr>
                  <th>Date</th><th>Session</th><th>SNR (dB)</th><th>HR (bpm)</th><th>TMS (%)</th><th>Respi (rpm)</th><th>Zone (%)</th><th>Score</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in tlPoints" :key="p.name">
                  <td>{{ formatDate(p.date) }}</td>
                  <td>
                    <router-link :to="`/analysis/${p.name}`" class="tl-link">{{ p.name }}</router-link>
                  </td>
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

// ── Batch analysis ────────────────────────────────────────────────────────────
const showBatch    = ref(false);
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
    // Poll each job
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
      if (data.status === "done") {
        batchJobs.value[sessionName] = "done";
        store.fetchSessions();
        return;
      }
      if (data.status === "error") {
        batchJobs.value[sessionName] = "error";
        return;
      }
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
  if (score >= 80) return { background: "rgba(34,212,126,0.12)", color: "var(--green)", border: "1px solid rgba(34,212,126,0.25)" };
  if (score >= 50) return { background: "rgba(245,158,11,0.10)", color: "var(--warn)",  border: "1px solid rgba(245,158,11,0.25)" };
  return { background: "rgba(239,68,68,0.10)", color: "var(--danger)", border: "1px solid rgba(239,68,68,0.25)" };
}

const CHART_C = { border: "#1a1a2e", muted: "#55556a" };

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
    legend: {
      data: ["SNR (dB)", "HR (bpm)", "Score", "Zone plaie (%)"],
      textStyle: { color: CHART_C.muted, fontSize: 11 },
      top: 4,
    },
    grid: { left: 48, right: 24, top: 36, bottom: 48 },
    xAxis: {
      type: "category",
      data: dates,
      axisLabel: { color: CHART_C.muted, fontSize: 10, rotate: 30 },
      axisLine:  { lineStyle: { color: CHART_C.border } },
    },
    yAxis: [
      { type: "value", name: "dB / bpm", nameTextStyle: { color: CHART_C.muted, fontSize: 10 },
        axisLabel: { color: CHART_C.muted, fontSize: 10 },
        splitLine: { lineStyle: { color: CHART_C.border } } },
      { type: "value", name: "Score", min: 0, max: 100,
        nameTextStyle: { color: CHART_C.muted, fontSize: 10 },
        axisLabel: { color: CHART_C.muted, fontSize: 10 },
        splitLine: { show: false } },
    ],
    series: [
      {
        name: "SNR (dB)", type: "line", yAxisIndex: 0, smooth: true, symbol: "circle",
        data: pts.map(p => p.snr_db),
        lineStyle: { color: "#06b6d4", width: 2 },
        itemStyle: { color: "#06b6d4" },
        areaStyle: { color: "rgba(6,182,212,0.07)" },
      },
      {
        name: "HR (bpm)", type: "line", yAxisIndex: 0, smooth: true, symbol: "circle",
        data: pts.map(p => p.hr_bpm),
        lineStyle: { color: "#e8622a", width: 2 },
        itemStyle: { color: "#e8622a" },
      },
      {
        name: "Score", type: "bar", yAxisIndex: 1,
        data: pts.map(p => p.score),
        itemStyle: { color: "rgba(168,139,250,0.35)", borderRadius: [3, 3, 0, 0] },
        barMaxWidth: 28,
      },
      {
        name: "Zone plaie (%)", type: "line", yAxisIndex: 1, smooth: true, symbol: "diamond",
        data: pts.map(p => p.wound_pct || null),
        lineStyle: { color: "#f43f5e", width: 2, type: "dashed" },
        itemStyle: { color: "#f43f5e" },
      },
    ],
  };
});
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
  gap: 16px;
}
.page-title { font-size: 2rem; font-weight: 900; margin: 0 0 4px; letter-spacing: -0.5px; }
.page-sub   { color: var(--muted); font-size: 0.78rem; font-weight: 500; }
.header-right { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 14px;
  min-width: 220px;
}
.search-input {
  background: none;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 0.83rem;
  width: 100%;
  font-family: inherit;
}
.search-input::placeholder { color: var(--muted); }

.view-toggle { display: flex; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.toggle-btn  { padding: 7px 11px; background: none; border: none; cursor: pointer; color: var(--muted); display: flex; align-items: center; transition: all 0.15s; }
.toggle-btn.active { background: var(--surface2); color: var(--accent); }

/* Card */
.session-card {
  display: block;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  text-decoration: none;
  overflow: hidden;
  transition: border-color 0.2s, transform 0.15s;
}
.session-card:hover { border-color: var(--border2); transform: translateY(-2px); }
.card-accent { height: 2px; width: 100%; }
.card-body   { padding: 16px; }
.s-name { font-size: 0.83rem; font-weight: 700; color: var(--text); word-break: break-all; margin-bottom: 3px; }
.s-date { font-size: 0.71rem; color: var(--muted); margin-bottom: 10px; }
.s-chips { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 8px; }
.chip { font-size: 0.69rem; font-weight: 600; padding: 2px 8px; border-radius: 5px; }
.chip--blue { background: rgba(2,132,199,0.12); color: #38bdf8; border: 1px solid rgba(2,132,199,0.2); }
.chip--teal { background: rgba(6,182,212,0.1);  color: #22d3ee; border: 1px solid rgba(6,182,212,0.2); }
.chip--gray { background: var(--surface2);       color: var(--muted); border: 1px solid var(--border); }
.s-tag { display: flex; align-items: center; gap: 4px; font-size: 0.72rem; color: var(--accent); margin-bottom: 8px; font-weight: 500; }
.s-status { display: flex; align-items: center; gap: 6px; font-size: 0.71rem; color: var(--muted); }
.status-dot { width: 6px; height: 6px; border-radius: 50%; }

.loading-block { display: flex; justify-content: center; padding: 60px; }
.empty-block { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 80px 20px; color: var(--muted); font-size: 0.88rem; text-align: center; }

/* Timeline */
.tl-filters { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-left: auto; }
.tl-input {
  background: var(--surface2); border: 1px solid var(--border); border-radius: 6px;
  color: var(--text); font-size: 0.78rem; padding: 5px 10px; outline: none;
  width: 130px; font-family: inherit;
}
.tl-input::placeholder { color: var(--muted); }
.btn-tl {
  display: flex; align-items: center; gap: 4px; padding: 5px 12px; border-radius: 6px;
  font-size: 0.78rem; font-weight: 600; cursor: pointer;
  background: var(--accent); color: #fff; border: none; transition: opacity 0.15s;
}
.btn-tl:hover { opacity: 0.85; }

.tl-table-wrap { overflow-x: auto; padding: 0 12px 14px; }
.tl-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
.tl-table th { text-align: left; color: var(--muted); font-weight: 600; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.5px; padding: 8px 10px; border-bottom: 1px solid var(--border); }
.tl-table td { padding: 8px 10px; border-bottom: 1px solid var(--border); color: var(--text2); }
.tl-table tr:last-child td { border-bottom: none; }
.tl-link { color: var(--accent); text-decoration: none; font-weight: 600; }
.tl-link:hover { text-decoration: underline; }
.score-chip { font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 5px; }

/* Batch */
.btn-batch {
  display: flex; align-items: center; gap: 5px; padding: 7px 12px; border-radius: 8px;
  font-size: 0.78rem; font-weight: 600; cursor: pointer;
  background: rgba(232,98,42,0.1); color: var(--accent); border: 1px solid rgba(232,98,42,0.25);
  font-family: inherit; transition: opacity 0.15s;
}
.btn-batch:hover { opacity: 0.85; }
.batch-row { display:flex; align-items:center; gap:10px; padding:5px 0; border-bottom:1px solid var(--border); font-size:0.8rem; }
.batch-row:last-child { border-bottom:none; }
.batch-check { accent-color:var(--accent); }
.batch-name  { flex:1; color:var(--text2); font-weight:500; }
.batch-status { font-size:0.7rem; font-weight:600; }
.batch-done    { color:var(--green); }
.batch-pending { color:var(--muted); }
.batch-job-status { font-size:0.68rem; font-weight:700; padding:1px 8px; border-radius:4px; }
.job-running { background:rgba(232,98,42,0.1); color:var(--accent); border:1px solid rgba(232,98,42,0.3); }
.job-done    { background:rgba(34,212,126,0.1); color:var(--green); border:1px solid rgba(34,212,126,0.3); }
.job-error   { background:rgba(248,81,73,0.1); color:var(--danger); border:1px solid rgba(248,81,73,0.3); }

/* Mask badge reuse */
.mask-badge { font-size:0.68rem; font-weight:700; padding:2px 9px; border-radius:5px; text-transform:none; letter-spacing:0; }
.mask-badge--off { background:var(--surface2); color:var(--muted); border:1px solid var(--border); }
</style>
