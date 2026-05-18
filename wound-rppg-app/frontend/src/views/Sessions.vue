<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title gradient-text">Sessions</h1>
        <p class="page-sub">{{ store.sessions.length }} session{{ store.sessions.length !== 1 ? 's' : '' }}</p>
      </div>
      <div class="search-box">
        <v-icon size="15" style="color: var(--muted)">mdi-magnify</v-icon>
        <input v-model="search" placeholder="Rechercher..." class="search-input" />
      </div>
    </div>

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
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
  gap: 16px;
}
.page-title { font-size: 2rem; font-weight: 900; margin: 0 0 4px; letter-spacing: -0.5px; }
.page-sub   { color: var(--muted); font-size: 0.78rem; font-weight: 500; }

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
.session-card:hover {
  border-color: var(--border2);
  transform: translateY(-2px);
}
.card-accent { height: 2px; width: 100%; }
.card-body   { padding: 16px; }
.s-name { font-size: 0.83rem; font-weight: 700; color: var(--text); word-break: break-all; margin-bottom: 3px; }
.s-date { font-size: 0.71rem; color: var(--muted); margin-bottom: 10px; }
.s-chips { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 8px; }
.chip {
  font-size: 0.69rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 5px;
}
.chip--blue { background: rgba(2,132,199,0.12); color: #38bdf8; border: 1px solid rgba(2,132,199,0.2); }
.chip--teal { background: rgba(6,182,212,0.1);  color: #22d3ee; border: 1px solid rgba(6,182,212,0.2); }
.chip--gray { background: var(--surface2);       color: var(--muted); border: 1px solid var(--border); }
.s-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  color: var(--accent);
  margin-bottom: 8px;
  font-weight: 500;
}
.s-status { display: flex; align-items: center; gap: 6px; font-size: 0.71rem; color: var(--muted); }
.status-dot { width: 6px; height: 6px; border-radius: 50%; }

.loading-block { display: flex; justify-content: center; padding: 60px; }
.empty-block { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 80px 20px; color: var(--muted); font-size: 0.88rem; text-align: center; }
</style>
