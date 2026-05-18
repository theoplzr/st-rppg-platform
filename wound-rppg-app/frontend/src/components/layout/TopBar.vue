<template>
  <header class="topbar">
    <div class="topbar-left">
      <span class="bc-root">Wound-rPPG</span>
      <span class="bc-sep">/</span>
      <span class="bc-current">{{ routeLabel }}</span>
    </div>
    <div class="topbar-right">
      <div class="tb-tag">
        <span class="tb-tag-dot" style="background:#e8622a" />
        POS · Wang 2017
      </div>
      <div class="tb-tag">
        <span class="tb-tag-dot" style="background:#22d47e; box-shadow: 0 0 5px rgba(34,212,126,0.6)" />
        v1.0
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const labels = {
  Dashboard:  "Tableau de bord",
  Sessions:   "Sessions",
  Analysis:   "Analyse",
  Scenarios:  "Scénarios",
  Report:     "Rapport",
  Acquire:    "Acquisition",
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
  background: rgba(0,0,0,0.8);
  border-bottom: 1px solid #0e0e1c;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 50;
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.bc-root {
  font-size: 0.75rem;
  font-weight: 500;
  color: #55556a;
  letter-spacing: 0.01em;
}
.bc-sep {
  font-size: 0.75rem;
  color: #1a1a2e;
}
.bc-current {
  font-size: 0.75rem;
  font-weight: 600;
  color: #b8b8cc;
  letter-spacing: 0.01em;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.tb-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  font-weight: 600;
  color: #55556a;
  background: #080810;
  border: 1px solid #1a1a2e;
  border-radius: 7px;
  padding: 4px 12px;
  letter-spacing: 0.03em;
}
.tb-tag-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
}
</style>
