<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title gradient-text">Patients</h1>
        <p class="page-sub">{{ patients.length }} patient{{ patients.length !== 1 ? 's' : '' }} enregistrés</p>
      </div>
      <button class="btn-accent" @click="showCreate = true">
        <svg width="13" height="13" viewBox="0 0 14 14" fill="none"><path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
        Nouveau patient
      </button>
    </div>

    <div v-if="loading" class="state-loading">
      <v-progress-circular indeterminate color="var(--accent)" size="28" width="2" />
      <span>Chargement…</span>
    </div>

    <div v-else-if="patients.length === 0" class="state-empty">
      <div class="empty-icon-wrap">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" stroke-width="1.3" stroke-linecap="round">
          <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
        </svg>
      </div>
      <p class="empty-title">Aucun patient</p>
      <p class="empty-sub">Créez un dossier patient pour regrouper vos sessions d'acquisition</p>
      <button class="btn-accent" @click="showCreate = true" style="margin-top:12px;font-size:0.78rem">
        <svg width="12" height="12" viewBox="0 0 14 14" fill="none"><path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
        Créer un patient
      </button>
    </div>

    <div v-else class="patient-grid">
      <router-link
        v-for="(p, i) in patients"
        :key="p.id"
        :to="`/patients/${p.id}`"
        class="patient-card"
        :style="{ animationDelay: `${i * 55}ms` }"
      >
        <div class="pc-top">
          <div class="pc-avatar" :style="{ '--avatar-hue': avatarHue(p.name) }">{{ initials(p.name) }}</div>
          <div class="pc-info">
            <div class="pc-name">{{ p.name }}</div>
            <div class="pc-type">{{ p.wound_type || 'Type non renseigné' }}</div>
          </div>
          <div class="pc-sessions-badge">
            {{ p.nb_sessions }}<span class="pc-sessions-unit"> sess.</span>
          </div>
        </div>

        <div v-if="p.notes" class="pc-notes">{{ p.notes }}</div>

        <div class="pc-footer">
          <span v-if="p.birth_year" class="pc-pill">
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><circle cx="5" cy="5" r="4" stroke="currentColor" stroke-width="1.2"/><path d="M5 3v2.5L7 7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
            {{ new Date().getFullYear() - p.birth_year }} ans
          </span>
          <span v-if="p.sex" class="pc-pill">{{ { M: 'Homme', F: 'Femme', O: 'Autre' }[p.sex] }}</span>
          <span class="pc-arrow">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M4 2l4 4-4 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </span>
        </div>
      </router-link>
    </div>

    <!-- Create dialog -->
    <v-dialog v-model="showCreate" max-width="500">
      <div class="dialog-card">
        <div class="dialog-head">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="color:var(--accent)">
            <circle cx="8" cy="6" r="3" stroke="currentColor" stroke-width="1.4"/>
            <path d="M2 14c0-3.3 2.7-6 6-6s6 2.7 6 6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <path d="M11 3h4M13 1v4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          Nouveau dossier patient
        </div>
        <div class="dialog-body">
          <div class="form-field">
            <label class="form-label">Nom / Identifiant <span class="form-required">*</span></label>
            <v-text-field v-model="form.name" placeholder="Ex: Patient_001" density="compact" variant="outlined" hide-details />
          </div>
          <div class="form-row">
            <div class="form-field">
              <label class="form-label">Année de naissance</label>
              <v-text-field v-model.number="form.birth_year" placeholder="1985" density="compact" variant="outlined" type="number" hide-details />
            </div>
            <div class="form-field">
              <label class="form-label">Sexe</label>
              <v-select v-model="form.sex" :items="[{title:'Homme',value:'M'},{title:'Femme',value:'F'},{title:'Autre',value:'O'}]"
                density="compact" variant="outlined" hide-details clearable />
            </div>
          </div>
          <div class="form-field">
            <label class="form-label">Type de plaie / pathologie</label>
            <v-text-field v-model="form.wound_type" placeholder="Ex: ulcère veineux, plaie chirurgicale" density="compact" variant="outlined" hide-details />
          </div>
          <div class="form-field">
            <label class="form-label">Notes cliniques</label>
            <v-textarea v-model="form.notes" placeholder="Antécédents, remarques…" density="compact" variant="outlined" hide-details rows="3" />
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-ghost" @click="showCreate = false">Annuler</button>
          <button class="btn-accent" @click="createPatient" :disabled="!form.name || saving">
            <v-progress-circular v-if="saving" indeterminate size="12" width="2" color="white" />
            <span v-else>Créer le patient</span>
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

function avatarHue(name) {
  let h = 0;
  for (let c of name) h = (h * 31 + c.charCodeAt(0)) % 360;
  return h;
}

onMounted(fetchPatients);
</script>

<style scoped>
/* Grid */
.patient-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
@media (max-width: 1000px) { .patient-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 560px)  { .patient-grid { grid-template-columns: 1fr; } }

/* Card */
.patient-card {
  display: flex;
  flex-direction: column;
  gap: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  text-decoration: none;
  overflow: hidden;
  transition: border-color 0.2s, transform 0.18s, box-shadow 0.2s, background 0.3s;
  animation: fadeInUp 0.45s ease both;
  padding: 18px 18px 14px;
}
.patient-card:hover {
  border-color: rgba(232,98,42,0.25);
  transform: translateY(-3px);
  box-shadow: 0 8px 28px var(--shadow);
}
.patient-card:hover .pc-arrow { color: var(--accent); transform: translateX(2px); }

.pc-top {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.pc-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: oklch(from hsl(var(--avatar-hue), 60%, 50%) l c h / 0.15);
  border: 1.5px solid oklch(from hsl(var(--avatar-hue), 60%, 50%) l c h / 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.82rem;
  font-weight: 800;
  color: var(--accent);
  flex-shrink: 0;
  background: rgba(232,98,42,0.12);
  border: 1.5px solid rgba(232,98,42,0.25);
}
.pc-info { flex: 1; min-width: 0; }
.pc-name { font-size: 0.9rem; font-weight: 700; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pc-type { font-size: 0.72rem; color: var(--muted); margin-top: 2px; }
.pc-sessions-badge {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--teal);
  letter-spacing: -0.04em;
  font-family: 'Syne', sans-serif;
  flex-shrink: 0;
}
.pc-sessions-unit { font-size: 0.62rem; font-weight: 500; color: var(--muted); }

.pc-notes {
  font-size: 0.74rem;
  color: var(--muted);
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}

.pc-footer { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: auto; }
.pc-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.68rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 5px;
  background: var(--surface2);
  color: var(--text2);
  border: 1px solid var(--border);
}
.pc-arrow { margin-left: auto; color: var(--border2); transition: color 0.15s, transform 0.15s; }

/* States */
.state-loading { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 80px 20px; color: var(--muted); font-size: 0.83rem; }
.state-empty   { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 80px 20px; text-align: center; }
.empty-icon-wrap { width: 56px; height: 56px; border-radius: 16px; background: var(--surface2); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; margin-bottom: 6px; }
.empty-title { font-size: 0.92rem; font-weight: 700; color: var(--text2); margin: 0; }
.empty-sub   { font-size: 0.76rem; color: var(--muted); margin: 0; max-width: 300px; }

/* Dialog */
.dialog-card { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; }
.dialog-head { display: flex; align-items: center; gap: 8px; padding: 18px 22px; font-size: 0.88rem; font-weight: 700; color: var(--text); border-bottom: 1px solid var(--border); }
.dialog-body { padding: 22px; display: flex; flex-direction: column; gap: 16px; }
.form-field { display: flex; flex-direction: column; gap: 6px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-label { font-size: 0.73rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
.form-required { color: var(--accent); }
.dialog-footer { display: flex; justify-content: flex-end; gap: 8px; padding: 16px 22px; border-top: 1px solid var(--border); background: var(--surface2); }
</style>
