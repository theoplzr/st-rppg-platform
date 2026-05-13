<template>
  <v-app theme="dark">
    <Sidebar />
    <v-main style="background: var(--bg)">
      <TopBar />
      <div class="page-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </v-main>
  </v-app>
</template>

<script setup>
import Sidebar from "./components/layout/Sidebar.vue";
import TopBar  from "./components/layout/TopBar.vue";
</script>

<style>
.page-content {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}
</style>
