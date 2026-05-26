<template>
  <aside class="ecrin-sidebar">
    <!-- Brand -->
    <div class="sb-brand">
      <div class="sb-mark">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M1 9h3l2-6 4 12 2-8 2 4 2-2" stroke="#e8622a" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div>
        <div class="sb-name">ST-rPPG</div>
        <div class="sb-sub">WOUND PLATFORM</div>
      </div>
    </div>

    <!-- Separator -->
    <div class="sb-rule" />

    <!-- Nav -->
    <nav class="sb-nav">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="sb-link"
        active-class="sb-link--active"
        exact-active-class="sb-link--active"
      >
        <span class="sb-link-indicator" />
        {{ item.label }}
      </router-link>
    </nav>

    <!-- Footer -->
    <div class="sb-footer">
      <div class="sb-footer-dot" />
      <div>
        <div class="sb-ref">ANR-24-CE45-7356</div>
        <div class="sb-lab">LCOMS · Université de Lorraine</div>
      </div>
    </div>
  </aside>
</template>

<script setup>
const navItems = [
  { to: "/",          label: "Dashboard"   },
  { to: "/acquire",   label: "Acquisition" },
  { to: "/sessions",  label: "Sessions"    },
  { to: "/patients",  label: "Patients"    },
  { to: "/scenarios", label: "Scénarios"   },
  { to: "/report",    label: "Rapport"     },
];
</script>

<style scoped>
.ecrin-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 220px;
  height: 100vh;
  background: #000;
  border-right: 1px solid #111122;
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: hidden;
}

/* Subtle ambient glow inside sidebar */
.ecrin-sidebar::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 220px;
  height: 300px;
  background: radial-gradient(ellipse at 30% 100%, rgba(232,98,42,0.07) 0%, transparent 70%);
  pointer-events: none;
}

/* ── Brand ─────────────────────────────────────────── */
.sb-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 28px 24px 24px;
}
.sb-mark {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: rgba(232,98,42,0.08);
  border: 1px solid rgba(232,98,42,0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.sb-name {
  font-family: 'Syne', 'Inter', sans-serif;
  font-size: 1rem;
  font-weight: 800;
  color: #f0f0f4;
  letter-spacing: -0.03em;
  line-height: 1;
}
.sb-sub {
  font-size: 0.55rem;
  font-weight: 600;
  color: #55556a;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-top: 4px;
}

/* ── Rule ──────────────────────────────────────────── */
.sb-rule {
  height: 1px;
  background: linear-gradient(to right, transparent, #1a1a2e 40%, transparent);
  margin: 0 24px 8px;
}

/* ── Nav ───────────────────────────────────────────── */
.sb-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 12px 16px 0;
  gap: 2px;
}
.sb-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 500;
  color: #55556a;
  text-decoration: none;
  transition: color 0.2s, background 0.2s;
  letter-spacing: -0.01em;
}
.sb-link-indicator {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--accent, #e8622a);
  opacity: 0;
  transition: opacity 0.2s, transform 0.2s;
  flex-shrink: 0;
}
.sb-link:hover {
  color: #b8b8cc;
  background: rgba(255,255,255,0.03);
}
.sb-link--active {
  color: #f0f0f4 !important;
  background: rgba(232,98,42,0.08) !important;
  font-weight: 600;
}
.sb-link--active .sb-link-indicator {
  opacity: 1;
  transform: scale(1.3);
}

/* ── Footer ────────────────────────────────────────── */
.sb-footer {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 20px 24px;
  border-top: 1px solid #0e0e1c;
  position: relative;
  z-index: 1;
}
.sb-footer-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #22d47e;
  margin-top: 5px;
  flex-shrink: 0;
  box-shadow: 0 0 6px rgba(34,212,126,0.5);
}
.sb-ref {
  font-size: 0.65rem;
  font-weight: 700;
  color: #b8b8cc;
  font-family: 'SF Mono', 'Fira Code', monospace;
  letter-spacing: 0.03em;
}
.sb-lab {
  font-size: 0.6rem;
  color: #55556a;
  margin-top: 3px;
  letter-spacing: 0.02em;
}
</style>
