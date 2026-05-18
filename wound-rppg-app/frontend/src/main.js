import { createApp } from "vue";
import { createPinia } from "pinia";
import { createVuetify } from "vuetify";
import { aliases, mdi } from "vuetify/iconsets/mdi";
import * as components from "vuetify/components";
import * as directives from "vuetify/directives";
import ECharts from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, BarChart, HeatmapChart } from "echarts/charts";
import {
  GridComponent, TooltipComponent, LegendComponent,
  MarkLineComponent, VisualMapComponent, DataZoomComponent,
} from "echarts/components";

import "vuetify/styles";
import "@mdi/font/css/materialdesignicons.css";
import "./styles/global.css";

import App    from "./App.vue";
import router from "./router/index.js";

use([
  CanvasRenderer, LineChart, BarChart, HeatmapChart,
  GridComponent, TooltipComponent, LegendComponent,
  MarkLineComponent, VisualMapComponent, DataZoomComponent,
]);

const vuetify = createVuetify({
  components,
  directives,
  icons: { defaultSet: "mdi", aliases, sets: { mdi } },
  theme: {
    defaultTheme: "dark",
    themes: {
      dark: {
        dark: true,
        colors: {
          background:  "#000000",
          surface:     "#080810",
          primary:     "#e8622a",
          secondary:   "#06b6d4",
          accent:      "#e8622a",
          error:       "#ef4444",
          warning:     "#f59e0b",
          info:        "#06b6d4",
          success:     "#22d47e",
          "surface-2": "#16161f",
          border:      "#252535",
        },
      },
    },
  },
});

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(vuetify);
app.component("v-chart", ECharts);
app.mount("#app");
