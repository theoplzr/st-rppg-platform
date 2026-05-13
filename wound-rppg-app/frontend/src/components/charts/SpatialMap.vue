<template>
  <div class="spatial-map-wrapper">
    <div class="map-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['map-tab', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <v-icon size="14">{{ tab.icon }}</v-icon>
        {{ tab.label }}
      </button>
    </div>
    <div class="map-container">
      <img
        v-if="currentMap"
        :src="`data:image/png;base64,${currentMap}`"
        class="map-image"
        :alt="activeTab"
      />
      <div v-else class="map-placeholder">
        <v-icon color="muted" size="40">mdi-image-off</v-icon>
        <span>Carte non disponible</span>
      </div>
    </div>
    <div class="map-legend">
      <span style="color: var(--muted)">Faible</span>
      <div class="legend-bar" />
      <span style="color: var(--muted)">Élevé</span>
    </div>
    <div v-if="stats" class="map-stats">
      <span>Moy: <b>{{ stats.mean?.toFixed(3) }}</b></span>
      <span>Max: <b>{{ stats.max?.toFixed(3) }}</b></span>
      <span>σ: <b>{{ stats.std?.toFixed(3) }}</b></span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  maps:  { type: Object, default: () => ({}) },
  stats: { type: Object, default: null },
});

const tabs = [
  { key: "amplitude",  label: "Amplitude",  icon: "mdi-pulse" },
  { key: "phase",      label: "Phase",       icon: "mdi-rotate-3d" },
  { key: "snr",        label: "SNR",         icon: "mdi-signal" },
  { key: "coherence",  label: "Cohérence",   icon: "mdi-link-variant" },
];

const activeTab  = ref("amplitude");
const currentMap = computed(() => props.maps[activeTab.value]);
</script>

<style scoped>
.spatial-map-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.map-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.map-tab {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--muted);
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.2s;
}
.map-tab:hover  { border-color: var(--accent); color: var(--text); }
.map-tab.active {
  background: rgba(0,200,255,0.1);
  border-color: var(--accent);
  color: var(--accent);
}
.map-container {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 10px;
  overflow: hidden;
  background: var(--surface2);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
}
.map-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  image-rendering: pixelated;
}
.map-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 0.8rem;
}
.map-legend {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.72rem;
}
.legend-bar {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(to right, #0d1117, #1a3a5c, #00c8ff, #7ee787, #f0883e, #f85149);
}
.map-stats {
  display: flex;
  gap: 16px;
  font-size: 0.76rem;
  color: var(--muted);
}
.map-stats b { color: var(--text); }
</style>
