<script setup>

  import { ref, onMounted } from "vue"
  import axios from "axios"

  import TracePreview from "./components/TracePreview.vue"


  const datasets = ref([])

  const newDatasetName = ref("")
  const newDatasetDescription = ref("")
  const creatingDataset = ref(false)
  const selectedDataset = ref(null)
  const loadingDatasets = ref(false)
  const loadingDatasetDetail = ref(false)
  const editDatasetName = ref("")
  const editDatasetDescription = ref("")
  const savingDataset = ref(false)

  const errorMessage = ref("")

  
  async function createDataset() {
  if (!newDatasetName.value.trim()) {
    errorMessage.value = "Bitte gib einen Dataset-Namen ein."
    return
  }

  creatingDataset.value = true
  errorMessage.value = ""

  try {
    const ownerId = "476a2e3b-3c01-4f90-b44e-e1011673dcf4"

    await axios.post(
      `http://localhost:8000/datasets?owner_id=${ownerId}`,
      {
        name: newDatasetName.value,
        description: newDatasetDescription.value,
      }
    )

    newDatasetName.value = ""
    newDatasetDescription.value = ""

    await loadDatasets()
  } catch (error) {
    console.error("Fehler beim Erstellen des Datasets:", error)
    errorMessage.value = "Dataset konnte nicht erstellt werden."
  } finally {
    creatingDataset.value = false
  }
}

  async function loadDatasets() {
    loadingDatasets.value = true
    errorMessage.value = ""

    try {
      const response = await axios.get("http://localhost:8000/datasets")
      datasets.value = response.data
    } catch (error) {
      console.error("Fehler beim Laden der Datasets:", error)
      errorMessage.value = "Datasets konnten nicht geladen werden."
    } finally {
      loadingDatasets.value = false
    }
  }

  async function selectDataset(datasetId) {
  loadingDatasetDetail.value = true
  errorMessage.value = ""

  try {
    const response = await axios.get(`http://localhost:8000/datasets/${datasetId}`)
    const dataset = response.data

    const filesWithPreviews = await Promise.all(
      dataset.files.map(async (file) => {
        try {
          const previewResponse = await axios.get(
            `http://localhost:8000/files/${file.id}/previews/trace_thumb`
          )

          return {
            ...file,
            preview: previewResponse.data,
          }
        } catch (error) {
          return {
            ...file,
            preview: null,
          }
        }
      })
    )

    selectedDataset.value = {
      ...dataset,
      files: filesWithPreviews,
    }
  } catch (error) {
    console.error("Fehler beim Laden des Dataset-Details:", error)
    errorMessage.value = "Dataset-Details konnten nicht geladen werden."
  } finally {
    loadingDatasetDetail.value = false
  }
  editDatasetName.value = selectedDataset.value.name
  editDatasetDescription.value = selectedDataset.value.description
}

  onMounted(async () => {
    await loadDatasets()
  })

  async function downloadFile(fileId) {
  try {
    const response = await axios.get(`http://localhost:8000/files/${fileId}/download`)
    const downloadUrl = response.data.download_url

    window.open(downloadUrl, "_blank")
  } catch (error) {
    console.error("Fehler beim Herunterladen der Datei:", error)
    errorMessage.value = "Datei konnte nicht heruntergeladen werden."
  }
}


async function updateDataset() {
  if (!selectedDataset.value) return

  savingDataset.value = true
  errorMessage.value = ""

  try {
    await axios.patch(
      `http://localhost:8000/datasets/${selectedDataset.value.id}`,
      {
        name: editDatasetName.value,
        description: editDatasetDescription.value,
      }
    )

    // direkt UI aktualisieren
    selectedDataset.value.name = editDatasetName.value
    selectedDataset.value.description = editDatasetDescription.value

    // linke Liste neu laden
    await loadDatasets()

  } catch (error) {
    console.error("Fehler beim Update:", error)
    errorMessage.value = "Dataset konnte nicht aktualisiert werden."
  } finally {
    savingDataset.value = false
  }
}


</script>




<template>

  <div class="page">
    <h1>Photon Data Hub</h1>

    <p v-if="loadingDatasets">Datasets werden geladen ...</p>
    <p v-if="errorMessage">{{ errorMessage }}</p>

    <div class="layout">
      <section class="panel">

        <h2>Datasets</h2>

        <div class="create-dataset-form">
          <input
            v-model="newDatasetName"
            type="text"
            placeholder="Dataset name"
            class="text-input"
          />

          <textarea
            v-model="newDatasetDescription"
            placeholder="Description"
            class="text-input textarea-input"
          ></textarea>

          <button
            class="primary-button"
            @click="createDataset"
            :disabled="creatingDataset"
          >
            {{ creatingDataset ? "Creating..." : "Create Dataset" }}
          </button>
        </div>

        <ul class="dataset-list">
          <li
            v-for="ds in datasets"
            :key="ds.id"
            class="dataset-item"
            @click="selectDataset(ds.id)"
          >
            <div class="dataset-name">{{ ds.name }}</div>
            <div class="dataset-meta">
              {{ ds.file_count }} files
            </div>
          </li>
        </ul>
      </section>

      <section class="panel">
        <h2>Dataset Details</h2>

        <p v-if="loadingDatasetDetail">Dataset-Details werden geladen ...</p>

        <div v-else-if="selectedDataset">
          <div class="edit-dataset-form">
            <input
              v-model="editDatasetName"
              class="text-input"
              placeholder="Dataset name"
            />

            <textarea
              v-model="editDatasetDescription"
              class="text-input textarea-input"
              placeholder="Description"
            ></textarea>

            <button
              class="primary-button"
              @click="updateDataset"
              :disabled="savingDataset"
            >
              {{ savingDataset ? "Saving..." : "Save changes" }}
            </button>
          </div>

          <h4>Files</h4>

          <ul class="file-list">
            <li
              v-for="file in selectedDataset.files"
              :key="file.id"
              class="file-item"
            >
              <div class="file-name">{{ file.filename }}</div>
              <div class="file-meta">{{ file.object_key }}</div>
              <TracePreview
                v-if="file.preview"
                :preview="file.preview.preview_data"
              />


              <button class="download-button" @click="downloadFile(file.id)">
                Download
              </button>
            </li>
          </ul>

          <p v-if="selectedDataset.files.length === 0" class="empty-state">
            Dieses Dataset enthält noch keine Files.
          </p>
        </div>

        <p v-else class="empty-state">Wähle links ein Dataset aus.</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
  .page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  font-family: Arial, sans-serif;
  background: #f6f7fb;
  min-height: 100vh;
  color: #222;
}

h1 {
  margin-bottom: 1.5rem;
  font-size: 2rem;
}

h2 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

h3 {
  margin-bottom: 0.5rem;
}

h4 {
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 1.5rem;
  align-items: start;
}

.panel {
  background: white;
  border-radius: 16px;
  padding: 1.25rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.dataset-list,
.file-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.dataset-item,
.file-item {
  background: #fafbff;
  border: 1px solid #e8ebf3;
  border-radius: 14px;
  padding: 0.9rem 1rem;
  margin-bottom: 0.9rem;
  transition: all 0.15s ease;
}

.dataset-item {
  cursor: pointer;
}

.dataset-item:hover {
  background: #f1f4ff;
  border-color: #d9e1ff;
  transform: translateY(-1px);
}

.dataset-name,
.file-name {
  font-weight: 600;
  margin-bottom: 0.35rem;
  font-size: 1rem;
}

.dataset-meta,
.file-meta {
  font-size: 0.9rem;
  color: #666;
  word-break: break-word;
}

.download-button {
  margin-top: 0.75rem;
  padding: 0.45rem 0.8rem;
  border: none;
  border-radius: 10px;
  background: #2f6fed;
  color: white;
  cursor: pointer;
  font-weight: 600;
}

.download-button:hover {
  background: #255dd0;
}

.empty-state {
  color: #666;
  font-style: italic;
}

.create-dataset-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.text-input {
  width: 100%;
  padding: 0.7rem 0.9rem;
  border: 1px solid #d9deea;
  border-radius: 10px;
  font-size: 0.95rem;
  box-sizing: border-box;
}

.textarea-input {
  min-height: 90px;
  resize: vertical;
}

.primary-button {
  padding: 0.7rem 1rem;
  border: none;
  border-radius: 10px;
  background: #2f6fed;
  color: white;
  cursor: pointer;
  font-weight: 600;
}

.primary-button:hover {
  background: #255dd0;
}

.primary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.edit-dataset-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
</style>