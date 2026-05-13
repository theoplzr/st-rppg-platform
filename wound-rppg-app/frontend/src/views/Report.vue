<template>
  <div>
    <div class="page-header">
      <h1 class="page-title gradient-text">Rapport d'export</h1>
      <p class="page-sub">Export des résultats pour publication scientifique</p>
    </div>

    <v-row>
      <v-col cols="12" md="6">
        <v-card class="glass-card">
          <v-card-title class="card-title">
            <v-icon color="primary" class="mr-2">mdi-file-table</v-icon>
            Export par session
          </v-card-title>
          <v-card-text>
            <v-select
              v-model="selectedSession"
              :items="sessionOptions"
              label="Session"
              density="compact"
              variant="outlined"
              class="mb-4"
            />
            <v-row>
              <v-col>
                <v-btn
                  block
                  color="primary"
                  variant="tonal"
                  prepend-icon="mdi-file-delimited"
                  :disabled="!selectedSession"
                  :href="selectedSession ? apiUrl(`/export/${selectedSession}/csv`) : '#'"
                  target="_blank"
                >
                  Exporter CSV
                </v-btn>
              </v-col>
              <v-col>
                <v-btn
                  block
                  color="secondary"
                  variant="tonal"
                  prepend-icon="mdi-code-json"
                  :disabled="!selectedSession"
                  :href="selectedSession ? apiUrl(`/export/${selectedSession}/json`) : '#'"
                  target="_blank"
                >
                  Exporter JSON
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card class="glass-card">
          <v-card-title class="card-title">
            <v-icon color="secondary" class="mr-2">mdi-table-large</v-icon>
            Tableau comparatif multi-sessions
          </v-card-title>
          <v-card-text>
            <p style="font-size: 0.82rem; color: var(--muted)" class="mb-3">
              Style tableau publication — inspiré Ahmad Hmedeh, LCOMS 2024
            </p>
            <v-select
              v-model="selectedSessions"
              :items="sessionOptions"
              label="Sélectionner les sessions"
              density="compact"
              variant="outlined"
              multiple
              chips
              class="mb-4"
            />
            <v-btn
              block
              color="warning"
              variant="tonal"
              prepend-icon="mdi-compare"
              :loading="loading"
              :disabled="selectedSessions.length < 2"
              @click="loadComparison"
            >
              Générer tableau
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Tableau comparatif -->
    <v-card v-if="comparisonData" class="glass-card mt-6">
      <v-card-title class="card-title">
        <v-icon color="primary" class="mr-2">mdi-chart-bar</v-icon>
        Résultats comparatifs — {{ comparisonData.n }} sessions
      </v-card-title>
      <v-card-text>
        <v-table density="compact" class="comparison-table">
          <thead>
            <tr>
              <th>Session</th>
              <th>Scénario</th>
              <th>HR (bpm)</th>
              <th>SNR (dB)</th>
              <th>TMS</th>
              <th>FPS</th>
              <th>Score</th>
              <th>Qualité</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in comparisonData.ranking" :key="s.name">
              <td style="font-size: 0.78rem; color: var(--muted)">{{ s.name }}</td>
              <td>
                <v-chip v-if="s.scenario?.label" size="x-small" color="primary" variant="tonal">
                  {{ s.scenario.label }}
                </v-chip>
              </td>
              <td :style="{ color: 'var(--warn)', fontWeight: 600 }">{{ s.hr_bpm }}</td>
              <td :style="{ color: s.snr_db >= 3 ? 'var(--green)' : s.snr_db >= 0 ? 'var(--warn)' : 'var(--danger)', fontWeight: 600 }">
                {{ s.snr_db }}
              </td>
              <td :style="{ color: s.tms >= 0.96 ? 'var(--green)' : 'var(--warn)' }">
                {{ (s.tms * 100)?.toFixed(1) }}%
              </td>
              <td style="color: var(--accent)">{{ s.fps?.toFixed(1) }}</td>
              <td style="font-weight: 700">{{ s.score }}/100</td>
              <td>
                <v-chip size="x-small" :color="s.color" variant="tonal">{{ s.label }}</v-chip>
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>
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

const sessionOptions = computed(() =>
  store.sessions.map(s => ({ title: s.name, value: s.name })));

async function loadComparison() {
  loading.value = true;
  try {
    const { data } = await axios.post(apiUrl("/scenarios/compare/multiple"),
      { sessions: selectedSessions.value });
    comparisonData.value = data;
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-title  { font-size: 1.8rem; font-weight: 700; margin: 0; }
.page-sub    { color: var(--muted); font-size: 0.82rem; }
.card-title  { font-size: 0.88rem !important; font-weight: 600; padding: 14px 16px 8px; display: flex; align-items: center; }
.comparison-table th {
  font-size: 0.78rem !important;
  color: var(--muted) !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: var(--surface2) !important;
}
.comparison-table td { font-size: 0.82rem !important; }
</style>
