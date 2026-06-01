<template>
  <div class="dash">
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
    <div class="stats-row">
      <div
        v-for="(stat, i) in globalStats"
        :key="stat.label"
        class="stat-col"
        :style="{ animationDelay: `${i * 70}ms` }"
      >
        <MetricCard v-bind="stat" />
      </div>
    </div>

    <!-- Main grid -->
    <div class="dash-grid">
      <!-- Recent sessions -->
      <div class="card-block dash-sessions" style="animation: fadeInUp 0.5s 0.25s ease both">
        <div class="card-head">
          <v-icon size="14" color="#e8622a">mdi-history</v-icon>
          <span>Sessions récentes</span>
          <span class="head-hint">{{ store.sessions.length }} au total</span>
          <router-link to="/sessions" class="card-head-cta">Tout voir →</router-link>
        </div>

        <div v-if="store.loading" class="state-center">
          <v-progress-circular indeterminate color="var(--accent)" size="24" width="2" />
        </div>

        <div v-else-if="!store.hasSessions" class="state-empty">
          <div class="empty-icon-wrap">
            <v-icon size="26" color="var(--muted)">mdi-folder-open-outline</v-icon>
          </div>
          <p class="empty-title">Aucune session enregistrée</p>
          <p class="empty-sub">Importez un ZIP ou lancez une acquisition caméra</p>
          <router-link to="/acquire" class="btn-accent" style="margin-top:12px;text-decoration:none;font-size:0.78rem;align-self:center">
            <v-icon size="13">mdi-camera-outline</v-icon> Démarrer une acquisition
          </router-link>
        </div>

        <div v-else class="session-feed">
          <router-link
            v-for="(s, i) in recentSessions"
            :key="s.name"
            :to="`/analysis/${s.name}`"
            class="feed-row"
            :style="{ animationDelay: `${0.3 + i * 0.04}s` }"
          >
            <div class="feed-dot" :class="s.has_results ? 'dot--green' : 'dot--warn'" />
            <div class="feed-info">
              <span class="feed-name">{{ s.name }}</span>
              <span class="feed-meta">{{ s.nb_frames }} frames · {{ s.fps?.toFixed(0) }} FPS · {{ s.duration_s }}s</span>
            </div>
            <div class="feed-right">
              <span v-if="s.scenario?.label" class="feed-scenario">{{ s.scenario.label }}</span>
              <span class="feed-badge" :class="s.has_results ? 'badge--ok' : 'badge--pending'">
                {{ s.has_results ? "Analysée" : "En attente" }}
              </span>
            </div>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" class="feed-arrow">
              <path d="M4 2l4 4-4 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </router-link>
        </div>
      </div>

      <!-- Side column -->
      <div class="dash-side">
        <!-- Analysis rate -->
        <div class="card-block" style="animation: fadeInUp 0.5s 0.32s ease both">
          <div class="card-head">
            <v-icon size="14" color="#06b6d4">mdi-chart-donut</v-icon>
            <span>Taux d'analyse</span>
          </div>
          <div class="rate-body">
            <div class="rate-donut-wrap">
              <svg viewBox="0 0 72 72" class="rate-donut">
                <circle cx="36" cy="36" r="28" fill="none" stroke="var(--border)" stroke-width="6"/>
                <circle
                  cx="36" cy="36" r="28" fill="none"
                  stroke="var(--green)" stroke-width="6"
                  stroke-linecap="round"
                  stroke-dasharray="175.9"
                  :stroke-dashoffset="175.9 * (1 - analysedPct / 100)"
                  style="transition: stroke-dashoffset 1s cubic-bezier(0.16,1,0.3,1); transform-origin: center; transform: rotate(-90deg)"
                />
              </svg>
              <div class="rate-pct">{{ analysedPct }}<span style="font-size:0.65rem">%</span></div>
            </div>
            <div class="rate-legend">
              <div class="rate-leg-row">
                <span class="rate-leg-dot" style="background:var(--green)"/>
                <span class="rate-leg-label">Analysées</span>
                <span class="rate-leg-val">{{ store.sessions.filter(s => s.has_results).length }}</span>
              </div>
              <div class="rate-leg-row">
                <span class="rate-leg-dot" style="background:var(--warn)"/>
                <span class="rate-leg-label">En attente</span>
                <span class="rate-leg-val">{{ store.sessions.filter(s => !s.has_results).length }}</span>
              </div>
              <div class="rate-leg-row">
                <span class="rate-leg-dot" style="background:var(--teal)"/>
                <span class="rate-leg-label">Avec scénario</span>
                <span class="rate-leg-val">{{ store.sessions.filter(s => s.scenario?.label).length }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick nav -->
        <div class="card-block" style="animation: fadeInUp 0.5s 0.38s ease both">
          <div class="card-head">
            <v-icon size="14" color="#a78bfa">mdi-lightning-bolt-outline</v-icon>
            <span>Accès rapide</span>
          </div>
          <div class="qa-grid">
            <router-link to="/acquire" class="qa-btn">
              <svg class="qa-icon" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="4" stroke="#e8622a" stroke-width="1.5"/><circle cx="10" cy="10" r="8" stroke="#e8622a" stroke-width="1.5" opacity="0.4"/></svg>
              <span>Acquisition</span>
            </router-link>
            <router-link to="/sessions" class="qa-btn">
              <svg class="qa-icon" viewBox="0 0 20 20" fill="none"><rect x="3" y="4" width="14" height="3" rx="1.5" stroke="#06b6d4" stroke-width="1.5"/><rect x="3" y="9" width="14" height="3" rx="1.5" stroke="#06b6d4" stroke-width="1.5"/><rect x="3" y="14" width="8" height="3" rx="1.5" stroke="#06b6d4" stroke-width="1.5"/></svg>
              <span>Sessions</span>
            </router-link>
            <router-link to="/patients" class="qa-btn">
              <svg class="qa-icon" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="7" r="3" stroke="#a78bfa" stroke-width="1.5"/><path d="M4 17c0-3.3 2.7-6 6-6s6 2.7 6 6" stroke="#a78bfa" stroke-width="1.5" stroke-linecap="round"/></svg>
              <span>Patients</span>
            </router-link>
            <router-link to="/scenarios" class="qa-btn">
              <svg class="qa-icon" viewBox="0 0 20 20" fill="none"><rect x="2" y="6" width="7" height="9" rx="1.5" stroke="#22d47e" stroke-width="1.5"/><rect x="11" y="6" width="7" height="9" rx="1.5" stroke="#22d47e" stroke-width="1.5"/><path d="M9.5 10.5h1" stroke="#22d47e" stroke-width="1.5" stroke-linecap="round"/></svg>
              <span>Scénarios</span>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useSessionStore } from "../stores/session.js";
import MetricCard from "../components/ui/MetricCard.vue";

const store = useSessionStore();
onMounted(() => store.fetchSessions());

const recentSessions = computed(() => store.sessions.slice(0, 8));

const analysedPct = computed(() => {
  if (!store.sessions.length) return 0;
  return Math.round(store.sessions.filter(s => s.has_results).length / store.sessions.length * 100);
});

const globalStats = computed(() => [
  { label: "Sessions",         value: store.sessions.length,                                icon: "mdi-folder-multiple-outline", color: "var(--accent)"  },
  { label: "Analysées",        value: store.sessions.filter(s => s.has_results).length,     icon: "mdi-check-circle-outline",    color: "var(--green)"   },
  { label: "Scénarios taggés", value: store.sessions.filter(s => s.scenario?.label).length, icon: "mdi-tag-multiple-outline",    color: "var(--teal)"    },
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
/* ── Stats ─────────────────────────────────────────── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}
.stat-col { animation: fadeInUp 0.5s ease both; }

@media (max-width: 900px)  { .stats-row { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 480px)  { .stats-row { grid-template-columns: 1fr 1fr; gap: 10px; } }

/* ── Main grid ─────────────────────────────────────── */
.dash-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 14px;
  align-items: start;
}
.dash-sessions { animation: fadeInUp 0.5s 0.2s ease both; }
.dash-side { display: flex; flex-direction: column; gap: 14px; }

@media (max-width: 1024px) { .dash-grid { grid-template-columns: 1fr; } }

/* ── Card head link ─────────────────────────────────── */
.card-head-cta {
  margin-left: auto;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--accent);
  text-decoration: none;
  opacity: 0.7;
  transition: opacity 0.15s;
}
.card-head-cta:hover { opacity: 1; }

/* ── States ─────────────────────────────────────────── */
.state-center {
  display: flex;
  justify-content: center;
  padding: 50px 20px;
}
.state-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 20px;
  gap: 6px;
}
.empty-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: var(--surface2);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
}
.empty-title {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text2);
  margin: 0;
}
.empty-sub {
  font-size: 0.75rem;
  color: var(--muted);
  margin: 0;
  text-align: center;
}

/* ── Session feed ───────────────────────────────────── */
.session-feed { display: flex; flex-direction: column; }
.feed-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 20px;
  border-bottom: 1px solid var(--border);
  text-decoration: none;
  transition: background 0.15s;
  animation: fadeInUp 0.4s ease both;
}
.feed-row:last-child { border-bottom: none; }
.feed-row:hover { background: var(--surface2); }
.feed-row:hover .feed-arrow { color: var(--accent); transform: translateX(2px); }
.feed-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: box-shadow 0.2s;
}
.dot--green { background: var(--green); box-shadow: 0 0 0 3px rgba(34,212,126,0.12); }
.dot--warn  { background: var(--warn);  box-shadow: 0 0 0 3px rgba(245,158,11,0.12); }
.feed-info   { flex: 1; min-width: 0; }
.feed-name   { display: block; font-size: 0.82rem; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.feed-meta   { display: block; font-size: 0.7rem; color: var(--muted); margin-top: 1px; }
.feed-right  { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.feed-scenario {
  font-size: 0.67rem; font-weight: 600; padding: 2px 7px; border-radius: 4px;
  background: rgba(232,98,42,0.1); color: var(--accent); border: 1px solid rgba(232,98,42,0.2);
}
.feed-badge  { font-size: 0.67rem; font-weight: 600; padding: 2px 7px; border-radius: 4px; }
.badge--ok      { background: rgba(34,212,126,0.1); color: var(--green); border: 1px solid rgba(34,212,126,0.2); }
.badge--pending { background: var(--surface2); color: var(--muted); border: 1px solid var(--border); }
.feed-arrow { color: var(--border2); transition: color 0.15s, transform 0.15s; flex-shrink: 0; }

/* ── Rate donut ─────────────────────────────────────── */
.rate-body { display: flex; align-items: center; gap: 20px; padding: 18px 20px; }
.rate-donut-wrap { position: relative; width: 72px; height: 72px; flex-shrink: 0; }
.rate-donut { width: 72px; height: 72px; }
.rate-pct {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Syne', sans-serif;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -0.03em;
}
.rate-legend { display: flex; flex-direction: column; gap: 8px; flex: 1; }
.rate-leg-row { display: flex; align-items: center; gap: 8px; }
.rate-leg-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.rate-leg-label { font-size: 0.72rem; color: var(--muted); flex: 1; }
.rate-leg-val { font-size: 0.82rem; font-weight: 700; color: var(--text2); }

/* ── Quick access ───────────────────────────────────── */
.qa-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 12px 14px;
}
.qa-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 14px 8px;
  border-radius: 10px;
  background: var(--surface2);
  border: 1px solid var(--border);
  text-decoration: none;
  color: var(--text2);
  font-size: 0.72rem;
  font-weight: 600;
  transition: border-color 0.18s, background 0.18s, transform 0.15s, color 0.18s;
}
.qa-btn:hover { border-color: var(--border2); background: var(--surface3); transform: translateY(-1px); color: var(--text); }
.qa-icon { width: 22px; height: 22px; }
</style>
