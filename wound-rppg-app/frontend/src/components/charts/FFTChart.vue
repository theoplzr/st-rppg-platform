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
  const maxF = 4.5;
  const pairs = props.freq
    .map((f, i) => [f, props.fft[i] ?? 0])
    .filter(([f]) => f <= maxF && f >= 0);

  if (!pairs.length) return {};

  const maxPwr = Math.max(...pairs.map(p => p[1])) || 1;

  return {
    backgroundColor: "transparent",
    grid: { top: 28, right: 20, bottom: 44, left: 54 },

    tooltip: {
      trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: "#55556a", type: "dashed" } },
      backgroundColor: "#0d0d16",
      borderColor: "#252535",
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: "#c8c8d8", fontSize: 11 },
      formatter: params => {
        const hz  = (+params[0]?.axisValue).toFixed(3);
        const bpm = (hz * 60).toFixed(0);
        const pwr = (+params[0]?.value[1]).toFixed(1);
        return `<div style="font-size:10px;color:#55556a;margin-bottom:3px">${hz} Hz · <b style="color:#f59e0b">${bpm} bpm</b></div>Puissance : <b>${pwr}</b>`;
      },
    },

    xAxis: {
      type: "value",
      min: 0,
      max: maxF,
      name: "Fréquence (Hz)",
      nameLocation: "end",
      nameGap: 8,
      nameTextStyle: { color: "#55556a", fontSize: 10 },
      axisLine:  { lineStyle: { color: "#252535" } },
      axisTick:  { show: false },
      axisLabel: {
        color: "#6b6b85", fontSize: 10,
        formatter: v => {
          const labels = { 0: "0", 1: "1 Hz\n60 bpm", 2: "2 Hz\n120 bpm", 3: "3 Hz\n180 bpm", 4: "4 Hz\n240 bpm" };
          return labels[v] ?? v.toFixed(1);
        },
        interval: "auto",
      },
      splitLine: { show: false },
    },

    yAxis: {
      type: "value",
      name: "Puissance",
      nameLocation: "middle",
      nameGap: 40,
      nameTextStyle: { color: "#55556a", fontSize: 10 },
      min: 0,
      max: Math.ceil(maxPwr * 1.15),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6b6b85", fontSize: 10 },
      splitLine: { lineStyle: { color: "#1a1a2a", type: "dashed" } },
    },

    series: [
      {
        type: "line",
        data: pairs,
        symbol: "none",
        smooth: 0.3,
        lineStyle: { color: "#e8622a", width: 2 },
        areaStyle: {
          color: {
            type: "linear", x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(232,98,42,0.28)" },
              { offset: 1, color: "rgba(232,98,42,0.02)" },
            ],
          },
        },
        markArea: {
          silent: true,
          data: [[
            { xAxis: 0.7, itemStyle: { color: "rgba(232,98,42,0.07)", borderWidth: 0 } },
            { xAxis: 3.0 },
          ]],
          label: {
            show: true, position: "insideTopLeft",
            formatter: "Bande cardiaque\n0.7 – 3.0 Hz",
            color: "#55556a", fontSize: 9, lineHeight: 14,
          },
        },
        markLine: props.hrHz ? {
          silent: true,
          symbol: ["none", "none"],
          data: [{
            xAxis: props.hrHz,
            lineStyle: { color: "#f59e0b", width: 2, type: "solid" },
            label: {
              formatter: props.hrBpm ? `${props.hrBpm} bpm` : "",
              color: "#f59e0b", fontSize: 12, fontWeight: 700,
              position: "insideEndTop",
            },
          }],
        } : undefined,
      },
    ],
  };
});
</script>
