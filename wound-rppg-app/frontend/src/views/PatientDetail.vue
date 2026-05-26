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
import { ref, onMounted } from "vue";
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
</style>
