<template>
  <div>
    <!-- Header -->
    <div class="page-header">
      <div>
        <router-link to="/sessions" class="back-link">
          <v-icon size="13">mdi-arrow-left</v-icon> Sessions
        </router-link>
        <h1 class="page-title">{{ sessionId }}</h1>
        <QualityBadge v-if="result" :label="result.quality?.label"
                      :score="result.quality?.score" :color="result.quality?.color" />
      </div>
      <div class="header-actions">
        <button class="btn-ghost" @click="runAnalysis(false)" :disabled="loading">
          <v-icon size="14">mdi-play-circle-outline</v-icon> Analyser
        </button>
        <button class="btn-ghost btn-ghost--warn" @click="runAnalysis(true)" :disabled="loading">
          <v-icon size="14">mdi-refresh</v-icon> Recalculer
        </button>
        <a v-if="result" class="btn-ghost btn-ghost--green" :href="apiUrl(`/export/${sessionId}/csv`)">
          <v-icon size="14">mdi-download</v-icon> CSV
        </a>
        <a v-if="result" class="btn-ghost btn-ghost--green" :href="apiUrl(`/export/${sessionId}/pdf`)">
          <v-icon size="14">mdi-file-pdf-box</v-icon> PDF
        </a>
      </div>
    </div>

    <!-- Non analysé -->
    <div v-if="!result && !loading" class="empty-card">
      <v-icon size="48" style="color: var(--border2)">mdi-flask-outline</v-icon>
      <p style="font-size:1rem; font-weight:700; color: var(--text2); margin:12px 0 6px">Session non analysée</p>
      <p style="font-size:0.83rem; color: var(--muted)">Cliquez sur <strong style="color:var(--accent)">Analyser</strong> pour lancer le pipeline POS (Wang et al. 2017)</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="empty-card">
      <v-progress-circular indeterminate color="#e8622a" size="36" class="mb-3" />
      <p style="font-size:0.85rem; color: var(--muted)">Calcul en cours — POS + cartes ST-rPPG...</p>
    </div>

    <!-- Résultats -->
    <template v-if="result && !loading">
      <!-- ── Métriques ───────────────────────────────────────────── -->
      <v-row class="mb-5">
        <v-col v-for="m in mainMetrics" :key="m.label" cols="6" md="2">
          <MetricCard v-bind="m" />
        </v-col>
      </v-row>

      <!-- ── Indicateur masque ─────────────────────────────────── -->
      <div class="mask-status-bar mb-4">
        <template v-if="result.has_mask">
          <v-icon size="13" color="#a78bfa">mdi-check-decagram</v-icon>
          <span class="msk-on">Analyse effectuée avec masque spatial</span>
          <span class="msk-sub">Signal, cartes et score de perfusion calculés uniquement sur la zone peinte</span>
          <span v-if="result.wound_area" class="msk-pct">{{ result.wound_area.pct }}% de la frame</span>
        </template>
        <template v-else>
          <v-icon size="13" color="#f59e0b">mdi-alert-outline</v-icon>
          <span class="msk-off">Analyse sans masque</span>
          <span class="msk-sub">Toute la frame est utilisée — dessinez un masque sur la zone de plaie pour cibler l'analyse</span>
        </template>
      </div>

      <!-- ── Signal POS + FFT ────────────────────────────────────── -->
      <v-row class="mb-5">
        <v-col cols="12" md="8">
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#e8622a">mdi-pulse</v-icon>
              Signal POS global
              <span class="head-hint">POS = Plane Orthogonal to Skin (Wang 2017) — moyenne spatiale de la zone</span>
              <span class="head-value">{{ result.hr?.hr_bpm }} bpm</span>
            </div>
            <div class="chart-area">
              <SignalChart :time="result.signal?.time||[]" :raw="result.signal?.raw||[]"
                :filtered="result.signal?.filt||[]" :peaks="result.signal?.peaks||[]"
                :hrBpm="result.hr?.hr_bpm" :height="230" />
            </div>
          </div>
        </v-col>
        <v-col cols="12" md="4">
          <div class="card-block" style="height:100%">
            <div class="card-head">
              <v-icon size="13" color="#06b6d4">mdi-chart-bell-curve</v-icon>
              Spectre FFT
              <span class="head-hint">FFT = Transformée de Fourier rapide — pic dominant = fréquence cardiaque</span>
</div>
          </div>
        </v-col>
      </v-row>

      <!-- ── Score de perfusion ──────────────────────────────────── -->
      <div v-if="result.healing_score" class="healing-banner mb-5">
        <div class="hb-left">
          <div class="hb-title">Score de perfusion</div>
          <div class="hb-sub">SNR · Amplitude RMS · Couverture masque</div>
        </div>
        <div class="hb-score" :style="{ color: result.healing_score.color }">
          {{ result.healing_score.score }}<span style="font-size:1rem;font-weight:400;color:var(--muted)">/100</span>
        </div>
        <div class="hb-label" :style="{ background: result.healing_score.color + '18', color: result.healing_score.color, border: '1px solid ' + result.healing_score.color + '44' }">
          {{ result.healing_score.label }}
        </div>
        <div class="hb-bars">
          <div class="hb-bar-row"><span>SNR</span><div class="hb-bar"><div :style="{ width: (result.healing_score.s_snr/40*100)+'%', background: result.healing_score.color }" /></div><span>{{ result.healing_score.s_snr }}/40</span></div>
          <div class="hb-bar-row"><span>Amp</span><div class="hb-bar"><div :style="{ width: (result.healing_score.s_amp/35*100)+'%', background: '#06b6d4' }" /></div><span>{{ result.healing_score.s_amp }}/35</span></div>
          <div class="hb-bar-row"><span>Zone</span><div class="hb-bar"><div :style="{ width: (result.healing_score.s_cov/25*100)+'%', background: '#a78bfa' }" /></div><span>{{ result.healing_score.s_cov }}/25</span></div>
        </div>
      </div>

      <!-- ── SNR + Cartes + TMS / Recommandations ───────────────── -->
      <v-row class="mb-5">
        <v-col cols="12" md="4">
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#f59e0b">mdi-signal</v-icon>
              SNR glissant
              <span class="head-hint">SNR = Signal-to-Noise Ratio (Rapport Signal/Bruit) dB — fenêtres 8 s sur la bande cardiaque [0,7–3,0 Hz]</span>
              <span class="head-value">{{ result.snr?.mean_snr }} dB</span>
            </div>
            <div class="chart-area">
              <SNRChart :time="result.snr?.time||[]" :snr="result.snr?.snr||[]"
                :meanSnr="result.snr?.mean_snr" :height="180" />
            </div>
          </div>
        </v-col>

        <v-col cols="12" md="4">
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#a78bfa">mdi-map-outline</v-icon>
              Cartes ST-rPPG
              <span class="head-hint">Amplitude = puissance PPG par pixel · Phase = décalage temporel · SNR = qualité signal · Cliquer pour signal local</span>
            </div>
            <div style="padding:14px">
              <SpatialMap :maps="result.maps||{}" :stats="result.amp_stats" @pixel-click="fetchPixelSignal" />
            </div>
          </div>
        </v-col>

        <v-col cols="12" md="4">
          <!-- TMS -->
          <div class="card-block mb-4">
            <div class="card-head">
              <v-icon size="13" color="#06b6d4">mdi-waveform</v-icon>
              TMS
              <span class="head-hint">Template Matching Score — corrélation de forme des cycles PPG</span>
            </div>
            <div class="tms-block">
              <div class="tms-value" :style="{ color: result.tms?.is_clean ? 'var(--green)' : 'var(--warn)' }">
                {{ (result.tms?.tms * 100)?.toFixed(1) }}<span class="tms-unit">%</span>
              </div>
              <span class="tms-chip" :class="result.tms?.is_clean ? 'chip-green' : 'chip-warn'">
                {{ result.tms?.is_clean ? "Signal propre" : "Signal bruité" }}
              </span>
              <p class="tms-meta">{{ result.tms?.n_cycles }} cycles détectés</p>
              <div class="tms-explain">
                Mesure la ressemblance entre tous les cycles cardiaques.
                <b>100%</b> = cycles identiques en forme ·
                <b>&gt;96%</b> = signal propre.
                Calculé par corrélation croisée normalisée cycle-à-cycle.
              </div>
            </div>
          </div>
          <!-- Recommandations -->
          <div class="card-block">
            <div class="card-head">
              <v-icon size="13" color="#f59e0b">mdi-lightbulb-outline</v-icon>
              Recommandations
              <button class="btn-ghost btn-ghost--sm" style="margin-left:auto" @click="showScoreInfo = !showScoreInfo">
                <v-icon size="11">mdi-help-circle-outline</v-icon> Score
              </button>
            </div>
            <div style="padding:14px">
              <div v-if="showScoreInfo" class="score-info-box">
                <div class="score-info-title">Score qualité signal (0–100) :</div>
                <div class="score-info-row"><span class="score-info-metric">SNR</span><span class="score-info-formula">SNR / 8 dB × 40 pts</span><span class="score-info-max">≤ 40</span></div>
                <div class="score-info-row"><span class="score-info-metric">TMS</span><span class="score-info-formula">(TMS − 0,6) / 0,4 × 40 pts</span><span class="score-info-max">≤ 40</span></div>
                <div class="score-info-row"><span class="score-info-metric">FPS</span><span class="score-info-formula">(FPS − 15) / 35 × 20 pts</span><span class="score-info-max">≤ 20</span></div>
                <div class="score-info-sep" />
                <div class="score-info-title" style="margin-top:8px">Score de perfusion (0–100) :</div>
                <div class="score-info-row"><span class="score-info-metric">SNR</span><span class="score-info-formula">SNR / 10 dB × 40 pts</span><span class="score-info-max">≤ 40</span></div>
                <div class="score-info-row"><span class="score-info-metric">Amplitude</span><span class="score-info-formula">RMS / 0,035 × 35 pts</span><span class="score-info-max">≤ 35</span></div>
                <div class="score-info-row"><span class="score-info-metric">Zone</span><span class="score-info-formula">Couverture / 25% × 25 pts</span><span class="score-info-max">≤ 25</span></div>
                <div class="score-info-note">RMS = amplitude quadratique · TMS = Template Matching Score · SNR = Rapport Signal/Bruit</div>
              </div>
              <div v-if="!result.quality?.recommendations?.length" class="rec-ok">
                <v-icon size="13" color="#22d47e">mdi-check-circle</v-icon>
                Signal de bonne qualité — aucune recommandation
              </div>
              <div v-for="r in result.quality?.recommendations" :key="r" class="rec-item">
                <v-icon size="12" color="#f59e0b">mdi-arrow-right-circle-outline</v-icon> {{ r }}
              </div>
            </div>
          </div>
        </v-col>
      </v-row>

      <!-- ── Masque spatial ─────────────────────────────────────── -->
      <div class="card-block mb-5">
        <div class="card-head">
          <v-icon size="13" color="#a78bfa">mdi-draw-pen</v-icon>
          Zone de plaie (masque spatial)
          <span v-if="maskSaved" class="mask-badge mask-badge--on">Masque actif</span>
          <span v-else class="mask-badge mask-badge--off">Aucun masque</span>
          <div class="mask-tools">
            <label class="mask-label">Pinceau</label>
            <input type="range" v-model.number="brushSize" min="4" max="48" step="2" class="brush-slider" />
            <button class="btn-mask" :class="{ 'btn-mask--active': !erasing }" @click="erasing = false"><v-icon size="13">mdi-brush</v-icon></button>
            <button class="btn-mask" :class="{ 'btn-mask--active': erasing }" @click="erasing = true"><v-icon size="13">mdi-eraser</v-icon></button>
            <button class="btn-mask" @click="runAutoSegment" :disabled="autoSegLoading" title="Segmentation automatique Otsu"><v-icon size="13">mdi-auto-fix</v-icon> Auto</button>
            <button class="btn-mask btn-mask--clear" @click="clearMask"><v-icon size="13">mdi-trash-can-outline</v-icon> Effacer</button>
            <button class="btn-mask btn-mask--save" @click="saveMask" :disabled="maskSaving">
              <v-icon size="13">mdi-content-save-outline</v-icon> {{ maskSaving ? "Enregistrement…" : "Sauvegarder" }}
            </button>
          </div>
        </div>
        <div class="mask-canvas-wrap">
          <canvas ref="maskBgCanvas" class="mask-bg" />
          <canvas ref="maskDrawCanvas" class="mask-draw"
            @mousedown="startDraw" @mousemove="draw" @mouseup="stopDraw"
            @mouseleave="stopDraw" @touchstart.prevent="startDraw" @touchmove.prevent="draw" @touchend="stopDraw" />
          <div v-if="!thumbnail" class="mask-placeholder">
            <v-icon size="32" style="color:var(--border2)">mdi-image-outline</v-icon>
            <span>Chargement de l'aperçu…</span>
          </div>
        </div>
        <div v-if="maskNeedsReanalysis" class="mask-reanalyze-banner">
          <v-icon size="13" color="#f59e0b">mdi-refresh-circle</v-icon>
          Masque enregistré — les résultats actuels ne l'intègrent pas encore.
          <button class="btn-reanalyze" @click="runAnalysis(true)" :disabled="loading">
            {{ loading ? 'Calcul…' : 'Relancer l\'analyse' }}
          </button>
        </div>
        <p v-else class="mask-hint">Peindre la zone de plaie en blanc · le masque sera appliqué à la prochaine analyse (bouton "Relancer").</p>
      </div>

      <!-- ── POS local vs global (si pixel cliqué) ─────────────── -->
      <div v-if="pixelSignal || pixelLoading" class="card-block mb-5">
        <div class="card-head">
          <v-icon size="13" color="#e8622a">mdi-vector-combine</v-icon>
          POS local vs global
          <span class="head-hint">r = corrélation de Pearson entre signal local (pixel) et signal global (moyenne spatiale)</span>
          <span v-if="pixelSignal" class="head-value" style="color:var(--muted);font-weight:500">pixel ({{ pixelSignal.pixel.x }}, {{ pixelSignal.pixel.y }})</span>
          <button v-if="pixelSignal" class="close-btn" @click="pixelSignal = null"><v-icon size="13">mdi-close</v-icon></button>
        </div>
        <div v-if="pixelLoading" style="display:flex;align-items:center;justify-content:center;height:180px;gap:10px">
          <v-progress-circular indeterminate size="20" width="2" color="#e8622a" />
          <span style="font-size:0.82rem;color:var(--muted)">Calcul POS local…</span>
        </div>
        <div v-else style="padding:8px 4px">
          <v-chart :option="pixelChartOption" autoresize style="height:200px" />
        </div>
        <div class="pixel-legend">
          <span class="pleg pleg-global">— Signal global</span>
          <span class="pleg pleg-local">— Signal local</span>
          <span v-if="pixelSignal" class="pleg" style="color:var(--muted)">r = {{ pixelCorr }}</span>
        </div>
      </div>

      <!-- ── Annoter le scénario ─────────────────────────────────── -->
      <div class="card-block mb-5">
        <div class="card-head">
          <v-icon size="13" color="#e8622a">mdi-tag-outline</v-icon>
          Annoter le scénario
        </div>
        <div class="scenario-form">
          <v-select v-model="scenarioLabel" :items="scenarioOptions" label="Type de tissu"
            density="compact" variant="outlined" hide-details />
          <v-text-field v-model="scenarioZone" label="Zone anatomique" density="compact"
            variant="outlined" hide-details placeholder="Ex: paume droite" />
          <v-text-field v-model="scenarioDesc" label="Description" density="compact"
            variant="outlined" hide-details placeholder="Ex: éclairage LED, repos" />
          <button class="btn-accent-sm" @click="saveTag" :disabled="!scenarioLabel">Enregistrer</button>
        </div>
      </div>

      <!-- ── Analyses avancées ───────────────────────────────────── -->
      <div class="advanced-toggle mb-3" @click="showAdvanced = !showAdvanced">
        <div class="adv-left">
          <v-icon size="14" color="#a78bfa">mdi-flask-outline</v-icon>
          <span>Analyses avancées</span>
          <div class="adv-chips">
            <span class="adv-chip">POS · CHROM · LGI</span>
            <span class="adv-chip">HRV</span>
            <span class="adv-chip">STFT</span>
            <span class="adv-chip">Zones 3D</span>
            <span class="adv-chip">ROI double</span>
          </div>
        </div>
        <v-icon size="16" color="#55556a" :style="{ transform: showAdvanced ? 'rotate(180deg)' : '', transition: 'transform 0.2s' }">mdi-chevron-down</v-icon>
      </div>

      <template v-if="showAdvanced">
        <!-- Algos + Respiration+HRV + Mouvement -->
        <v-row class="mb-5">
          <v-col cols="12" md="4">
            <div class="card-block">
              <div class="card-head">
                <v-icon size="13" color="#06b6d4">mdi-compare</v-icon>
                Comparaison algorithmes rPPG
                <span class="head-hint">rPPG = remote PhotoPlethysmoGraphy — mesure du pouls par caméra sans contact</span>
              </div>
              <div style="padding:12px 14px; display:flex; flex-direction:column; gap:10px">
                <div class="algo-row">
                  <span class="algo-name" title="Plane Orthogonal to Skin — Wang et al. IEEE TBME 2017">POS</span>
                  <span class="algo-val">{{ result.hr?.hr_bpm }} bpm</span>
                  <span class="algo-snr" :class="(result.snr?.mean_snr||0)>=3?'snr-ok':'snr-bad'">{{ result.snr?.mean_snr }} dB</span>
                </div>
                <div class="algo-row">
                  <span class="algo-name" title="CHROMinance-based — de Haan & Jeanne, IEEE TBME 2013">CHROM</span>
                  <span class="algo-val">{{ result.chrom?.hr_bpm ?? '—' }} bpm</span>
                  <span class="algo-snr" :class="(result.chrom?.snr_db||0)>=3?'snr-ok':'snr-bad'">{{ result.chrom?.snr_db ?? '—' }} dB</span>
                </div>
                <div class="algo-row">
                  <span class="algo-name" title="Local Group Invariance — Pilz et al. CVPRW 2018 · robuste peaux sombres">LGI</span>
                  <span class="algo-val">{{ result.lgi?.hr_bpm ?? '—' }} bpm</span>
                  <span class="algo-snr" :class="(result.lgi?.snr_db||0)>=3?'snr-ok':'snr-bad'">{{ result.lgi?.snr_db ?? '—' }} dB</span>
                </div>
                <div class="algo-legend"><span>bpm = battements/min · dB = décibels (SNR)</span></div>
                <div class="algo-hint">
                  <v-icon size="11" color="#a78bfa">mdi-information-outline</v-icon>
                  {{ algoConsistency }}
                </div>
                <div v-if="result.hr_ci" class="algo-ci">
                  <v-icon size="10" color="#55556a">mdi-trending-neutral</v-icon>
                  IC {{ result.hr_ci.ci_pct }}% : {{ result.hr_ci.hr_ci_lo }}–{{ result.hr_ci.hr_ci_hi }} bpm · σ={{ result.hr_ci.hr_std }} bpm
                  <span class="algo-ci-note">(IC = Intervalle de Confiance, {{ result.hr_ci.n_windows }} fenêtres)</span>
                </div>
                <v-chart v-if="chromChartOption" :option="chromChartOption" autoresize style="height:80px" />
              </div>
            </div>
          </v-col>

          <v-col cols="12" md="4">
            <div class="card-block mb-4">
              <div class="card-head">
                <v-icon size="13" color="#22d3ee">mdi-lungs</v-icon>
                Fréquence respiratoire
                <span class="head-hint">Estimée par filtrage [0,15–0,50 Hz] sur le canal vert · rpm = respirations/min · Normale : 12–20 rpm</span>
                <span class="head-value">{{ result.respiration?.rr_bpm ?? '—' }} rpm</span>
              </div>
              <div style="padding:14px;display:flex;flex-direction:column;align-items:center;gap:6px">
                <div class="big-metric" style="color:#22d3ee">{{ result.respiration?.rr_bpm ?? '—' }}<span style="font-size:1rem;font-weight:400;color:var(--muted)"> rpm</span></div>
                <span class="tms-chip" :class="rrClass">{{ rrLabel }}</span>
              </div>
            </div>
            <div class="card-block">
              <div class="card-head">
                <v-icon size="13" color="#f43f5e">mdi-heart-pulse</v-icon>
                HRV — Variabilité de la Fréquence Cardiaque
                <span class="head-hint">Heart Rate Variability — fluctuations des intervalles RR entre battements</span>
              </div>
              <div v-if="result.hrv?.sdnn_ms" style="padding:12px 14px;display:grid;grid-template-columns:1fr 1fr;gap:8px">
                <div class="hrv-cell" title="Standard Deviation of NN intervals — écart-type des intervalles RR">
                  <div class="hrv-label">SDNN <span class="hrv-acro">écart-type RR</span></div>
                  <div class="hrv-val">{{ result.hrv?.sdnn_ms }} ms</div>
                </div>
                <div class="hrv-cell" title="Root Mean Square of Successive Differences — variabilité beat-to-beat">
                  <div class="hrv-label">RMSSD <span class="hrv-acro">variabilité bat/bat</span></div>
                  <div class="hrv-val">{{ result.hrv?.rmssd_ms }} ms</div>
                </div>
                <div class="hrv-cell" title="Pourcentage de différences successives RR supérieures à 50 ms">
                  <div class="hrv-label">pNN50 <span class="hrv-acro">%ΔRR &gt; 50 ms</span></div>
                  <div class="hrv-val">{{ result.hrv?.pnn50 }}%</div>
                </div>
                <div class="hrv-cell">
                  <div class="hrv-label">Pics PPG <span class="hrv-acro">ondes systoliques</span></div>
                  <div class="hrv-val">{{ result.hrv?.n_peaks }}</div>
                </div>
              </div>
              <div v-else style="padding:14px;font-size:0.8rem;color:var(--muted)">Signal trop court pour HRV (minimum 5 pics requis).</div>
            </div>
          </v-col>

          <v-col cols="12" md="4">
            <div class="card-block">
              <div class="card-head">
                <v-icon size="13" :color="motionColor">mdi-motion</v-icon>
                Artefacts de mouvement
                <span class="head-value" :style="{ color: motionColor }">{{ result.motion?.pct_bad ?? '—' }}%</span>
              </div>
              <div style="padding:14px;display:flex;flex-direction:column;gap:10px">
                <div style="display:flex;align-items:center;gap:10px">
                  <div class="big-metric" :style="{ color: motionColor }">{{ result.motion?.pct_bad ?? '—' }}<span style="font-size:1rem;font-weight:400;color:var(--muted)">%</span></div>
                  <span class="tms-chip" :style="motionChipStyle">{{ motionLabel }}</span>
                </div>
                <div v-if="result.motion?.diff?.length"><v-chart :option="motionChartOption" autoresize style="height:80px" /></div>
                <p style="font-size:0.72rem;color:var(--muted);margin:0">{{ result.motion?.n_bad ?? 0 }} frames corrompues / {{ result.n_frames }}</p>
              </div>
            </div>
          </v-col>
        </v-row>

        <!-- STFT -->
        <div class="card-block mb-5">
          <div class="card-head">
            <v-icon size="13" color="#f59e0b">mdi-chart-scatter-plot</v-icon>
            Spectrogramme STFT
            <span class="head-hint">STFT = Short-Time Fourier Transform — évolution temporelle de la fréquence cardiaque dominante</span>
            <span v-if="result.hr?.hr_bpm" class="head-value">{{ result.hr?.hr_bpm }} bpm</span>
          </div>
          <div style="padding:8px">
            <v-chart v-if="stftChartOption" :option="stftChartOption" autoresize style="height:200px" />
          </div>
        </div>

        <!-- Zones + 3D -->
        <div class="card-block mb-5">
          <div class="card-head">
            <v-icon size="13" color="#a78bfa">mdi-grid</v-icon>
            Analyse par zones — grille spatiale
            <span class="head-hint">Divise l'image en N×M zones, calcule HR et SNR indépendamment par zone</span>
          </div>
          <div style="padding:14px;display:flex;flex-direction:column;gap:14px">
            <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
              <div style="display:flex;align-items:center;gap:8px">
                <span style="font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.4px">Lignes</span>
                <v-slider v-model="zoneRows" :min="2" :max="8" :step="1" density="compact" hide-details style="width:100px" color="#a78bfa" />
                <span style="font-size:0.8rem;font-weight:700;color:var(--text);min-width:14px">{{ zoneRows }}</span>
              </div>
              <div style="display:flex;align-items:center;gap:8px">
                <span style="font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.4px">Colonnes</span>
                <v-slider v-model="zoneCols" :min="2" :max="8" :step="1" density="compact" hide-details style="width:100px" color="#a78bfa" />
                <span style="font-size:0.8rem;font-weight:700;color:var(--text);min-width:14px">{{ zoneCols }}</span>
              </div>
              <button class="btn-accent-sm" @click="fetchZones" :disabled="zoneLoading">
                <v-icon size="13">mdi-play-circle-outline</v-icon>
                {{ zoneLoading ? 'Calcul…' : `Analyser ${zoneRows}×${zoneCols}` }}
              </button>
            </div>

            <div v-if="zoneResult" style="display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap">
              <div>
                <div class="zone-legend">
                  <span style="font-size:0.68rem;font-weight:700;color:var(--muted)">SNR</span>
                  <div style="display:flex;gap:2px;align-items:center">
                    <div v-for="c in snrColorScale" :key="c" :style="{width:'14px',height:'8px',background:c,borderRadius:'2px'}" />
                  </div>
                  <span style="font-size:0.65rem;color:var(--muted)">bas → haut</span>
                </div>
                <div class="zone-grid" :style="`grid-template-columns: repeat(${zoneResult.n_cols}, 1fr);`">
                  <div v-for="zone in zoneResult.zones" :key="zone.id"
                    class="zone-cell"
                    :class="{ 'zone-cell--inactive': !zone.active, 'zone-cell--selected': selectedZone?.id === zone.id }"
                    :style="zoneCellStyle(zone)"
                    @click="zone.active && (selectedZone = zone)">
                    <template v-if="zone.active">
                      <div class="zone-hr">{{ zone.hr_bpm }}</div>
                      <div class="zone-snr">{{ zone.snr_db }}dB</div>
                    </template>
                    <v-icon v-else size="10" style="color:#2a2a3a">mdi-close</v-icon>
                  </div>
                </div>
                <div style="display:flex;gap:10px;margin-top:6px">
                  <span style="font-size:0.7rem;color:var(--muted)">{{ zoneResult.zones.filter(z=>z.active).length }} zones actives</span>
                  <span style="font-size:0.7rem;color:var(--muted)">HR moy. <b style="color:var(--warn)">{{ zoneHrMean }}</b> bpm</span>
                  <span style="font-size:0.7rem;color:var(--muted)">SNR moy. <b style="color:#06b6d4">{{ zoneSnrMean }}</b> dB</span>
                </div>
              </div>
              <div v-if="selectedZone" style="min-width:280px;flex:1">
                <div style="font-size:0.75rem;font-weight:700;color:var(--text);margin-bottom:8px">
                  Zone ({{ selectedZone.r }},{{ selectedZone.c }}) —
                  <span style="color:var(--warn)">{{ selectedZone.hr_bpm }} bpm</span>
                  · <span style="color:#06b6d4">{{ selectedZone.snr_db }} dB</span>
                </div>
                <v-chart v-if="zoneSignalOption" :option="zoneSignalOption" autoresize style="height:140px" />
              </div>
            </div>

          </div>
        </div>

        <!-- ROI double -->
        <div class="card-block mb-5">
          <div class="card-head">
            <v-icon size="13" color="#e8622a">mdi-compare-horizontal</v-icon>
            ROI double — Plaie vs peau saine
            <span class="head-hint">ROI = Region Of Interest — compare le signal rPPG sur deux zones distinctes</span>
            <button class="btn-ghost btn-ghost--sm" style="margin-left:auto" @click="showDualRoi = !showDualRoi">
              <v-icon size="12">{{ showDualRoi ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              {{ showDualRoi ? 'Masquer' : 'Configurer' }}
            </button>
          </div>
          <div v-if="showDualRoi" style="padding:14px;display:flex;flex-direction:column;gap:12px">
            <p style="font-size:0.8rem;color:var(--muted);margin:0">Coordonnées (x, y, largeur, hauteur) en résolution d'analyse (64×64 px).</p>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
              <div>
                <div class="param-label mb-2" style="color:#e8622a">Zone plaie</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
                  <v-text-field v-model.number="dualRoiWound[0]" label="x" density="compact" variant="outlined" type="number" hide-details />
                  <v-text-field v-model.number="dualRoiWound[1]" label="y" density="compact" variant="outlined" type="number" hide-details />
                  <v-text-field v-model.number="dualRoiWound[2]" label="w" density="compact" variant="outlined" type="number" hide-details />
                  <v-text-field v-model.number="dualRoiWound[3]" label="h" density="compact" variant="outlined" type="number" hide-details />
                </div>
              </div>
              <div>
                <div class="param-label mb-2" style="color:#22d3ee">Peau saine</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
                  <v-text-field v-model.number="dualRoiHealthy[0]" label="x" density="compact" variant="outlined" type="number" hide-details />
                  <v-text-field v-model.number="dualRoiHealthy[1]" label="y" density="compact" variant="outlined" type="number" hide-details />
                  <v-text-field v-model.number="dualRoiHealthy[2]" label="w" density="compact" variant="outlined" type="number" hide-details />
                  <v-text-field v-model.number="dualRoiHealthy[3]" label="h" density="compact" variant="outlined" type="number" hide-details />
                </div>
              </div>
            </div>
            <button class="btn-accent-sm" style="align-self:flex-start" @click="fetchDualRoi" :disabled="dualRoiLoading">
              {{ dualRoiLoading ? 'Calcul…' : 'Comparer les deux zones' }}
            </button>
            <div v-if="dualRoiResult" class="dual-result">
              <div class="dual-col" style="border-color:rgba(232,98,42,0.3)">
                <div class="dual-title" style="color:#e8622a">Plaie</div>
                <div class="dual-metric">HR : <b>{{ dualRoiResult.wound?.hr?.hr_bpm }} bpm</b></div>
                <div class="dual-metric">SNR : <b>{{ dualRoiResult.wound?.snr?.mean_snr }} dB</b></div>
                <div class="dual-metric">TMS : <b>{{ ((dualRoiResult.wound?.tms?.tms||0)*100).toFixed(1) }}%</b></div>
              </div>
              <div class="dual-ratio">
                <div style="font-size:0.68rem;color:var(--muted);margin-bottom:4px">Ratio perfusion</div>
                <div style="font-size:2rem;font-weight:900;color:var(--accent)">{{ dualRoiResult.perfusion_ratio }}</div>
                <div style="font-size:0.7rem;color:var(--muted)">plaie / saine</div>
                <div style="font-size:0.75rem;margin-top:8px">ΔHR : <b :style="{color:Math.abs(dualRoiResult.hr_diff_bpm)>10?'var(--warn)':'var(--green)'}">{{ dualRoiResult.hr_diff_bpm > 0 ? '+' : '' }}{{ dualRoiResult.hr_diff_bpm }} bpm</b></div>
                <div style="font-size:0.75rem">ΔSNR : <b :style="{color:dualRoiResult.snr_diff_db>0?'var(--green)':'var(--warn)'}">{{ dualRoiResult.snr_diff_db > 0 ? '+' : '' }}{{ dualRoiResult.snr_diff_db }} dB</b></div>
              </div>
              <div class="dual-col" style="border-color:rgba(34,211,238,0.3)">
                <div class="dual-title" style="color:#22d3ee">Peau saine</div>
                <div class="dual-metric">HR : <b>{{ dualRoiResult.healthy?.hr?.hr_bpm }} bpm</b></div>
                <div class="dual-metric">SNR : <b>{{ dualRoiResult.healthy?.snr?.mean_snr }} dB</b></div>
                <div class="dual-metric">TMS : <b>{{ ((dualRoiResult.healthy?.tms?.tms||0)*100).toFixed(1) }}%</b></div>
              </div>
            </div>
          </div>
        </div>

        <!-- IA Interpretation -->
        <div v-if="result.interpretation" class="interp-block mb-4">
          <div class="interp-header">
            <div class="interp-icon"><v-icon size="16" color="#e8622a">mdi-brain</v-icon></div>
            <div>
              <div class="interp-title">Interprétation scientifique</div>
              <div class="interp-algo">{{ result.interpretation.algorithm }} · Rule-based</div>
            </div>
            <span class="interp-badge">ST-rPPG</span>
          </div>
          <p class="interp-narrative">{{ result.interpretation.narrative }}</p>
          <div class="interp-grid">
            <div v-for="item in interpItems" :key="item.key" class="interp-item" :style="{ '--ic': item.color }">
              <div class="item-icon"><v-icon size="14" :style="{ color: item.color }">{{ item.icon }}</v-icon></div>
              <div class="item-content">
                <div class="item-label">{{ item.label }}</div>
                <div class="item-short" :style="{ color: item.color }">{{ item.short }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import axios from "axios";
import { useSessionStore } from "../stores/session.js";
import { apiUrl } from "../lib/api.js";
import MetricCard   from "../components/ui/MetricCard.vue";
import QualityBadge from "../components/ui/QualityBadge.vue";
import SignalChart  from "../components/charts/SignalChart.vue";
import FFTChart     from "../components/charts/FFTChart.vue";
import SpatialMap   from "../components/charts/SpatialMap.vue";
import SNRChart     from "../components/charts/SNRChart.vue";

const route = useRoute();
const store = useSessionStore();
const sessionId = computed(() => route.params.id);
const result  = ref(null);
const loading = ref(false);

// ── Pixel POS comparison ──────────────────────────────────────────────────────
const pixelSignal  = ref(null);
const pixelLoading = ref(false);

async function fetchPixelSignal({ nx, ny }) {
  pixelLoading.value = true;
  pixelSignal.value  = null;
  try {
    const { data } = await axios.post(
      apiUrl(`/analysis/${sessionId.value}/pixel_pos`),
      { nx, ny },
    );
    pixelSignal.value = data;
  } finally {
    pixelLoading.value = false;
  }
}

function pearson(a, b) {
  const n = Math.min(a.length, b.length);
  if (n < 2) return 0;
  const ma = a.slice(0, n).reduce((s, v) => s + v, 0) / n;
  const mb = b.slice(0, n).reduce((s, v) => s + v, 0) / n;
  let num = 0, da = 0, db = 0;
  for (let i = 0; i < n; i++) {
    const ai = a[i] - ma, bi = b[i] - mb;
    num += ai * bi; da += ai * ai; db += bi * bi;
  }
  return da && db ? num / Math.sqrt(da * db) : 0;
}

const pixelCorr = computed(() => {
  if (!pixelSignal.value) return "—";
  const r = pearson(pixelSignal.value.global, pixelSignal.value.local);
  return r.toFixed(3);
});

const CHART_C = { bg: "transparent", border: "#1a1a2e", muted: "#55556a", text: "#b8b8cc" };

const pixelChartOption = computed(() => {
  if (!pixelSignal.value) return {};
  const { global: g, local: l, time: t } = pixelSignal.value;
  const n = Math.min(g.length, l.length, t.length);
  const gd = g.slice(0, n).map((v, i) => [t[i], +v.toFixed(4)]);
  const ld = l.slice(0, n).map((v, i) => [t[i], +v.toFixed(4)]);
  return {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", formatter: ps =>
      `<b>${(+ps[0].value[0]).toFixed(2)}s</b><br/>` +
      ps.map(p => `<span style="color:${p.color}">●</span> ${p.seriesName}: ${(+p.value[1]).toFixed(3)}`).join("<br/>")
    },
    legend: { data: ["Global", "Local"], textStyle: { color: CHART_C.muted, fontSize: 11 }, top: 0, right: 0 },
    grid: { left: 40, right: 20, top: 28, bottom: 30 },
    xAxis: {
      type: "value", name: "s", min: t[0], max: t[n - 1],
      nameTextStyle: { color: CHART_C.muted, fontSize: 10 },
      axisLabel: { color: CHART_C.muted, fontSize: 10 },
      axisLine: { lineStyle: { color: CHART_C.border } },
      splitLine: { show: false },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: CHART_C.muted, fontSize: 10 },
      splitLine: { lineStyle: { color: CHART_C.border } },
    },
    series: [
      {
        name: "Global", type: "line", data: gd, smooth: true, symbol: "none",
        lineStyle: { color: "#06b6d4", width: 1.8 },
        areaStyle: { color: "rgba(6,182,212,0.06)" },
      },
      {
        name: "Local", type: "line", data: ld, smooth: true, symbol: "none",
        lineStyle: { color: "#e8622a", width: 1.8 },
        areaStyle: { color: "rgba(232,98,42,0.06)" },
      },
    ],
  };
});

// ── CHROM chart ──────────────────────────────────────────────────────────────
const chromChartOption = computed(() => {
  if (!result.value?.chrom?.signal?.length || !result.value?.signal?.time?.length) return null;
  const t = result.value.signal.time;
  const pos = result.value.signal.filt;
  const chr = result.value.chrom.signal;
  const n = Math.min(t.length, pos.length, chr.length);
  return {
    backgroundColor: "transparent",
    grid: { left: 8, right: 8, top: 4, bottom: 4 },
    xAxis: { type: "value", show: false, min: t[0], max: t[n-1] },
    yAxis: { type: "value", show: false },
    series: [
      { type: "line", data: pos.slice(0,n).map((v,i)=>[t[i],v]), smooth: true, symbol: "none",
        lineStyle: { color: "#e8622a", width: 1.4 }, areaStyle: { color: "rgba(232,98,42,0.05)" } },
      { type: "line", data: chr.slice(0,n).map((v,i)=>[t[i],v]), smooth: true, symbol: "none",
        lineStyle: { color: "#06b6d4", width: 1.4 }, areaStyle: { color: "rgba(6,182,212,0.05)" } },
    ],
  };
});

const algoConsistency = computed(() => {
  const hrs = [
    result.value?.hr?.hr_bpm,
    result.value?.chrom?.hr_bpm,
    result.value?.lgi?.hr_bpm,
  ].filter(v => v != null);
  if (hrs.length < 2) return "Données insuffisantes";
  const spread = Math.max(...hrs) - Math.min(...hrs);
  if (spread < 3)  return `Consensus fort (Δ ${spread.toFixed(1)} bpm) — fiable`;
  if (spread < 8)  return `Divergence modérée (Δ ${spread.toFixed(1)} bpm)`;
  return `Divergence forte (Δ ${spread.toFixed(1)} bpm) — artefacts probables`;
});

// ── Motion chart ──────────────────────────────────────────────────────────────
const motionColor = computed(() => {
  const s = result.value?.motion?.severity;
  if (s === "none" || !s) return "var(--green)";
  if (s === "low") return "var(--green)";
  if (s === "moderate") return "var(--warn)";
  return "var(--danger)";
});
const motionLabel = computed(() => {
  const s = result.value?.motion?.severity;
  return { none: "Aucun artefact", low: "Faible", moderate: "Modéré", high: "Élevé" }[s] ?? "—";
});
const motionChipStyle = computed(() => {
  const c = motionColor.value;
  return { background: `${c}18`, color: c, border: `1px solid ${c}44` };
});
const motionChartOption = computed(() => {
  const diff = result.value?.motion?.diff;
  const thr  = result.value?.motion?.threshold;
  if (!diff?.length) return null;
  const fps  = result.value?.fps || 30;
  return {
    backgroundColor: "transparent",
    grid: { left: 4, right: 4, top: 4, bottom: 4 },
    xAxis: { type: "value", show: false },
    yAxis: { type: "value", show: false },
    series: [
      { type: "line", data: diff.map((v,i)=>[i/fps,v]), smooth: false, symbol: "none",
        lineStyle: { color: "#55556a", width: 1 },
        markLine: thr ? { silent: true, data:[{yAxis: thr}],
          lineStyle: { color: "var(--danger)", type: "dashed", width: 1 },
          label: { show: false } } : undefined,
      },
    ],
  };
});

// ── Respiratory quality ───────────────────────────────────────────────────────
const rrClass = computed(() => {
  const rr = result.value?.respiration?.rr_bpm;
  if (!rr) return "chip-gray";
  if (rr >= 12 && rr <= 20) return "chip-green";
  if (rr >= 8  && rr <= 25) return "chip-warn";
  return "chip-warn";
});
const rrLabel = computed(() => {
  const rr = result.value?.respiration?.rr_bpm;
  if (!rr) return "Non détecté";
  if (rr >= 12 && rr <= 20) return "Normal (12–20 rpm)";
  if (rr < 12) return "Bradypnée (<12 rpm)";
  return "Tachypnée (>20 rpm)";
});

// ── STFT chart ────────────────────────────────────────────────────────────────
const stftChartOption = computed(() => {
  const stft = result.value?.stft;
  if (!stft?.time?.length || !stft?.freq?.length) return null;
  const { time, freq, power } = stft;

  const data = [];
  for (let fi = 0; fi < freq.length; fi++) {
    for (let ti = 0; ti < time.length; ti++) {
      data.push([ti, fi, power[fi][ti]]);
    }
  }
  return {
    backgroundColor: "transparent",
    tooltip: { formatter: p => `${time[p.data[0]].toFixed(1)}s / ${(freq[p.data[1]]*60).toFixed(0)} bpm` },
    grid: { left: 48, right: 16, top: 8, bottom: 32 },
    xAxis: { type: "category", data: time.map(t => t.toFixed(1)),
      axisLabel: { color: "#55556a", fontSize: 9, interval: Math.floor(time.length/6) },
      name: "s", nameTextStyle: { color: "#55556a", fontSize: 9 } },
    yAxis: { type: "category", data: freq.map(f => (f*60).toFixed(0)),
      axisLabel: { color: "#55556a", fontSize: 9 },
      name: "bpm", nameTextStyle: { color: "#55556a", fontSize: 9 } },
    visualMap: { min: 0, max: 1, show: false,
      inRange: { color: ["#0d1117","#1a3a5c","#00c8ff","#7ee787","#f0883e","#f85149"] } },
    series: [{ type: "heatmap", data, emphasis: { disabled: true } }],
  };
});

// ── Zone grid analysis ────────────────────────────────────────────────────────
const zoneResult   = ref(null);
const zoneLoading  = ref(false);
const showZones    = ref(false);
const zoneRows     = ref(4);
const zoneCols     = ref(4);
const selectedZone = ref(null);

const snrColorScale = ["#1a1a2e","#1e3a5f","#0369a1","#0ea5e9","#22d3ee","#22d47e"];

function snrToColor(snr) {
  if (snr === null || snr === undefined) return snrColorScale[0];
  if (snr < 0)  return snrColorScale[0];
  if (snr < 2)  return snrColorScale[1];
  if (snr < 4)  return snrColorScale[2];
  if (snr < 6)  return snrColorScale[3];
  if (snr < 10) return snrColorScale[4];
  return snrColorScale[5];
}

function zoneCellStyle(zone) {
  if (!zone.active) return { background: "#0a0a12", borderColor: "#1a1a2e", cursor: "default" };
  const col = snrToColor(zone.snr_db);
  return { background: `${col}30`, borderColor: col, cursor: "pointer" };
}

async function fetchZones() {
  zoneLoading.value  = true;
  zoneResult.value   = null;
  selectedZone.value = null;
  try {
    const { data } = await axios.post(
      apiUrl(`/analysis/${sessionId.value}/zones?n_rows=${zoneRows.value}&n_cols=${zoneCols.value}&surface=true`),
      {},
    );
    zoneResult.value = data;
  } finally {
    zoneLoading.value = false;
  }
}

const zoneHrMean = computed(() => {
  const active = zoneResult.value?.zones?.filter(z => z.active && z.hr_bpm);
  if (!active?.length) return "—";
  return (active.reduce((s, z) => s + z.hr_bpm, 0) / active.length).toFixed(1);
});

const zoneSnrMean = computed(() => {
  const active = zoneResult.value?.zones?.filter(z => z.active && z.snr_db !== null);
  if (!active?.length) return "—";
  return (active.reduce((s, z) => s + z.snr_db, 0) / active.length).toFixed(1);
});

const zoneSignalOption = computed(() => {
  const z = selectedZone.value;
  if (!z?.signal?.length) return null;
  const fps = zoneResult.value?.fps || 30;
  const t   = z.signal.map((_, i) => +(i / fps).toFixed(3));
  return {
    backgroundColor: "transparent",
    grid: { left: 36, right: 8, top: 8, bottom: 28 },
    xAxis: {
      type: "value", min: 0, max: t[t.length - 1],
      axisLabel: { color: "#55556a", fontSize: 9 },
      axisLine: { lineStyle: { color: "#1a1a2e" } },
      splitLine: { show: false },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#55556a", fontSize: 9 },
      splitLine: { lineStyle: { color: "#1a1a2e" } },
    },
    series: [{
      type: "line",
      data: z.signal.map((v, i) => [t[i], +v.toFixed(4)]),
      smooth: true, symbol: "none",
      lineStyle: { color: "#a78bfa", width: 1.6 },
      areaStyle: { color: "rgba(167,139,250,0.1)" },
    }],
  };
});

const zoneSurfaceOption = computed(() => {
  const surf = zoneResult.value?.surface3d;
  if (!surf?.data?.length) return null;
  const snrVals = surf.data.map(d => d[3]).filter(v => v !== null && !isNaN(v));
  const minSnr  = snrVals.length ? Math.min(...snrVals) : -10;
  const maxSnr  = snrVals.length ? Math.max(...snrVals) : 20;
  return {
    backgroundColor: "transparent",
    visualMap: {
      show: true,
      dimension: 3,
      min: minSnr,
      max: maxSnr,
      left: 10,
      bottom: 10,
      textStyle: { color: "#55556a", fontSize: 9 },
      inRange: { color: ["#1a1a2e","#1e3a5f","#0369a1","#0ea5e9","#22d3ee","#22d47e","#f59e0b","#e8622a"] },
    },
    grid3D: {
      show: false,
      boxWidth: 180,
      boxHeight: 60,
      boxDepth: 120,
      axisLine: { lineStyle: { color: "#1a1a2e" } },
      splitArea: { show: false },
      splitLine: { lineStyle: { color: "#1a1a2e", opacity: 0.3 } },
    },
    xAxis3D: { type: "value", name: "col", nameTextStyle: { color: "#55556a", fontSize: 9 }, axisLabel: { color: "#55556a", fontSize: 8 } },
    yAxis3D: { type: "value", name: "lig", nameTextStyle: { color: "#55556a", fontSize: 9 }, axisLabel: { color: "#55556a", fontSize: 8 } },
    zAxis3D: { type: "value", name: "amp", nameTextStyle: { color: "#55556a", fontSize: 9 }, axisLabel: { color: "#55556a", fontSize: 8 } },
    series: [{
      type: "surface",
      data: surf.data,
      encode: { x: 0, y: 1, z: 2 },
      wireframe: { show: true, lineStyle: { color: "rgba(255,255,255,0.04)", width: 0.5 } },
      itemStyle: { opacity: 0.92 },
    }],
  };
});

// ── Dual ROI ──────────────────────────────────────────────────────────────────
const showDualRoi    = ref(false);
const dualRoiWound   = ref([0, 0, 16, 16]);
const dualRoiHealthy = ref([32, 0, 16, 16]);
const dualRoiResult  = ref(null);
const dualRoiLoading = ref(false);

async function fetchDualRoi() {
  dualRoiLoading.value = true;
  dualRoiResult.value  = null;
  try {
    const { data } = await axios.post(
      apiUrl(`/analysis/${sessionId.value}/dual_roi`),
      { roi_wound: dualRoiWound.value, roi_healthy: dualRoiHealthy.value }
    );
    dualRoiResult.value = data;
  } finally {
    dualRoiLoading.value = false;
  }
}

// ── Auto-segmentation ─────────────────────────────────────────────────────────
const autoSegLoading = ref(false);

async function runAutoSegment() {
  autoSegLoading.value = true;
  try {
    const { data } = await axios.post(
      apiUrl(`/analysis/${sessionId.value}/auto_segment`), {}
    );
    if (!data.mask_b64 || !maskDrawCanvas.value) return;
    // Draw the auto-generated mask onto the draw canvas
    const ctx = maskDrawCanvas.value.getContext("2d");
    const img = new Image();
    img.onload = () => {
      ctx.clearRect(0, 0, MASK_W, MASK_H);
      ctx.globalCompositeOperation = "source-over";
      ctx.globalAlpha = 0.72;
      ctx.drawImage(img, 0, 0, MASK_W, MASK_H);
      ctx.globalAlpha = 1.0;
    };
    img.src = data.mask_b64;
  } catch {
    /* silent — likely no analysis yet */
  } finally {
    autoSegLoading.value = false;
  }
}

// ── Mask editor ──────────────────────────────────────────────────────────────
const maskBgCanvas   = ref(null);
const maskDrawCanvas = ref(null);
const thumbnail      = ref(null);
const maskSaved             = ref(false);
const maskSaving            = ref(false);
const maskNeedsReanalysis   = ref(false);
const brushSize      = ref(18);
const erasing        = ref(false);
let   isDrawing      = false;

const MASK_W = 320;
const MASK_H = 240;

function getCanvasPos(e, canvas) {
  const rect  = canvas.getBoundingClientRect();
  const touch = e.touches?.[0] || e;
  const scaleX = MASK_W / rect.width;
  const scaleY = MASK_H / rect.height;
  return [(touch.clientX - rect.left) * scaleX, (touch.clientY - rect.top) * scaleY];
}

function paintCircle(x, y) {
  const ctx = maskDrawCanvas.value?.getContext("2d");
  if (!ctx) return;
  ctx.globalCompositeOperation = erasing.value ? "destination-out" : "source-over";
  ctx.fillStyle = "rgba(168,139,250,0.75)";
  ctx.beginPath();
  ctx.arc(x, y, brushSize.value, 0, Math.PI * 2);
  ctx.fill();
}

function startDraw(e) {
  isDrawing = true;
  const [x, y] = getCanvasPos(e, maskDrawCanvas.value);
  paintCircle(x, y);
}
function draw(e) {
  if (!isDrawing) return;
  const [x, y] = getCanvasPos(e, maskDrawCanvas.value);
  paintCircle(x, y);
}
function stopDraw() { isDrawing = false; }

function clearMask() {
  const ctx = maskDrawCanvas.value?.getContext("2d");
  if (!ctx) return;
  ctx.clearRect(0, 0, MASK_W, MASK_H);
}

async function saveMask() {
  const drawCtx = maskDrawCanvas.value?.getContext("2d");
  if (!drawCtx) return;

  // Build binary mask: painted pixels → white, rest → black
  const offscreen = document.createElement("canvas");
  offscreen.width  = MASK_W;
  offscreen.height = MASK_H;
  const off = offscreen.getContext("2d");

  off.fillStyle = "#000";
  off.fillRect(0, 0, MASK_W, MASK_H);

  const imgData = drawCtx.getImageData(0, 0, MASK_W, MASK_H);
  const outData = off.getImageData(0, 0, MASK_W, MASK_H);
  for (let i = 0; i < imgData.data.length; i += 4) {
    if (imgData.data[i + 3] > 64) {   // alpha > 25%
      outData.data[i]     = 255;
      outData.data[i + 1] = 255;
      outData.data[i + 2] = 255;
      outData.data[i + 3] = 255;
    }
  }
  off.putImageData(outData, 0, 0);

  const b64 = offscreen.toDataURL("image/png").split(",")[1];
  maskSaving.value = true;
  try {
    await axios.post(apiUrl(`/sessions/${sessionId.value}/mask`), { mask: b64 });
    maskSaved.value = true;
    maskNeedsReanalysis.value = true;
  } finally {
    maskSaving.value = false;
  }
}

async function loadThumbnailAndMask() {
  try {
    const { data: tData } = await axios.get(apiUrl(`/sessions/${sessionId.value}/thumbnail`));
    thumbnail.value = tData.thumbnail;
    await nextTick();
    if (maskBgCanvas.value) {
      const ctx = maskBgCanvas.value.getContext("2d");
      maskBgCanvas.value.width  = MASK_W;
      maskBgCanvas.value.height = MASK_H;
      maskDrawCanvas.value.width  = MASK_W;
      maskDrawCanvas.value.height = MASK_H;
      const img = new Image();
      img.onload = () => ctx.drawImage(img, 0, 0, MASK_W, MASK_H);
      img.src = `data:image/jpeg;base64,${tData.thumbnail}`;
    }
  } catch { /* no thumbnail yet */ }

  try {
    const { data: mData } = await axios.get(apiUrl(`/sessions/${sessionId.value}/mask`));
    maskSaved.value = mData.has_mask;
    if (mData.has_mask && maskDrawCanvas.value) {
      await nextTick();
      const ctx = maskDrawCanvas.value.getContext("2d");
      const img = new Image();
      img.onload = () => {
        ctx.globalCompositeOperation = "source-over";
        ctx.globalAlpha = 0.75;
        ctx.drawImage(img, 0, 0, MASK_W, MASK_H);
        ctx.globalAlpha = 1.0;
      };
      img.src = `data:image/png;base64,${mData.mask}`;
    }
  } catch { /* no mask */ }
}

// ── Score info toggle ─────────────────────────────────────────────────────────
const showScoreInfo = ref(false);
const showAdvanced  = ref(false);

// ── Scenario tag ──────────────────────────────────────────────────────────────
const scenarioLabel = ref("");
const scenarioZone  = ref("");
const scenarioDesc  = ref("");

const scenarioOptions = [
  "peau_saine", "visage", "main_paume", "main_dos",
  "avant_bras", "tache_naissance", "cicatrice",
  "compression", "plaie_chronique", "autre",
];

onMounted(async () => {
  try { result.value = await store.getResult(sessionId.value); }
  catch { /* not yet analyzed */ }
  loadThumbnailAndMask();
});

async function runAnalysis(force) {
  loading.value = true;
  maskNeedsReanalysis.value = false;
  try { result.value = await store.analyze(sessionId.value, force); }
  finally { loading.value = false; }
}

async function saveTag() {
  await store.tagScenario(sessionId.value, scenarioLabel.value, scenarioDesc.value, scenarioZone.value);
}

const mainMetrics = computed(() => {
  if (!result.value) return [];
  const r = result.value;
  return [
    { label: "HR estimée",  value: r.hr?.hr_bpm,                        unit: "bpm", icon: "mdi-heart-pulse",         color: "var(--warn)"   },
    { label: "SNR moyen",   value: r.snr?.mean_snr,                      unit: "dB",  icon: "mdi-signal",              color: (r.snr?.mean_snr||0) >= 3 ? "var(--green)" : "var(--danger)" },
    { label: "Respiration", value: r.respiration?.rr_bpm ?? "—",         unit: "rpm", icon: "mdi-lungs",               color: "var(--teal)"   },
    { label: "TMS",         value: ((r.tms?.tms||0)*100).toFixed(1),     unit: "%",   icon: "mdi-waveform",            color: r.tms?.is_clean ? "var(--green)" : "var(--warn)" },
    { label: "FPS réel",    value: r.fps?.toFixed(1),                    unit: "Hz",  icon: "mdi-speedometer-outline", color: "var(--accent)"  },
    { label: "Mouvement",   value: r.motion?.pct_bad ?? "—",             unit: "%",   icon: "mdi-motion",              color: (r.motion?.pct_bad||0) < 5 ? "var(--green)" : "var(--warn)" },
  ];
});

const interpItems = computed(() => {
  const i = result.value?.interpretation;
  if (!i) return [];
  return [
    { key: "signal_quality", label: "Qualité signal",   short: i.signal_quality?.short, color: i.signal_quality?.color, icon: "mdi-signal" },
    { key: "heart_rate",     label: "Fréquence card.",  short: i.heart_rate?.short,     color: i.heart_rate?.color,     icon: "mdi-heart-pulse" },
    { key: "morphology",     label: "Morphologie PPG",  short: i.morphology?.short,     color: i.morphology?.color,     icon: "mdi-waveform" },
    { key: "perfusion",      label: "Perfusion",        short: i.perfusion?.short,      color: i.perfusion?.color,      icon: "mdi-map-outline" },
  ];
});
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
  gap: 16px;
}
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.75rem;
  color: var(--muted);
  text-decoration: none;
  margin-bottom: 6px;
  transition: color 0.15s;
}
.back-link:hover { color: var(--accent); }
.page-title { font-size: 1.1rem; font-weight: 800; color: var(--text); margin: 0 0 8px; word-break: break-all; }
.header-actions { display: flex; gap: 8px; flex-shrink: 0; flex-wrap: wrap; }

.btn-ghost {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 14px;
  border-radius: 7px;
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--text2);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: border-color 0.15s;
}
.btn-ghost:hover { border-color: var(--accent); color: var(--accent); }
.btn-ghost:disabled { opacity: 0.4; cursor: default; }
.btn-ghost--warn:hover { border-color: var(--warn); color: var(--warn); }
.btn-ghost--green:hover { border-color: var(--green); color: var(--green); }

.empty-card {
  display: flex; flex-direction: column; align-items: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 64px 32px;
  text-align: center;
  gap: 0;
}

.head-value { margin-left: auto; font-size: 0.88rem; font-weight: 800; color: var(--warn); text-transform: none; letter-spacing: 0; }
.chart-area { padding: 12px 8px 8px; }

/* TMS */
.tms-block { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 20px 16px; }
.tms-value { font-size: 2.8rem; font-weight: 900; letter-spacing: -1px; }
.tms-unit  { font-size: 1.2rem; font-weight: 400; color: var(--muted); margin-left: 2px; }
.tms-chip  { font-size: 0.74rem; font-weight: 700; padding: 3px 12px; border-radius: 6px; }
.chip-green { background: rgba(34,212,126,0.1); color: var(--green); border: 1px solid rgba(34,212,126,0.25); }
.chip-warn  { background: rgba(245,158,11,0.1);  color: var(--warn);  border: 1px solid rgba(245,158,11,0.25); }
.tms-meta   { font-size: 0.73rem; color: var(--muted); margin: 0; }

/* Recommendations */
.rec-ok { display: flex; align-items: center; gap: 7px; font-size: 0.82rem; color: var(--green); font-weight: 500; }
.rec-item { display: flex; align-items: flex-start; gap: 7px; font-size: 0.8rem; color: var(--warn); padding: 5px 0; border-bottom: 1px solid var(--border); }
.rec-item:last-child { border-bottom: none; }

/* Scenario tag */
.btn-accent-sm {
  padding: 8px 16px; border-radius: 7px; background: var(--accent); color: #fff;
  font-size: 0.8rem; font-weight: 600; border: none; cursor: pointer; transition: opacity 0.15s;
}
.btn-accent-sm:hover { opacity: 0.85; }
.btn-accent-sm:disabled { opacity: 0.4; cursor: default; }

/* POS comparison */
.close-btn {
  margin-left: auto; background: none; border: none; color: var(--muted);
  cursor: pointer; padding: 0 2px; display: flex; align-items: center;
  transition: color 0.15s;
}
.close-btn:hover { color: var(--danger); }
.pixel-legend {
  display: flex; gap: 16px; align-items: center; flex-wrap: wrap;
  padding: 8px 14px 14px;
  font-size: 0.73rem;
}
.pleg { font-weight: 600; }
.pleg-global { color: #06b6d4; }
.pleg-local  { color: #e8622a; }

/* AI Interpretation block */
.interp-block {
  background: var(--surface);
  border: 1px solid rgba(232,98,42,0.25);
  border-radius: 12px;
  overflow: hidden;
}
.interp-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  background: rgba(232,98,42,0.05);
}
.interp-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: rgba(232,98,42,0.12);
  border: 1px solid rgba(232,98,42,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.interp-title { font-size: 0.85rem; font-weight: 700; color: var(--text); }
.interp-algo  { font-size: 0.68rem; color: var(--muted); font-family: monospace; margin-top: 2px; }
.interp-badge {
  margin-left: auto;
  font-size: 0.68rem; font-weight: 700;
  padding: 3px 10px; border-radius: 5px;
  background: rgba(232,98,42,0.1);
  border: 1px solid rgba(232,98,42,0.25);
  color: var(--accent);
  letter-spacing: 0.5px;
}
.interp-narrative {
  padding: 16px 20px;
  font-size: 0.85rem;
  color: var(--text2);
  line-height: 1.6;
  margin: 0;
  border-bottom: 1px solid var(--border);
}
.interp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0;
}
.interp-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 20px;
  border-right: 1px solid var(--border);
}
.interp-item:last-child { border-right: none; }
.item-icon {
  width: 30px;
  height: 30px;
  border-radius: 7px;
  background: color-mix(in srgb, var(--ic, #e8622a) 10%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
}
.item-label { font-size: 0.68rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px; }
.item-short { font-size: 0.8rem; font-weight: 600; }

/* CHROM */
.algo-row { display:flex; align-items:center; gap:8px; padding:6px 0; border-bottom:1px solid var(--border); }
.algo-row:last-of-type { border-bottom:none; }
.algo-name { font-size:0.75rem; font-weight:700; color:var(--text); min-width:44px; }
.algo-val  { font-size:0.83rem; font-weight:800; color:var(--warn); flex:1; }
.algo-snr  { font-size:0.73rem; font-weight:700; padding:1px 8px; border-radius:4px; }
.snr-ok    { background:rgba(34,212,126,0.1); color:var(--green); border:1px solid rgba(34,212,126,0.3); }
.snr-bad   { background:rgba(248,81,73,0.1); color:var(--danger); border:1px solid rgba(248,81,73,0.3); }
.algo-hint { font-size:0.72rem; color:var(--muted); display:flex; align-items:center; gap:4px; }

/* Big metric */
.big-metric { font-size:2.4rem; font-weight:900; letter-spacing:-1px; line-height:1; }

/* HRV */
.hrv-cell  { background:var(--surface2); border:1px solid var(--border); border-radius:7px; padding:8px 12px; }
.hrv-label { font-size:0.65rem; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:2px; }
.hrv-val   { font-size:0.95rem; font-weight:800; color:var(--text); }

/* Dual ROI */
.btn-ghost--sm { font-size:0.73rem !important; padding:4px 10px !important; }
.dual-result { display:flex; gap:12px; align-items:stretch; flex-wrap:wrap; }
.dual-col { flex:1; min-width:120px; background:var(--surface2); border:1px solid; border-radius:10px; padding:14px; }
.dual-title  { font-size:0.75rem; font-weight:800; margin-bottom:10px; }
.dual-metric { font-size:0.8rem; color:var(--muted); padding:3px 0; }
.dual-metric b { color:var(--text); }
.dual-ratio  { flex:0 0 130px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }

/* Mask editor */
.mask-badge {
  font-size: 0.68rem; font-weight: 700; padding: 2px 9px; border-radius: 5px;
  text-transform: none; letter-spacing: 0;
}
.mask-badge--on  { background: rgba(168,139,250,0.12); color: #a78bfa; border: 1px solid rgba(168,139,250,0.3); }
.mask-badge--off { background: var(--surface2); color: var(--muted); border: 1px solid var(--border); }
.mask-tools {
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-left: auto;
}
.mask-label { font-size: 0.72rem; color: var(--muted); }
.brush-slider { width: 80px; accent-color: #a78bfa; }
.btn-mask {
  display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px;
  font-size: 0.74rem; font-weight: 600; cursor: pointer; border: 1px solid var(--border);
  background: var(--surface2); color: var(--muted); transition: all 0.15s;
  text-transform: none; letter-spacing: 0;
}
.btn-mask:hover { border-color: #a78bfa; color: #a78bfa; }
.btn-mask--active { border-color: #a78bfa; color: #a78bfa; background: rgba(168,139,250,0.1); }
.btn-mask--clear:hover { border-color: var(--danger); color: var(--danger); }
.btn-mask--save { background: #a78bfa; color: #fff; border-color: #a78bfa; }
.btn-mask--save:hover { opacity: 0.85; }
.btn-mask--save:disabled { opacity: 0.5; cursor: default; }

.mask-canvas-wrap {
  position: relative;
  width: 320px;
  height: 240px;
  margin: 14px auto;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: #000;
}
.mask-bg, .mask-draw {
  position: absolute;
  top: 0; left: 0;
  width: 100%;
  height: 100%;
}
.mask-draw { cursor: crosshair; }
.mask-placeholder {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 8px;
  font-size: 0.8rem; color: var(--muted);
}
.mask-hint { font-size: 0.72rem; color: var(--muted); text-align: center; padding: 0 16px 14px; margin: 0; }

/* Banner après sauvegarde masque */
.mask-reanalyze-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(245,158,11,0.08);
  border-top: 1px solid rgba(245,158,11,0.2);
  padding: 10px 16px;
  font-size: 0.78rem;
  color: #f59e0b;
  font-weight: 500;
}
.btn-reanalyze {
  margin-left: auto;
  padding: 5px 12px;
  border-radius: 6px;
  background: rgba(245,158,11,0.15);
  border: 1px solid rgba(245,158,11,0.35);
  color: #f59e0b;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
  transition: opacity 0.15s;
  white-space: nowrap;
}
.btn-reanalyze:hover { opacity: 0.8; }
.btn-reanalyze:disabled { opacity: 0.4; cursor: default; }

/* Barre d'état masque dans les résultats */
.mask-status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 0.75rem;
}
.mask-status-bar:has(.msk-on)  { background: rgba(167,139,250,0.07); border: 1px solid rgba(167,139,250,0.2); }
.mask-status-bar:has(.msk-off) { background: rgba(245,158,11,0.06);  border: 1px solid rgba(245,158,11,0.2);  }
.msk-on  { font-weight: 700; color: #a78bfa; }
.msk-off { font-weight: 700; color: #f59e0b; }
.msk-sub { color: var(--muted); font-size: 0.7rem; }
.msk-pct { margin-left: auto; font-weight: 700; color: #a78bfa; font-size: 0.72rem; }

/* Card head hint (acronym subtitle) */
.head-hint {
  font-size: 0.62rem; font-weight: 400; color: var(--muted);
  text-transform: none; letter-spacing: 0; margin-left: 6px;
  font-style: italic; line-height: 1.2;
}

/* Algorithm legend */
.algo-legend { display:flex; flex-wrap:wrap; gap:8px; font-size:0.62rem; color:var(--muted); padding:4px 0; border-top:1px solid var(--border); }

/* Algorithm CI */
.algo-ci { font-size:0.7rem; color:var(--muted); display:flex; align-items:center; gap:4px; padding:4px 0; border-top:1px solid var(--border); flex-wrap:wrap; }
.algo-ci-note { font-size:0.62rem; color:var(--muted); font-style:italic; }

/* HRV acronym sub-label */
.hrv-acro { font-size:0.55rem; font-weight:400; color:var(--muted); display:block; margin-top:1px; }

/* Score info box */
.score-info-box { background:var(--surface2); border:1px solid var(--border); border-radius:8px; padding:10px 12px; margin-bottom:10px; }
.score-info-title { font-size:0.72rem; font-weight:700; color:var(--text); margin-bottom:6px; }
.score-info-row { display:flex; align-items:center; gap:6px; padding:3px 0; font-size:0.72rem; }
.score-info-metric { min-width:64px; font-weight:700; color:var(--accent); font-family:monospace; }
.score-info-formula { flex:1; color:var(--text2); }
.score-info-max { font-size:0.65rem; font-weight:700; color:var(--muted); white-space:nowrap; }
.score-info-sep { height:1px; background:var(--border); margin:4px 0; }
.score-info-note { font-size:0.62rem; color:var(--muted); margin-top:6px; font-style:italic; line-height:1.4; }

/* Healing score banner */
.healing-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 20px;
}
.hb-left { flex: 1; min-width: 120px; }
.hb-title { font-size: 0.82rem; font-weight: 800; color: var(--text); }
.hb-sub   { font-size: 0.65rem; color: var(--muted); margin-top: 2px; font-family: monospace; }
.hb-score { font-size: 2.8rem; font-weight: 900; letter-spacing: -1px; line-height: 1; flex-shrink: 0; }
.hb-label { font-size: 0.75rem; font-weight: 700; padding: 4px 14px; border-radius: 7px; flex-shrink: 0; }
.hb-bars  { flex: 1; min-width: 160px; display: flex; flex-direction: column; gap: 5px; }
.hb-bar-row { display: flex; align-items: center; gap: 6px; font-size: 0.7rem; color: var(--muted); }
.hb-bar-row span:first-child { min-width: 32px; font-weight: 700; }
.hb-bar-row span:last-child  { min-width: 36px; text-align: right; }
.hb-bar { flex: 1; height: 5px; background: var(--surface2); border-radius: 3px; overflow: hidden; }
.hb-bar > div { height: 100%; border-radius: 3px; transition: width 0.4s ease; }

/* Zone grid */
.zone-legend { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.zone-grid {
  display: grid;
  gap: 3px;
}
.zone-cell {
  aspect-ratio: 1;
  border: 1px solid;
  border-radius: 5px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  min-height: 48px;
  transition: filter 0.15s;
}
.zone-cell:hover:not(.zone-cell--inactive) { filter: brightness(1.4); }
.zone-cell--inactive { background: #0a0a12 !important; border-color: #1a1a2e !important; }
.zone-cell--selected { box-shadow: 0 0 0 2px #a78bfa; }
.zone-hr  { font-size: 0.72rem; font-weight: 800; color: var(--text); line-height: 1; }
.zone-snr { font-size: 0.6rem; color: var(--muted); }

/* TMS explanation */
.tms-explain {
  font-size: 0.73rem;
  color: var(--muted);
  line-height: 1.5;
  padding: 8px 0 2px;
  border-top: 1px solid var(--border);
  margin-top: 8px;
}

/* Advanced toggle bar */
.advanced-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 16px;
  cursor: pointer;
  user-select: none;
  transition: border-color 0.15s;
}
.advanced-toggle:hover { border-color: #a78bfa44; }
.adv-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text2);
}
.adv-chips { display: flex; gap: 5px; flex-wrap: wrap; }
.adv-chip {
  font-size: 0.67rem;
  font-weight: 600;
  color: #a78bfa;
  background: rgba(167,139,250,0.1);
  border: 1px solid rgba(167,139,250,0.2);
  border-radius: 4px;
  padding: 1px 6px;
}

/* 3D Surface block */
.surface3d-block {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  width: 100%;
}
.surface3d-head {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 16px;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text2);
  border-bottom: 1px solid var(--border);
}
.surface3d-head span {
  font-size: 0.67rem;
  color: var(--muted);
  font-weight: 400;
  margin-left: 4px;
}

/* Scenario annotation form */
.scenario-form {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr auto;
  gap: 12px;
  align-items: end;
}
@media (max-width: 800px) {
  .scenario-form { grid-template-columns: 1fr 1fr; }
}
</style>
