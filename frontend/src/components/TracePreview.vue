<script setup>
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale
} from 'chart.js'

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale)

const props = defineProps({
  preview: Object
})

const data = {
  labels: props.preview.x,
  datasets: [
    {
      data: props.preview.y,
      borderWidth: 1,
      pointRadius: 0,
      borderColor: 'green'
    }
  ]
}
</script>

<template>
  <Line :data="data" />
</template>