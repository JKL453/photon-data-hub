<script setup>
import { computed } from "vue"
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
})

const defaultColors = [
  "#2f6fed",
  "#f08a24",
  "#2ecc71",
  "#e74c3c",
  "#9b59b6",
  "#f1c40f",
]

const chartData = computed(() => {
  const x = props.preview.x ?? []
  const series = props.preview.series ?? []

  return {
    labels: x,
    datasets: series.map((s, i) => ({
    label: s.label,
    data: s.y,
    borderWidth: 2,
    pointRadius: 0,
    tension: 0,
    borderColor: defaultColors[i % defaultColors.length],
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
  scales: {
    x: {
      title: {
        display: true,
        text: `Time/s`,
      },
      ticks: {
        maxTicksLimit: 6,
        stepSize: 1,
        callback(value) {
          const label = this.getLabelForValue(value)
          const num = Number(label)
          if (!Number.isFinite(num)) return label
          return Math.round(num)
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
</script>

<template>
  <div class="trace-preview-wrapper">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.trace-preview-wrapper {
  height: 180px;
}
</style>