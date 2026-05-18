<template>
  <div>
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title gradient-text">Acquisition</h1>
        <p class="page-sub">Protocole ST-rPPG · POS (Wang 2017) · 512 × 512</p>
      </div>
      <span v-if="phase === 'done'" class="done-badge">
        <v-icon size="13" color="#22d47e">mdi-check-circle</v-icon> Session enregistrée
      </span>
    </div>

    <!-- Mode tabs -->
    <div class="acq-tabs mb-5">
      <button :class="['acq-tab', { active: mode === 'camera' }]" :disabled="phase !== 'idle'"
        @click="mode = 'camera'">
        <v-icon size="14">mdi-record-circle-outline</v-icon> Caméra live
      </button>
      <button :class="['acq-tab', { active: mode === 'upload' }]" :disabled="phase !== 'idle'"
        @click="mode = 'upload'">
        <v-icon size="14">mdi-folder-upload-outline</v-icon> Session existante
      </button>
    </div>

    <!-- ── CAMERA MODE ── -->
    <template v-if="mode === 'camera'">
      <v-row>
        <!-- Camera preview -->
        <v-col cols="12" md="7">
          <div class="card-block" style="position: relative; overflow: hidden">
            <div class="camera-wrapper">
              <video ref="videoEl" autoplay playsinline muted class="camera-video" />
              <canvas ref="canvasEl" :width="CFG.width" :height="CFG.height" style="display:none" />

              <div v-if="!cameraReady && !cameraError" class="camera-overlay">
                <v-progress-circular indeterminate color="primary" size="48" />
                <p class="mt-3" style="color:var(--muted)">Initialisation de la caméra…</p>
              </div>

              <div v-if="cameraError" class="camera-overlay">
                <v-icon size="56" color="error">mdi-camera-off</v-icon>
                <p class="mt-3" style="color:var(--danger)">{{ cameraError }}</p>
                <button class="btn-ghost mt-3" @click="initCamera">Réessayer</button>
              </div>

              <div v-if="phase === 'recording'" class="rec-badge">
                <span class="pulse">●</span> REC
              </div>

              <transition name="fade">
                <div v-if="countdown > 0" class="countdown-overlay">{{ countdown }}</div>
              </transition>

              <div v-if="phase === 'recording'" class="video-progress">
                <div class="video-progress-fill" :style="{ width: progressPct + '%' }" />
              </div>
            </div>

            <div v-if="phase === 'recording'" class="frame-bar">
              <v-icon size="15" style="color:var(--accent)">mdi-image-multiple</v-icon>
              <span class="frame-count">{{ capturedFrames }}</span>
              <span style="color:var(--muted)"> / {{ totalFrames }} frames</span>
              <span class="ml-auto" style="color:var(--muted); font-size:0.8rem">
                {{ elapsedSec.toFixed(1) }} s / {{ recordDuration }} s
              </span>
            </div>
          </div>
        </v-col>

        <!-- Controls -->
        <v-col cols="12" md="5">
          <div class="card-block mb-3">
            <div class="card-head">
              <v-icon size="13" color="#e8622a">mdi-tune</v-icon>
              Protocole d'acquisition
            </div>
            <div style="padding: 16px">
              <div class="param-grid mb-4">
                <div class="param-item">
                  <div class="param-label">Résolution</div>
                  <div class="param-value">{{ CFG.width }} × {{ CFG.height }}</div>
                </div>
                <div class="param-item">
                  <div class="param-label">Format</div>
                  <div class="param-value">PNG</div>
                </div>
                <div class="param-item">
                  <div class="param-label">Durée</div>
                  <div class="param-value">{{ recordDuration }} s</div>
                </div>
                <div class="param-item">
                  <div class="param-label">Frames totales</div>
                  <div class="param-value">{{ totalFrames }}</div>
                </div>
              </div>

              <!-- FPS selector -->
              <div class="param-label mb-2">Cadence (FPS)</div>
              <v-btn-toggle v-model="recordFps" mandatory density="compact"
                color="primary" variant="outlined" :disabled="phase !== 'idle'" class="mb-4">
                <v-btn :value="25">25 FPS</v-btn>
                <v-btn :value="30">30 FPS</v-btn>
                <v-btn :value="50">50 FPS <v-chip size="x-small" color="primary" variant="tonal" class="ml-1">Lab</v-chip></v-btn>
                <v-btn :value="60">60 FPS</v-btn>
              </v-btn-toggle>

              <!-- Duration slider -->
              <div class="d-flex justify-space-between mb-1">
                <span style="font-size:0.78rem; color:var(--muted)">Durée d'enregistrement</span>
                <span style="font-size:0.78rem; color:var(--accent); font-weight:600">{{ recordDuration }} s</span>
              </div>
              <v-slider v-model="recordDuration" :min="10" :max="60" :step="5"
                color="primary" track-color="border" hide-details
                :disabled="phase !== 'idle'" density="compact" class="mb-1" />
              <div class="d-flex justify-space-between mb-4" style="font-size:0.7rem; color:var(--muted)">
                <span>10 s</span><span>60 s</span>
              </div>

              <div style="height:1px; background:var(--border); margin-bottom:16px" />
              <v-text-field
                v-model="sessionLabel"
                label="Identifiant de session (optionnel)"
                placeholder="Ex: plaie_J3, paume_droite"
                density="compact"
                variant="outlined"
                :disabled="phase !== 'idle'"
                prepend-inner-icon="mdi-tag-outline"
                hide-details
              />
            </div>
          </div>

          <button v-if="phase === 'idle'" class="btn-accent" style="width:100%; justify-content:center; padding:14px"
            :disabled="!cameraReady" @click="startCountdown">
            <v-icon size="16">mdi-record-circle-outline</v-icon>
            Lancer l'acquisition
          </button>

          <button v-if="phase === 'recording'" class="btn-stop" style="width:100%" @click="abortRecording">
            <v-icon size="16">mdi-stop-circle-outline</v-icon>
            Arrêter
          </button>

          <div v-if="phase !== 'idle' && phase !== 'recording'" class="card-block mt-3">
            <div class="status-row" style="padding: 14px 16px">
              <v-progress-circular v-if="phase !== 'done' && phase !== 'error'"
                indeterminate color="primary" size="20" width="2" class="mr-3" />
              <v-icon v-else-if="phase === 'done'" size="20" style="color:var(--green)" class="mr-3">mdi-check-circle</v-icon>
              <v-icon v-else size="20" style="color:var(--danger)" class="mr-3">mdi-alert-circle</v-icon>
              <span :style="{ color: phase === 'error' ? 'var(--danger)' : phase === 'done' ? 'var(--green)' : 'var(--accent)', fontSize: '0.85rem' }">
                {{ statusMessage }}
              </span>
            </div>
            <div v-if="phase === 'uploading' && uploadProgress > 0" style="padding: 0 16px 14px">
              <div class="progress-track">
                <div class="progress-fill" :style="{ width: uploadProgress + '%' }" />
              </div>
            </div>
          </div>
        </v-col>
      </v-row>
    </template>

    <!-- ── UPLOAD MODE ── -->
    <template v-if="mode === 'upload'">
      <v-row justify="center">
        <v-col cols="12" md="8">
          <div
            class="drop-zone"
            :class="{ 'drop-zone--active': isDragging, 'drop-zone--disabled': phase !== 'idle' }"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @drop.prevent="onDrop"
            @click="phase === 'idle' && fileInput.click()"
          >
            <input ref="fileInput" type="file" accept=".zip,.avi" style="display:none"
                   @change="onFileChange" />

            <template v-if="phase === 'idle'">
              <v-icon size="52" color="primary" class="mb-4">mdi-folder-upload-outline</v-icon>
              <div class="drop-title">Déposer la session ici</div>
              <div class="drop-sub mb-4">ou cliquer pour sélectionner le fichier</div>
              <div class="d-flex gap-2 justify-center mb-3">
                <span class="format-chip">
                  <v-icon size="12">mdi-zip-box</v-icon> ZIP
                </span>
                <span class="format-chip format-chip--teal">
                  <v-icon size="12">mdi-video</v-icon> AVI
                </span>
              </div>
              <div class="drop-sub">Session exportée depuis le protocole d'acquisition · conversion automatique</div>
            </template>

            <template v-else-if="phase !== 'done' && phase !== 'error'">
              <v-progress-circular indeterminate color="primary" size="48" class="mb-4" />
              <div class="drop-title" style="color:var(--accent)">{{ statusMessage }}</div>
              <div v-if="phase === 'uploading' && uploadProgress > 0" class="mt-4" style="width:100%;max-width:300px">
                <div class="progress-track">
                  <div class="progress-fill" :style="{ width: uploadProgress + '%' }" />
                </div>
              </div>
            </template>

            <template v-else-if="phase === 'done'">
              <v-icon size="52" style="color:var(--green)" class="mb-4">mdi-check-circle</v-icon>
              <div class="drop-title" style="color:var(--green)">Analyse terminée</div>
            </template>

            <template v-else>
              <v-icon size="52" style="color:var(--danger)" class="mb-4">mdi-alert-circle</v-icon>
              <div class="drop-title" style="color:var(--danger)">{{ statusMessage }}</div>
              <button class="btn-ghost mt-4" @click.stop="resetAcquisition">Réessayer</button>
            </template>
          </div>
        </v-col>
      </v-row>
    </template>

    <!-- Results -->
    <transition name="slide-up">
      <div v-if="analysisResult" class="mt-6">
        <div style="height:1px; background:var(--border); margin-bottom:28px" />

        <!-- Quality verdict banner -->
        <div class="card-block mb-5" :style="{ borderColor: qualityColor }">
          <div class="verdict-banner">
            <div class="verdict-icon" :style="{ background: qualityColor + '18', borderColor: qualityColor + '44' }">
              <v-icon :style="{ color: qualityColor }" size="28">{{ qualityIcon }}</v-icon>
            </div>
            <div class="verdict-text">
              <div class="verdict-label" :style="{ color: qualityColor }">
                {{ analysisResult.quality?.label }}
              </div>
              <div class="verdict-sub">
                Score qualité : <strong :style="{ color: qualityColor }">{{ analysisResult.quality?.score }}</strong> / 100
                &nbsp;·&nbsp; FC estimée : <strong style="color:var(--warn)">{{ analysisResult.hr?.hr_bpm }} bpm</strong>
              </div>
              <div v-if="!analysisResult.quality?.recommendations?.length" class="verdict-ok">
                <v-icon size="12" style="color:var(--green)">mdi-check-circle</v-icon>
                Signal de bonne qualité — aucune recommandation
              </div>
              <div v-for="r in analysisResult.quality?.recommendations" :key="r" class="verdict-rec">
                <v-icon size="12" style="color:var(--warn)">mdi-arrow-right-circle-outline</v-icon> {{ r }}
              </div>
            </div>
            <router-link :to="`/analysis/${currentSession}`" class="btn-ghost btn-ghost--accent ml-auto">
              <v-icon size="14">mdi-open-in-new</v-icon> Analyse complète
            </router-link>
          </div>
        </div>

        <!-- Metric cards -->
        <v-row class="mb-5">
          <v-col v-for="m in resultMetrics" :key="m.label" cols="6" md="3">
            <MetricCard v-bind="m" />
          </v-col>
        </v-row>

        <!-- Signal + FFT -->
        <v-row>
          <v-col cols="12" md="8">
            <div class="card-block">
              <div class="card-head">
                <v-icon size="13" color="#e8622a">mdi-pulse</v-icon>
                Signal rPPG
                <span class="head-tag" :style="{ background: analysisResult.tms?.is_clean ? 'rgba(34,212,126,0.1)' : 'rgba(245,158,11,0.1)', color: analysisResult.tms?.is_clean ? 'var(--green)' : 'var(--warn)', borderColor: analysisResult.tms?.is_clean ? 'rgba(34,212,126,0.3)' : 'rgba(245,158,11,0.3)' }">
                  {{ analysisResult.tms?.is_clean ? 'Morphologie propre' : 'Morphologie irrégulière' }}
                </span>
              </div>
              <div style="padding: 12px 8px 8px">
                <SignalChart :time="analysisResult.signal?.time||[]" :raw="analysisResult.signal?.raw||[]"
                  :filtered="analysisResult.signal?.filt||[]" :peaks="analysisResult.signal?.peaks||[]"
                  :hrBpm="analysisResult.hr?.hr_bpm" :height="200" />
              </div>
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="card-block">
              <div class="card-head">
                <v-icon size="13" color="#06b6d4">mdi-chart-bell-curve</v-icon>
                Spectre fréquentiel
              </div>
              <div style="padding: 12px 8px 8px">
                <FFTChart :freq="analysisResult.hr?.freq||[]" :fft="analysisResult.hr?.fft||[]"
                  :hrHz="analysisResult.hr?.hr_hz" :hrBpm="analysisResult.hr?.hr_bpm" :height="200" />
              </div>
            </div>
          </v-col>
        </v-row>

        <div class="text-center mt-5">
          <button class="btn-ghost" @click="resetAcquisition">
            <v-icon size="14">mdi-refresh</v-icon> Nouvelle acquisition
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import axios from "axios";
import JSZip from "jszip";
import MetricCard  from "../components/ui/MetricCard.vue";
import SignalChart from "../components/charts/SignalChart.vue";
import FFTChart    from "../components/charts/FFTChart.vue";
import { apiUrl } from "../lib/api.js";

// Acquisition protocol — resolution matches colleagues' OpenCV script (512×512)
// fps and duration are user-configurable
const CFG = { width: 512, height: 512 };

const recordFps      = ref(50);  // default matches lab camera (50fps)
const recordDuration = ref(30);  // seconds — minimum 30s for reliable rPPG
const totalFrames    = computed(() => recordFps.value * recordDuration.value);

// Refs — DOM
const videoEl   = ref(null);
const canvasEl  = ref(null);
const fileInput = ref(null);

// State
const mode           = ref("camera");  // "camera" | "upload"
const isDragging     = ref(false);
const cameraReady    = ref(false);
const cameraError    = ref("");
const sessionLabel   = ref("");
const phase          = ref("idle");   // idle | countdown | recording | packaging | uploading | analyzing | done | error
const countdown      = ref(0);
const capturedFrames = ref(0);
const elapsedSec     = ref(0);
const uploadProgress = ref(0);
const currentSession = ref("");
const analysisResult = ref(null);
const statusMessage  = ref("");

// Camera stream
let stream       = null;
let captureTimer = null;
let elapsedTimer = null;

// Captured data
let frames     = [];
let timestamps = [];
let startTime  = null;

// ── Camera setup ──────────────────────────────────────────
async function initCamera() {
  cameraError.value = "";
  cameraReady.value = false;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width:     { ideal: CFG.width },
        height:    { ideal: CFG.height },
        frameRate: { ideal: recordFps.value },
      },
      audio: false,
    });
    videoEl.value.srcObject = stream;
    await new Promise(r => (videoEl.value.onloadedmetadata = r));
    cameraReady.value = true;
  } catch (e) {
    cameraError.value = e.name === "NotAllowedError"
      ? "Accès à la caméra refusé. Autorisez l'accès dans les paramètres du navigateur."
      : `Erreur caméra : ${e.message}`;
  }
}

// ── Countdown then record ─────────────────────────────────
async function startCountdown() {
  if (!cameraReady.value) return;

  phase.value = "countdown";
  for (let i = 3; i >= 1; i--) {
    countdown.value = i;
    await new Promise(r => setTimeout(r, 1000));
  }
  countdown.value = 0;
  startRecording();
}

// ── Recording ─────────────────────────────────────────────
function startRecording() {
  phase.value    = "recording";
  frames         = [];
  timestamps     = [];
  capturedFrames.value = 0;
  elapsedSec.value     = 0;
  startTime = performance.now();

  const ctx      = canvasEl.value.getContext("2d");
  const interval = 1000 / recordFps.value;

  // Elapsed display
  elapsedTimer = setInterval(() => {
    elapsedSec.value = (performance.now() - startTime) / 1000;
  }, 100);

  captureTimer = setInterval(() => {
    const t = (performance.now() - startTime) / 1000;
    ctx.drawImage(videoEl.value, 0, 0, CFG.width, CFG.height);
    frames.push(canvasEl.value.toDataURL("image/png"));
    timestamps.push(parseFloat(t.toFixed(6)));
    capturedFrames.value++;

    if (capturedFrames.value >= totalFrames.value) {
      stopCapture();
      packageAndUpload();
    }
  }, interval);
}

function stopCapture() {
  clearInterval(captureTimer);
  clearInterval(elapsedTimer);
  captureTimer = null;
  elapsedTimer = null;
}

function abortRecording() {
  stopCapture();
  frames     = [];
  timestamps = [];
  phase.value = "idle";
}

const progressPct = computed(() => {
  if (!startTime) return 0;
  return Math.min(100, (capturedFrames.value / totalFrames.value) * 100);
});

// ── ZIP packaging ─────────────────────────────────────────
async function packageAndUpload() {
  phase.value      = "packaging";
  statusMessage.value = "Préparation de la session…";

  const now        = new Date();
  const stamp      = now.toISOString().replace(/[-:T]/g, "").slice(0, 15);
  const suffix     = sessionLabel.value
    ? "_" + sessionLabel.value.replace(/[^a-zA-Z0-9_\-.]/g, "_")
    : "";
  const sessionName = `session_${stamp}${suffix}`;
  currentSession.value = sessionName;

  const measuredFps = frames.length / timestamps[timestamps.length - 1];
  const metadata = {
    session_name:   sessionName,
    date:           now.toISOString(),
    platform:       "browser",
    camera_index:   1,          // colleagues' script uses camera index 1
    codec:          "MJPG",     // matches CAP_PROP_FOURCC in acquisition script
    requested_fps:  recordFps.value,
    measured_fps:   parseFloat(measuredFps.toFixed(3)),
    nb_frames:      frames.length,
    duration_s:     parseFloat(timestamps[timestamps.length - 1].toFixed(3)),
    frame_width:    CFG.width,
    frame_height:   CFG.height,
    save_format:    "png",
    timestamps_rel: timestamps,
  };

  const zip         = new JSZip();
  const rootFolder  = zip.folder(sessionName);
  const framesFolder = rootFolder.folder("frames");

  for (let i = 0; i < frames.length; i++) {
    const base64 = frames[i].split(",")[1];
    // Naming matches colleagues' OpenCV script: 0000.png, 0001.png, …
    const num = String(i).padStart(4, "0");
    framesFolder.file(`${num}.png`, base64, { base64: true });
  }
  rootFolder.file("metadata.json", JSON.stringify(metadata, null, 2));
  frames = []; // free memory before generating ZIP

  const zipBlob = await zip.generateAsync({
    type:               "blob",
    compression:        "DEFLATE",
    compressionOptions: { level: 1 }, // PNG already compressed — minimal overhead
  });

  await uploadSession(sessionName, zipBlob);
}

// ── Upload from existing ZIP file ─────────────────────────
function onDrop(e) {
  isDragging.value = false;
  const file = e.dataTransfer.files[0];
  if (file) handleZipFile(file);
}

function onFileChange(e) {
  const file = e.target.files[0];
  if (file) handleZipFile(file);
  e.target.value = "";
}

async function handleZipFile(file) {
  const name = file.name.toLowerCase();
  if (!name.endsWith(".zip") && !name.endsWith(".avi")) {
    phase.value         = "error";
    statusMessage.value = "Seuls les fichiers .zip ou .avi sont acceptés.";
    return;
  }
  await uploadSession(null, file);
}

// ── Upload ────────────────────────────────────────────────
async function uploadSession(sessionName, zipBlob) {
  phase.value          = "uploading";
  statusMessage.value  = "Transfert en cours…";
  uploadProgress.value = 0;

  const filename = sessionName ? `${sessionName}.zip` : zipBlob.name || "session.zip";
  const form = new FormData();
  form.append("file", zipBlob, filename);

  let uploadedName;
  try {
    const { data } = await axios.post(apiUrl("/upload/"), form, {
      onUploadProgress: e => {
        uploadProgress.value = e.total ? Math.round((e.loaded / e.total) * 100) : 0;
      },
    });
    // Use session name returned by the server (extracted from ZIP folder)
    uploadedName = data.sessions?.[0] || sessionName;
  } catch (e) {
    phase.value         = "error";
    statusMessage.value = e.response?.data?.error || "Erreur lors de l'upload.";
    return;
  }

  await submitAnalysis(uploadedName);
}

// ── Analysis ──────────────────────────────────────────────
async function submitAnalysis(sessionName) {
  phase.value         = "analyzing";
  statusMessage.value = "Analyse ST-rPPG en cours…";

  try {
    const { data: jobData } = await axios.post(
      apiUrl(`/analysis/${sessionName}`),
      { force: false },
    );
    const jobId = jobData.job_id;
    await pollJob(sessionName, jobId);
  } catch (e) {
    phase.value         = "error";
    statusMessage.value = e.response?.data?.error || "Erreur lors du lancement de l'analyse.";
  }
}

async function pollJob(sessionName, jobId) {
  let consecutiveErrors = 0;
  const maxErrors = 3;

  while (true) {
    await new Promise(r => setTimeout(r, 2000));
    try {
      const { data } = await axios.get(apiUrl(`/analysis/${sessionName}/status/${jobId}`));
      
      // On réinitialise le compteur d'erreurs si la requête réussit
      consecutiveErrors = 0;

      if (data.status === "done") break;
      
      if (data.status === "error") {
        phase.value = "error";
        statusMessage.value = data.error || "L'analyse a échoué.";
        return; // ON ARRÊTE LA BOUCLE
      }
    } catch (e) {
      consecutiveErrors++;
      const status = e.response?.status;

      // SI 404 (Job perdu après crash) ou 500 (Crash serveur)
      if (status === 404 || status === 500 || consecutiveErrors >= maxErrors) {
        console.error("Arrêt du polling : Erreur critique serveur", status);
        phase.value = "error";
        statusMessage.value = status === 404 
          ? "Session perdue (le serveur a redémarré)." 
          : "Le serveur a rencontré une erreur critique.";
        return; // ON ARRÊTE LA BOUCLE ICI (Fini les 500 requêtes/minute)
      }
      // Pour les autres erreurs (timeout réseau léger), on laisse une chance
    }
  }

  // Fetch full result (seulement si on est sorti du while par le "break")
  try {
    const { data: result } = await axios.get(apiUrl(`/analysis/${sessionName}`));
    analysisResult.value = result;
    phase.value          = "done";
    statusMessage.value  = "Analyse terminée.";
  } catch (e) {
    phase.value         = "error";
    statusMessage.value = "Impossible de récupérer les résultats.";
  }
}

// ── Reset ─────────────────────────────────────────────────
function resetAcquisition() {
  phase.value          = "idle";
  statusMessage.value  = "";
  analysisResult.value = null;
  currentSession.value = "";
  capturedFrames.value = 0;
  elapsedSec.value     = 0;
  uploadProgress.value = 0;
  frames               = [];
  timestamps           = [];
}

// ── Computed ──────────────────────────────────────────────
const qualityColor = computed(() => {
  const label = analysisResult.value?.quality?.label?.toUpperCase() || "";
  if (label === "EXCELLENT") return "var(--green)";
  if (label === "GOOD")      return "var(--green)";
  if (label === "POOR")      return "var(--warn)";
  if (label === "BAD")       return "var(--danger)";
  return "var(--muted)";
});

const qualityIcon = computed(() => {
  const label = analysisResult.value?.quality?.label?.toUpperCase() || "";
  if (label === "EXCELLENT") return "mdi-check-circle";
  if (label === "GOOD")      return "mdi-check-circle";
  if (label === "POOR")      return "mdi-alert-circle";
  if (label === "BAD")       return "mdi-close-circle";
  return "mdi-help-circle";
});

const resultMetrics = computed(() => {
  if (!analysisResult.value) return [];
  const r = analysisResult.value;
  const snrOk = (r.snr?.mean_snr ?? 0) >= 3;
  return [
    { label: "HR estimée",  value: r.hr?.hr_bpm,                       unit: "bpm", icon: "mdi-heart-pulse",  color: "var(--warn)"   },
    { label: "SNR moyen",   value: r.snr?.mean_snr,                    unit: "dB",  icon: "mdi-signal",       color: snrOk ? "var(--green)" : "var(--danger)" },
    { label: "TMS",         value: ((r.tms?.tms || 0) * 100).toFixed(1), unit: "%", icon: "mdi-waveform",     color: r.tms?.is_clean ? "var(--green)" : "var(--warn)" },
    { label: "FPS réel",    value: r.fps?.toFixed(1),                  unit: "Hz",  icon: "mdi-speedometer",  color: "var(--accent)"  },
  ];
});

// ── Lifecycle ─────────────────────────────────────────────
onMounted(initCamera);

onUnmounted(() => {
  stopCapture();
  if (stream) stream.getTracks().forEach(t => t.stop());
});
</script>

<style scoped>
/* ── Tabs ──────────────────────────────────────────────── */
.acq-tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--border); padding-bottom: 0; }
.acq-tab {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 8px 18px; border-radius: 8px 8px 0 0;
  background: transparent; border: none; border-bottom: 2px solid transparent;
  color: var(--muted); font-size: 0.8rem; font-weight: 600;
  cursor: pointer; transition: all 0.15s; margin-bottom: -1px;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.acq-tab:hover { color: var(--text2); }
.acq-tab.active { color: var(--accent); border-bottom-color: var(--accent); }
.acq-tab:disabled { opacity: 0.4; cursor: default; }

/* ── Done badge ─────────────────────────────────────────── */
.done-badge {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 0.78rem; font-weight: 600; color: var(--green);
  background: rgba(34,212,126,0.1); border: 1px solid rgba(34,212,126,0.25);
  border-radius: 8px; padding: 6px 14px;
}

/* ── Camera ─────────────────────────────────────────────── */
.camera-wrapper { position: relative; width: 100%; aspect-ratio: 4/3; background: #070c14; overflow: hidden; }
.camera-video   { width: 100%; height: 100%; object-fit: cover; display: block; }
.camera-overlay {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: rgba(7,7,12,0.88);
}
.rec-badge {
  position: absolute; top: 12px; left: 12px;
  background: rgba(248,81,73,0.9); color: #fff;
  font-size: 0.75rem; font-weight: 700; letter-spacing: 1px;
  padding: 3px 10px; border-radius: 4px;
  display: flex; align-items: center; gap: 6px;
}
.countdown-overlay {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.6);
  font-size: 7rem; font-weight: 900; color: #fff;
  text-shadow: 0 0 40px var(--accent);
}
.video-progress { position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: rgba(255,255,255,0.08); }
.video-progress-fill { height: 100%; background: var(--accent); transition: width 0.1s linear; box-shadow: 0 0 8px var(--accent); }
.frame-bar { display: flex; align-items: center; gap: 6px; padding: 8px 14px; font-size: 0.8rem; color: var(--text); border-top: 1px solid var(--border); }
.frame-count { color: var(--accent); font-weight: 700; }

/* ── Params ─────────────────────────────────────────────── */
.param-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.param-item { background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; }
.param-label { font-size: 0.67rem; color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px; }
.param-value { font-size: 0.95rem; font-weight: 800; color: var(--accent); }

/* ── Stop button ────────────────────────────────────────── */
.btn-stop {
  display: inline-flex; align-items: center; justify-content: center; gap: 7px;
  padding: 14px 18px; border-radius: 8px;
  background: rgba(248,81,73,0.1); color: var(--danger);
  border: 1px solid rgba(248,81,73,0.3);
  font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: opacity 0.15s;
}
.btn-stop:hover { opacity: 0.82; }

/* ── Progress bar ───────────────────────────────────────── */
.progress-track { height: 4px; background: var(--surface3); border-radius: 3px; overflow: hidden; }
.progress-fill  { height: 100%; background: var(--accent); transition: width 0.3s ease; border-radius: 3px; }

/* ── Status row ─────────────────────────────────────────── */
.status-row { display: flex; align-items: center; }

/* ── Verdict banner ─────────────────────────────────────── */
.verdict-banner { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; padding: 20px 22px; }
.verdict-icon { width: 52px; height: 52px; border-radius: 12px; border: 1px solid; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.verdict-text { flex: 1; min-width: 180px; }
.verdict-label { font-size: 1.4rem; font-weight: 800; line-height: 1.2; }
.verdict-sub { font-size: 0.83rem; color: var(--muted); margin: 4px 0 6px; }
.verdict-ok  { display: flex; align-items: center; gap: 5px; font-size: 0.78rem; color: var(--green); }
.verdict-rec { display: flex; align-items: center; gap: 5px; font-size: 0.78rem; color: var(--warn); padding: 1px 0; }
.btn-ghost--accent { color: var(--accent) !important; border-color: rgba(232,98,42,0.3) !important; }
.btn-ghost--accent:hover { background: rgba(232,98,42,0.08) !important; border-color: var(--accent) !important; }
.head-tag {
  margin-left: auto; font-size: 0.68rem; font-weight: 700;
  padding: 2px 10px; border-radius: 5px; border: 1px solid;
  text-transform: none; letter-spacing: 0;
}

/* ── Drop zone ──────────────────────────────────────────── */
.drop-zone {
  border: 1px dashed var(--border2); border-radius: 14px; padding: 64px 24px;
  text-align: center; cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  background: var(--surface2);
  display: flex; flex-direction: column; align-items: center;
}
.drop-zone:hover:not(.drop-zone--disabled) { border-color: var(--accent); background: rgba(232,98,42,0.04); }
.drop-zone--active   { border-color: var(--accent) !important; background: rgba(232,98,42,0.07) !important; }
.drop-zone--disabled { cursor: default; }
.drop-title { font-size: 1.1rem; font-weight: 700; color: var(--text); margin-bottom: 6px; }
.drop-sub   { font-size: 0.8rem; color: var(--muted); }
.format-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 700;
  background: rgba(232,98,42,0.1); color: var(--accent); border: 1px solid rgba(232,98,42,0.25);
}
.format-chip--teal { background: rgba(6,182,212,0.1); color: var(--teal); border-color: rgba(6,182,212,0.25); }
</style>
