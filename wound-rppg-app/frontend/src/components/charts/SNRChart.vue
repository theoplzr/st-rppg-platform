<template>
  <v-chart :option="option" :style="{ height: height + 'px', width: '100%' }" autoresize />
</template>

<script setup>
import { computed } from "vue";
const props = defineProps({
  time:    { type: Array, default: () => [] },
  snr:     { type: Array, default: () => [] },
  meanSnr: Number,
  height:  { type: Number, default: 200 },
});
const option = computed(() => ({
  backgroundColor: "transparent",
  grid: { top: 24, right: 20, bottom: 36, left: 48 },
  tooltip: { trigger: "axis", backgroundColor: "#161b22", borderColor: "#30363d", textStyle: { color: "#e6edf3", fontSize: 11 } },
  xAxis: {
    type: "category",
    data: props.time.map(t => t.toFixed(1)),
    axisLine: { lineStyle: { color: "#30363d" } },
    axisTick: { show: false },
    axisLabel: { color: "#8b949e", fontSize: 10 },
  },
  yAxis: {
    type: "value",
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: "#21262d" } },
    axisLabel: { color: "#8b949e", fontSize: 10, formatter: v => v + " dB" },
  },
  series: [{
    type: "line",
    data: props.snr,
    lineStyle: { color: "#7ee787", width: 2 },
    areaStyle: {
      color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: "rgba(126,231,135,0.2)" },
          { offset: 1, color: "rgba(126,231,135,0)" },
        ]},
    },
    symbol: "none",
    smooth: true,
    markLine: {
      silent: true,
      symbol: "none",
      data: [
        { yAxis: 0, lineStyle: { color: "#f85149", type: "dashed", width: 1 }, label: { formatter: "0 dB", color: "#f85149", fontSize: 10 } },
        { yAxis: 3, lineStyle: { color: "#f0883e", type: "dashed", width: 1 }, label: { formatter: "3 dB", color: "#f0883e", fontSize: 10 } },
        { yAxis: 6, lineStyle: { color: "#00c8ff", type: "dashed", width: 1 }, label: { formatter: "6 dB", color: "#00c8ff", fontSize: 10 } },
      ],
    },
  }],
}));
</script>
