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
  grid: { top: 20, right: 16, bottom: 32, left: 48 },
  tooltip: {
    trigger: "axis",
    backgroundColor: "#0f0f17",
    borderColor: "#252535",
    textStyle: { color: "#c8c8d8", fontSize: 11 },
  },
  xAxis: {
    type: "category",
    data: props.time.map(t => t.toFixed(1)),
    axisLine: { lineStyle: { color: "#252535" } },
    axisTick: { show: false },
    axisLabel: { color: "#6b6b85", fontSize: 10 },
  },
  yAxis: {
    type: "value",
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: "#16161f" } },
    axisLabel: { color: "#6b6b85", fontSize: 10, formatter: v => v + " dB" },
  },
  series: [{
    type: "line",
    data: props.snr,
    lineStyle: { color: "#22d47e", width: 2 },
    areaStyle: {
      color: {
        type: "linear", x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: "rgba(34,212,126,0.18)" },
          { offset: 1, color: "rgba(34,212,126,0)" },
        ],
      },
    },
    symbol: "none",
    smooth: true,
    markLine: {
      silent: true,
      symbol: "none",
      data: [
        { yAxis: 0, lineStyle: { color: "#ef4444", type: "dashed", width: 1 }, label: { formatter: "0 dB", color: "#ef4444", fontSize: 10 } },
        { yAxis: 3, lineStyle: { color: "#f59e0b", type: "dashed", width: 1 }, label: { formatter: "3 dB", color: "#f59e0b", fontSize: 10 } },
        { yAxis: 6, lineStyle: { color: "#e8622a", type: "dashed", width: 1 }, label: { formatter: "6 dB", color: "#e8622a", fontSize: 10 } },
      ],
    },
  }],
}));
</script>
