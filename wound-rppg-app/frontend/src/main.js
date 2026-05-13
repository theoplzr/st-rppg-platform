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

// ECharts
use([
  CanvasRenderer, LineChart, BarChart, HeatmapChart,
  GridComponent, TooltipComponent, LegendComponent,
  MarkLineComponent, VisualMapComponent, DataZoomComponent,
]);

// Vuetify dark theme
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
          background:  "#0d1117",
          surface:     "#161b22",
          primary:     "#00c8ff",
          secondary:   "#7ee787",
          accent:      "#f0883e",
          error:       "#f85149",
          warning:     "#f0883e",
          info:        "#00c8ff",
          success:     "#7ee787",
          "surface-2": "#21262d",
          border:      "#30363d",
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
