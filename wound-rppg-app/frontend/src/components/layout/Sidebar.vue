<template>
  <v-navigation-drawer
    permanent
    :width="220"
    style="background: var(--surface); border-right: 1px solid var(--border);"
  >
    <!-- Logo -->
    <div class="sidebar-logo">
      <v-icon color="primary" size="28">mdi-pulse</v-icon>
      <div>
        <div class="logo-title gradient-text">Wound-rPPG</div>
        <div class="logo-sub">ANR · LCOMS</div>
      </div>
    </div>

    <v-divider style="border-color: var(--border)" />

    <!-- Navigation -->
    <v-list nav density="compact" class="mt-2">
      <v-list-item
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :prepend-icon="item.icon"
        :title="item.label"
        rounded="lg"
        class="nav-item"
        active-class="nav-item-active"
      />
    </v-list>

    <template #append>
      <v-divider style="border-color: var(--border)" />
      <div class="sidebar-footer">
        <v-icon size="14" color="success">mdi-circle</v-icon>
        <span>Backend connecté</span>
      </div>
    </template>
  </v-navigation-drawer>
</template>

<script setup>
const navItems = [
  { to: "/",          icon: "mdi-view-dashboard",     label: "Dashboard" },
  { to: "/acquire",   icon: "mdi-record-circle",      label: "Acquisition" },
  { to: "/sessions",  icon: "mdi-folder-multiple",    label: "Sessions" },
  { to: "/scenarios", icon: "mdi-compare",            label: "Scénarios" },
  { to: "/report",    icon: "mdi-file-chart-outline", label: "Rapport" },
];
</script>

<style scoped>
.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px;
}
.logo-title {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.logo-sub {
  font-size: 0.7rem;
  color: var(--muted);
}
.nav-item {
  margin-bottom: 2px;
  color: var(--muted) !important;
  font-size: 0.88rem;
}
.nav-item-active {
  background: rgba(0, 200, 255, 0.1) !important;
  color: var(--accent) !important;
  border-left: 2px solid var(--accent);
}
.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  font-size: 0.75rem;
  color: var(--muted);
}
</style>
