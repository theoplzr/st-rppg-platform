<template>
  <div class="app-root">
    <Sidebar />
    <div class="app-main">
      <TopBar />
      <main class="page-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import Sidebar from "./components/layout/Sidebar.vue";
import TopBar  from "./components/layout/TopBar.vue";
</script>

<style>
html, body, #app { height: 100%; margin: 0; }

.app-root {
  display: flex;
  min-height: 100vh;
  background: #000;
}

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
  max-width: 1440px;
  position: relative;
  z-index: 1;
}

@media (max-width: 768px) {
  .app-main   { margin-left: 0; }
  .page-content { padding: 20px 18px; }
}
</style>
