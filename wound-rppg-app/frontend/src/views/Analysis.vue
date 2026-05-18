<template>
  <div>
    <!-- Header -->
    <div class="page-header">
      <div>
        <router-link to="/sessions" class="back-link">
          <v-icon size="13">mdi-arrow-left</v-icon> Sessions
        </router-link>
        <h1 class="page-title">{{ sessionId }}</h1>
        <QualityBadge v-if="result" :label="result.quality?.label"
                      :score="result.quality?.score" :color="result.quality?.color" />
      </div>
      <div class="header-actions">
        <button class="btn-ghost" @click="runAnalysis(false)" :disabled="loading">
          <v-icon size="14">mdi-play-circle-outline</v-icon> Analyser
        </button>
        <button class="btn-ghost btn-ghost--warn" @click="runAnalysis(true)" :disabled="loading">
          <v-icon size="14">mdi-refresh</v-icon> Recalculer
        </button>
        <a v-if="result" class="btn-ghost btn-ghost--green" :href="apiUrl(`/export/${sessionId}/csv`)">
          <v-icon size="14">mdi-download</v-icon> CSV
        </a>
      </div>
    </div>

    <!-- Non analysé -->
    <div v-if="!result && !loading" class="empty-card">
      <v-icon size="48" style="color: var(--border2)">mdi-flask-outline</v-icon>
      <p style="font-size:1rem; font-weight:700; color: var(--text2); margin:12px 0 6px">Session non analysée</p>
      <p style="font-size:0.83rem; color: var(--muted)">Cliquez sur <strong style="color:var(--accent)">Analyser</strong> pour lancer le pipeline POS (Wang et al. 2017)</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="empty-card">
      <v-progress-circular indeterminate color="#e8622a" size="36" class="mb-3" />
      <p style="font-size:0.85rem; color: var(--muted)">Calcul en cours — POS + cartes ST-rPPG...</p>
    </div>

    <!-- Résultats -->
    <template v-if="result && !loading">
      <!-- Métriques -->
      <v-row class="mb-6">
        <v-col v-for="m in mainMetrics" :key="m.label" cols="6" md="3">
          <MetricCard v-bind="m" />
        </v-col>
      </v-row>

      <!-- Signal + FFT -->
      <v-row class="mb-5">
        <v-col cols="12" md="8">
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#e8622a">mdi-pulse</v-icon>
              Signal POS
              <span class="head-value">{{ result.hr?.hr_bpm }} bpm</span>
            </div>
            <div class="chart-area">
              <SignalChart :time="result.signal?.time||[]" :raw="result.signal?.raw||[]"
                :filtered="result.signal?.filt||[]" :peaks="result.signal?.peaks||[]"
                :hrBpm="result.hr?.hr_bpm" :height="230" />
            </div>
          </div>
        </v-col>
        <v-col cols="12" md="4">
          <div class="card-block" style="height:100%">
            <div class="card-head">
              <v-icon size="13" color="#06b6d4">mdi-chart-bell-curve</v-icon>
              Spectre FFT
            </div>
            <div class="chart-area">
              <FFTChart :freq="result.hr?.freq||[]" :fft="result.hr?.fft||[]"
                :hrHz="result.hr?.hr_hz" :hrBpm="result.hr?.hr_bpm" :height="230" />
            </div>
          </div>
        </v-col>
      </v-row>

      <!-- SNR + Maps + Recommandations + Tag -->
      <v-row class="mb-5">
        <v-col cols="12" md="4">
          <div class="card-block mb-4">
            <div class="card-head">
              <v-icon size="13" color="#f59e0b">mdi-signal</v-icon>
              SNR glissant
              <span class="head-value">{{ result.snr?.mean_snr }} dB</span>
            </div>
            <div class="chart-area">
              <SNRChart :time="result.snr?.time||[]" :snr="result.snr?.snr||[]"
                :meanSnr="result.snr?.mean_snr" :height="180" />
            </div>
          </div>
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#06b6d4">mdi-waveform</v-icon>
              Template Matching Score
            </div>
            <div class="tms-block">
              <div class="tms-value" :style="{ color: result.tms?.is_clean ? 'var(--green)' : 'var(--warn)' }">
                {{ (result.tms?.tms * 100)?.toFixed(1) }}<span class="tms-unit">%</span>
              </div>
              <span class="tms-chip" :class="result.tms?.is_clean ? 'chip-green' : 'chip-warn'">
                {{ result.tms?.is_clean ? "Signal propre" : "Signal bruité" }}
              </span>
              <p class="tms-meta">{{ result.tms?.n_cycles }} cycles détectés</p>
            </div>
          </div>
        </v-col>

        <v-col cols="12" md="4">
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#a78bfa">mdi-map-outline</v-icon>
              Cartes ST-rPPG
            </div>
            <div style="padding: 14px">
              <SpatialMap :maps="result.maps||{}" :stats="result.amp_stats" />
            </div>
          </div>
        </v-col>

        <v-col cols="12" md="4">
          <div class="card-block mb-4">
            <div class="card-head">
              <v-icon size="13" color="#f59e0b">mdi-lightbulb-outline</v-icon>
              Recommandations
            </div>
            <div style="padding: 14px">
              <div v-if="!result.quality?.recommendations?.length" class="rec-ok">
                <v-icon size="13" color="#22d47e">mdi-check-circle</v-icon>
                Signal de bonne qualité — aucune recommandation
              </div>
              <div v-for="r in result.quality?.recommendations" :key="r" class="rec-item">
                <v-icon size="12" color="#f59e0b">mdi-arrow-right-circle-outline</v-icon>
                {{ r }}
              </div>
            </div>
          </div>
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#e8622a">mdi-tag-outline</v-icon>
              Annoter le scénario
            </div>
            <div style="padding: 14px; display: flex; flex-direction: column; gap: 10px">
              <v-select v-model="scenarioLabel" :items="scenarioOptions" label="Type de tissu"
                density="compact" variant="outlined" />
              <v-text-field v-model="scenarioZone" label="Zone anatomique" density="compact"
                variant="outlined" placeholder="Ex: paume droite" />
              <v-text-field v-model="scenarioDesc" label="Description" density="compact"
                variant="outlined" placeholder="Ex: éclairage LED, repos" />
              <button class="btn-accent-sm" @click="saveTag" :disabled="!scenarioLabel">
                Enregistrer
              </button>
            </div>
          </div>
        </v-col>
      </v-row>

      <!-- AI Interpretation -->
      <div v-if="result.interpretation" class="interp-block">
        <div class="interp-header">
          <div class="interp-icon">
            <v-icon size="16" color="#e8622a">mdi-brain</v-icon>
          </div>
          <div>
            <div class="interp-title">Interprétation scientifique</div>
            <div class="interp-algo">{{ result.interpretation.algorithm }} · Rule-based</div>
          </div>
          <span class="interp-badge">ST-rPPG</span>
        </div>

        <p class="interp-narrative">{{ result.interpretation.narrative }}</p>

        <div class="interp-grid">
          <div v-for="item in interpItems" :key="item.key" class="interp-item" :style="{ '--ic': item.color }">
            <div class="item-icon">
              <v-icon size="14" :style="{ color: item.color }">{{ item.icon }}</v-icon>
            </div>
            <div class="item-content">
              <div class="item-label">{{ item.label }}</div>
              <div class="item-short" :style="{ color: item.color }">{{ item.short }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useSessionStore } from "../stores/session.js";
import { apiUrl } from "../lib/api.js";
import MetricCard   from "../components/ui/MetricCard.vue";
import QualityBadge from "../components/ui/QualityBadge.vue";
import SignalChart  from "../components/charts/SignalChart.vue";
import FFTChart     from "../components/charts/FFTChart.vue";
import SpatialMap   from "../components/charts/SpatialMap.vue";
import SNRChart     from "../components/charts/SNRChart.vue";

const route = useRoute();
const store = useSessionStore();
const sessionId = computed(() => route.params.id);
const result  = ref(null);
const loading = ref(false);

const scenarioLabel = ref("");
const scenarioZone  = ref("");
const scenarioDesc  = ref("");

const scenarioOptions = [
  "peau_saine", "visage", "main_paume", "main_dos",
  "avant_bras", "tache_naissance", "cicatrice",
  "compression", "plaie_chronique", "autre",
];

onMounted(async () => {
  try { result.value = await store.getResult(sessionId.value); }
  catch { /* not yet analyzed */ }
});

async function runAnalysis(force) {
  loading.value = true;
  try { result.value = await store.analyze(sessionId.value, force); }
  finally { loading.value = false; }
}

async function saveTag() {
  await store.tagScenario(sessionId.value, scenarioLabel.value, scenarioDesc.value, scenarioZone.value);
}

const mainMetrics = computed(() => {
  if (!result.value) return [];
  const r = result.value;
  return [
    { label: "HR estimée", value: r.hr?.hr_bpm,                        unit: "bpm", icon: "mdi-heart-pulse",         color: "var(--warn)"   },
    { label: "SNR moyen",  value: r.snr?.mean_snr,                      unit: "dB",  icon: "mdi-signal",              color: r.snr?.mean_snr >= 3 ? "var(--green)" : "var(--danger)" },
    { label: "TMS",        value: ((r.tms?.tms||0)*100).toFixed(1),     unit: "%",   icon: "mdi-waveform",            color: r.tms?.is_clean ? "var(--green)" : "var(--warn)" },
    { label: "FPS réel",   value: r.fps?.toFixed(1),                    unit: "Hz",  icon: "mdi-speedometer-outline", color: "var(--teal)"   },
  ];
});

const interpItems = computed(() => {
  const i = result.value?.interpretation;
  if (!i) return [];
  return [
    { key: "signal_quality", label: "Qualité signal",   short: i.signal_quality?.short, color: i.signal_quality?.color, icon: "mdi-signal" },
    { key: "heart_rate",     label: "Fréquence card.",  short: i.heart_rate?.short,     color: i.heart_rate?.color,     icon: "mdi-heart-pulse" },
    { key: "morphology",     label: "Morphologie PPG",  short: i.morphology?.short,     color: i.morphology?.color,     icon: "mdi-waveform" },
    { key: "perfusion",      label: "Perfusion",        short: i.perfusion?.short,      color: i.perfusion?.color,      icon: "mdi-map-outline" },
  ];
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
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.75rem;
  color: var(--muted);
  text-decoration: none;
  margin-bottom: 6px;
  transition: color 0.15s;
}
.back-link:hover { color: var(--accent); }
.page-title { font-size: 1.1rem; font-weight: 800; color: var(--text); margin: 0 0 8px; word-break: break-all; }
.header-actions { display: flex; gap: 8px; flex-shrink: 0; flex-wrap: wrap; }

.btn-ghost {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 14px;
  border-radius: 7px;
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--text2);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: border-color 0.15s;
}
.btn-ghost:hover { border-color: var(--accent); color: var(--accent); }
.btn-ghost:disabled { opacity: 0.4; cursor: default; }
.btn-ghost--warn:hover { border-color: var(--warn); color: var(--warn); }
.btn-ghost--green:hover { border-color: var(--green); color: var(--green); }

.empty-card {
  display: flex; flex-direction: column; align-items: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 64px 32px;
  text-align: center;
  gap: 0;
}

.head-value { margin-left: auto; font-size: 0.88rem; font-weight: 800; color: var(--warn); text-transform: none; letter-spacing: 0; }
.chart-area { padding: 12px 8px 8px; }

/* TMS */
.tms-block { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 20px 16px; }
.tms-value { font-size: 2.8rem; font-weight: 900; letter-spacing: -1px; }
.tms-unit  { font-size: 1.2rem; font-weight: 400; color: var(--muted); margin-left: 2px; }
.tms-chip  { font-size: 0.74rem; font-weight: 700; padding: 3px 12px; border-radius: 6px; }
.chip-green { background: rgba(34,212,126,0.1); color: var(--green); border: 1px solid rgba(34,212,126,0.25); }
.chip-warn  { background: rgba(245,158,11,0.1);  color: var(--warn);  border: 1px solid rgba(245,158,11,0.25); }
.tms-meta   { font-size: 0.73rem; color: var(--muted); margin: 0; }

/* Recommendations */
.rec-ok { display: flex; align-items: center; gap: 7px; font-size: 0.82rem; color: var(--green); font-weight: 500; }
.rec-item { display: flex; align-items: flex-start; gap: 7px; font-size: 0.8rem; color: var(--warn); padding: 5px 0; border-bottom: 1px solid var(--border); }
.rec-item:last-child { border-bottom: none; }

/* Scenario tag */
.btn-accent-sm {
  padding: 8px 16px; border-radius: 7px; background: var(--accent); color: #fff;
  font-size: 0.8rem; font-weight: 600; border: none; cursor: pointer; transition: opacity 0.15s;
}
.btn-accent-sm:hover { opacity: 0.85; }
.btn-accent-sm:disabled { opacity: 0.4; cursor: default; }

/* AI Interpretation block */
.interp-block {
  background: var(--surface);
  border: 1px solid rgba(232,98,42,0.25);
  border-radius: 12px;
  overflow: hidden;
}
.interp-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  background: rgba(232,98,42,0.05);
}
.interp-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: rgba(232,98,42,0.12);
  border: 1px solid rgba(232,98,42,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.interp-title { font-size: 0.85rem; font-weight: 700; color: var(--text); }
.interp-algo  { font-size: 0.68rem; color: var(--muted); font-family: monospace; margin-top: 2px; }
.interp-badge {
  margin-left: auto;
  font-size: 0.68rem; font-weight: 700;
  padding: 3px 10px; border-radius: 5px;
  background: rgba(232,98,42,0.1);
  border: 1px solid rgba(232,98,42,0.25);
  color: var(--accent);
  letter-spacing: 0.5px;
}
.interp-narrative {
  padding: 16px 20px;
  font-size: 0.85rem;
  color: var(--text2);
  line-height: 1.6;
  margin: 0;
  border-bottom: 1px solid var(--border);
}
.interp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0;
}
.interp-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 20px;
  border-right: 1px solid var(--border);
}
.interp-item:last-child { border-right: none; }
.item-icon {
  width: 30px;
  height: 30px;
  border-radius: 7px;
  background: color-mix(in srgb, var(--ic, #e8622a) 10%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
}
.item-label { font-size: 0.68rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px; }
.item-short { font-size: 0.8rem; font-weight: 600; }
</style>
