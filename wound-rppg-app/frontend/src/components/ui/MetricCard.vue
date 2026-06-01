<template>
  <div class="metric-card" :style="{ '--c': color }">
    <div class="metric-glow" />
    <div class="metric-top">
      <div class="metric-icon">
        <v-icon :icon="icon" size="16" :style="{ color }" />
      </div>
    </div>
    <div class="metric-value" :style="{ color }">
      {{ value }}<span v-if="unit" class="metric-unit">{{ unit }}</span>
    </div>
    <div class="metric-label">{{ label }}</div>
    <div class="metric-bar" :style="{ background: color }" />
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number],
  unit:  String,
  icon:  { type: String, default: "mdi-chart-line" },
  color: { type: String, default: "var(--accent)" },
});
</script>

<style scoped>
.metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px 22px 16px;
  position: relative;
  overflow: hidden;
  transition: border-color 0.25s, box-shadow 0.25s, transform 0.15s, background 0.3s;
  cursor: default;
}
.metric-card:hover {
  border-color: color-mix(in srgb, var(--c, #e8622a) 35%, transparent);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--c, #e8622a) 10%, transparent),
              0 12px 32px var(--shadow);
  transform: translateY(-2px);
}
.metric-glow {
  position: absolute;
  top: -30px;
  right: -20px;
  width: 100px;
  height: 100px;
  background: radial-gradient(ellipse, color-mix(in srgb, var(--c, #e8622a) 20%, transparent) 0%, transparent 70%);
  pointer-events: none;
}
.metric-top   { margin-bottom: 16px; }
.metric-icon  {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--c, #e8622a) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--c, #e8622a) 20%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
}
.metric-value {
  font-family: 'Syne', 'Inter', sans-serif;
  font-size: 2rem;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 7px;
  letter-spacing: -0.04em;
}
.metric-unit {
  font-family: 'Inter', sans-serif;
  font-size: 0.82rem;
  font-weight: 400;
  margin-left: 4px;
  color: var(--muted);
  letter-spacing: 0;
}
.metric-label {
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.metric-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  opacity: 0.5;
}
</style>
