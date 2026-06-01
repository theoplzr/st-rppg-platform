<template>
  <div>
    <div class="page-header">
      <div>
        <router-link to="/patients" class="back-link">
          <v-icon size="13">mdi-arrow-left</v-icon> Patients
        </router-link>
        <h1 class="page-title">{{ patient?.name }}</h1>
        <p class="page-sub" v-if="patient">{{ patient.wound_type || '' }}</p>
      </div>
      <div class="header-actions">
        <button class="btn-ghost btn-ghost--warn" @click="confirmDelete = true">
          <v-icon size="14">mdi-delete-outline</v-icon> Supprimer
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-block">
      <v-progress-circular indeterminate color="#e8622a" size="32" />
    </div>

    <template v-else-if="patient">
      <!-- Patient info card -->
      <v-row class="mb-5">
        <v-col cols="12" md="4">
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#e8622a">mdi-account-outline</v-icon>
              Informations cliniques
            </div>
            <div style="padding:16px; display:flex; flex-direction:column; gap:12px">
              <div v-if="editing">
                <v-text-field v-model="editForm.name"       label="Nom"        density="compact" variant="outlined" hide-details class="mb-3" />
                <v-text-field v-model.number="editForm.birth_year" label="Année naiss." density="compact" variant="outlined" type="number" hide-details class="mb-3" />
                <v-select     v-model="editForm.sex"        label="Sexe"       density="compact" variant="outlined" hide-details class="mb-3"
                  :items="[{title:'Homme',value:'M'},{title:'Femme',value:'F'},{title:'Autre',value:'O'}]" clearable />
                <v-text-field v-model="editForm.wound_type" label="Type plaie" density="compact" variant="outlined" hide-details class="mb-3" />
                <v-textarea   v-model="editForm.notes"      label="Notes"      density="compact" variant="outlined" hide-details rows="3" class="mb-3" />
                <div style="display:flex;gap:8px">
                  <button class="btn-accent-sm" @click="saveEdit" :disabled="saving">
                    {{ saving ? 'Sauvegarde…' : 'Enregistrer' }}
                  </button>
                  <button class="btn-ghost" style="padding:6px 12px;font-size:0.78rem" @click="editing=false">Annuler</button>
                </div>
              </div>
              <template v-else>
                <div class="info-row"><span class="info-label">Né(e) en</span><span>{{ patient.birth_year || '—' }}</span></div>
                <div class="info-row"><span class="info-label">Sexe</span><span>{{ { M:'Homme', F:'Femme', O:'Autre' }[patient.sex] || '—' }}</span></div>
                <div class="info-row"><span class="info-label">Type plaie</span><span>{{ patient.wound_type || '—' }}</span></div>
                <div class="info-row" v-if="patient.notes"><span class="info-label">Notes</span><span>{{ patient.notes }}</span></div>
                <button class="btn-ghost" style="align-self:flex-start;font-size:0.75rem;padding:5px 12px" @click="startEdit">
                  <v-icon size="12">mdi-pencil-outline</v-icon> Modifier
                </button>
              </template>
            </div>
          </div>
        </v-col>

        <!-- Assign unlinked sessions -->
        <v-col cols="12" md="8">
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#06b6d4">mdi-link-variant</v-icon>
              Associer des sessions
              <span style="font-size:0.68rem;color:var(--muted);font-weight:400;text-transform:none;letter-spacing:0;margin-left:4px">sessions sans patient</span>
            </div>
            <div style="padding:14px; max-height:200px; overflow-y:auto">
              <div v-if="unlinkedSessions.length === 0" style="font-size:0.8rem;color:var(--muted)">
                Toutes les sessions sont déjà associées à un patient.
              </div>
              <div v-for="s in unlinkedSessions" :key="s.name" class="link-row">
                <span class="link-name">{{ s.name }}</span>
                <span class="link-date">{{ formatDate(s.date) }}</span>
                <button class="btn-link" @click="attachSession(s.name)">
                  <v-icon size="12">mdi-plus-circle-outline</v-icon> Associer
                </button>
              </div>
            </div>
          </div>
        </v-col>
      </v-row>

      <!-- Healing timeline -->
      <template v-if="trendStats">
        <div class="section-title mt-5 mb-3">
          <v-icon size="12" color="#e8622a" style="margin-right:5px">mdi-chart-timeline-variant</v-icon>
          Timeline de guérison
        </div>

        <v-row class="mb-3">
          <v-col cols="6" sm="3">
            <div class="tl-stat">
              <div class="tl-stat-label">Sessions analysées</div>
              <div class="tl-stat-value">{{ trendStats.count }}</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="tl-stat">
              <div class="tl-stat-label">Score initial → actuel</div>
              <div class="tl-stat-value" :style="{ color: trendStats.delta > 5 ? 'var(--green)' : trendStats.delta < -5 ? 'var(--danger)' : 'var(--text)' }">
                {{ trendStats.firstScore ?? '—' }} → {{ trendStats.lastScore ?? '—' }}
                <span class="tl-delta">{{ trendStats.trend === 'up' ? '↑' : trendStats.trend === 'down' ? '↓' : '→' }} {{ trendStats.delta > 0 ? '+' : '' }}{{ trendStats.delta }}</span>
              </div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="tl-stat">
              <div class="tl-stat-label">Dernière FC</div>
              <div class="tl-stat-value">{{ trendStats.lastHr?.toFixed(0) ?? '—' }} <span class="tl-unit">bpm</span></div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="tl-stat">
              <div class="tl-stat-label">Dernier SNR</div>
              <div class="tl-stat-value" :style="{ color: (trendStats.lastSnr ?? 0) >= 3 ? 'var(--green)' : 'var(--warn)' }">
                {{ trendStats.lastSnr?.toFixed(1) ?? '—' }} <span class="tl-unit">dB</span>
              </div>
            </div>
          </v-col>
        </v-row>

        <div class="tl-chart-block mb-6">
          <v-chart :option="timelineOption" autoresize style="height:260px;width:100%" @click="onChartClick" />
          <div class="tl-hint">Cliquez sur un point pour ouvrir l'analyse · <span style="color:#e8622a">Score</span> · <span style="color:#22d3ee">SNR</span> · <span style="color:#a78bfa">FC</span></div>
        </div>
      </template>

      <!-- Sessions of this patient -->
      <div class="section-title">Sessions ({{ patient.sessions?.length || 0 }})</div>
      <div v-if="!patient.sessions?.length" class="empty-block" style="padding:40px 20px">
        <v-icon size="32" style="color:var(--border2)">mdi-folder-outline</v-icon>
        <p>Aucune session associée à ce patient.</p>
      </div>
      <v-row v-else>
        <v-col v-for="s in patient.sessions" :key="s.name" cols="12" sm="6" md="4">
          <router-link :to="`/analysis/${s.name}`" class="session-card">
            <div class="card-accent" :style="{ background: s.has_results ? 'var(--green)' : 'var(--warn)' }" />
            <div class="card-body">
              <div class="s-name">{{ s.name }}</div>
              <div class="s-date">{{ formatDate(s.date) }}</div>
              <div class="s-chips">
                <span v-if="s.fps" class="chip chip--blue">{{ s.fps?.toFixed(0) }} FPS</span>
                <span v-if="s.score" class="chip chip--teal">Score {{ s.score }}</span>
                <span v-if="s.snr_db" class="chip chip--gray">{{ s.snr_db }} dB</span>
              </div>
              <div v-if="s.scenario_label" class="s-tag">
                <v-icon size="10" color="#e8622a">mdi-tag-outline</v-icon>
                {{ s.scenario_label }}
              </div>
            </div>
          </router-link>
        </v-col>
      </v-row>
    </template>

    <!-- Delete confirmation -->
    <v-dialog v-model="confirmDelete" max-width="380">
      <div class="dialog-card">
        <div class="dialog-head" style="color:var(--danger)">
          <v-icon size="14" color="var(--danger)">mdi-delete-outline</v-icon>
          Supprimer le patient
        </div>
        <div style="padding:20px;font-size:0.85rem;color:var(--text2)">
          Supprimer <strong>{{ patient?.name }}</strong> ? Les sessions associées ne seront pas supprimées.
        </div>
        <div class="dialog-footer">
          <button class="btn-ghost" @click="confirmDelete = false">Annuler</button>
          <button class="btn-ghost btn-ghost--warn" @click="deletePatient">Supprimer</button>
        </div>
      </div>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import axios from "axios";
import { apiUrl } from "../lib/api.js";
import { useSessionStore } from "../stores/session.js";

const route   = useRoute();
const router  = useRouter();
const store   = useSessionStore();

const patient         = ref(null);
const loading         = ref(true);
const editing         = ref(false);
const saving          = ref(false);
const confirmDelete   = ref(false);
const editForm        = ref({});
const unlinkedSessions = ref([]);

async function fetchPatient() {
  loading.value = true;
  try {
    const { data } = await axios.get(apiUrl(`/patients/${route.params.id}`));
    patient.value = data;
    editForm.value = { name: data.name, birth_year: data.birth_year, sex: data.sex, wound_type: data.wound_type, notes: data.notes };
  } finally {
    loading.value = false;
  }
}

async function fetchUnlinked() {
  await store.fetchSessions();
  const linked = new Set((patient.value?.sessions || []).map(s => s.name));
  unlinkedSessions.value = store.sessions.filter(s => !linked.has(s.name));
}

function startEdit() {
  editing.value = true;
}

async function saveEdit() {
  saving.value = true;
  try {
    await axios.patch(apiUrl(`/patients/${route.params.id}`), editForm.value);
    editing.value = false;
    await fetchPatient();
  } finally {
    saving.value = false;
  }
}

async function attachSession(sessionName) {
  await axios.post(apiUrl(`/patients/${route.params.id}/sessions/${sessionName}`));
  await fetchPatient();
  await fetchUnlinked();
}

async function deletePatient() {
  await axios.delete(apiUrl(`/patients/${route.params.id}`));
  router.push("/patients");
}

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("fr-FR", { day:"2-digit", month:"short", year:"numeric" });
}

const healingSessions = computed(() => {
  if (!patient.value?.sessions) return [];
  return [...patient.value.sessions]
    .filter(s => s.score != null || s.snr_db != null)
    .sort((a, b) => new Date(a.date) - new Date(b.date));
});

const trendStats = computed(() => {
  const ss = healingSessions.value;
  if (ss.length < 2) return null;
  const first = ss[0], last = ss[ss.length - 1];
  const delta = Math.round((last.score ?? 0) - (first.score ?? 0));
  return {
    count:      ss.length,
    firstScore: first.score,
    lastScore:  last.score,
    delta,
    trend:   delta > 5 ? "up" : delta < -5 ? "down" : "stable",
    lastHr:  last.hr_bpm,
    lastSnr: last.snr_db,
  };
});

const timelineOption = computed(() => {
  const ss = healingSessions.value;
  if (ss.length < 2) return null;
  const dates     = ss.map(s => formatDate(s.date));
  const scores    = ss.map(s => s.score     ?? null);
  const snrs      = ss.map(s => s.snr_db    != null ? +s.snr_db.toFixed(1)    : null);
  const hrs       = ss.map(s => s.hr_bpm    != null ? +s.hr_bpm.toFixed(1)    : null);
  const woundPcts = ss.map(s => s.wound_pct != null ? +s.wound_pct.toFixed(1) : null);
  const hasWound  = woundPcts.some(v => v != null);
  const ax = {
    axisLine:  { lineStyle: { color: "#2a2a3e" } },
    axisTick:  { show: false },
    axisLabel: { color: "#8b8b9e", fontSize: 10 },
    splitLine: { lineStyle: { color: "#1e1e2e", type: "dashed" } },
  };
  return {
    backgroundColor: "transparent",
    grid: { top: 32, right: 52, bottom: 38, left: 46 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#16162a",
      borderColor: "#2a2a3e",
      textStyle: { color: "#c9c9e0", fontSize: 11 },
      formatter(params) {
        let h = `<div style="font-size:.72rem;font-weight:700;color:#8b8b9e;margin-bottom:4px">${params[0].axisValue}</div>`;
        params.forEach(p => {
          if (p.value == null) return;
          h += `<div style="display:flex;align-items:center;gap:6px;margin:2px 0">
            <span style="width:8px;height:8px;border-radius:50%;background:${p.color};display:inline-block"></span>
            <span>${p.seriesName}</span>
            <span style="font-weight:700;margin-left:auto;padding-left:12px">${p.value}</span></div>`;
        });
        return h;
      },
    },
    legend: {
      data: ["Score", "SNR (dB)", "FC (bpm)", ...(hasWound ? ["Plaie (%)"] : [])],
      textStyle: { color: "#8b8b9e", fontSize: 10 },
      top: 4, right: 8, itemWidth: 12, itemHeight: 8,
    },
    xAxis: { type: "category", data: dates, ...ax, axisLabel: { ...ax.axisLabel, rotate: dates.length > 5 ? 25 : 0 } },
    yAxis: [
      { min: 0, max: 100, ...ax },
      { ...ax, splitLine: { show: false } },
    ],
    series: [
      {
        name: "Score", type: "line", yAxisIndex: 0, data: scores, smooth: true,
        symbol: "circle", symbolSize: 7,
        lineStyle: { color: "#e8622a", width: 2.5 },
        itemStyle: { color: "#e8622a" },
        areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "rgba(232,98,42,.22)" }, { offset: 1, color: "rgba(232,98,42,.01)" }] } },
      },
      {
        name: "SNR (dB)", type: "line", yAxisIndex: 1, data: snrs, smooth: true,
        symbol: "circle", symbolSize: 5,
        lineStyle: { color: "#22d3ee", width: 1.8 },
        itemStyle: { color: "#22d3ee" },
      },
      {
        name: "FC (bpm)", type: "line", yAxisIndex: 1, data: hrs, smooth: true,
        symbol: "circle", symbolSize: 5,
        lineStyle: { color: "#a78bfa", width: 1.8 },
        itemStyle: { color: "#a78bfa" },
      },
      ...(hasWound ? [{
        name: "Plaie (%)", type: "line", yAxisIndex: 0, data: woundPcts, smooth: true,
        symbol: "circle", symbolSize: 5,
        lineStyle: { color: "#f43f5e", width: 1.8, type: "dashed" },
        itemStyle: { color: "#f43f5e" },
      }] : []),
    ],
  };
});

function onChartClick(params) {
  if (params.componentType === "series") {
    const session = healingSessions.value[params.dataIndex];
    if (session) router.push(`/analysis/${session.name}`);
  }
}

onMounted(async () => {
  await fetchPatient();
  await fetchUnlinked();
});
</script>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:28px; gap:16px; }
.back-link { display:inline-flex; align-items:center; gap:5px; font-size:0.75rem; color:var(--muted); text-decoration:none; margin-bottom:6px; transition:color 0.15s; }
.back-link:hover { color:var(--accent); }
.page-title { font-size:1.4rem; font-weight:900; color:var(--text); margin:0 0 4px; }
.page-sub   { color:var(--muted); font-size:0.78rem; }
.header-actions { display:flex; gap:8px; }

.section-title { font-size:0.8rem; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:14px; }

/* Info rows */
.info-row { display:flex; justify-content:space-between; align-items:center; font-size:0.82rem; color:var(--text2); padding:6px 0; border-bottom:1px solid var(--border); }
.info-row:last-of-type { border-bottom:none; }
.info-label { font-size:0.68rem; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:0.4px; }

/* Link sessions */
.link-row  { display:flex; align-items:center; gap:8px; padding:6px 0; border-bottom:1px solid var(--border); font-size:0.8rem; }
.link-row:last-child { border-bottom:none; }
.link-name { flex:1; color:var(--text2); font-weight:500; }
.link-date { font-size:0.7rem; color:var(--muted); }
.btn-link  { display:flex; align-items:center; gap:4px; font-size:0.72rem; font-weight:600; padding:3px 8px; border-radius:5px; background:rgba(232,98,42,0.1); color:var(--accent); border:1px solid rgba(232,98,42,0.25); cursor:pointer; font-family:inherit; transition:opacity 0.15s; }
.btn-link:hover { opacity:0.8; }

/* Session cards */
.session-card { display:block; background:var(--surface); border:1px solid var(--border); border-radius:12px; text-decoration:none; overflow:hidden; transition:border-color 0.2s, transform 0.15s; }
.session-card:hover { border-color:var(--border2); transform:translateY(-2px); }
.card-accent { height:2px; width:100%; }
.card-body   { padding:14px; }
.s-name  { font-size:0.82rem; font-weight:700; color:var(--text); word-break:break-all; margin-bottom:2px; }
.s-date  { font-size:0.7rem; color:var(--muted); margin-bottom:8px; }
.s-chips { display:flex; gap:5px; flex-wrap:wrap; margin-bottom:6px; }
.chip { font-size:0.68rem; font-weight:600; padding:2px 7px; border-radius:4px; }
.chip--blue { background:rgba(2,132,199,0.12); color:#38bdf8; border:1px solid rgba(2,132,199,0.2); }
.chip--teal { background:rgba(6,182,212,0.1); color:#22d3ee; border:1px solid rgba(6,182,212,0.2); }
.chip--gray { background:var(--surface2); color:var(--muted); border:1px solid var(--border); }
.s-tag { display:flex; align-items:center; gap:4px; font-size:0.72rem; color:var(--accent); font-weight:500; }

/* Dialog */
.dialog-card   { background:var(--surface); border:1px solid var(--border); border-radius:14px; overflow:hidden; }
.dialog-head   { display:flex; align-items:center; gap:8px; padding:14px 20px; font-size:0.82rem; font-weight:700; color:var(--text); border-bottom:1px solid var(--border); background:var(--surface2); text-transform:uppercase; letter-spacing:0.5px; }
.dialog-footer { display:flex; justify-content:flex-end; gap:8px; padding:12px 20px; border-top:1px solid var(--border); }

.loading-block { display:flex; justify-content:center; padding:60px; }
.empty-block   { display:flex; flex-direction:column; align-items:center; gap:12px; color:var(--muted); font-size:0.88rem; text-align:center; }

.btn-accent-sm { padding:7px 14px; border-radius:7px; background:var(--accent); color:#fff; font-size:0.78rem; font-weight:600; border:none; cursor:pointer; transition:opacity 0.15s; font-family:inherit; }
.btn-accent-sm:hover { opacity:0.85; }
.btn-accent-sm:disabled { opacity:0.4; cursor:default; }

/* Timeline */
.tl-stat {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 16px;
  height: 100%;
}
.tl-stat-label { font-size: 0.68rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 4px; }
.tl-stat-value { font-size: 1.05rem; font-weight: 800; color: var(--text); display: flex; align-items: baseline; gap: 5px; }
.tl-unit  { font-size: 0.7rem; font-weight: 500; color: var(--muted); }
.tl-delta { font-size: 0.72rem; font-weight: 700; margin-left: 4px; }

.tl-chart-block {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 8px 4px;
}
.tl-hint {
  font-size: 0.68rem;
  color: var(--muted);
  text-align: center;
  padding: 6px 0 8px;
}
</style>
