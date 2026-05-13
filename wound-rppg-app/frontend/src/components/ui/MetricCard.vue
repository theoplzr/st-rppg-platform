<template>
  <v-card class="glass-card metric-card" :style="{ borderColor: color + '44' }">
    <div class="metric-inner">
      <div class="metric-icon" :style="{ background: color + '22', color }">
        <v-icon :icon="icon" size="20" />
      </div>
      <div class="metric-content">
        <div class="metric-label">{{ label }}</div>
        <div class="metric-value" :style="{ color }">
          {{ value }}
          <span v-if="unit" class="metric-unit">{{ unit }}</span>
        </div>
        <div v-if="sub" class="metric-sub">{{ sub }}</div>
      </div>
    </div>
    <div v-if="trend !== undefined" class="metric-trend">
      <v-icon :color="trend >= 0 ? 'success' : 'error'" size="14">
        {{ trend >= 0 ? "mdi-trending-up" : "mdi-trending-down" }}
      </v-icon>
      <span :style="{ color: trend >= 0 ? 'var(--green)' : 'var(--danger)' }">
        {{ Math.abs(trend) }}
      </span>
    </div>
  </v-card>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number],
  unit:  String,
  sub:   String,
  icon:  { type: String, default: "mdi-chart-line" },
  color: { type: String, default: "var(--accent)" },
  trend: Number,
});
</script>

<style scoped>
.metric-card {
  padding: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 200, 255, 0.1) !important;
}
.metric-inner {
  display: flex;
  align-items: center;
  gap: 14px;
}
.metric-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.metric-label {
  font-size: 0.75rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 2px;
}
.metric-value {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
}
.metric-unit {
  font-size: 0.85rem;
  font-weight: 400;
  margin-left: 3px;
  color: var(--muted);
}
.metric-sub {
  font-size: 0.72rem;
  color: var(--muted);
  margin-top: 3px;
}
.metric-trend {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 0.75rem;
  margin-top: 8px;
}
</style>
