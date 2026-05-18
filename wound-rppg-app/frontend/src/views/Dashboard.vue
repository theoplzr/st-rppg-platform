<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title gradient-text">Dashboard</h1>
        <p class="page-sub">Wound-rPPG · ANR-24-CE45-7356 · LCOMS</p>
      </div>
      <button class="btn-accent" @click="store.fetchSessions()" :disabled="store.loading">
        <v-icon size="14">mdi-refresh</v-icon>
        Actualiser
      </button>
    </div>

    <!-- Stats -->
    <v-row class="mb-7">
      <v-col v-for="stat in globalStats" :key="stat.label" cols="12" sm="6" md="3">
        <MetricCard v-bind="stat" />
      </v-col>
    </v-row>

    <!-- Sessions + qualité -->
    <v-row>
      <v-col cols="12" md="7">
        <div class="card-block">
          <div class="card-head">
            <v-icon size="14" color="#e8622a">mdi-history</v-icon>
            <span>Sessions récentes</span>
          </div>
          <div v-if="!store.hasSessions" class="empty-state">
            <v-icon size="36" style="color: var(--border2)">mdi-folder-open-outline</v-icon>
            <p>Aucune session.<br>
              <span style="color: var(--muted); font-size: 0.78rem">Importez un ZIP ou lancez une acquisition.</span>
            </p>
          </div>
          <div v-else class="session-list">
            <router-link
              v-for="s in recentSessions"
              :key="s.name"
              :to="`/analysis/${s.name}`"
              class="session-row"
            >
              <div class="session-dot" :style="{ background: s.has_results ? 'var(--green)' : 'var(--warn)' }" />
              <div class="session-info">
                <span class="session-name">{{ s.name }}</span>
                <span class="session-meta">{{ s.nb_frames }} frames · {{ s.fps?.toFixed(1) }} FPS · {{ s.duration_s }}s</span>
              </div>
              <v-chip v-if="s.scenario?.label" size="x-small" color="primary" variant="tonal">
                {{ s.scenario.label }}
              </v-chip>
              <v-icon size="14" style="color: var(--muted)">mdi-chevron-right</v-icon>
            </router-link>
          </div>
        </div>
      </v-col>

      <v-col cols="12" md="5">
        <div class="card-block" style="height: 100%">
          <div class="card-head">
            <v-icon size="14" color="#06b6d4">mdi-chart-bar</v-icon>
            <span>Qualité des analyses</span>
          </div>
          <div class="empty-state">
            <p style="color: var(--muted); font-size: 0.82rem">Analysez des sessions pour voir les statistiques.</p>
          </div>
        </div>
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
  { label: "Sessions",          value: store.sessions.length,                               icon: "mdi-folder-multiple-outline", color: "var(--accent)" },
  { label: "Analysées",         value: store.sessions.filter(s => s.has_results).length,    icon: "mdi-check-circle-outline",    color: "var(--green)"  },
  { label: "Scénarios taggés",  value: store.sessions.filter(s => s.scenario?.label).length, icon: "mdi-tag-multiple-outline",   color: "var(--teal)"   },
  {
    label: "FPS moyen", icon: "mdi-speedometer", color: "var(--purple)",
    value: store.sessions.length
      ? (store.sessions.reduce((a, s) => a + (s.fps || 0), 0) / store.sessions.length).toFixed(1)
      : "—",
    unit: "Hz",
  },
]);

</script>

<style scoped>
/* Session list */
.session-list { display: flex; flex-direction: column; }
.session-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 18px;
  border-bottom: 1px solid var(--border);
  text-decoration: none;
  transition: background 0.15s;
}
.session-row:last-child { border-bottom: none; }
.session-row:hover { background: var(--surface2); }
.session-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.session-info { flex: 1; min-width: 0; }
.session-name {
  display: block;
  font-size: 0.83rem;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-meta {
  display: block;
  font-size: 0.71rem;
  color: var(--muted);
  margin-top: 1px;
}

.empty-state { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 40px 20px; color: var(--muted); font-size: 0.85rem; text-align: center; }
</style>
