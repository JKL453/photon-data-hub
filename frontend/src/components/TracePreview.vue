<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from "vue"
import { Line } from "vue-chartjs"
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  LogarithmicScale,
  CategoryScale,
  Legend,
  Tooltip,
} from "chart.js"
import Plotly from "plotly.js-dist-min"

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  LogarithmicScale,
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
  // "trace" | "acf" — controls layout hints for thumb variant
  plotKind: {
    type: String,
    default: "trace",
  },
  xScale: {
    type: String,
    default: "category",
  },
  yMin: {
    type: Number,
    default: null,
  },
})

const plotlyTarget = ref(null)

const channelColors = {
  0: "#2f6fed",
  1: "#f08a24",
  2: "#2ecc71",
  3: "#e74c3c",
}

function cssVar(name, fallback) {
  if (typeof window === "undefined") return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

const chartTheme = computed(() => ({
  background: cssVar("--p-content-background", "white"),
  border: cssVar("--p-content-border-color", "#e5e7eb"),
  text: cssVar("--p-text-color", "#1f2937"),
  mutedText: cssVar("--p-text-muted-color", "#6b7280"),
}))

const hasSeries = computed(() => {
  return Array.isArray(props.preview?.series) && props.preview.series.length > 0
})

// For ACF thumb: only show a limited number of x-points to keep it compact
const displayX = computed(() => {
  return props.preview?.x ?? []
})

const chartData = computed(() => {
  if (!hasSeries.value) return { labels: [], datasets: [] }

  const x = displayX.value
  const series = props.preview.series ?? []

  return {
    labels: props.xScale === "logarithmic" ? undefined : x,
    datasets: series.map((s, i) => ({
      label: s.label,
      data:
        props.xScale === "logarithmic"
          ? (s.y ?? [])
              .map((y, index) => ({ x: Number(x[index]), y }))
              .filter((point) => Number.isFinite(point.x) && point.x > 0)
          : s.y,
      borderWidth: props.variant === "thumb" ? 1.2 : 1.5,
      pointRadius: 0,
      tension: 0,
      borderColor:
        channelColors[s.channel] ??
        ["#2f6fed", "#f08a24", "#2ecc71", "#e74c3c", "#9b59b6", "#666"][i % 6],
    })),
  }
})

// Padding: trace thumb gets wider/flatter, ACF thumb gets tighter/squarish
const thumbPadding = computed(() => {
  if (props.plotKind === "acf") {
    return { top: 10, bottom: 24, left: 42, right: 8 }
  }
  return { top: 6, bottom: 24, left: 42, right: 8 }
})

const chartOptions = computed(() => {
  const isThumb = props.variant === "thumb"
  const isAcf = props.plotKind === "acf"

  // For ACF thumb: show fewer ticks since range is compact
  const xMaxTicks = isAcf ? 4 : 5
  const yMaxTicks = isAcf ? 4 : 4

  return {
    responsive: true,
    maintainAspectRatio: false,
    color: chartTheme.value.text,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: !isThumb,
      },
    },
    layout: {
      padding: isThumb
        ? thumbPadding.value
        : { top: 10, bottom: 4, left: 5, right: 5 },
    },
    scales: {
      x: {
        type: props.xScale,
        ticks: {
          display: true,
          color: chartTheme.value.mutedText,
          maxTicksLimit: xMaxTicks,
          font: { size: isThumb ? 11 : 12 },
          maxRotation: 0,
          callback(value) {
            if (props.xScale === "logarithmic") {
              const num = Number(value)
              if (!Number.isFinite(num)) return String(value)
              if (isThumb) {
                if (num < 1e-3) return `${(num * 1e6).toFixed(0)}µ`
                if (num < 1) return `${(num * 1e3).toFixed(0)}m`
                return `${num.toFixed(0)}`
              }
              return num >= 1 ? String(Math.round(num)) : num.toPrecision(1)
            }

            const label = this.getLabelForValue(value)
            const num = Number(label)
            if (!Number.isFinite(num)) return label

            // For trace thumb: show as seconds with 1 decimal
            if (isThumb) {
              return num < 10 ? `${num.toFixed(1)}` : `${Math.round(num)}`
            }
            return String(Math.round(num))
          },
        },
        grid: {
          display: false,
        },
        border: {
          display: true,
          color: chartTheme.value.border,
        },
        title: {
          display: isThumb,
          text: isAcf ? "τ (s)" : "t (s)",
          color: chartTheme.value.mutedText,
          font: { size: 11 },
          padding: { top: 2 },
        },
      },
      y: {
        ticks: {
          display: true,
          color: chartTheme.value.mutedText,
          maxTicksLimit: yMaxTicks,
          font: { size: 11 },
          // For ACF: show G(τ) values nicely
          callback(value) {
            if (isAcf) {
              const num = Number(value)
              if (num >= 10) return Math.round(num)
              if (num >= 1) return num.toFixed(1)
              return num.toPrecision(2)
            }
            const num = Number(value)
            if (num >= 1000) return `${(num / 1000).toFixed(0)}k`
            return Math.round(num)
          },
        },
        grid: {
          display: false,
        },
        border: {
          display: true,
          color: chartTheme.value.border,
        },
        title: {
          display: isThumb,
          text: isAcf ? "G(τ)" : "cts",
          color: chartTheme.value.mutedText,
          font: { size: 11 },
          padding: { bottom: 2 },
        },
        beginAtZero: props.yMin === null && !isAcf,
        min: props.yMin ?? undefined,
      },
    },
  }
})

const isDetailVariant = computed(() => props.variant === "detail")

function renderPlotlyDetail() {
  if (!plotlyTarget.value || !hasSeries.value || !isDetailVariant.value) return

  const traces = (props.preview.series ?? []).map((s, i) => ({
    x: props.preview.x ?? [],
    y: s.y,
    type: "scattergl",
    mode: "lines",
    name: s.label,
    line: {
      width: 2,
      color:
        channelColors[s.channel] ??
        ["#2f6fed", "#f08a24", "#2ecc71", "#e74c3c", "#9b59b6", "#666"][i % 6],
    },
  }))

  const layout = {
    autosize: true,
    margin: { l: 55, r: 20, t: 20, b: 80 },
    paper_bgcolor: chartTheme.value.background,
    plot_bgcolor: chartTheme.value.background,
    font: { color: chartTheme.value.text },
    xaxis: {
      title: `Time (${props.preview?.x_unit ?? "s"})`,
      type: props.preview?.preview_kind === "acf_detail" ? "log" : "linear",
      zeroline: false,
      gridcolor: chartTheme.value.border,
      linecolor: chartTheme.value.border,
      tickfont: { color: chartTheme.value.mutedText },
      titlefont: { color: chartTheme.value.mutedText },
    },
    yaxis: {
      title: props.preview?.y_unit ?? "Counts / bin",
      zeroline: false,
      range: [1, null],
      gridcolor: chartTheme.value.border,
      linecolor: chartTheme.value.border,
      tickfont: { color: chartTheme.value.mutedText },
      titlefont: { color: chartTheme.value.mutedText },
    },
    legend: {
      orientation: "h",
      y: -0.22,
      x: 0,
      xanchor: "left",
      yanchor: "top",
      font: { size: 10, color: chartTheme.value.text },
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
  if (isDetailVariant.value) renderPlotlyDetail()
})

watch(
  () => [props.preview, props.variant],
  () => {
    if (isDetailVariant.value) renderPlotlyDetail()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (plotlyTarget.value) Plotly.purge(plotlyTarget.value)
})
</script>

<template>
  <div :class="['trace-preview-wrapper', `trace-preview-wrapper--${variant}`, `trace-preview-wrapper--${plotKind}`]">
    <div v-if="variant === 'detail'" ref="plotlyTarget" class="plotly-wrapper"></div>
    <Line v-else :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.trace-preview-wrapper {
  width: 100%;
}

.trace-preview-wrapper--thumb {
  height: 100%;
}

.trace-preview-wrapper--detail {
  height: 320px;
}

.plotly-wrapper {
  width: 100%;
  height: 100%;
}
</style>