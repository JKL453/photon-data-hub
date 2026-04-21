import { createApp } from 'vue'
import '@fontsource-variable/inter'
import './style.css'
import App from './App.vue'
import router from './router'

import PrimeVue from 'primevue/config'
import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'
import 'primeicons/primeicons.css'

const PhotonPreset = definePreset(Aura, {
  semantic: {
    fontFamily: "'Inter Variable', 'Inter', system-ui, sans-serif",
    borderRadius: {
      none: '0',
      xs:   '3px',
      sm:   '5px',
      md:   '7px',
      lg:   '10px',
      xl:   '14px',
    },
  },
})

const app = createApp(App)

app.use(PrimeVue, {
  theme: {
    preset: PhotonPreset,
    options: {
      darkModeSelector: 'system',
    },
  },
})

app.use(router)
app.mount('#app')
