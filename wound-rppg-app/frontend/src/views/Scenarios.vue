<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title gradient-text">Scénarios</h1>
        <p class="page-sub">Comparaison multi-sessions · LCOMS</p>
      </div>
    </div>

    <!-- Session selector -->
    <div class="card-block selector-card">
      <div class="card-head">
        <svg width="13" height="13" viewBox="0 0 14 14" fill="none" style="color:var(--accent)"><rect x="1" y="1" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/><rect x="8" y="1" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/><path d="M3.5 9.5h7M7 7v5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
        Sélectionner les sessions à comparer
      </div>
      <div class="selector-body">
        <div class="selector-row">
          <div class="session-select-wrap session-select-wrap--a">
            <div class="select-label">
              <span class="select-badge select-badge--a">A</span>
              Session A
            </div>
            <v-select v-model="sessionA" :items="sessionOptions" placeholder="Choisir une session…"
              density="compact" variant="outlined" prepend-inner-icon="mdi-alpha-a-circle-outline" />
          </div>

          <div class="vs-divider">
            <div class="vs-line"/>
            <span class="vs-text">VS</span>
            <div class="vs-line"/>
          </div>

          <div class="session-select-wrap session-select-wrap--b">
            <div class="select-label">
              <span class="select-badge select-badge--b">B</span>
              Session B
            </div>
            <v-select v-model="sessionB" :items="sessionOptions" placeholder="Choisir une session…"
              density="compact" variant="outlined" prepend-inner-icon="mdi-alpha-b-circle-outline" />
          </div>
        </div>

        <button
          class="btn-accent compare-btn"
          :disabled="!sessionA || !sessionB || loading"
          @click="compare"
        >
          <v-progress-circular v-if="loading" indeterminate size="14" width="2" color="white" />
          <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="1" y="1" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/><rect x="8" y="1" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/><path d="M3.5 9.5h7M7 7v5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
          {{ loading ? 'Analyse en cours…' : 'Lancer la comparaison' }}
        </button>
      </div>
    </div>

    <!-- Comparison results -->
    <Transition name="slide-up">
      <div v-if="comparison" class="comparison-result">

        <!-- Metric comparison -->
        <div class="cmp-panels">
          <!-- Session A -->
          <div class="card-block cmp-panel cmp-panel--a">
            <div class="card-head" style="color:var(--accent)">
              <span class="select-badge select-badge--a">A</span>
              {{ comparison.session_a.name }}
            </div>
            <div class="cmp-metrics">
              <div v-for="m in metricsA" :key="m.key" class="cmp-metric">
                <span class="cmp-metric-label">{{ m.label }}</span>
                <span class="cmp-metric-value" :style="{ color: m.color }">
                  {{ m.value }}<small>{{ m.unit }}</small>
                </span>
              </div>
            </div>
            <div class="cmp-badge-wrap">
              <QualityBadge :label="comparison.session_a.label" :score="comparison.session_a.score" :color="comparison.session_a.color" />
            </div>
          </div>

          <!-- Diff -->
          <div class="cmp-diff">
            <div class="diff-head">Δ</div>
            <div v-for="d in diffMetrics" :key="d.key" class="diff-row">
              <span class="diff-label">{{ d.label }}</span>
              <span class="diff-val" :style="{ color: d.color }">
                {{ d.value > 0 ? "+" : "" }}{{ d.value }}
              </span>
            </div>
          </div>

          <!-- Session B -->
          <div class="card-block cmp-panel cmp-panel--b">
            <div class="card-head" style="color:var(--green)">
              <span class="select-badge select-badge--b">B</span>
              {{ comparison.session_b.name }}
            </div>
            <div class="cmp-metrics">
              <div v-for="m in metricsB" :key="m.key" class="cmp-metric">
                <span class="cmp-metric-label">{{ m.label }}</span>
                <span class="cmp-metric-value" :style="{ color: m.color }">
                  {{ m.value }}<small>{{ m.unit }}</small>
                </span>
              </div>
            </div>
            <div class="cmp-badge-wrap">
              <QualityBadge :label="comparison.session_b.label" :score="comparison.session_b.score" :color="comparison.session_b.color" />
            </div>
          </div>
        </div>

        <!-- Spatial maps -->
        <div class="maps-row">
          <div class="card-block">
            <div class="card-head">
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none" style="color:#a78bfa"><rect x="1" y="3" width="12" height="8" rx="1.5" stroke="currentColor" stroke-width="1.3"/><path d="M5 3V1M9 3V1M1 7h12" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
              Carte ST-rPPG — <span style="color:var(--accent)">A</span>
            </div>
            <div style="padding:14px"><SpatialMap :maps="comparison.maps_a||{}" /></div>
          </div>
          <div class="card-block">
            <div class="card-head">
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none" style="color:#22d47e"><rect x="1" y="3" width="12" height="8" rx="1.5" stroke="currentColor" stroke-width="1.3"/><path d="M5 3V1M9 3V1M1 7h12" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
              Carte ST-rPPG — <span style="color:var(--green)">B</span>
            </div>
            <div style="padding:14px"><SpatialMap :maps="comparison.maps_b||{}" /></div>
          </div>
        </div>

      </div>
    </Transition>

    <!-- Placeholder when no comparison -->
    <div v-if="!comparison && !loading" class="placeholder-state">
      <div class="ph-visual">
        <div class="ph-box ph-box--a">A</div>
        <div class="ph-arrow">→</div>
        <div class="ph-box ph-box--b">B</div>
      </div>
      <p class="ph-title">Comparez deux sessions</p>
      <p class="ph-sub">Sélectionnez deux sessions pour visualiser les différences de perfusion et de signal rPPG</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import axios from "axios";
import { useSessionStore } from "../stores/session.js";
import { apiUrl } from "../lib/api.js";
import QualityBadge from "../components/ui/QualityBadge.vue";
import SpatialMap   from "../components/charts/SpatialMap.vue";

const store      = useSessionStore();
const sessionA   = ref("");
const sessionB   = ref("");
const comparison = ref(null);
const loading    = ref(false);

onMounted(() => store.fetchSessions());
const sessionOptions = computed(() => store.sessions.map(s => ({ title: s.name, value: s.name })));

async function compare() {
  loading.value = true;
  try {
    const { data } = await axios.post(apiUrl("/scenarios/compare/two"), { session_a: sessionA.value, session_b: sessionB.value });
    comparison.value = data;
  } finally { loading.value = false; }
}

function mc(key, val) {
  if (key === "snr_db") return val >= 3 ? "var(--green)" : val >= 0 ? "var(--warn)" : "var(--danger)";
  if (key === "tms")    return val >= 0.96 ? "var(--green)" : "var(--warn)";
  return "var(--text2)";
}

const metricsA = computed(() => {
  if (!comparison.value) return [];
  const s = comparison.value.session_a;
  return [
    { key:"hr_bpm", label:"FC",    value: s.hr_bpm,              unit:" bpm",  color:"var(--warn)"  },
    { key:"snr_db", label:"SNR",   value: s.snr_db,              unit:" dB",   color: mc("snr_db", s.snr_db) },
    { key:"tms",    label:"TMS",   value:(s.tms*100).toFixed(1), unit:"%",     color: mc("tms", s.tms) },
    { key:"score",  label:"Score", value: s.score,               unit:"/100",  color:"var(--accent)" },
  ];
});
const metricsB = computed(() => {
  if (!comparison.value) return [];
  const s = comparison.value.session_b;
  return [
    { key:"hr_bpm", label:"FC",    value: s.hr_bpm,              unit:" bpm",  color:"var(--warn)"  },
    { key:"snr_db", label:"SNR",   value: s.snr_db,              unit:" dB",   color: mc("snr_db", s.snr_db) },
    { key:"tms",    label:"TMS",   value:(s.tms*100).toFixed(1), unit:"%",     color: mc("tms", s.tms) },
    { key:"score",  label:"Score", value: s.score,               unit:"/100",  color:"var(--accent)" },
  ];
});
const diffMetrics = computed(() => {
  if (!comparison.value) return [];
  const d = comparison.value.diff;
  return [
    { key:"hr_bpm", label:"FC",    value: d.hr_bpm, color: "var(--muted)" },
    { key:"snr_db", label:"SNR",   value: d.snr_db, color: d.snr_db > 0 ? "var(--green)" : "var(--danger)" },
    { key:"score",  label:"Score", value: d.score,  color: d.score  > 0 ? "var(--green)" : "var(--danger)" },
  ];
});
</script>

<style scoped>
/* Selector */
.selector-card { animation: fadeInUp 0.5s ease both; }
.selector-body { padding: 20px; }
.selector-row  { display: grid; grid-template-columns: 1fr auto 1fr; gap: 20px; align-items: end; margin-bottom: 16px; }

.session-select-wrap { display: flex; flex-direction: column; gap: 8px; }
.select-label  { display: flex; align-items: center; gap: 8px; font-size: 0.72rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }

.select-badge {
  width: 20px; height: 20px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.68rem; font-weight: 900; flex-shrink: 0;
}
.select-badge--a { background: rgba(232,98,42,0.15); color: var(--accent); border: 1px solid rgba(232,98,42,0.3); }
.select-badge--b { background: rgba(34,212,126,0.12); color: var(--green); border: 1px solid rgba(34,212,126,0.25); }

.vs-divider { display: flex; flex-direction: column; align-items: center; gap: 4px; padding-bottom: 2px; }
.vs-line    { flex: 1; width: 1px; background: var(--border); }
.vs-text    { font-size: 0.65rem; font-weight: 900; color: var(--muted); letter-spacing: 0.1em; padding: 4px 0; }

.compare-btn {
  display: flex; align-items: center; gap: 8px; width: 100%; justify-content: center;
  padding: 12px; font-size: 0.85rem;
}

@media (max-width: 700px) {
  .selector-row { grid-template-columns: 1fr; }
  .vs-divider { flex-direction: row; height: 20px; }
  .vs-line { flex: 1; height: 1px; width: auto; }
}

/* Comparison result */
.comparison-result { margin-top: 20px; display: flex; flex-direction: column; gap: 16px; }

.cmp-panels {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 14px;
  align-items: start;
}
@media (max-width: 800px) { .cmp-panels { grid-template-columns: 1fr; } }

.cmp-panel { animation: scaleIn 0.4s ease both; }
.cmp-panel--a { border-color: rgba(232,98,42,0.25) !important; }
.cmp-panel--b { border-color: rgba(34,212,126,0.2) !important; }

.cmp-metrics { display: flex; flex-direction: column; gap: 0; padding: 4px 0; }
.cmp-metric  { display: flex; justify-content: space-between; align-items: center; padding: 10px 18px; border-bottom: 1px solid var(--border); }
.cmp-metric:last-child { border-bottom: none; }
.cmp-metric-label { font-size: 0.72rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
.cmp-metric-value { font-size: 1.15rem; font-weight: 800; font-family: 'Syne', sans-serif; letter-spacing: -0.03em; }
.cmp-metric-value small { font-size: 0.7rem; font-weight: 400; color: var(--muted); margin-left: 3px; font-family: 'Inter', sans-serif; letter-spacing: 0; }
.cmp-badge-wrap { padding: 14px 18px; }

/* Diff column */
.cmp-diff {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  min-width: 90px;
  animation: scaleIn 0.4s 0.1s ease both;
}
.diff-head {
  width: 100%;
  text-align: center;
  padding: 10px;
  font-size: 0.65rem;
  font-weight: 900;
  color: var(--muted);
  letter-spacing: 0.15em;
  border-bottom: 1px solid var(--border);
  text-transform: uppercase;
}
.diff-row  { display: flex; flex-direction: column; align-items: center; padding: 14px 12px; width: 100%; border-bottom: 1px solid var(--border); }
.diff-row:last-child { border-bottom: none; }
.diff-label { font-size: 0.62rem; color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }
.diff-val   { font-size: 1.05rem; font-weight: 900; font-family: 'Syne', sans-serif; letter-spacing: -0.03em; }

/* Maps */
.maps-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
@media (max-width: 800px) { .maps-row { grid-template-columns: 1fr; } }

/* Placeholder */
.placeholder-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 80px 20px;
  text-align: center;
  animation: fadeInUp 0.5s 0.1s ease both;
}
.ph-visual { display: flex; align-items: center; gap: 16px; margin-bottom: 8px; }
.ph-box {
  width: 56px; height: 56px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; font-weight: 900;
}
.ph-box--a { background: rgba(232,98,42,0.1); border: 1.5px solid rgba(232,98,42,0.25); color: var(--accent); }
.ph-box--b { background: rgba(34,212,126,0.1); border: 1.5px solid rgba(34,212,126,0.2); color: var(--green); }
.ph-arrow  { font-size: 1.4rem; color: var(--border2); }
.ph-title  { font-size: 0.9rem; font-weight: 700; color: var(--text2); margin: 0; }
.ph-sub    { font-size: 0.76rem; color: var(--muted); margin: 0; max-width: 380px; line-height: 1.6; }
</style>
