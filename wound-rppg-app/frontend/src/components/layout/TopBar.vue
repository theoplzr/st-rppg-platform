<template>
  <v-app-bar
    flat
    style="background: rgba(13,17,23,0.95); border-bottom: 1px solid var(--border); backdrop-filter: blur(8px);"
  >
    <v-app-bar-title>
      <span style="color: var(--muted); font-size: 0.85rem;">
        {{ routeLabel }}
      </span>
    </v-app-bar-title>
    <template #append>
      <v-chip
        size="small"
        color="primary"
        variant="tonal"
        prepend-icon="mdi-flask"
        class="mr-3"
      >
        Wound-rPPG v1.0
      </v-chip>
    </template>
  </v-app-bar>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const labels = {
  Dashboard:  "Vue d'ensemble",
  Sessions:   "Sessions d'acquisition",
  Analysis:   "Analyse du signal",
  Scenarios:  "Comparaison de scénarios",
  Report:     "Rapport d'export",
};
const routeLabel = computed(() => labels[route.name] || route.name);
</script>
