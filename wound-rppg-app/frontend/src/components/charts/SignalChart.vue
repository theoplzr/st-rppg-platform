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
  time:       { type: Array, default: () => [] },
  raw:        { type: Array, default: () => [] },
  filtered:   { type: Array, default: () => [] },
  peaks:      { type: Array, default: () => [] },
  hrBpm:      Number,
  height:     { type: Number, default: 250 },
});

const option = computed(() => {
  const peakData = props.peaks.map(i => ({
    coord: [props.time[i], props.filtered[i]],
  }));

  return {
    backgroundColor: "transparent",
    grid: { top: 36, right: 20, bottom: 40, left: 52 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#161b22",
      borderColor: "#30363d",
      textStyle: { color: "#e6edf3", fontSize: 11 },
      formatter: (params) => {
        const t = params[0]?.axisValue?.toFixed(2);
        return params.map(p =>
          `<span style="color:${p.color}">●</span> ${p.seriesName}: ${p.value?.toFixed(3)}`
        ).join("<br/>") + `<br/>t = ${t}s`;
      },
    },
    legend: {
      data: ["POS brut", "POS filtré"],
      textStyle: { color: "#8b949e", fontSize: 11 },
      top: 4,
    },
    xAxis: {
      type: "category",
      data: props.time.map(t => t.toFixed(1)),
      axisLine:  { lineStyle: { color: "#30363d" } },
      axisTick:  { show: false },
      axisLabel: { color: "#8b949e", fontSize: 10, interval: Math.floor(props.time.length / 8) },
      name: "Temps (s)",
      nameTextStyle: { color: "#8b949e", fontSize: 10 },
      nameLocation: "end",
    },
    yAxis: {
      type: "value",
      axisLine:  { show: false },
      axisTick:  { show: false },
      splitLine: { lineStyle: { color: "#21262d" } },
      axisLabel: { color: "#8b949e", fontSize: 10 },
      name: "Amplitude",
      nameTextStyle: { color: "#8b949e", fontSize: 10 },
    },
    series: [
      {
        name: "POS brut",
        type: "line",
        data: props.raw,
        lineStyle: { color: "#8b949e", width: 0.8, opacity: 0.5 },
        symbol: "none",
        smooth: false,
      },
      {
        name: "POS filtré",
        type: "line",
        data: props.filtered,
        lineStyle: { color: "#00c8ff", width: 2 },
        areaStyle: {
          color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(0,200,255,0.15)" },
              { offset: 1, color: "rgba(0,200,255,0)" },
            ]},
        },
        symbol: "none",
        smooth: true,
        markPoint: {
          data: peakData.map(p => ({
            coord: p.coord,
            symbol: "circle",
            symbolSize: 8,
            itemStyle: { color: "#f0883e" },
          })),
          tooltip: { show: false },
        },
      },
    ],
  };
});
</script>
