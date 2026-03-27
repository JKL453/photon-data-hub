<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from "vue"
import { Line } from "vue-chartjs"
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Legend,
  Tooltip,
} from "chart.js"
import Plotly from "plotly.js-dist-min"

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Legend,
  Tooltip
)

const props = defineProps({
  preview: {
    type: Object,
    required: true,
  },
  variant: {
    type: String,
    default: "thumb",
  },
})

const plotlyTarget = ref(null)

const channelColors = {
  0: "#2f6fed",
  1: "#f08a24",
  2: "#2ecc71",
  3: "#e74c3c",
}

const hasSeries = computed(() => {
  return Array.isArray(props.preview?.series) && props.preview.series.length > 0
})

const chartData = computed(() => {
  if (!hasSeries.value) {
    return {
      labels: [],
      datasets: [],
    }
  }

  const x = props.preview.x ?? []
  const series = props.preview.series ?? []

  return {
    labels: x,
    datasets: series.map((s, i) => ({
      label: s.label,
      data: s.y,
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0,
      borderColor: channelColors[s.channel] ?? ["#2f6fed", "#f08a24", "#2ecc71", "#e74c3c", "#9b59b6", "#666"][i % 6],
    })),
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: "top",
    },
  },
  layout: {
    padding: {
      top: 10,
      bottom: 10,
      left: 5,
      right: 5,
    },
  },
  scales: {
    x: {
      title: {
        display: true,
        text: "Time (s)",
      },
      ticks: {
        maxTicksLimit: 6,
        callback(value) {
          const label = this.getLabelForValue(value)
          const num = Number(label)

          if (!Number.isFinite(num)) {
            return label
          }

          return String(Math.round(num))
        },
      },
    },
    y: {
      title: {
        display: true,
        text: "Counts / bin",
      },
      beginAtZero: true,
    },
  },
}))

const isDetailVariant = computed(() => props.variant === "detail")

function renderPlotlyDetail() {
  if (!plotlyTarget.value || !hasSeries.value || !isDetailVariant.value) {
    return
  }

  const traces = (props.preview.series ?? []).map((s, i) => ({
    x: props.preview.x ?? [],
    y: s.y,
    type: "scattergl",
    mode: "lines",
    name: s.label,
    line: {
      width: 2,
      color: channelColors[s.channel] ?? ["#2f6fed", "#f08a24", "#2ecc71", "#e74c3c", "#9b59b6", "#666"][i % 6],
    },
  }))

  const layout = {
    autosize: true,
    margin: { l: 55, r: 20, t: 35, b: 55 },
    paper_bgcolor: "white",
    plot_bgcolor: "white",
    xaxis: {
      title: `Time (${props.preview?.x_unit ?? "s"})`,
      zeroline: false,
    },
    yaxis: {
      title: "Counts / bin",
      rangemode: "tozero",
      zeroline: false,
    },
    legend: {
      orientation: "h",
      y: 1.12,
      x: 0,
    },
  }

  const config = {
    responsive: true,
    displaylogo: false,
    scrollZoom: true,
  }

  Plotly.react(plotlyTarget.value, traces, layout, config)
}

onMounted(() => {
  if (isDetailVariant.value) {
    renderPlotlyDetail()
  }
})

watch(
  () => [props.preview, props.variant],
  () => {
    if (isDetailVariant.value) {
      renderPlotlyDetail()
    }
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (plotlyTarget.value) {
    Plotly.purge(plotlyTarget.value)
  }
})
</script>

<template>
  <div :class="['trace-preview-wrapper', `trace-preview-wrapper--${variant}`]">
    <div v-if="variant === 'detail'" ref="plotlyTarget" class="plotly-wrapper"></div>
    <Line v-else :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.trace-preview-wrapper {
  width: 100%;
}

.trace-preview-wrapper--thumb {
  height: 180px;
}

.trace-preview-wrapper--detail {
  height: 320px;
}

.plotly-wrapper {
  width: 100%;
  height: 100%;
}
</style>