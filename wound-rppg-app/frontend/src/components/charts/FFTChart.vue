<template>
  <v-chart
    :option="option"
    :style="{ height: height + 'px', width: '100%' }"
    autoresize
  />
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

  return {
    backgroundColor: "transparent",
    grid: { top: 36, right: 20, bottom: 40, left: 52 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#161b22",
      borderColor: "#30363d",
      textStyle: { color: "#e6edf3", fontSize: 11 },
    },
    xAxis: {
      type: "category",
      data: freqFiltered.map(f => f.toFixed(2)),
      axisLine:  { lineStyle: { color: "#30363d" } },
      axisTick:  { show: false },
      axisLabel: { color: "#8b949e", fontSize: 10, interval: Math.floor(freqFiltered.length / 8) },
      name: "Fréquence (Hz)",
      nameLocation: "end",
      nameTextStyle: { color: "#8b949e", fontSize: 10 },
    },
    yAxis: {
      type: "value",
      axisLine:  { show: false },
      axisTick:  { show: false },
      splitLine: { lineStyle: { color: "#21262d" } },
      axisLabel: { color: "#8b949e", fontSize: 10 },
    },
    visualMap: {
      show: false,
      dimension: 0,
      pieces: [
        { min: 0,   max: Math.floor(0.7 / (5 / freqFiltered.length)),    color: "#21262d" },
        { min: Math.floor(0.7 / (5 / freqFiltered.length)),
          max: Math.floor(3.5 / (5 / freqFiltered.length)),               color: "#00c8ff" },
        { min: Math.floor(3.5 / (5 / freqFiltered.length)), max: 9999,   color: "#21262d" },
      ],
    },
    series: [
      {
        type: "bar",
        data: fftFiltered,
        barWidth: "60%",
        markLine: props.hrHz ? {
          silent: true,
          symbol: "none",
          data: [{ xAxis: String(props.hrHz.toFixed(2)), lineStyle: { color: "#f0883e", width: 2, type: "dashed" } }],
          label: {
            formatter: props.hrBpm ? `HR = ${props.hrBpm} bpm` : "",
            color: "#f0883e",
            fontSize: 11,
          },
        } : undefined,
      },
    ],
  };
});
</script>
