<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title gradient-text">Rapport</h1>
        <p class="page-sub">Export pour publication scientifique · LCOMS</p>
      </div>
    </div>

    <v-row class="mb-6">
      <v-col cols="12" md="6">
        <div class="card-block">
          <div class="card-head">
            <v-icon size="13" color="#e8622a">mdi-file-table-outline</v-icon>
            Export par session
          </div>
          <div style="padding: 18px">
            <v-select v-model="selectedSession" :items="sessionOptions" label="Session"
              density="compact" variant="outlined" class="mb-4" />
            <div style="display: flex; gap: 10px">
              <a class="btn-export btn-export--primary" :class="{ disabled: !selectedSession }"
                :href="selectedSession ? apiUrl(`/export/${selectedSession}/csv`) : '#'" target="_blank">
                <v-icon size="13">mdi-file-delimited-outline</v-icon> CSV
              </a>
              <a class="btn-export btn-export--teal" :class="{ disabled: !selectedSession }"
                :href="selectedSession ? apiUrl(`/export/${selectedSession}/json`) : '#'" target="_blank">
                <v-icon size="13">mdi-code-json</v-icon> JSON
              </a>
            </div>
          </div>
        </div>
      </v-col>

      <v-col cols="12" md="6">
        <div class="card-block">
          <div class="card-head">
            <v-icon size="13" color="#06b6d4">mdi-table-large</v-icon>
            Comparaison multi-sessions
          </div>
          <div style="padding: 18px">
            <v-select v-model="selectedSessions" :items="sessionOptions"
              label="Sélectionner les sessions" density="compact" variant="outlined"
              multiple chips class="mb-4" />
            <button class="btn-accent" :disabled="selectedSessions.length < 2 || loading" @click="loadComparison">
              <v-progress-circular v-if="loading" indeterminate size="13" width="2" color="white" />
              <v-icon v-else size="13">mdi-compare</v-icon>
              Générer tableau
            </button>
          </div>
        </div>
      </v-col>
    </v-row>

    <template v-if="comparisonData">
      <!-- Table -->
      <div class="card-block mb-5">
        <div class="card-head">
          <v-icon size="13" color="#e8622a">mdi-table-large</v-icon>
          Résultats — {{ comparisonData.n }} sessions
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Session</th>
                <th>Scénario</th>
                <th>FC (bpm)</th>
                <th>SNR (dB)</th>
                <th>TMS</th>
                <th>FPS</th>
                <th>Score</th>
                <th>Qualité</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in comparisonData.ranking" :key="s.name">
                <td class="td-mono">{{ s.name }}</td>
                <td>
                  <span v-if="s.scenario?.label" class="tag-chip">{{ s.scenario.label }}</span>
                </td>
                <td :style="{ color: 'var(--warn)', fontWeight: 700 }">{{ s.hr_bpm }}</td>
                <td :style="{ color: s.snr_db>=3?'var(--green)':s.snr_db>=0?'var(--warn)':'var(--danger)', fontWeight:700 }">{{ s.snr_db }}</td>
                <td :style="{ color: s.tms>=0.96?'var(--green)':'var(--warn)', fontWeight:700 }">{{ (s.tms*100)?.toFixed(1) }}%</td>
                <td style="color: var(--teal); font-weight:700">{{ s.fps?.toFixed(1) }}</td>
                <td style="font-weight:900; color: var(--text)">{{ s.score }}/100</td>
                <td>
                  <span class="quality-pill" :style="{ background: s.color+'18', color: s.color, borderColor: s.color+'44' }">
                    {{ s.label }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Charts row -->
      <v-row class="mb-5">
        <!-- Bar chart — score par session -->
        <v-col cols="12" md="6">
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#e8622a">mdi-chart-bar</v-icon>
              Score qualité par session
            </div>
            <div style="padding: 8px 4px">
              <v-chart :option="scoreBarOption" autoresize style="height:260px" />
            </div>
          </div>
        </v-col>

        <!-- Heatmap — matrice des métriques -->
        <v-col cols="12" md="6">
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#a78bfa">mdi-grid</v-icon>
              Matrice des métriques (normalisée)
            </div>
            <div style="padding: 8px 4px">
              <v-chart :option="metricsHeatmapOption" autoresize style="height:260px" />
            </div>
          </div>
        </v-col>
      </v-row>

      <!-- SNR distribution -->
      <div class="card-block mb-5">
        <div class="card-head">
          <v-icon size="13" color="#06b6d4">mdi-chart-timeline-variant</v-icon>
          Distribution SNR · TMS par session
        </div>
        <div style="padding: 8px 4px">
          <v-chart :option="snrTmsOption" autoresize style="height:220px" />
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

const store            = useSessionStore();
const selectedSession  = ref("");
const selectedSessions = ref([]);
const comparisonData   = ref(null);
const loading          = ref(false);

onMounted(() => store.fetchSessions());
const sessionOptions = computed(() => store.sessions.map(s => ({ title: s.name, value: s.name })));

async function loadComparison() {
  loading.value = true;
  try {
    const { data } = await axios.post(apiUrl("/scenarios/compare/multiple"), { sessions: selectedSessions.value });
    comparisonData.value = data;
  } finally { loading.value = false; }
}

// ── Chart helpers ─────────────────────────────────────────────────────────────

function shortName(name) {
  return name.length > 14 ? name.slice(0, 12) + "…" : name;
}

const CHART_DARK = {
  bg: "transparent",
  text: "#b8b8cc",
  muted: "#55556a",
  border: "#1a1a2e",
  accent: "#e8622a",
  teal: "#06b6d4",
  green: "#22d47e",
  warn: "#f59e0b",
  purple: "#a78bfa",
};

// Bar chart — score /100 par session
const scoreBarOption = computed(() => {
  if (!comparisonData.value) return {};
  const rows = comparisonData.value.ranking;
  const names = rows.map(r => shortName(r.name));
  const scores = rows.map(r => r.score);
  const colors = rows.map(r => r.color || CHART_DARK.accent);
  return {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", formatter: p => `<b>${rows[p[0].dataIndex].name}</b><br/>Score : ${p[0].value}/100` },
    grid: { left: 40, right: 20, top: 20, bottom: 60 },
    xAxis: {
      type: "category",
      data: names,
      axisLabel: { color: CHART_DARK.muted, fontSize: 10, rotate: 30, interval: 0 },
      axisLine: { lineStyle: { color: CHART_DARK.border } },
    },
    yAxis: {
      type: "value",
      min: 0, max: 100,
      axisLabel: { color: CHART_DARK.muted, fontSize: 10 },
      splitLine: { lineStyle: { color: CHART_DARK.border } },
    },
    series: [{
      type: "bar",
      data: scores.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: [4, 4, 0, 0] } })),
      label: { show: true, position: "top", color: CHART_DARK.text, fontSize: 10, fontWeight: 700,
               formatter: p => `${p.value}` },
      barMaxWidth: 48,
    }],
  };
});

// Heatmap — sessions × métriques normalisées
const metricsHeatmapOption = computed(() => {
  if (!comparisonData.value) return {};
  const rows = comparisonData.value.ranking;
  const metrics = ["FC", "SNR", "TMS", "Score"];

  // Extract raw values per metric
  const raw = {
    FC:    rows.map(r => r.hr_bpm   ?? 0),
    SNR:   rows.map(r => r.snr_db   ?? 0),
    TMS:   rows.map(r => (r.tms ?? 0) * 100),
    Score: rows.map(r => r.score    ?? 0),
  };

  // Min-max normalize per column
  function normalize(arr) {
    const mn = Math.min(...arr), mx = Math.max(...arr);
    return arr.map(v => mx === mn ? 0.5 : (v - mn) / (mx - mn));
  }

  const norm = {};
  for (const k of metrics) norm[k] = normalize(raw[k]);

  const data = [];
  rows.forEach((_r, ri) => {
    metrics.forEach((m, mi) => {
      data.push([mi, ri, +norm[m][ri].toFixed(3)]);
    });
  });

  const sessionLabels = rows.map(r => shortName(r.name));

  return {
    backgroundColor: "transparent",
    tooltip: {
      formatter: p => {
        const r = rows[p.data[1]], m = metrics[p.data[0]];
        const rawVal = { FC: r.hr_bpm, SNR: r.snr_db, TMS: ((r.tms??0)*100).toFixed(1)+'%', Score: r.score }[m];
        return `<b>${r.name}</b><br/>${m} : ${rawVal}`;
      },
    },
    grid: { left: 80, right: 60, top: 10, bottom: 60 },
    xAxis: {
      type: "category",
      data: metrics,
      axisLabel: { color: CHART_DARK.text, fontSize: 11, fontWeight: 700 },
      axisLine: { lineStyle: { color: CHART_DARK.border } },
      splitArea: { show: true, areaStyle: { color: ["rgba(255,255,255,0.01)", "transparent"] } },
    },
    yAxis: {
      type: "category",
      data: sessionLabels,
      axisLabel: { color: CHART_DARK.muted, fontSize: 10 },
      axisLine: { lineStyle: { color: CHART_DARK.border } },
      splitArea: { show: true, areaStyle: { color: ["rgba(255,255,255,0.01)", "transparent"] } },
    },
    visualMap: {
      min: 0, max: 1,
      calculable: false,
      show: true,
      right: 0,
      top: "middle",
      orient: "vertical",
      itemWidth: 12,
      itemHeight: 80,
      inRange: { color: ["#0d1b2a", "#1a3a5c", "#06b6d4", "#22d47e", "#f59e0b", "#e8622a"] },
      textStyle: { color: CHART_DARK.muted, fontSize: 10 },
      text: ["Élevé", "Faible"],
    },
    series: [{
      type: "heatmap",
      data,
      label: { show: true, fontSize: 10, color: "#fff",
               formatter: p => (p.data[2] * 100).toFixed(0) },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.5)" } },
    }],
  };
});

// Double bar — SNR + TMS
const snrTmsOption = computed(() => {
  if (!comparisonData.value) return {};
  const rows = comparisonData.value.ranking;
  const names = rows.map(r => shortName(r.name));
  return {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    legend: {
      data: ["SNR (dB)", "TMS (%)"],
      textStyle: { color: CHART_DARK.muted, fontSize: 11 },
      top: 0, right: 0,
    },
    grid: { left: 40, right: 20, top: 32, bottom: 60 },
    xAxis: {
      type: "category",
      data: names,
      axisLabel: { color: CHART_DARK.muted, fontSize: 10, rotate: 30, interval: 0 },
      axisLine: { lineStyle: { color: CHART_DARK.border } },
    },
    yAxis: [
      { type: "value", name: "dB", nameTextStyle: { color: CHART_DARK.muted, fontSize: 10 },
        axisLabel: { color: CHART_DARK.muted, fontSize: 10 },
        splitLine: { lineStyle: { color: CHART_DARK.border } } },
      { type: "value", name: "%",  nameTextStyle: { color: CHART_DARK.muted, fontSize: 10 },
        axisLabel: { color: CHART_DARK.muted, fontSize: 10 },
        min: 0, max: 100, splitLine: { show: false } },
    ],
    series: [
      { name: "SNR (dB)", type: "bar", yAxisIndex: 0, barMaxWidth: 32,
        data: rows.map(r => ({ value: r.snr_db, itemStyle: { color: CHART_DARK.teal, borderRadius: [3,3,0,0] } })),
        label: { show: true, position: "top", color: CHART_DARK.teal, fontSize: 9, formatter: p => `${p.value}` } },
      { name: "TMS (%)",  type: "bar", yAxisIndex: 1, barMaxWidth: 32,
        data: rows.map(r => ({ value: +((r.tms??0)*100).toFixed(1), itemStyle: { color: CHART_DARK.purple, borderRadius: [3,3,0,0] } })),
        label: { show: true, position: "top", color: CHART_DARK.purple, fontSize: 9, formatter: p => `${p.value}` } },
    ],
  };
});
</script>

<style scoped>
.btn-export {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 20px; border-radius: 8px; font-size: 0.82rem; font-weight: 600;
  text-decoration: none; transition: opacity 0.15s; border: 1px solid transparent;
}
.btn-export--primary {
  background: rgba(232,98,42,0.12); color: var(--accent); border-color: rgba(232,98,42,0.25);
}
.btn-export--teal {
  background: rgba(6,182,212,0.1); color: var(--teal); border-color: rgba(6,182,212,0.25);
}
.btn-export:hover { opacity: 0.78; }
.btn-export.disabled { opacity: 0.35; pointer-events: none; }

.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  font-size: 0.68rem; font-weight: 700; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.6px;
  padding: 10px 16px; background: var(--surface2);
  border-bottom: 1px solid var(--border); text-align: left;
}
.data-table td {
  font-size: 0.82rem; padding: 10px 16px;
  border-bottom: 1px solid var(--border); color: var(--text2);
}
.data-table tbody tr:hover { background: var(--surface2); }
.data-table tbody tr:last-child td { border-bottom: none; }
.td-mono { font-family: monospace; font-size: 0.75rem; color: var(--muted); }
.tag-chip {
  font-size: 0.7rem; font-weight: 600; padding: 2px 8px; border-radius: 5px;
  background: rgba(232,98,42,0.1); color: var(--accent); border: 1px solid rgba(232,98,42,0.2);
}
.quality-pill {
  font-size: 0.7rem; font-weight: 700; padding: 2px 10px; border-radius: 5px; border: 1px solid;
}
</style>
