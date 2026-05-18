<template>
  <v-chart :option="option" :style="{ height: height + 'px', width: '100%' }" autoresize />
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  freq:   { type: Array, default: () => [] },
  fft:    { type: Array, default: () => [] },
  hrHz:   Number,
  hrBpm:  Number,
  height: { type: Number, default: 250 },
});

const option = computed(() => {
  const freqFiltered = props.freq.filter(f => f <= 5);
  const fftFiltered  = props.fft.slice(0, freqFiltered.length);
  const n = freqFiltered.length;

  return {
    backgroundColor: "transparent",
    grid: { top: 32, right: 16, bottom: 36, left: 48 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#0f0f17",
      borderColor: "#252535",
      textStyle: { color: "#c8c8d8", fontSize: 11 },
    },
    xAxis: {
      type: "category",
      data: freqFiltered.map(f => f.toFixed(2)),
      axisLine:  { lineStyle: { color: "#252535" } },
      axisTick:  { show: false },
      axisLabel: { color: "#6b6b85", fontSize: 10, interval: Math.floor(n / 8) },
      name: "Hz",
      nameLocation: "end",
      nameTextStyle: { color: "#6b6b85", fontSize: 10 },
    },
    yAxis: {
      type: "value",
      axisLine:  { show: false },
      axisTick:  { show: false },
      splitLine: { lineStyle: { color: "#16161f" } },
      axisLabel: { color: "#6b6b85", fontSize: 10 },
    },
    visualMap: {
      show: false,
      dimension: 0,
      pieces: [
        { min: 0,                                    max: Math.floor(0.7 / (5 / n)),  color: "#252535" },
        { min: Math.floor(0.7 / (5 / n)),            max: Math.floor(3.5 / (5 / n)), color: "#e8622a" },
        { min: Math.floor(3.5 / (5 / n)), max: 9999,                                color: "#252535" },
      ],
    },
    series: [{
      type: "bar",
      data: fftFiltered,
      barWidth: "60%",
      markLine: props.hrHz ? {
        silent: true,
        symbol: "none",
        data: [{ xAxis: String(props.hrHz.toFixed(2)), lineStyle: { color: "#f59e0b", width: 2, type: "dashed" } }],
        label: { formatter: props.hrBpm ? `${props.hrBpm} bpm` : "", color: "#f59e0b", fontSize: 11 },
      } : undefined,
    }],
  };
});
</script>
