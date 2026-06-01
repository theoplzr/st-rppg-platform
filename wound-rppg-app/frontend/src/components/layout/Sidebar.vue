<template>
  <aside class="ecrin-sidebar" :class="{ 'is-open': isOpen }">
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

    <div class="sb-rule" />

    <nav class="sb-nav">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="sb-link"
        active-class="sb-link--active"
        exact-active-class="sb-link--active"
        @click="$emit('close')"
      >
        <span class="sb-link-indicator" />
        <svg class="sb-icon" width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path :d="item.icon" />
        </svg>
        {{ item.label }}
      </router-link>
    </nav>

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
defineProps({ isOpen: { type: Boolean, default: false } });
defineEmits(["close"]);

const navItems = [
  { to: "/",          label: "Dashboard",   icon: "M2 2h5v5H2zM9 2h5v5H9zM2 9h5v5H2zM9 9h5v5H9z" },
  { to: "/acquire",   label: "Acquisition", icon: "M8 2a4 4 0 100 8 4 4 0 000-8zM8 14s-6-2-6-5" },
  { to: "/sessions",  label: "Sessions",    icon: "M2 4h12M2 8h8M2 12h10" },
  { to: "/patients",  label: "Patients",    icon: "M8 8a3 3 0 100-6 3 3 0 000 6zM2 14c0-3 2.7-5 6-5s6 2 6 5" },
  { to: "/scenarios", label: "Scénarios",   icon: "M3 8l3 3 7-7" },
];
</script>

<style scoped>
.ecrin-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 220px;
  height: 100vh;
  background: var(--bg);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: hidden;
  transition: transform 0.32s cubic-bezier(0.16, 1, 0.3, 1),
              box-shadow 0.32s,
              background 0.3s,
              border-color 0.3s;
}

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

@media (max-width: 768px) {
  .ecrin-sidebar {
    transform: translateX(-100%);
    box-shadow: none;
  }
  .ecrin-sidebar.is-open {
    transform: translateX(0);
    box-shadow: 0 0 60px rgba(0,0,0,0.5);
  }
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
  transition: background 0.3s, border-color 0.3s;
}
.sb-name {
  font-family: 'Syne', 'Inter', sans-serif;
  font-size: 1rem;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -0.03em;
  line-height: 1;
  transition: color 0.3s;
}
.sb-sub {
  font-size: 0.55rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-top: 4px;
  transition: color 0.3s;
}

/* ── Rule ──────────────────────────────────────────── */
.sb-rule {
  height: 1px;
  background: linear-gradient(to right, transparent, var(--border) 40%, transparent);
  margin: 0 24px 8px;
  transition: background 0.3s;
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
  gap: 9px;
  padding: 9px 12px;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--muted);
  text-decoration: none;
  transition: color 0.2s, background 0.2s;
  letter-spacing: -0.01em;
}
.sb-link-indicator {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--accent);
  opacity: 0;
  transition: opacity 0.2s, transform 0.2s;
  flex-shrink: 0;
}
.sb-icon {
  opacity: 0.5;
  transition: opacity 0.2s;
  flex-shrink: 0;
}
.sb-link:hover {
  color: var(--text2);
  background: rgba(255,255,255,0.03);
}
.sb-link:hover .sb-icon { opacity: 0.75; }
.sb-link--active {
  color: var(--text) !important;
  background: rgba(232,98,42,0.08) !important;
  font-weight: 600;
}
.sb-link--active .sb-link-indicator {
  opacity: 1;
  transform: scale(1.3);
}
.sb-link--active .sb-icon { opacity: 1; }

/* ── Footer ────────────────────────────────────────── */
.sb-footer {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 20px 24px;
  border-top: 1px solid var(--border);
  position: relative;
  z-index: 1;
  transition: border-color 0.3s;
}
.sb-footer-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--green);
  margin-top: 5px;
  flex-shrink: 0;
  box-shadow: 0 0 6px rgba(34,212,126,0.5);
}
.sb-ref {
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--text2);
  font-family: 'SF Mono', 'Fira Code', monospace;
  letter-spacing: 0.03em;
  transition: color 0.3s;
}
.sb-lab {
  font-size: 0.6rem;
  color: var(--muted);
  margin-top: 3px;
  letter-spacing: 0.02em;
  transition: color 0.3s;
}
</style>
