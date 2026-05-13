import { createRouter, createWebHistory } from "vue-router";

const routes = [
  { path: "/",            name: "Dashboard",   component: () => import("../views/Dashboard.vue") },
  { path: "/sessions",    name: "Sessions",    component: () => import("../views/Sessions.vue") },
  { path: "/analysis/:id", name: "Analysis",  component: () => import("../views/Analysis.vue") },
  { path: "/scenarios",   name: "Scenarios",   component: () => import("../views/Scenarios.vue") },
  { path: "/report",      name: "Report",      component: () => import("../views/Report.vue") },
  { path: "/acquire",     name: "Acquire",     component: () => import("../views/Acquire.vue") },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
