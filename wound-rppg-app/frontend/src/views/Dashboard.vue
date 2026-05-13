<template>
  <div>
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title gradient-text">Dashboard</h1>
        <p class="page-sub">Vue d'ensemble du projet Wound-rPPG · ANR-24-CE45-7356</p>
      </div>
      <v-btn color="primary" variant="tonal" prepend-icon="mdi-refresh"
             @click="store.fetchSessions()" :loading="store.loading">
        Actualiser
      </v-btn>
    </div>

    <!-- Stats globales -->
    <v-row class="mb-6">
      <v-col v-for="stat in globalStats" :key="stat.label" cols="12" sm="6" md="3">
        <MetricCard v-bind="stat" />
      </v-col>
    </v-row>

    <!-- Sessions récentes -->
    <v-row>
      <v-col cols="12" md="7">
        <v-card class="glass-card">
          <v-card-title class="card-title">
            <v-icon color="primary" class="mr-2">mdi-history</v-icon>
            Sessions récentes
          </v-card-title>
          <v-card-text>
            <div v-if="!store.hasSessions" class="empty-state">
              <v-icon size="48" color="muted">mdi-folder-open</v-icon>
              <p>Aucune session trouvée.<br>Lancez une acquisition avec <code>wound_rppg_capture.py</code></p>
            </div>
            <v-list v-else density="compact" class="session-list">
              <v-list-item
                v-for="s in recentSessions"
                :key="s.name"
                :to="`/analysis/${s.name}`"
                rounded="lg"
                class="session-item"
              >
                <template #prepend>
                  <v-icon :color="s.has_results ? 'success' : 'warning'">
                    {{ s.has_results ? "mdi-check-circle" : "mdi-clock-outline" }}
                  </v-icon>
                </template>
                <v-list-item-title style="font-size: 0.85rem">{{ s.name }}</v-list-item-title>
                <v-list-item-subtitle style="font-size: 0.75rem">
                  {{ s.nb_frames }} frames · {{ s.fps?.toFixed(1) }} FPS · {{ s.duration_s }}s
                </v-list-item-subtitle>
                <template #append>
                  <v-chip
                    v-if="s.scenario?.label"
                    size="x-small"
                    color="primary"
                    variant="tonal"
                  >
                    {{ s.scenario.label }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Résumé qualité -->
      <v-col cols="12" md="5">
        <v-card class="glass-card" height="100%">
          <v-card-title class="card-title">
            <v-icon color="secondary" class="mr-2">mdi-chart-bar</v-icon>
            Qualité des analyses
          </v-card-title>
          <v-card-text>
            <div v-if="qualitySummary.length === 0" class="empty-state">
              <p>Analysez des sessions pour voir les statistiques.</p>
            </div>
            <div v-else class="quality-bars">
              <div v-for="q in qualitySummary" :key="q.label" class="quality-row">
                <span class="q-label">{{ q.label }}</span>
                <v-progress-linear
                  :model-value="q.pct"
                  :color="q.color"
                  rounded
                  height="8"
                  style="flex: 1"
                />
                <span class="q-count" :style="{ color: q.color }">{{ q.count }}</span>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useSessionStore } from "../stores/session.js";
import MetricCard from "../components/ui/MetricCard.vue";

const store = useSessionStore();
onMounted(() => store.fetchSessions());

const recentSessions = computed(() => store.sessions.slice(0, 8));

const globalStats = computed(() => [
  {
    label: "Sessions totales",
    value: store.sessions.length,
    icon:  "mdi-folder-multiple",
    color: "var(--accent)",
  },
  {
    label: "Analyses effectuées",
    value: store.sessions.filter(s => s.has_results).length,
    icon:  "mdi-check-circle",
    color: "var(--green)",
  },
  {
    label: "Scénarios taggés",
    value: store.sessions.filter(s => s.scenario?.label).length,
    icon:  "mdi-tag-multiple",
    color: "var(--warn)",
  },
  {
    label: "FPS moyen",
    value: store.sessions.length
      ? (store.sessions.reduce((a, s) => a + (s.fps || 0), 0) / store.sessions.length).toFixed(1)
      : "—",
    unit:  "Hz",
    icon:  "mdi-speedometer",
    color: "#a78bfa",
  },
]);

const qualitySummary = computed(() => {
  const labels = ["EXCELLENT", "BON", "FAIBLE", "MAUVAIS"];
  const colors  = { EXCELLENT: "#7ee787", BON: "#00c8ff", FAIBLE: "#f0883e", MAUVAIS: "#f85149" };
  const total   = store.sessions.filter(s => s.has_results).length || 1;
  return labels.map(label => ({
    label,
    color: colors[label],
    count: 0,
    pct:   0,
  }));
});
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
}
.page-title { font-size: 1.8rem; font-weight: 700; margin: 0; }
.page-sub   { color: var(--muted); font-size: 0.85rem; margin: 4px 0 0; }
.card-title {
  font-size: 0.9rem !important;
  font-weight: 600;
  color: var(--text);
  padding: 16px 16px 8px;
  display: flex;
  align-items: center;
}
.session-item {
  border: 1px solid transparent;
  transition: all 0.2s;
  margin-bottom: 3px;
}
.session-item:hover { border-color: var(--border); background: var(--surface2); }
.empty-state {
  text-align: center;
  padding: 32px;
  color: var(--muted);
  font-size: 0.85rem;
}
.quality-bars { display: flex; flex-direction: column; gap: 12px; }
.quality-row  { display: flex; align-items: center; gap: 12px; }
.q-label { width: 80px; font-size: 0.78rem; color: var(--muted); }
.q-count { width: 24px; text-align: right; font-size: 0.78rem; font-weight: 700; }
</style>
