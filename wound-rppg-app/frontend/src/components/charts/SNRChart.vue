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

const option = computed(() => {
  const n = props.time.length;
  if (!n) return {};

  const pairs = props.time.map((t, i) => [t, props.snr[i] ?? 0]);
  const yMin  = Math.min(...props.snr, -3) - 1;
  const yMax  = Math.max(...props.snr,  7) + 1;
  const mean  = props.meanSnr ?? 0;

  const labelBox = (color) => ({
    backgroundColor: "#0e0e18",
    borderColor: color,
    borderWidth: 1,
    borderRadius: 3,
    padding: [2, 5],
  });

  return {
    backgroundColor: "transparent",
    grid: { top: 20, right: 80, bottom: 36, left: 54 },

    tooltip: {
      trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: "#55556a", type: "dashed" } },
      backgroundColor: "#0d0d16",
      borderColor: "#252535",
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: "#c8c8d8", fontSize: 11 },
      formatter: params => {
        const t   = (+params[0]?.axisValue).toFixed(1);
        const val = (+params[0]?.value[1]).toFixed(2);
        const col = +val >= 3 ? "#22d47e" : +val >= 0 ? "#f59e0b" : "#ef4444";
        return `<div style="font-size:10px;color:#55556a;margin-bottom:3px">t = ${t} s</div>SNR : <b style="color:${col}">${val} dB</b>`;
      },
    },

    xAxis: {
      type: "value",
      min: props.time[0],
      max: props.time[n - 1],
      name: "Temps (s)",
      nameLocation: "start",
      nameGap: 6,
      nameTextStyle: { color: "#55556a", fontSize: 10, align: "right" },
      axisLine:  { lineStyle: { color: "#252535" } },
      axisTick:  { show: false },
      axisLabel: { color: "#6b6b85", fontSize: 10, formatter: v => v.toFixed(0) + "s" },
      splitLine: { show: false },
    },

    yAxis: {
      type: "value",
      min: yMin,
      max: yMax,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6b6b85", fontSize: 10, formatter: v => v + " dB" },
      splitLine: { show: false },
    },

    series: [
      {
        type: "line",
        data: pairs,
        symbol: "none",
        smooth: true,
        lineStyle: { color: "#22d47e", width: 2.2 },
        areaStyle: {
          color: {
            type: "linear", x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(34,212,126,0.18)" },
              { offset: 1, color: "rgba(34,212,126,0.02)" },
            ],
          },
        },

        markArea: {
          silent: true,
          data: [
            [{ yAxis: yMin, itemStyle: { color: "rgba(239,68,68,0.07)" }  }, { yAxis: 0 }],
            [{ yAxis: 0,    itemStyle: { color: "rgba(245,158,11,0.05)" } }, { yAxis: 3 }],
            [{ yAxis: 3,    itemStyle: { color: "rgba(34,212,126,0.05)" } }, { yAxis: yMax }],
          ],
        },

        markLine: {
          silent: true,
          symbol: ["none", "none"],
          data: [
            {
              yAxis: 0,
              lineStyle: { color: "#ef4444", type: "dashed", width: 1 },
              label: {
                formatter: "0 dB", color: "#ef4444", fontSize: 10,
                position: "insideStartBottom",
                ...labelBox("#ef444466"),
              },
            },
            {
              yAxis: 3,
              lineStyle: { color: "#f59e0b", type: "dashed", width: 1 },
              label: {
                formatter: "3 dB ✓", color: "#f59e0b", fontSize: 10,
                position: "insideStartTop",
                ...labelBox("#f59e0b66"),
              },
            },
            {
              yAxis: 6,
              lineStyle: { color: "#22d47e", type: "dashed", width: 1 },
              label: {
                formatter: "6 dB ★", color: "#22d47e", fontSize: 10,
                position: "insideStartTop",
                ...labelBox("#22d47e66"),
              },
            },
            {
              yAxis: mean,
              lineStyle: { color: "#06b6d4", type: "dotted", width: 2 },
              label: {
                formatter: `moy ${mean.toFixed(1)} dB`,
                color: "#06b6d4", fontSize: 11, fontWeight: 700,
                position: "end",
                ...labelBox("#06b6d466"),
              },
            },
          ],
        },
      },
    ],
  };
});
</script>
