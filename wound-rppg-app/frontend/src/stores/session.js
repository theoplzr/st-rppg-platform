import { defineStore } from "pinia";
import { ref, computed } from "vue";
import axios from "axios";
import { apiUrl } from "../lib/api.js";

export const useSessionStore = defineStore("session", () => {
  const sessions     = ref([]);
  const loading      = ref(false);
  const current      = ref(null);
  const currentResult = ref(null);

  const hasSessions  = computed(() => sessions.value.length > 0);

  async function fetchSessions() {
    loading.value = true;
    try {
      const { data } = await axios.get(apiUrl("/sessions/"));
      sessions.value = data;
    } finally {
      loading.value = false;
    }
  }

  async function analyze(sessionName, force = false) {
    loading.value = true;
    try {
      const { data: jobData } = await axios.post(
        apiUrl(`/analysis/${sessionName}`),
        { force });

      const jobId = jobData.job_id;
      if (!jobId) {
        throw new Error("Missing analysis job id.");
      }

      let status = "pending";
      while (status === "pending" || status === "running") {
        await new Promise(resolve => setTimeout(resolve, 1500));
        const { data } = await axios.get(
          apiUrl(`/analysis/${sessionName}/status/${jobId}`),
        );
        status = data.status;
        if (status === "error") {
          throw new Error(data.error || "Analysis failed.");
        }
      }

      const { data: result } = await axios.get(apiUrl(`/analysis/${sessionName}`));
      currentResult.value = result;

      const s = sessions.value.find(s => s.name === sessionName);
      if (s) s.has_results = true;
      return result;
    } finally {
      loading.value = false;
    }
  }

  async function getResult(sessionName) {
    const { data } = await axios.get(apiUrl(`/analysis/${sessionName}`));
    currentResult.value = data;
    return data;
  }

  async function tagScenario(sessionName, label, description, zone) {
    await axios.post(apiUrl(`/sessions/${sessionName}/scenario`),
      { label, description, zone });
    await fetchSessions();
  }

  return {
    sessions, loading, current, currentResult,
    hasSessions,
    fetchSessions, analyze, getResult, tagScenario,
  };
});
