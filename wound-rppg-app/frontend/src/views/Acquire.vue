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
      <button :class="['acq-tab', { active: mode === 'frames' }]" :disabled="phase !== 'idle'"
        @click="mode = 'frames'">
        <v-icon size="14">mdi-image-multiple-outline</v-icon> Déposer des frames
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

              <!-- Live quality badge (top-right, shown once signal is established) -->
              <transition name="fade">
                <div v-if="phase === 'recording' && liveQuality !== 'wait'"
                     class="live-qual-badge" :class="`qual-${liveQuality}`">
                  <span class="qual-dot" />
                  {{ { good: 'Bon signal', ok: 'Signal moyen', poor: 'Éclairage insuffisant' }[liveQuality] }}
                </div>
              </transition>

              <transition name="fade">
                <div v-if="countdown > 0" class="countdown-overlay">{{ countdown }}</div>
              </transition>

              <div v-if="phase === 'recording'" class="video-progress">
                <div class="video-progress-fill" :style="{ width: progressPct + '%' }" />
              </div>
            </div>

            <!-- Frame bar with live FPS -->
            <div v-if="phase === 'recording'" class="frame-bar">
              <v-icon size="15" style="color:var(--accent)">mdi-image-multiple</v-icon>
              <span class="frame-count">{{ capturedFrames }}</span>
              <span style="color:var(--muted)"> / {{ totalFrames }} frames</span>

              <span class="fps-live" :class="{ 'fps-warn': liveFpsDropped }">
                <v-icon size="12">mdi-speedometer</v-icon>
                {{ liveFpsReal > 0 ? liveFpsReal : '…' }} fps
                <span v-if="liveFpsDropped" style="font-size:0.68rem; margin-left:2px">⚠ drops</span>
              </span>

              <span class="ml-auto" style="color:var(--muted); font-size:0.8rem">
                {{ elapsedSec.toFixed(1) }} s / {{ recordDuration }} s
              </span>
            </div>

            <!-- Live rPPG signal chart -->
            <div v-if="phase === 'recording'" class="live-signal-block">
              <div class="live-sig-head">
                <v-icon size="11" color="#22d47e">mdi-pulse</v-icon>
                <span>Signal vert — rPPG live</span>
                <span v-if="liveQuality === 'wait'" class="sig-tag sig-wait">Initialisation…</span>
                <span v-else-if="liveQuality === 'good'" class="sig-tag sig-good">
                  <v-icon size="10">mdi-check-circle</v-icon> Bon signal
                </span>
                <span v-else-if="liveQuality === 'ok'" class="sig-tag sig-ok">
                  <v-icon size="10">mdi-alert-circle-outline</v-icon> Signal moyen
                </span>
                <span v-else class="sig-tag sig-poor">
                  <v-icon size="10">mdi-alert</v-icon> Éclairage insuffisant
                </span>
              </div>
              <svg viewBox="0 0 300 60" class="live-signal-svg" preserveAspectRatio="none">
                <polyline v-if="liveSignalPoints"
                  :points="liveSignalPoints"
                  fill="none"
                  :stroke="liveQuality === 'poor' ? '#ef4444' : liveQuality === 'ok' ? '#f59e0b' : '#22d47e'"
                  stroke-width="1.5"
                  stroke-linejoin="round"
                  stroke-linecap="round"
                />
              </svg>
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
                  <div class="param-label">{{ captureMode === 'duration' ? 'Durée' : 'Durée estimée' }}</div>
                  <div class="param-value">{{ captureMode === 'duration' ? recordDuration + ' s' : (targetFrames / recordFps).toFixed(1) + ' s' }}</div>
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

              <!-- Capture mode toggle -->
              <div class="param-label mb-2">Mode d'arrêt</div>
              <div class="mode-toggle mb-4" :class="{ disabled: phase !== 'idle' }">
                <button class="mode-btn" :class="{ active: captureMode === 'duration' }"
                  :disabled="phase !== 'idle'" @click="captureMode = 'duration'">
                  <v-icon size="13">mdi-timer-outline</v-icon> Durée
                </button>
                <button class="mode-btn" :class="{ active: captureMode === 'frames' }"
                  :disabled="phase !== 'idle'" @click="captureMode = 'frames'">
                  <v-icon size="13">mdi-image-multiple-outline</v-icon> Frames
                </button>
              </div>

              <!-- Duration slider -->
              <template v-if="captureMode === 'duration'">
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
              </template>

              <!-- Frame count slider -->
              <template v-else>
                <div class="d-flex justify-space-between mb-1">
                  <span style="font-size:0.78rem; color:var(--muted)">Nombre de frames</span>
                  <span style="font-size:0.78rem; color:var(--accent); font-weight:600">{{ targetFrames }} frames</span>
                </div>
                <v-slider v-model="targetFrames" :min="100" :max="1200" :step="50"
                  color="primary" track-color="border" hide-details
                  :disabled="phase !== 'idle'" density="compact" class="mb-1" />
                <div class="d-flex justify-space-between mb-4" style="font-size:0.7rem; color:var(--muted)">
                  <span>100</span>
                  <span style="color:var(--muted)">≈ {{ (targetFrames / recordFps).toFixed(1) }} s à {{ recordFps }} FPS</span>
                  <span>1200</span>
                </div>
              </template>

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

    <!-- ── FRAMES MODE ── -->
    <template v-if="mode === 'frames'">
      <v-row justify="center">
        <v-col cols="12" md="8">
          <div
            class="drop-zone frames-drop"
            :class="{ 'drop-zone--active': frameDropDragging, 'drop-zone--disabled': phase !== 'idle' }"
            @dragover.prevent="frameDropDragging = true"
            @dragleave="frameDropDragging = false"
            @drop.prevent="onFramesDrop"
            @click="phase === 'idle' && !frameFiles.length && frameFileInput.click()"
          >
            <input ref="frameFileInput" type="file" accept=".png,.jpg,.jpeg" multiple
                   style="display:none" @change="onFramesInput" />

            <template v-if="!frameFiles.length && phase === 'idle'">
              <v-icon size="52" color="primary" class="mb-4">mdi-image-multiple-outline</v-icon>
              <div class="drop-title">Déposer les frames ici</div>
              <div class="drop-sub mb-4">ou cliquer pour sélectionner les images</div>
              <div class="d-flex gap-2 justify-center mb-3">
                <span class="format-chip">
                  <v-icon size="12">mdi-image-outline</v-icon> PNG
                </span>
                <span class="format-chip format-chip--teal">
                  <v-icon size="12">mdi-image-outline</v-icon> JPG
                </span>
              </div>
              <div class="drop-sub">Images triées par nom de fichier (ordre numérique)</div>
            </template>

            <template v-else-if="phase === 'idle' && frameFiles.length">
              <div class="frames-preview-row">
                <img v-if="framePreviewUrl" :src="framePreviewUrl" class="frames-thumb" />
                <div class="frames-info">
                  <div class="frames-count">{{ frameFiles.length }}<span> frames</span></div>
                  <div class="frames-detail">Premier : {{ frameFiles[0]?.name }}</div>
                  <div class="frames-detail">Dernier  : {{ frameFiles[frameFiles.length - 1]?.name }}</div>
                  <div class="frames-detail mt-1" style="color:var(--accent)">
                    Durée estimée : {{ (frameFiles.length / frameFps).toFixed(1) }} s à {{ frameFps }} FPS
                  </div>
                </div>
              </div>
              <button class="btn-ghost mt-4" @click.stop="clearFrames">
                <v-icon size="14">mdi-close</v-icon> Effacer
              </button>
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

      <v-row v-if="frameFiles.length && phase === 'idle'" justify="center" class="mt-4">
        <v-col cols="12" md="8">
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#e8622a">mdi-tune</v-icon>
              Paramètres de la session
            </div>
            <div style="padding: 16px">
              <div class="param-label mb-2">Cadence d'acquisition (FPS)</div>
              <v-btn-toggle v-model="frameFps" mandatory density="compact"
                color="primary" variant="outlined" class="mb-4">
                <v-btn :value="25">25 FPS</v-btn>
                <v-btn :value="30">30 FPS</v-btn>
                <v-btn :value="50">50 FPS</v-btn>
                <v-btn :value="60">60 FPS</v-btn>
              </v-btn-toggle>

              <div style="height:1px; background:var(--border); margin-bottom:16px" />
              <v-text-field
                v-model="frameSessionLabel"
                label="Identifiant de session (optionnel)"
                placeholder="Ex: plaie_J3, paume_droite"
                density="compact"
                variant="outlined"
                prepend-inner-icon="mdi-tag-outline"
                hide-details
              />
              <div class="mt-4">
                <button class="btn-accent" style="width:100%; justify-content:center; padding:14px"
                  @click="buildFrameSession">
                  <v-icon size="16">mdi-play-circle-outline</v-icon>
                  Créer et analyser la session
                </button>
              </div>
            </div>
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
const CFG = { width: 512, height: 512 };

const recordFps      = ref(50);
const recordDuration = ref(30);
const captureMode    = ref("duration");   // "duration" | "frames"
const targetFrames   = ref(400);
const totalFrames    = computed(() =>
  captureMode.value === "frames"
    ? targetFrames.value
    : recordFps.value * recordDuration.value
);

// Refs — DOM
const videoEl   = ref(null);
const canvasEl  = ref(null);
const fileInput = ref(null);

// State
const mode           = ref("camera");
const isDragging     = ref(false);
const cameraReady    = ref(false);
const cameraError    = ref("");
const sessionLabel   = ref("");
const phase          = ref("idle");
const countdown      = ref(0);
const capturedFrames = ref(0);
const elapsedSec     = ref(0);
const uploadProgress = ref(0);
const currentSession = ref("");
const analysisResult = ref(null);
const statusMessage  = ref("");

// Live signal state
const liveSignalPoints = ref("");
const liveQuality      = ref("wait");  // "wait" | "good" | "ok" | "poor"
const liveFpsReal      = ref(0);
const liveFpsDropped   = ref(false);

// Camera stream
let stream = null;

// RAF-based capture
let rafId         = null;
let canvasCtx     = null;   // initialized once per recording to enable willReadFrequently
let startTime     = null;

// Captured data
let frames     = [];
let timestamps = [];

// Live green channel ring buffer (last LIVE_BUF_SEC seconds)
const LIVE_BUF_SEC = 8;
let liveGreenBuf = [];

// FPS tracking
let fpsFrameCount = 0;
let fpsStartTime  = 0;

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

// ── Recording (RAF-based) ─────────────────────────────────
function startRecording() {
  phase.value = "recording";
  frames      = [];
  timestamps  = [];
  liveGreenBuf.length = 0;
  capturedFrames.value = 0;
  elapsedSec.value     = 0;
  liveSignalPoints.value = "";
  liveQuality.value      = "wait";
  liveFpsReal.value      = 0;
  liveFpsDropped.value   = false;

  // willReadFrequently = true: browser optimizes canvas for getImageData calls
  canvasCtx = canvasEl.value.getContext("2d", { willReadFrequently: true });

  startTime     = performance.now();
  fpsFrameCount = 0;
  fpsStartTime  = startTime;

  rafId = requestAnimationFrame(captureLoop);
}

function captureLoop(timestamp) {
  if (phase.value !== "recording") return;

  const elapsedMs       = timestamp - startTime;
  const expectedFrames  = Math.floor(elapsedMs * recordFps.value / 1000);
  elapsedSec.value      = elapsedMs / 1000;

  if (capturedFrames.value < expectedFrames) {
    // Draw current video frame to hidden canvas
    canvasCtx.drawImage(videoEl.value, 0, 0, CFG.width, CFG.height);
    frames.push(canvasEl.value.toDataURL("image/png"));
    timestamps.push(parseFloat((elapsedMs / 1000).toFixed(6)));

    // Extract mean green channel (stride = 16 px → 16384 samples for 512×512)
    const px = canvasCtx.getImageData(0, 0, CFG.width, CFG.height).data;
    let g = 0, n = 0;
    for (let i = 0; i < px.length; i += 64) { // 64 bytes = 16 RGBA pixels
      g += px[i + 1]; // green is byte 1 of each RGBA group
      n++;
    }
    liveGreenBuf.push(g / n);

    // Trim ring buffer to LIVE_BUF_SEC
    const maxBuf = Math.ceil(recordFps.value * LIVE_BUF_SEC);
    if (liveGreenBuf.length > maxBuf) liveGreenBuf.shift();

    capturedFrames.value++;

    // Live FPS: update every second
    fpsFrameCount++;
    const fpsDt = timestamp - fpsStartTime;
    if (fpsDt >= 1000) {
      liveFpsReal.value    = Math.round(fpsFrameCount / fpsDt * 1000);
      liveFpsDropped.value = liveFpsReal.value < recordFps.value * 0.85;
      fpsFrameCount = 0;
      fpsStartTime  = timestamp;
    }

    // Update live chart every 15 frames
    if (capturedFrames.value % 15 === 0) updateLiveSignal();

    if (capturedFrames.value >= totalFrames.value) {
      cancelAnimationFrame(rafId);
      rafId = null;
      packageAndUpload();
      return;
    }
  }

  rafId = requestAnimationFrame(captureLoop);
}

// ── Live signal processing ────────────────────────────────
function updateLiveSignal() {
  const buf = [...liveGreenBuf];
  if (buf.length < 10) return;

  const N  = buf.length;
  const dc = buf.reduce((a, b) => a + b, 0) / N;

  // Linear detrend: subtract best-fit line to remove slow drift
  const mx  = (N - 1) / 2;
  let num = 0, den = 0;
  for (let i = 0; i < N; i++) {
    num += (i - mx) * (buf[i] - dc);
    den += (i - mx) ** 2;
  }
  const slope = den > 0 ? num / den : 0;
  const detrended = buf.map((v, i) => v - (dc + slope * (i - mx)));

  // Normalize for display
  const peak = Math.max(...detrended.map(Math.abs)) + 1e-8;
  const norm = detrended.map(v => v / peak);

  // SVG polyline: viewBox 0 0 300 60, signal centered at y=30
  const W = 300, H = 60, pad = 4;
  liveSignalPoints.value = norm.map((v, i) => {
    const x = pad + (i / (norm.length - 1)) * (W - 2 * pad);
    const y = H / 2 - v * (H / 2 - pad);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");

  // Quality from AC/DC ratio (need at least 3 seconds of data)
  const minSamples = Math.round(recordFps.value * 3);
  if (buf.length < minSamples) {
    liveQuality.value = "wait";
    return;
  }
  const acRms = Math.sqrt(detrended.reduce((a, v) => a + v * v, 0) / N);
  const ratio = acRms / (dc + 1e-8);

  if (ratio > 0.015)      liveQuality.value = "good";
  else if (ratio > 0.005) liveQuality.value = "ok";
  else                    liveQuality.value = "poor";
}

function stopCapture() {
  if (rafId) {
    cancelAnimationFrame(rafId);
    rafId = null;
  }
}

function abortRecording() {
  stopCapture();
  frames           = [];
  timestamps       = [];
  liveGreenBuf.length = 0;
  phase.value      = "idle";
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
    camera_index:   1,
    codec:          "MJPG",
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
    const num = String(i).padStart(4, "0");
    framesFolder.file(`${num}.png`, base64, { base64: true });
  }
  rootFolder.file("metadata.json", JSON.stringify(metadata, null, 2));
  frames = [];

  const zipBlob = await zip.generateAsync({
    type:               "blob",
    compression:        "DEFLATE",
    compressionOptions: { level: 1 },
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
      consecutiveErrors = 0;

      if (data.status === "done") break;

      if (data.status === "error") {
        phase.value = "error";
        statusMessage.value = data.error || "L'analyse a échoué.";
        return;
      }
    } catch (e) {
      consecutiveErrors++;
      const status = e.response?.status;

      if (status === 404 || status === 500 || consecutiveErrors >= maxErrors) {
        phase.value = "error";
        statusMessage.value = status === 404
          ? "Session perdue (le serveur a redémarré)."
          : "Le serveur a rencontré une erreur critique.";
        return;
      }
    }
  }

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

// ── Frames mode ───────────────────────────────────────────
const frameFiles        = ref([]);
const frameDropDragging = ref(false);
const framePreviewUrl   = ref("");
const frameFps          = ref(30);
const frameSessionLabel = ref("");
const frameFileInput    = ref(null);

function naturalSort(files) {
  return [...files].sort((a, b) => {
    const re = /(\d+)/g;
    const pa = a.name.split(re), pb = b.name.split(re);
    for (let i = 0; i < Math.min(pa.length, pb.length); i++) {
      const diff = isNaN(pa[i]) ? pa[i].localeCompare(pb[i]) : Number(pa[i]) - Number(pb[i]);
      if (diff !== 0) return diff;
    }
    return pa.length - pb.length;
  });
}

function setFrameFiles(files) {
  const sorted = naturalSort(files);
  frameFiles.value = sorted;
  if (framePreviewUrl.value) URL.revokeObjectURL(framePreviewUrl.value);
  framePreviewUrl.value = sorted.length ? URL.createObjectURL(sorted[0]) : "";
}

function onFramesDrop(e) {
  frameDropDragging.value = false;
  const files = [...e.dataTransfer.files].filter(f => /\.(png|jpe?g)$/i.test(f.name));
  if (files.length) setFrameFiles(files);
}

function onFramesInput(e) {
  const files = [...e.target.files].filter(f => /\.(png|jpe?g)$/i.test(f.name));
  if (files.length) setFrameFiles(files);
  e.target.value = "";
}

function clearFrames() {
  frameFiles.value = [];
  if (framePreviewUrl.value) URL.revokeObjectURL(framePreviewUrl.value);
  framePreviewUrl.value = "";
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload  = () => resolve(reader.result.split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function buildFrameSession() {
  if (!frameFiles.value.length) return;
  phase.value         = "packaging";
  statusMessage.value = "Préparation de la session…";

  const now     = new Date();
  const stamp   = now.toISOString().replace(/[-:T]/g, "").slice(0, 15);
  const suffix  = frameSessionLabel.value
    ? "_" + frameSessionLabel.value.replace(/[^a-zA-Z0-9_\-.]/g, "_")
    : "";
  const sessionName = `session_${stamp}${suffix}`;
  currentSession.value = sessionName;

  const files = frameFiles.value;
  const n     = files.length;
  const metadata = {
    session_name:  sessionName,
    date:          now.toISOString(),
    platform:      "browser-frames",
    requested_fps: frameFps.value,
    measured_fps:  frameFps.value,
    nb_frames:     n,
    duration_s:    parseFloat((n / frameFps.value).toFixed(3)),
    save_format:   "png",
  };

  const zip          = new JSZip();
  const rootFolder   = zip.folder(sessionName);
  const framesFolder = rootFolder.folder("frames");

  for (let i = 0; i < n; i++) {
    statusMessage.value = `Préparation… ${i + 1} / ${n}`;
    const b64 = await fileToBase64(files[i]);
    const num = String(i).padStart(4, "0");
    framesFolder.file(`${num}.png`, b64, { base64: true });
  }
  rootFolder.file("metadata.json", JSON.stringify(metadata, null, 2));

  const zipBlob = await zip.generateAsync({
    type:               "blob",
    compression:        "DEFLATE",
    compressionOptions: { level: 1 },
  });

  await uploadSession(sessionName, zipBlob);
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
  liveSignalPoints.value = "";
  liveQuality.value      = "wait";
  liveFpsReal.value      = 0;
  liveFpsDropped.value   = false;
  frames     = [];
  timestamps = [];
  liveGreenBuf.length = 0;
  clearFrames();
  frameSessionLabel.value = "";
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

/* ── Live quality badge (camera overlay, top-right) ─────── */
.live-qual-badge {
  position: absolute; top: 12px; right: 12px;
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 0.72rem; font-weight: 700;
  padding: 4px 10px; border-radius: 5px;
  backdrop-filter: blur(4px);
}
.qual-good { background: rgba(34,212,126,0.18); color: #22d47e; border: 1px solid rgba(34,212,126,0.4); }
.qual-ok   { background: rgba(245,158,11,0.18); color: #f59e0b; border: 1px solid rgba(245,158,11,0.4); }
.qual-poor { background: rgba(239,68,68,0.18);  color: #ef4444; border: 1px solid rgba(239,68,68,0.4); }
.qual-dot  { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

/* ── Frame bar ──────────────────────────────────────────── */
.frame-bar { display: flex; align-items: center; gap: 6px; padding: 8px 14px; font-size: 0.8rem; color: var(--text); border-top: 1px solid var(--border); }
.frame-count { color: var(--accent); font-weight: 700; }

.fps-live {
  display: inline-flex; align-items: center; gap: 4px;
  margin-left: 8px; font-size: 0.76rem; color: var(--muted);
  padding: 1px 7px; border-radius: 4px;
  border: 1px solid var(--border);
}
.fps-warn { color: var(--danger) !important; border-color: rgba(239,68,68,0.4) !important; font-weight: 700; }

/* ── Live signal chart ───────────────────────────────────── */
.live-signal-block {
  padding: 8px 14px 10px;
  border-top: 1px solid var(--border);
  background: var(--surface2);
}
.live-sig-head {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.72rem; color: var(--muted); margin-bottom: 6px;
}
.live-signal-svg {
  display: block; width: 100%; height: 64px;
  background: rgba(0,0,0,0.15); border-radius: 4px;
}

/* Signal quality tags */
.sig-tag {
  display: inline-flex; align-items: center; gap: 4px;
  margin-left: auto; font-size: 0.68rem; font-weight: 700;
  padding: 1px 8px; border-radius: 4px; border: 1px solid;
}
.sig-wait { color: var(--muted);   border-color: var(--border);              background: transparent; }
.sig-good { color: #22d47e;        border-color: rgba(34,212,126,0.35);      background: rgba(34,212,126,0.08); }
.sig-ok   { color: #f59e0b;        border-color: rgba(245,158,11,0.35);      background: rgba(245,158,11,0.08); }
.sig-poor { color: #ef4444;        border-color: rgba(239,68,68,0.35);       background: rgba(239,68,68,0.08); }

/* ── Capture mode toggle ─────────────────────────────────── */
.mode-toggle { display: flex; background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.mode-toggle.disabled { opacity: 0.5; pointer-events: none; }
.mode-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 7px 12px; background: none; border: none; cursor: pointer;
  font-size: 0.78rem; font-weight: 600; color: var(--muted);
  transition: all 0.15s; font-family: inherit;
}
.mode-btn.active { background: var(--accent); color: #fff; }
.mode-btn:not(.active):hover { color: var(--text2); }

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

/* ── Frames mode ─────────────────────────────────────────── */
.frames-drop { min-height: 260px; }
.frames-preview-row {
  display: flex; align-items: center; gap: 24px; flex-wrap: wrap; justify-content: center;
}
.frames-thumb {
  width: 140px; height: 100px; object-fit: cover;
  border-radius: 8px; border: 1px solid var(--border);
  flex-shrink: 0;
}
.frames-info { text-align: left; min-width: 160px; }
.frames-count {
  font-size: 2.2rem; font-weight: 800; color: var(--accent); line-height: 1.1; margin-bottom: 6px;
}
.frames-count span { font-size: 0.9rem; color: var(--muted); font-weight: 600; }
.frames-detail { font-size: 0.74rem; color: var(--muted); font-family: monospace; }
</style>
