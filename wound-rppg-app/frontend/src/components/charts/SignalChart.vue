<template>
  <v-chart :option="option" :style="{ height: height + 'px', width: '100%' }" autoresize />
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  time:     { type: Array, default: () => [] },
  raw:      { type: Array, default: () => [] },
  filtered: { type: Array, default: () => [] },
  peaks:    { type: Array, default: () => [] },
  hrBpm:    Number,
  height:   { type: Number, default: 260 },
});

const option = computed(() => {
  const n = props.time.length;
  if (!n) return {};

  const rawData  = props.time.map((t, i) => [t, props.raw[i]  ?? 0]);
  const filtData = props.time.map((t, i) => [t, props.filtered[i] ?? 0]);
  const peakData = props.peaks
    .filter(i => i >= 0 && i < n)
    .map(i => ({ value: [props.time[i], props.filtered[i]], symbolSize: 8 }));

  const tMin = props.time[0];
  const tMax = props.time[n - 1];

  return {
    backgroundColor: "transparent",
    grid: { top: 36, right: 20, bottom: 44, left: 54 },

    tooltip: {
      trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: "#55556a", type: "dashed" } },
      backgroundColor: "#0d0d16",
      borderColor: "#252535",
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: "#c8c8d8", fontSize: 11 },
      formatter: params => {
        const t = (+params[0]?.axisValue).toFixed(2);
        const lines = params
          .filter(p => p.seriesType !== "scatter")
          .map(p => `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color};margin-right:5px"></span>${p.seriesName}: <b>${(+p.value[1]).toFixed(3)}</b>`);
        return `<div style="font-size:10px;color:#55556a;margin-bottom:4px">t = ${t} s</div>` + lines.join("<br/>");
      },
    },

    legend: {
      data: ["POS brut (pré-filtre)", "POS filtré (0.7–3 Hz)"],
      top: 4,
      right: 12,
      textStyle: { color: "#6b6b85", fontSize: 11 },
      itemWidth: 20,
      itemHeight: 3,
    },

    xAxis: {
      type: "value",
      min: tMin,
      max: tMax,
      name: "Temps (s)",
      nameLocation: "end",
      nameGap: 8,
      nameTextStyle: { color: "#55556a", fontSize: 10 },
      axisLine:  { lineStyle: { color: "#252535" } },
      axisTick:  { show: false },
      axisLabel: { color: "#6b6b85", fontSize: 10, formatter: v => v.toFixed(0) + "s" },
      splitLine: { show: false },
    },

    yAxis: {
      type: "value",
      name: "Amplitude",
      nameLocation: "middle",
      nameGap: 40,
      nameTextStyle: { color: "#55556a", fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6b6b85", fontSize: 10, formatter: v => v.toFixed(1) },
      splitLine: { lineStyle: { color: "#1a1a2a", type: "dashed" } },
    },

    dataZoom: [
      { type: "inside", start: 0, end: 100, zoomOnMouseWheel: true },
      {
        type: "slider", bottom: 4, height: 18,
        borderColor: "#252535", backgroundColor: "#0d0d16",
        dataBackground: { lineStyle: { color: "#252535" }, areaStyle: { color: "#252535" } },
        selectedDataBackground: { lineStyle: { color: "#e8622a" }, areaStyle: { color: "rgba(232,98,42,0.15)" } },
        handleStyle: { color: "#e8622a" },
        textStyle: { color: "#55556a", fontSize: 9 },
        fillerColor: "rgba(232,98,42,0.08)",
      },
    ],

    series: [
      {
        name: "POS brut (pré-filtre)",
        type: "line",
        data: rawData,
        lineStyle: { color: "rgba(120,120,170,0.45)", width: 1 },
        symbol: "none",
        smooth: false,
        z: 1,
        tooltip: { show: false },
      },
      {
        name: "POS filtré (0.7–3 Hz)",
        type: "line",
        data: filtData,
        lineStyle: { color: "#e8622a", width: 2.2 },
        symbol: "none",
        smooth: true,
        z: 2,
        areaStyle: {
          color: {
            type: "linear", x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(232,98,42,0.14)" },
              { offset: 1, color: "rgba(232,98,42,0.01)" },
            ],
          },
        },
      },
      {
        name: "Pics systoliques",
        type: "scatter",
        data: peakData,
        symbol: "circle",
        itemStyle: { color: "#f59e0b", borderColor: "#fff", borderWidth: 1.5 },
        tooltip: { show: false },
        z: 3,
      },
    ],
  };
});
</script>
