<template>
  <span class="quality-badge" :style="{ '--c': color }">
    <v-icon :icon="icon" size="12" :style="{ color }" />
    <span class="badge-label" :style="{ color }">{{ label }}</span>
    <span v-if="score !== undefined" class="badge-score">{{ score }}/100</span>
  </span>
</template>

<script setup>
import { computed } from "vue";
const props = defineProps({
  label: String,
  score: Number,
  color: { type: String, default: "#e8622a" },
});
const icon = computed(() => {
  if (props.label === "EXCELLENT") return "mdi-star";
  if (props.label === "GOOD")      return "mdi-check-circle";
  if (props.label === "POOR")      return "mdi-alert";
  return "mdi-close-circle";
});
</script>

<style scoped>
.quality-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--c, #e8622a) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--c, #e8622a) 30%, transparent);
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.4px;
}
.badge-label { }
.badge-score {
  opacity: 0.55;
  font-weight: 400;
  margin-left: 2px;
}
</style>
