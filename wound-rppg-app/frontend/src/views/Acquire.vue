<template>
  <div>
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">
          <v-icon color="primary" size="26" class="mr-2">mdi-record-circle</v-icon>
          Acquisition en direct
        </h1>
        <p class="page-sub">
          Protocole ST-rPPG · 50 fps · 8 s · 512 × 512 · PNG
        </p>
      </div>
      <v-chip v-if="phase === 'done'" color="success" variant="tonal" prepend-icon="mdi-check-circle">
        Session analysée
      </v-chip>
    </div>

    <!-- Mode tabs -->
    <v-tabs v-model="mode" color="primary" class="mb-4" :disabled="phase !== 'idle'">
      <v-tab value="camera" prepend-icon="mdi-record-circle-outline">Caméra live</v-tab>
      <v-tab value="upload" prepend-icon="mdi-folder-upload-outline">Session existante</v-tab>
    </v-tabs>

    <!-- ── CAMERA MODE ── -->
    <v-window v-model="mode">
      <v-window-item value="camera">
        <v-row>
          <!-- Camera preview -->
          <v-col cols="12" md="7">
            <v-card class="glass-card overflow-hidden" style="position: relative">
              <div class="camera-wrapper">
                <video ref="videoEl" autoplay playsinline muted class="camera-video" />
                <canvas ref="canvasEl" :width="CFG.width" :height="CFG.height" style="display:none" />

                <div v-if="!cameraReady && !cameraError" class="camera-overlay">
                  <v-progress-circular indeterminate color="primary" size="48" />
                  <p class="mt-3" style="color:var(--muted)">Accès à la caméra…</p>
                </div>

                <div v-if="cameraError" class="camera-overlay">
                  <v-icon size="56" color="error">mdi-camera-off</v-icon>
                  <p class="mt-3" style="color:var(--danger)">{{ cameraError }}</p>
                  <v-btn variant="tonal" color="primary" class="mt-3" @click="initCamera">Réessayer</v-btn>
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
                <v-icon size="16" color="accent" class="mr-1">mdi-image-multiple</v-icon>
                <span class="frame-count">{{ capturedFrames }}</span>
                <span style="color:var(--muted)"> / {{ totalFrames }} frames</span>
                <span class="ml-auto" style="color:var(--muted); font-size:0.8rem">
                  {{ elapsedSec.toFixed(1) }} s / {{ recordDuration }} s
                </span>
              </div>
            </v-card>
          </v-col>

          <!-- Controls -->
          <v-col cols="12" md="5">
            <v-card class="glass-card mb-3">
              <v-card-title class="card-title">
                <v-icon color="primary" class="mr-2">mdi-tune</v-icon>
                Protocole d'acquisition
              </v-card-title>
              <v-card-text class="pt-0">
                <div class="param-grid">
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
                <div class="mt-3">
                  <div class="param-label mb-1">Cadence (FPS)</div>
                  <v-btn-toggle v-model="recordFps" mandatory density="compact"
                    color="primary" variant="outlined" :disabled="phase !== 'idle'">
                    <v-btn :value="25">25 fps</v-btn>
                    <v-btn :value="30">30 fps</v-btn>
                    <v-btn :value="50">50 fps <v-chip size="x-small" color="primary" variant="tonal" class="ml-1">lab</v-chip></v-btn>
                    <v-btn :value="60">60 fps</v-btn>
                  </v-btn-toggle>
                </div>
                <!-- Duration slider -->
                <div class="mt-3 mb-1">
                  <div class="d-flex justify-space-between mb-1">
                    <span style="font-size:0.78rem; color:var(--muted)">Durée d'enregistrement</span>
                    <span style="font-size:0.78rem; color:var(--accent); font-weight:600">{{ recordDuration }} s</span>
                  </div>
                  <v-slider v-model="recordDuration" :min="10" :max="60" :step="5"
                    color="primary" track-color="border" hide-details
                    :disabled="phase !== 'idle'" density="compact" />
                  <div class="d-flex justify-space-between" style="font-size:0.7rem; color:var(--muted); margin-top:-4px">
                    <span>10 s</span><span>60 s</span>
                  </div>
                </div>
                <v-divider class="my-3" style="border-color:var(--border)" />
                <v-text-field
                  v-model="sessionLabel"
                  label="Label de session (optionnel)"
                  placeholder="Ex: paume_droite, plaie_J3"
                  density="compact"
                  variant="outlined"
                  :disabled="phase !== 'idle'"
                  prepend-inner-icon="mdi-tag-outline"
                  hide-details
                />
              </v-card-text>
            </v-card>

            <template v-if="phase === 'idle'">
              <v-btn color="primary" block size="large" :disabled="!cameraReady"
                     @click="startCountdown" prepend-icon="mdi-record-circle-outline" class="mb-2">
                Lancer l'acquisition
              </v-btn>
            </template>

            <v-btn v-if="phase === 'recording'" color="error" block size="large" variant="tonal"
                   @click="abortRecording" prepend-icon="mdi-stop-circle-outline">
              Annuler l'enregistrement
            </v-btn>

            <v-card v-if="phase !== 'idle' && phase !== 'recording'" class="glass-card mt-3">
              <v-card-text>
                <div class="status-row">
                  <v-progress-circular v-if="phase !== 'done' && phase !== 'error'"
                    indeterminate color="primary" size="22" width="2" class="mr-3" />
                  <v-icon v-else-if="phase === 'done'" color="success" class="mr-3">mdi-check-circle</v-icon>
                  <v-icon v-else color="error" class="mr-3">mdi-alert-circle</v-icon>
                  <span :style="{ color: phase === 'error' ? 'var(--danger)' : phase === 'done' ? 'var(--green)' : 'var(--accent)' }">
                    {{ statusMessage }}
                  </span>
                </div>
                <v-progress-linear v-if="phase === 'uploading' && uploadProgress > 0"
                  :model-value="uploadProgress" color="primary" class="mt-3" rounded height="6" />
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-window-item>

      <!-- ── UPLOAD MODE ── -->
      <v-window-item value="upload">
        <v-row justify="center">
          <v-col cols="12" md="7">
            <!-- Drop zone -->
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
                <v-icon size="56" color="primary" class="mb-3">mdi-folder-upload-outline</v-icon>
                <div class="drop-title">Glisse ton fichier ici</div>
                <div class="drop-sub">ou clique pour choisir</div>
                <div class="d-flex gap-2 justify-center mt-3">
                  <v-chip size="small" variant="tonal" color="primary" prepend-icon="mdi-zip-box">ZIP</v-chip>
                  <v-chip size="small" variant="tonal" color="secondary" prepend-icon="mdi-video">AVI</v-chip>
                </div>
                <div class="drop-sub mt-2">ZIP : <code>session/frames/*.png + metadata.json</code></div>
                <div class="drop-sub">AVI : converti automatiquement côté serveur</div>
              </template>

              <template v-else-if="phase !== 'done' && phase !== 'error'">
                <v-progress-circular indeterminate color="primary" size="48" class="mb-3" />
                <div class="drop-title" style="color:var(--accent)">{{ statusMessage }}</div>
                <v-progress-linear v-if="phase === 'uploading' && uploadProgress > 0"
                  :model-value="uploadProgress" color="primary" class="mt-4" rounded height="6"
                  style="width:100%;max-width:300px" />
              </template>

              <template v-else-if="phase === 'done'">
                <v-icon size="56" color="success" class="mb-3">mdi-check-circle</v-icon>
                <div class="drop-title" style="color:var(--green)">Analyse terminée</div>
              </template>

              <template v-else>
                <v-icon size="56" color="error" class="mb-3">mdi-alert-circle</v-icon>
                <div class="drop-title" style="color:var(--danger)">{{ statusMessage }}</div>
                <v-btn variant="tonal" color="primary" class="mt-3" @click.stop="resetAcquisition">
                  Réessayer
                </v-btn>
              </template>
            </div>
          </v-col>
        </v-row>
      </v-window-item>
    </v-window>

    <!-- Results -->
    <transition name="slide-up">
      <div v-if="analysisResult" class="mt-6">
        <v-divider class="mb-5" style="border-color:var(--border)" />

        <!-- Quality verdict banner -->
        <v-card class="glass-card mb-5" :style="{ borderColor: qualityColor + ' !important' }">
          <v-card-text>
            <div class="verdict-banner">
              <v-icon :color="qualityColor" size="52">{{ qualityIcon }}</v-icon>
              <div class="verdict-text">
                <div class="verdict-label" :style="{ color: qualityColor }">
                  Signal {{ analysisResult.quality?.label }}
                </div>
                <div class="verdict-sub">
                  Score qualité :
                  <strong :style="{ color: qualityColor }">{{ analysisResult.quality?.score?.toFixed(2) }}</strong>
                  · HR estimée : <strong style="color:var(--warn)">{{ analysisResult.hr?.hr_bpm }} bpm</strong>
                </div>
                <div v-if="analysisResult.quality?.recommendations?.length === 0" style="color:var(--green); font-size:0.82rem">
                  ✓ Aucune recommandation — signal de bonne qualité
                </div>
                <div v-for="r in analysisResult.quality?.recommendations" :key="r" class="rec-item">
                  <v-icon color="warning" size="14">mdi-arrow-right</v-icon> {{ r }}
                </div>
              </div>
              <v-btn
                color="primary"
                variant="tonal"
                :to="`/analysis/${currentSession}`"
                prepend-icon="mdi-open-in-new"
                class="ml-auto"
              >
                Analyse complète
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- Metric cards -->
        <v-row class="mb-4">
          <v-col v-for="m in resultMetrics" :key="m.label" cols="6" md="3">
            <MetricCard v-bind="m" />
          </v-col>
        </v-row>

        <!-- Signal + FFT -->
        <v-row>
          <v-col cols="12" md="8">
            <v-card class="glass-card">
              <v-card-title class="card-title">
                <v-icon color="primary" class="mr-2">mdi-pulse</v-icon>
                Signal POS — sinusoïdal ?
                <v-chip
                  size="x-small"
                  :color="analysisResult.tms?.is_clean ? 'success' : 'warning'"
                  variant="tonal"
                  class="ml-2"
                >
                  {{ analysisResult.tms?.is_clean ? 'Propre ✓' : 'Bruité' }}
                </v-chip>
              </v-card-title>
              <v-card-text>
                <SignalChart
                  :time="analysisResult.signal?.time || []"
                  :raw="analysisResult.signal?.raw || []"
                  :filtered="analysisResult.signal?.filt || []"
                  :peaks="analysisResult.signal?.peaks || []"
                  :hrBpm="analysisResult.hr?.hr_bpm"
                  :height="200"
                />
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="4">
            <v-card class="glass-card">
              <v-card-title class="card-title">
                <v-icon color="secondary" class="mr-2">mdi-chart-bell-curve</v-icon>
                Spectre FFT
              </v-card-title>
              <v-card-text>
                <FFTChart
                  :freq="analysisResult.hr?.freq || []"
                  :fft="analysisResult.hr?.fft || []"
                  :hrHz="analysisResult.hr?.hr_hz"
                  :hrBpm="analysisResult.hr?.hr_bpm"
                  :height="200"
                />
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- New acquisition -->
        <div class="text-center mt-4">
          <v-btn color="primary" variant="tonal" prepend-icon="mdi-refresh" @click="resetAcquisition">
            Nouvelle acquisition
          </v-btn>
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
  statusMessage.value = "Assemblage du ZIP…";

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
  statusMessage.value  = "Upload vers le serveur…";
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
  statusMessage.value = "Analyse POS en cours…";

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
  if (label === "GOOD")      return "var(--green)";
  if (label === "POOR")      return "var(--warn)";
  if (label === "BAD")       return "var(--danger)";
  return "var(--muted)";
});

const qualityIcon = computed(() => {
  const label = analysisResult.value?.quality?.label?.toUpperCase() || "";
  if (label === "GOOD")  return "mdi-check-circle";
  if (label === "POOR")  return "mdi-alert-circle";
  if (label === "BAD")   return "mdi-close-circle";
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
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
}
.page-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--text);
  display: flex;
  align-items: center;
  margin: 0 0 4px;
}
.page-sub {
  font-size: 0.8rem;
  color: var(--muted);
  margin: 0;
}
.card-title {
  font-size: 0.88rem !important;
  font-weight: 600;
  padding: 14px 16px 10px;
  display: flex;
  align-items: center;
}

/* Camera */
.camera-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background: #0a0e14;
  overflow: hidden;
}
.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.camera-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(10, 14, 20, 0.85);
}

/* REC badge */
.rec-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(248, 81, 73, 0.9);
  color: #fff;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 3px 10px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Countdown */
.countdown-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.55);
  font-size: 7rem;
  font-weight: 900;
  color: #fff;
  text-shadow: 0 0 40px var(--accent);
}

/* Recording progress bar */
.video-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
}
.video-progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.1s linear;
  box-shadow: 0 0 8px var(--accent);
}

/* Frame bar below video */
.frame-bar {
  display: flex;
  align-items: center;
  padding: 8px 14px;
  font-size: 0.82rem;
  color: var(--text);
  border-top: 1px solid var(--border);
}
.frame-count {
  color: var(--accent);
  font-weight: 700;
  font-size: 0.95rem;
}

/* Params grid */
.param-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.param-item {
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 14px;
}
.param-label {
  font-size: 0.72rem;
  color: var(--muted);
  margin-bottom: 2px;
}
.param-value {
  font-size: 1rem;
  font-weight: 700;
  color: var(--accent);
}

/* Status */
.status-row {
  display: flex;
  align-items: center;
  font-size: 0.88rem;
}

/* Verdict banner */
.verdict-banner {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
.verdict-text { flex: 1; min-width: 180px; }
.verdict-label {
  font-size: 1.6rem;
  font-weight: 800;
  line-height: 1.2;
}
.verdict-sub {
  font-size: 0.85rem;
  color: var(--muted);
  margin: 4px 0 6px;
}
.rec-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--warn);
  padding: 2px 0;
}

/* Drop zone */
.drop-zone {
  border: 2px dashed var(--border);
  border-radius: 16px;
  padding: 56px 24px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  background: rgba(255,255,255,0.02);
  display: flex;
  flex-direction: column;
  align-items: center;
}
.drop-zone:hover:not(.drop-zone--disabled) {
  border-color: var(--accent);
  background: rgba(0, 200, 255, 0.04);
}
.drop-zone--active {
  border-color: var(--accent) !important;
  background: rgba(0, 200, 255, 0.08) !important;
}
.drop-zone--disabled {
  cursor: default;
}
.drop-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 6px;
}
.drop-sub {
  font-size: 0.8rem;
  color: var(--muted);
}
.drop-sub code {
  background: rgba(255,255,255,0.06);
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 0.75rem;
}
</style>
