<template>
  <header class="topbar">
    <div class="topbar-left">
      <button class="tb-hamburger" @click="$emit('toggle-sidebar')" aria-label="Menu">
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
          <path d="M1.5 3.5h12M1.5 7.5h12M1.5 11.5h12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        </svg>
      </button>
      <span class="bc-root">Wound-rPPG</span>
      <span class="bc-sep">/</span>
      <span class="bc-current">{{ routeLabel }}</span>
    </div>

    <div class="topbar-right">
      <div class="tb-tag tb-tag--hide-sm">
        <span class="tb-tag-dot" style="background:#e8622a" />
        POS · Wang 2017
      </div>
      <div class="tb-tag tb-tag--hide-sm">
        <span class="tb-tag-dot" style="background:#22d47e; box-shadow: 0 0 5px rgba(34,212,126,0.6)" />
        v1.0
      </div>

      <button
        class="tb-theme-btn"
        @click="toggleTheme"
        :title="theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'"
      >
        <!-- Sun — shown in dark mode, click → light -->
        <svg v-if="theme === 'dark'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <circle cx="12" cy="12" r="5"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>
        <!-- Moon — shown in light mode, click → dark -->
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed, inject } from "vue";
import { useRoute } from "vue-router";

defineEmits(["toggle-sidebar"]);

const theme = inject("theme");
const toggleTheme = inject("toggleTheme");

const route = useRoute();
const labels = {
  Dashboard: "Tableau de bord",
  Sessions:  "Sessions",
  Analysis:  "Analyse",
  Scenarios: "Scénarios",
  Acquire:   "Acquisition",
  Patients:  "Patients",
  Patient:   "Dossier patient",
};
const routeLabel = computed(() => labels[route.name] || route.name || "");
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 44px;
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 50;
  transition: background 0.3s, border-color 0.3s;
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tb-hamburger {
  display: none;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: none;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  border-radius: 8px;
  transition: color 0.2s, background 0.2s;
  padding: 0;
  flex-shrink: 0;
}
.tb-hamburger:hover {
  color: var(--text);
  background: var(--surface2);
}
.bc-root {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: 0.01em;
  transition: color 0.3s;
}
.bc-sep {
  font-size: 0.75rem;
  color: var(--border2);
  transition: color 0.3s;
}
.bc-current {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text2);
  letter-spacing: 0.01em;
  transition: color 0.3s;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tb-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--muted);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 7px;
  padding: 4px 12px;
  letter-spacing: 0.03em;
  transition: background 0.3s, border-color 0.3s, color 0.3s;
}
.tb-tag-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
}
.tb-theme-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--border2);
  background: var(--surface2);
  color: var(--text2);
  cursor: pointer;
  border-radius: 8px;
  transition: color 0.2s, background 0.2s, border-color 0.2s, transform 0.2s;
  padding: 0;
  flex-shrink: 0;
}
.tb-theme-btn:hover {
  color: var(--accent);
  border-color: var(--accent);
  background: rgba(232,98,42,0.07);
  transform: rotate(20deg) scale(1.05);
}

@media (max-width: 768px) {
  .topbar      { padding: 0 14px; }
  .tb-hamburger { display: flex; }
  .tb-tag--hide-sm { display: none; }
}
</style>
