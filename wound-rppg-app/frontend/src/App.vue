<template>
  <div class="app-root">
    <Transition name="overlay">
      <div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen = false" />
    </Transition>
    <Sidebar :is-open="sidebarOpen" @close="sidebarOpen = false" />
    <div class="app-main">
      <TopBar @toggle-sidebar="sidebarOpen = !sidebarOpen" />
      <main class="page-content">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, provide, watch } from "vue";
import Sidebar from "./components/layout/Sidebar.vue";
import TopBar  from "./components/layout/TopBar.vue";

const theme = ref(localStorage.getItem("theme") || "dark");
const sidebarOpen = ref(false);

function toggleTheme() {
  theme.value = theme.value === "dark" ? "light" : "dark";
  localStorage.setItem("theme", theme.value);
}

watch(theme, (t) => {
  document.documentElement.setAttribute("data-theme", t);
}, { immediate: true });

provide("theme", theme);
provide("toggleTheme", toggleTheme);
</script>

<style>
html, body, #app { height: 100%; margin: 0; }

.app-root {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
  position: relative;
}

.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: var(--overlay);
  z-index: 99;
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
}

.overlay-enter-active,
.overlay-leave-active { transition: opacity 0.22s ease; }
.overlay-enter-from,
.overlay-leave-to     { opacity: 0; }

.app-main {
  flex: 1;
  margin-left: 220px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-width: 0;
  position: relative;
}

.page-content {
  flex: 1;
  padding: 36px 44px;
  position: relative;
  z-index: 1;
}

@media (max-width: 768px) {
  .app-main     { margin-left: 0; }
  .page-content { padding: 20px 18px; }
}
</style>
