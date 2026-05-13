<template>
  <div class="quality-badge" :style="{ background: color + '22', borderColor: color, color }">
    <v-icon :icon="icon" size="14" />
    <span>{{ label }}</span>
    <span v-if="score !== undefined" class="badge-score">{{ score }}/100</span>
  </div>
</template>

<script setup>
import { computed } from "vue";
const props = defineProps({
  label: String,
  score: Number,
  color: { type: String, default: "#00c8ff" },
});
const icon = computed(() => {
  if (props.label === "EXCELLENT") return "mdi-star";
  if (props.label === "BON")       return "mdi-check-circle";
  if (props.label === "FAIBLE")    return "mdi-alert";
  return "mdi-close-circle";
});
</script>

<style scoped>
.quality-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 20px;
  border: 1px solid;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.badge-score {
  opacity: 0.7;
  font-weight: 400;
}
</style>
