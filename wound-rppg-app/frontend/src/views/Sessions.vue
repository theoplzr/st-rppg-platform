<template>
  <div>
    <div class="page-header">
      <h1 class="page-title gradient-text">Sessions</h1>
      <v-text-field
        v-model="search"
        prepend-inner-icon="mdi-magnify"
        placeholder="Rechercher..."
        density="compact"
        variant="outlined"
        hide-details
        style="max-width: 260px"
      />
    </div>

    <v-row v-if="!store.loading">
      <v-col
        v-for="s in filteredSessions"
        :key="s.name"
        cols="12" sm="6" md="4" lg="3"
      >
        <v-card
          class="glass-card session-card"
          :to="`/analysis/${s.name}`"
        >
          <div class="session-status-bar"
               :style="{ background: s.has_results ? 'var(--green)' : 'var(--warn)' }" />
          <v-card-text>
            <div class="session-name">{{ s.name }}</div>
            <div class="session-date">{{ formatDate(s.date) }}</div>

            <div class="session-chips mt-2">
              <v-chip size="x-small" variant="tonal" color="primary">
                {{ s.fps?.toFixed(0) }} FPS
              </v-chip>
              <v-chip size="x-small" variant="tonal" color="secondary">
                {{ s.nb_frames }} frames
              </v-chip>
              <v-chip size="x-small" variant="tonal" color="info">
                {{ s.duration_s }}s
              </v-chip>
            </div>

            <div v-if="s.scenario?.label" class="mt-2">
              <v-chip size="x-small" color="warning" variant="tonal"
                      prepend-icon="mdi-tag">
                {{ s.scenario.label }}
              </v-chip>
            </div>

            <div class="session-footer mt-3">
              <v-icon
                :color="s.has_results ? 'success' : 'warning'"
                size="14"
              >
                {{ s.has_results ? "mdi-check-circle" : "mdi-clock-outline" }}
              </v-icon>
              <span style="font-size: 0.72rem; color: var(--muted)">
                {{ s.has_results ? "Analysée" : "Non analysée" }}
              </span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <div v-if="store.loading" class="text-center pa-8">
      <v-progress-circular indeterminate color="primary" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useSessionStore } from "../stores/session.js";

const store  = useSessionStore();
const search = ref("");

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
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-title  { font-size: 1.8rem; font-weight: 700; margin: 0; }
.session-card { cursor: pointer; transition: all 0.2s; overflow: hidden; padding-top: 3px !important; }
.session-card:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,200,255,0.12) !important; }
.session-status-bar { height: 3px; width: 100%; margin-bottom: 2px; }
.session-name { font-size: 0.82rem; font-weight: 600; color: var(--text); word-break: break-all; }
.session-date { font-size: 0.72rem; color: var(--muted); margin-top: 3px; }
.session-chips { display: flex; gap: 4px; flex-wrap: wrap; }
.session-footer { display: flex; align-items: center; gap: 5px; }
</style>
