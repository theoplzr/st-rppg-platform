<template>
  <div>
    <div class="page-header">
      <div>
        <v-btn variant="text" size="small" prepend-icon="mdi-arrow-left"
               to="/sessions" color="primary" class="mb-2">
          Sessions
        </v-btn>
        <h1 class="page-title">{{ sessionId }}</h1>
        <QualityBadge v-if="result" :label="result.quality?.label"
                      :score="result.quality?.score" :color="result.quality?.color" />
      </div>
      <div class="header-actions">
        <v-btn variant="tonal" color="primary" prepend-icon="mdi-play"
               @click="runAnalysis(false)" :loading="loading">
          Analyser
        </v-btn>
        <v-btn variant="tonal" color="warning" prepend-icon="mdi-refresh"
               @click="runAnalysis(true)" :loading="loading">
          Recalculer
        </v-btn>
        <v-btn v-if="result" variant="tonal" color="secondary"
               prepend-icon="mdi-download" :href="apiUrl(`/export/${sessionId}/csv`)">
          CSV
        </v-btn>
      </div>
    </div>

    <!-- Pas encore analysé -->
    <v-card v-if="!result && !loading" class="glass-card text-center pa-8">
      <v-icon size="64" color="primary" class="mb-4">mdi-flask-outline</v-icon>
      <h3 style="color: var(--text)">Session non analysée</h3>
      <p style="color: var(--muted)">Cliquez sur "Analyser" pour lancer le pipeline POS</p>
    </v-card>

    <!-- Loading -->
    <v-card v-if="loading" class="glass-card text-center pa-8">
      <v-progress-circular indeterminate color="primary" size="48" class="mb-4" />
      <p style="color: var(--muted)">Calcul en cours — POS + cartes ST-rPPG...</p>
    </v-card>

    <!-- Résultats -->
    <template v-if="result && !loading">
      <!-- Métriques principales -->
      <v-row class="mb-4">
        <v-col v-for="m in mainMetrics" :key="m.label" cols="6" md="3">
          <MetricCard v-bind="m" />
        </v-col>
      </v-row>

      <!-- Signal + FFT -->
      <v-row class="mb-4">
        <v-col cols="12" md="8">
          <v-card class="glass-card">
            <v-card-title class="card-title">
              <v-icon color="primary" class="mr-2">mdi-pulse</v-icon>
              Signal POS — HR estimée :
              <span style="color: var(--warn); margin-left: 6px">
                {{ result.hr?.hr_bpm }} bpm
              </span>
            </v-card-title>
            <v-card-text>
              <SignalChart
                :time="result.signal?.time || []"
                :raw="result.signal?.raw || []"
                :filtered="result.signal?.filt || []"
                :peaks="result.signal?.peaks || []"
                :hrBpm="result.hr?.hr_bpm"
                :height="240"
              />
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="4">
          <v-card class="glass-card" height="100%">
            <v-card-title class="card-title">
              <v-icon color="secondary" class="mr-2">mdi-chart-bell-curve</v-icon>
              Spectre FFT
            </v-card-title>
            <v-card-text>
              <FFTChart
                :freq="result.hr?.freq || []"
                :fft="result.hr?.fft || []"
                :hrHz="result.hr?.hr_hz"
                :hrBpm="result.hr?.hr_bpm"
                :height="240"
              />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- SNR + Cartes spatiales -->
      <v-row>
        <v-col cols="12" md="4">
          <v-card class="glass-card">
            <v-card-title class="card-title">
              <v-icon color="warning" class="mr-2">mdi-signal</v-icon>
              SNR glissant — moy: {{ result.snr?.mean_snr }} dB
            </v-card-title>
            <v-card-text>
              <SNRChart
                :time="result.snr?.time || []"
                :snr="result.snr?.snr || []"
                :meanSnr="result.snr?.mean_snr"
                :height="200"
              />
            </v-card-text>
          </v-card>

          <!-- TMS -->
          <v-card class="glass-card mt-3">
            <v-card-title class="card-title">
              <v-icon color="secondary" class="mr-2">mdi-waveform</v-icon>
              Template Matching Score
            </v-card-title>
            <v-card-text>
              <div class="tms-display">
                <div class="tms-value" :style="{ color: result.tms?.is_clean ? 'var(--green)' : 'var(--warn)' }">
                  {{ (result.tms?.tms * 100)?.toFixed(1) }}%
                </div>
                <v-chip
                  size="small"
                  :color="result.tms?.is_clean ? 'success' : 'warning'"
                  variant="tonal"
                >
                  {{ result.tms?.is_clean ? "Signal propre ✓" : "Signal bruité" }}
                </v-chip>
                <div style="color: var(--muted); font-size: 0.8rem">
                  {{ result.tms?.n_cycles }} cycles détectés
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Cartes ST-rPPG -->
        <v-col cols="12" md="4">
          <v-card class="glass-card">
            <v-card-title class="card-title">
              <v-icon color="accent" class="mr-2">mdi-map</v-icon>
              Cartes ST-rPPG
            </v-card-title>
            <v-card-text>
              <SpatialMap
                :maps="result.maps || {}"
                :stats="result.amp_stats"
              />
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Recommandations + tag scénario -->
        <v-col cols="12" md="4">
          <v-card class="glass-card">
            <v-card-title class="card-title">
              <v-icon color="warning" class="mr-2">mdi-lightbulb</v-icon>
              Recommandations
            </v-card-title>
            <v-card-text>
              <div v-if="result.quality?.recommendations?.length === 0"
                   style="color: var(--green); font-size: 0.85rem">
                ✓ Aucune recommandation — signal de bonne qualité
              </div>
              <div v-for="r in result.quality?.recommendations" :key="r"
                   class="rec-item">
                <v-icon color="warning" size="14">mdi-arrow-right</v-icon>
                {{ r }}
              </div>
            </v-card-text>
          </v-card>

          <!-- Tag scénario -->
          <v-card class="glass-card mt-3">
            <v-card-title class="card-title">
              <v-icon color="primary" class="mr-2">mdi-tag</v-icon>
              Tagger le scénario
            </v-card-title>
            <v-card-text>
              <v-select
                v-model="scenarioLabel"
                :items="scenarioOptions"
                label="Type de tissu"
                density="compact"
                variant="outlined"
                class="mb-2"
              />
              <v-text-field
                v-model="scenarioZone"
                label="Zone anatomique"
                density="compact"
                variant="outlined"
                placeholder="Ex: paume droite"
                class="mb-2"
              />
              <v-text-field
                v-model="scenarioDesc"
                label="Description"
                density="compact"
                variant="outlined"
                placeholder="Ex: éclairage LED, repos"
              />
              <v-btn color="primary" variant="tonal" block class="mt-2"
                     @click="saveTag" :disabled="!scenarioLabel">
                Enregistrer
              </v-btn>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useSessionStore } from "../stores/session.js";
import { apiUrl } from "../lib/api.js";
import MetricCard  from "../components/ui/MetricCard.vue";
import QualityBadge from "../components/ui/QualityBadge.vue";
import SignalChart from "../components/charts/SignalChart.vue";
import FFTChart    from "../components/charts/FFTChart.vue";
import SpatialMap  from "../components/charts/SpatialMap.vue";
import SNRChart    from "../components/charts/SNRChart.vue";

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
  catch { /* pas encore analysé */ }
});

async function runAnalysis(force) {
  loading.value = true;
  try {
    result.value = await store.analyze(sessionId.value, force);
  } finally {
    loading.value = false;
  }
}

async function saveTag() {
  await store.tagScenario(sessionId.value, scenarioLabel.value, scenarioDesc.value, scenarioZone.value);
}

const mainMetrics = computed(() => {
  if (!result.value) return [];
  const r = result.value;
  return [
    { label: "HR estimée",  value: r.hr?.hr_bpm,         unit: "bpm",  icon: "mdi-heart-pulse",   color: "var(--warn)" },
    { label: "SNR moyen",   value: r.snr?.mean_snr,       unit: "dB",   icon: "mdi-signal",        color: r.snr?.mean_snr >= 3 ? "var(--green)" : "var(--danger)" },
    { label: "TMS",         value: ((r.tms?.tms || 0) * 100).toFixed(1), unit: "%", icon: "mdi-waveform", color: r.tms?.is_clean ? "var(--green)" : "var(--warn)" },
    { label: "FPS réel",    value: r.fps?.toFixed(1),     unit: "Hz",   icon: "mdi-speedometer",   color: "var(--accent)" },
  ];
});
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
}
.page-title { font-size: 1.2rem; font-weight: 600; color: var(--text); margin: 4px 0; }
.header-actions { display: flex; gap: 8px; align-items: center; }
.card-title {
  font-size: 0.88rem !important;
  font-weight: 600;
  padding: 14px 16px 8px;
  display: flex;
  align-items: center;
}
.tms-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 16px 0;
}
.tms-value { font-size: 2.5rem; font-weight: 700; }
.rec-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
  color: var(--warn);
  padding: 4px 0;
}
</style>
