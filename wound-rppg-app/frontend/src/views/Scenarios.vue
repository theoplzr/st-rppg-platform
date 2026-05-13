<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title gradient-text">Comparaison de scénarios</h1>
        <p class="page-sub">Inspiré de l'approche Ahmad Hmedeh · LCOMS 2024</p>
      </div>
    </div>

    <!-- Sélecteur de sessions -->
    <v-card class="glass-card mb-6">
      <v-card-title class="card-title">
        <v-icon color="primary" class="mr-2">mdi-select-multiple</v-icon>
        Sélectionner les sessions à comparer
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="5">
            <v-select
              v-model="sessionA"
              :items="sessionOptions"
              label="Session A"
              density="compact"
              variant="outlined"
              prepend-inner-icon="mdi-alpha-a-circle"
            />
          </v-col>
          <v-col cols="12" md="5">
            <v-select
              v-model="sessionB"
              :items="sessionOptions"
              label="Session B"
              density="compact"
              variant="outlined"
              prepend-inner-icon="mdi-alpha-b-circle"
            />
          </v-col>
          <v-col cols="12" md="2">
            <v-btn
              color="primary"
              variant="tonal"
              block
              height="40"
              :loading="loading"
              :disabled="!sessionA || !sessionB"
              @click="compare"
            >
              Comparer
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Résultats comparaison -->
    <template v-if="comparison">
      <!-- Métriques côte à côte -->
      <v-row class="mb-4">
        <v-col cols="12" md="5">
          <v-card class="glass-card" style="border-color: var(--accent)44">
            <v-card-title class="card-title" style="color: var(--accent)">
              <v-icon color="primary" class="mr-2">mdi-alpha-a-circle</v-icon>
              {{ comparison.session_a.name }}
            </v-card-title>
            <v-card-text>
              <div class="compare-metrics">
                <div v-for="m in metricsA" :key="m.key" class="compare-row">
                  <span class="cmp-label">{{ m.label }}</span>
                  <span class="cmp-value" :style="{ color: m.color }">
                    {{ m.value }} <small>{{ m.unit }}</small>
                  </span>
                </div>
                <QualityBadge
                  :label="comparison.session_a.label"
                  :score="comparison.session_a.score"
                  :color="comparison.session_a.color"
                  class="mt-3"
                />
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Diff -->
        <v-col cols="12" md="2">
          <v-card class="glass-card" style="border-color: var(--border)">
            <v-card-title class="card-title justify-center" style="font-size: 0.8rem">
              Δ Différence
            </v-card-title>
            <v-card-text>
              <div class="diff-metrics">
                <div v-for="d in diffMetrics" :key="d.key" class="diff-row">
                  <span class="diff-label">{{ d.label }}</span>
                  <span class="diff-value" :style="{ color: d.color }">
                    {{ d.value > 0 ? "+" : "" }}{{ d.value }}
                  </span>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="5">
          <v-card class="glass-card" style="border-color: var(--green)44">
            <v-card-title class="card-title" style="color: var(--green)">
              <v-icon color="secondary" class="mr-2">mdi-alpha-b-circle</v-icon>
              {{ comparison.session_b.name }}
            </v-card-title>
            <v-card-text>
              <div class="compare-metrics">
                <div v-for="m in metricsB" :key="m.key" class="compare-row">
                  <span class="cmp-label">{{ m.label }}</span>
                  <span class="cmp-value" :style="{ color: m.color }">
                    {{ m.value }} <small>{{ m.unit }}</small>
                  </span>
                </div>
                <QualityBadge
                  :label="comparison.session_b.label"
                  :score="comparison.session_b.score"
                  :color="comparison.session_b.color"
                  class="mt-3"
                />
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Cartes spatiales côte à côte -->
      <v-row>
        <v-col cols="12" md="6">
          <v-card class="glass-card">
            <v-card-title class="card-title">Carte ST-rPPG — Session A</v-card-title>
            <v-card-text>
              <SpatialMap :maps="comparison.maps_a || {}" />
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="6">
          <v-card class="glass-card">
            <v-card-title class="card-title">Carte ST-rPPG — Session B</v-card-title>
            <v-card-text>
              <SpatialMap :maps="comparison.maps_b || {}" />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
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

const sessionOptions = computed(() =>
  store.sessions.map(s => ({ title: s.name, value: s.name })));

async function compare() {
  loading.value = true;
  try {
    const { data } = await axios.post(apiUrl("/scenarios/compare/two"), {
      session_a: sessionA.value,
      session_b: sessionB.value,
    });
    comparison.value = data;
  } finally {
    loading.value = false;
  }
}

function metricColor(key, val) {
  if (key === "snr_db") return val >= 3 ? "var(--green)" : val >= 0 ? "var(--warn)" : "var(--danger)";
  if (key === "tms")    return val >= 0.96 ? "var(--green)" : "var(--warn)";
  return "var(--text)";
}

const metricsA = computed(() => {
  if (!comparison.value) return [];
  const s = comparison.value.session_a;
  return [
    { key: "hr_bpm", label: "HR",    value: s.hr_bpm,                unit: "bpm", color: "var(--warn)" },
    { key: "snr_db", label: "SNR",   value: s.snr_db,                unit: "dB",  color: metricColor("snr_db", s.snr_db) },
    { key: "tms",    label: "TMS",   value: (s.tms * 100).toFixed(1), unit: "%",   color: metricColor("tms", s.tms) },
    { key: "score",  label: "Score", value: s.score,                  unit: "/100", color: "var(--accent)" },
  ];
});

const metricsB = computed(() => {
  if (!comparison.value) return [];
  const s = comparison.value.session_b;
  return [
    { key: "hr_bpm", label: "HR",    value: s.hr_bpm,                unit: "bpm", color: "var(--warn)" },
    { key: "snr_db", label: "SNR",   value: s.snr_db,                unit: "dB",  color: metricColor("snr_db", s.snr_db) },
    { key: "tms",    label: "TMS",   value: (s.tms * 100).toFixed(1), unit: "%",   color: metricColor("tms", s.tms) },
    { key: "score",  label: "Score", value: s.score,                  unit: "/100", color: "var(--accent)" },
  ];
});

const diffMetrics = computed(() => {
  if (!comparison.value) return [];
  const d = comparison.value.diff;
  return [
    { key: "hr_bpm", label: "HR",    value: d.hr_bpm, color: "var(--muted)" },
    { key: "snr_db", label: "SNR",   value: d.snr_db, color: d.snr_db > 0 ? "var(--green)" : "var(--danger)" },
    { key: "score",  label: "Score", value: d.score,  color: d.score > 0 ? "var(--green)" : "var(--danger)" },
  ];
});
</script>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-title  { font-size: 1.8rem; font-weight: 700; margin: 0; }
.page-sub    { color: var(--muted); font-size: 0.82rem; font-style: italic; }
.card-title  { font-size: 0.88rem !important; font-weight: 600; padding: 14px 16px 8px; display: flex; align-items: center; }
.compare-metrics { display: flex; flex-direction: column; gap: 10px; }
.compare-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--border); }
.cmp-label   { font-size: 0.82rem; color: var(--muted); }
.cmp-value   { font-size: 1rem; font-weight: 700; }
.diff-metrics { display: flex; flex-direction: column; gap: 18px; padding: 8px 0; }
.diff-row    { display: flex; flex-direction: column; align-items: center; gap: 3px; }
.diff-label  { font-size: 0.72rem; color: var(--muted); }
.diff-value  { font-size: 1.1rem; font-weight: 700; }
</style>
