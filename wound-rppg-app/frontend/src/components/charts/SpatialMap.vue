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

    <div class="map-container" ref="containerRef" @click="onMapClick">
      <img
        v-if="currentMap"
        :src="`data:image/png;base64,${currentMap}`"
        class="map-image"
        :alt="activeTab"
        draggable="false"
      />
      <div v-else class="map-placeholder">
        <v-icon color="muted" size="40">mdi-image-off</v-icon>
        <span>Carte non disponible</span>
      </div>
      <!-- crosshair marker -->
      <div v-if="marker && currentMap" class="map-marker"
           :style="{ left: marker.x + '%', top: marker.y + '%' }" />
    </div>

    <div class="map-hint" v-if="currentMap">
      <v-icon size="11" color="#55556a">mdi-cursor-default-click-outline</v-icon>
      Cliquer sur la carte pour comparer POS local vs global
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

const emit = defineEmits(["pixel-click"]);

const tabs = [
  { key: "amplitude",  label: "Amplitude",  icon: "mdi-pulse" },
  { key: "phase",      label: "Phase",       icon: "mdi-rotate-3d" },
  { key: "snr",        label: "SNR",         icon: "mdi-signal" },
  { key: "coherence",  label: "Cohérence",   icon: "mdi-link-variant" },
];

const activeTab    = ref("amplitude");
const currentMap   = computed(() => props.maps[activeTab.value]);
const containerRef = ref(null);
const marker       = ref(null);

function onMapClick(event) {
  if (!currentMap.value) return;
  const rect = containerRef.value.getBoundingClientRect();
  const nx = Math.min(Math.max((event.clientX - rect.left)  / rect.width,  0), 1);
  const ny = Math.min(Math.max((event.clientY - rect.top)   / rect.height, 0), 1);
  marker.value = { x: nx * 100, y: ny * 100 };
  emit("pixel-click", { nx, ny });
}
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
  background: rgba(232,98,42,0.1);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
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
  position: relative;
  cursor: crosshair;
}
.map-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  image-rendering: pixelated;
  pointer-events: none;
}
.map-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 0.8rem;
}
.map-marker {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(232, 98, 42, 0.9);
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px rgba(232,98,42,0.5);
  transform: translate(-50%, -50%);
  pointer-events: none;
  animation: pulse-marker 1.2s ease-out forwards;
}
@keyframes pulse-marker {
  0%   { box-shadow: 0 0 0 0 rgba(232,98,42,0.7); }
  70%  { box-shadow: 0 0 0 8px rgba(232,98,42,0); }
  100% { box-shadow: 0 0 0 2px rgba(232,98,42,0.5); }
}
.map-hint {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.7rem;
  color: var(--muted);
  opacity: 0.7;
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
