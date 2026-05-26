<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title gradient-text">Patients</h1>
        <p class="page-sub">{{ patients.length }} patient{{ patients.length !== 1 ? 's' : '' }}</p>
      </div>
      <button class="btn-accent" @click="showCreate = true">
        <v-icon size="14">mdi-plus</v-icon> Nouveau patient
      </button>
    </div>

    <div v-if="loading" class="loading-block">
      <v-progress-circular indeterminate color="#e8622a" size="32" />
    </div>

    <div v-else-if="patients.length === 0" class="empty-block">
      <v-icon size="44" style="color: var(--border2)">mdi-account-group-outline</v-icon>
      <p>Aucun patient. Créez un patient pour regrouper vos sessions.</p>
    </div>

    <v-row v-else>
      <v-col v-for="p in patients" :key="p.id" cols="12" sm="6" md="4">
        <router-link :to="`/patients/${p.id}`" class="patient-card">
          <div class="pc-header">
            <div class="pc-avatar">{{ initials(p.name) }}</div>
            <div>
              <div class="pc-name">{{ p.name }}</div>
              <div class="pc-meta">{{ p.wound_type || 'Type non renseigné' }}</div>
            </div>
            <span class="pc-chip">{{ p.nb_sessions }} session{{ p.nb_sessions !== 1 ? 's' : '' }}</span>
          </div>
          <div v-if="p.notes" class="pc-notes">{{ p.notes }}</div>
          <div class="pc-footer">
            <span v-if="p.birth_year" class="pc-tag">{{ new Date().getFullYear() - p.birth_year }} ans</span>
            <span v-if="p.sex" class="pc-tag">{{ { M: 'Homme', F: 'Femme', O: 'Autre' }[p.sex] }}</span>
          </div>
        </router-link>
      </v-col>
    </v-row>

    <!-- Create dialog -->
    <v-dialog v-model="showCreate" max-width="480">
      <div class="dialog-card">
        <div class="dialog-head">
          <v-icon size="14" color="#e8622a">mdi-account-plus</v-icon>
          Nouveau patient
        </div>
        <div class="dialog-body">
          <v-text-field v-model="form.name" label="Nom / Identifiant *" density="compact" variant="outlined" hide-details class="mb-3" />
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px" class="mb-3">
            <v-text-field v-model.number="form.birth_year" label="Année de naissance" density="compact" variant="outlined" type="number" hide-details />
            <v-select v-model="form.sex" label="Sexe" :items="[{title:'Homme',value:'M'},{title:'Femme',value:'F'},{title:'Autre',value:'O'}]"
              density="compact" variant="outlined" hide-details clearable />
          </div>
          <v-text-field v-model="form.wound_type" label="Type de plaie / pathologie" density="compact" variant="outlined" hide-details class="mb-3"
            placeholder="Ex: ulcère veineux, plaie chirurgicale" />
          <v-textarea v-model="form.notes" label="Notes cliniques" density="compact" variant="outlined" hide-details rows="3" />
        </div>
        <div class="dialog-footer">
          <button class="btn-ghost" @click="showCreate = false">Annuler</button>
          <button class="btn-accent" @click="createPatient" :disabled="!form.name || saving">
            {{ saving ? 'Enregistrement…' : 'Créer' }}
          </button>
        </div>
      </div>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";
import { apiUrl } from "../lib/api.js";

const patients   = ref([]);
const loading    = ref(true);
const showCreate = ref(false);
const saving     = ref(false);
const form       = ref({ name: "", birth_year: null, sex: null, wound_type: "", notes: "" });

async function fetchPatients() {
  loading.value = true;
  try {
    const { data } = await axios.get(apiUrl("/patients/"));
    patients.value = data;
  } finally {
    loading.value = false;
  }
}

async function createPatient() {
  if (!form.value.name) return;
  saving.value = true;
  try {
    await axios.post(apiUrl("/patients/"), form.value);
    showCreate.value = false;
    form.value = { name: "", birth_year: null, sex: null, wound_type: "", notes: "" };
    await fetchPatients();
  } finally {
    saving.value = false;
  }
}

function initials(name) {
  return name.split(/\s+/).slice(0, 2).map(w => w[0].toUpperCase()).join("");
}

onMounted(fetchPatients);
</script>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:28px; gap:16px; }
.page-title  { font-size:2rem; font-weight:900; margin:0 0 4px; letter-spacing:-0.5px; }
.page-sub    { color:var(--muted); font-size:0.78rem; font-weight:500; }

.patient-card {
  display:block; text-decoration:none;
  background:var(--surface); border:1px solid var(--border); border-radius:12px;
  overflow:hidden; transition:border-color 0.2s, transform 0.15s;
  padding:16px;
}
.patient-card:hover { border-color:var(--border2); transform:translateY(-2px); }

.pc-header  { display:flex; align-items:center; gap:12px; margin-bottom:10px; }
.pc-avatar  { width:38px; height:38px; border-radius:50%; background:rgba(232,98,42,0.15); border:1px solid rgba(232,98,42,0.3); display:flex; align-items:center; justify-content:center; font-size:0.82rem; font-weight:800; color:var(--accent); flex-shrink:0; }
.pc-name    { font-size:0.88rem; font-weight:700; color:var(--text); }
.pc-meta    { font-size:0.72rem; color:var(--muted); }
.pc-chip    { margin-left:auto; font-size:0.68rem; font-weight:700; padding:2px 9px; border-radius:5px; background:rgba(6,182,212,0.1); color:#22d3ee; border:1px solid rgba(6,182,212,0.25); white-space:nowrap; }
.pc-notes   { font-size:0.75rem; color:var(--muted); margin-bottom:10px; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.pc-footer  { display:flex; gap:6px; flex-wrap:wrap; }
.pc-tag     { font-size:0.68rem; font-weight:600; padding:1px 8px; border-radius:4px; background:var(--surface2); color:var(--muted); border:1px solid var(--border); }

.loading-block { display:flex; justify-content:center; padding:60px; }
.empty-block   { display:flex; flex-direction:column; align-items:center; gap:12px; padding:80px 20px; color:var(--muted); font-size:0.88rem; text-align:center; }

/* Dialog */
.dialog-card   { background:var(--surface); border:1px solid var(--border); border-radius:14px; overflow:hidden; }
.dialog-head   { display:flex; align-items:center; gap:8px; padding:16px 20px; font-size:0.85rem; font-weight:700; color:var(--text); border-bottom:1px solid var(--border); background:var(--surface2); text-transform:uppercase; letter-spacing:0.5px; }
.dialog-body   { padding:20px; }
.dialog-footer { display:flex; justify-content:flex-end; gap:8px; padding:14px 20px; border-top:1px solid var(--border); }
</style>
