<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title gradient-text">Scénarios</h1>
        <p class="page-sub">Comparaison multi-sessions · LCOMS</p>
      </div>
    </div>

    <div class="card-block mb-6">
      <div class="card-head">
        <v-icon size="13" color="#e8622a">mdi-select-multiple</v-icon>
        Sélectionner les sessions
      </div>
      <div style="padding: 18px">
        <v-row>
          <v-col cols="12" md="5">
            <v-select v-model="sessionA" :items="sessionOptions" label="Session A"
              density="compact" variant="outlined" prepend-inner-icon="mdi-alpha-a-circle-outline" />
          </v-col>
          <v-col cols="12" md="5">
            <v-select v-model="sessionB" :items="sessionOptions" label="Session B"
              density="compact" variant="outlined" prepend-inner-icon="mdi-alpha-b-circle-outline" />
          </v-col>
          <v-col cols="12" md="2">
            <button class="btn-accent" style="width:100%; height:40px; justify-content:center"
              :disabled="!sessionA || !sessionB || loading" @click="compare">
              <v-progress-circular v-if="loading" indeterminate size="14" width="2" color="white" />
              <span v-else>Comparer</span>
            </button>
          </v-col>
        </v-row>
      </div>
    </div>

    <template v-if="comparison">
      <v-row class="mb-5">
        <v-col cols="12" md="5">
          <div class="card-block" style="border-color: rgba(232,98,42,0.3)">
            <div class="card-head" style="color: var(--accent)">
              <v-icon size="13" color="#e8622a">mdi-alpha-a-circle</v-icon>
              {{ comparison.session_a.name }}
            </div>
            <div style="padding: 16px">
              <div class="cmp-rows">
                <div v-for="m in metricsA" :key="m.key" class="cmp-row">
                  <span class="cmp-label">{{ m.label }}</span>
                  <span class="cmp-val" :style="{ color: m.color }">{{ m.value }}<small> {{ m.unit }}</small></span>
                </div>
              </div>
              <QualityBadge :label="comparison.session_a.label" :score="comparison.session_a.score"
                :color="comparison.session_a.color" class="mt-3" />
            </div>
          </div>
        </v-col>

        <v-col cols="12" md="2">
          <div class="card-block" style="background: var(--surface2)">
            <div class="card-head justify-center">Δ diff</div>
            <div class="diff-col">
              <div v-for="d in diffMetrics" :key="d.key" class="diff-item">
                <span class="diff-label">{{ d.label }}</span>
                <span class="diff-val" :style="{ color: d.color }">
                  {{ d.value > 0 ? "+" : "" }}{{ d.value }}
                </span>
              </div>
            </div>
          </div>
        </v-col>

        <v-col cols="12" md="5">
          <div class="card-block" style="border-color: rgba(34,212,126,0.3)">
            <div class="card-head" style="color: var(--green)">
              <v-icon size="13" color="#22d47e">mdi-alpha-b-circle</v-icon>
              {{ comparison.session_b.name }}
            </div>
            <div style="padding: 16px">
              <div class="cmp-rows">
                <div v-for="m in metricsB" :key="m.key" class="cmp-row">
                  <span class="cmp-label">{{ m.label }}</span>
                  <span class="cmp-val" :style="{ color: m.color }">{{ m.value }}<small> {{ m.unit }}</small></span>
                </div>
              </div>
              <QualityBadge :label="comparison.session_b.label" :score="comparison.session_b.score"
                :color="comparison.session_b.color" class="mt-3" />
            </div>
          </div>
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="12" md="6">
          <div class="card-block">
            <div class="card-head"><v-icon size="13" color="#a78bfa">mdi-map-outline</v-icon>Carte ST-rPPG — A</div>
            <div style="padding: 14px"><SpatialMap :maps="comparison.maps_a||{}" /></div>
          </div>
        </v-col>
        <v-col cols="12" md="6">
          <div class="card-block">
            <div class="card-head"><v-icon size="13" color="#22d47e">mdi-map-outline</v-icon>Carte ST-rPPG — B</div>
            <div style="padding: 14px"><SpatialMap :maps="comparison.maps_b||{}" /></div>
          </div>
        </v-col>
      </v-row>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import axios from "axios";
import { useSessionStore } from "../stores/session.js";
import { apiUrl } from "../lib/api.js";
import QualityBadge from "../components/ui/QualityBadge.vue";
import SpatialMap   from "../components/charts/SpatialMap.vue";

const store      = useSessionStore();
const sessionA   = ref("");
const sessionB   = ref("");
const comparison = ref(null);
const loading    = ref(false);

onMounted(() => store.fetchSessions());
const sessionOptions = computed(() => store.sessions.map(s => ({ title: s.name, value: s.name })));

async function compare() {
  loading.value = true;
  try {
    const { data } = await axios.post(apiUrl("/scenarios/compare/two"), { session_a: sessionA.value, session_b: sessionB.value });
    comparison.value = data;
  } finally { loading.value = false; }
}

function mc(key, val) {
  if (key === "snr_db") return val >= 3 ? "var(--green)" : val >= 0 ? "var(--warn)" : "var(--danger)";
  if (key === "tms")    return val >= 0.96 ? "var(--green)" : "var(--warn)";
  return "var(--text2)";
}

const metricsA = computed(() => {
  if (!comparison.value) return [];
  const s = comparison.value.session_a;
  return [
    { key:"hr_bpm", label:"FC",    value: s.hr_bpm,                unit:"bpm",  color:"var(--warn)"  },
    { key:"snr_db", label:"SNR",   value: s.snr_db,                unit:"dB",   color: mc("snr_db", s.snr_db) },
    { key:"tms",    label:"TMS",   value:(s.tms*100).toFixed(1),   unit:"%",    color: mc("tms", s.tms) },
    { key:"score",  label:"Score", value: s.score,                  unit:"/100", color:"var(--accent)" },
  ];
});
const metricsB = computed(() => {
  if (!comparison.value) return [];
  const s = comparison.value.session_b;
  return [
    { key:"hr_bpm", label:"FC",    value: s.hr_bpm,                unit:"bpm",  color:"var(--warn)"  },
    { key:"snr_db", label:"SNR",   value: s.snr_db,                unit:"dB",   color: mc("snr_db", s.snr_db) },
    { key:"tms",    label:"TMS",   value:(s.tms*100).toFixed(1),   unit:"%",    color: mc("tms", s.tms) },
    { key:"score",  label:"Score", value: s.score,                  unit:"/100", color:"var(--accent)" },
  ];
});
const diffMetrics = computed(() => {
  if (!comparison.value) return [];
  const d = comparison.value.diff;
  return [
    { key:"hr_bpm", label:"FC",    value: d.hr_bpm, color:"var(--muted)" },
    { key:"snr_db", label:"SNR",   value: d.snr_db, color: d.snr_db>0?"var(--green)":"var(--danger)" },
    { key:"score",  label:"Score", value: d.score,  color: d.score>0?"var(--green)":"var(--danger)" },
  ];
});
</script>

<style scoped>
.cmp-rows { display: flex; flex-direction: column; gap: 8px; }
.cmp-row  { display: flex; justify-content: space-between; align-items: center; padding: 7px 0; border-bottom: 1px solid var(--border); }
.cmp-row:last-child { border-bottom: none; }
.cmp-label { font-size: 0.75rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px; }
.cmp-val   { font-size: 1.05rem; font-weight: 800; }
.cmp-val small { font-size: 0.72rem; font-weight: 400; color: var(--muted); }

.diff-col  { display: flex; flex-direction: column; gap: 20px; padding: 18px 12px; align-items: center; }
.diff-item { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.diff-label { font-size: 0.65rem; color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.diff-val   { font-size: 1.1rem; font-weight: 900; }
</style>
