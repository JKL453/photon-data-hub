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
  const selectedFileIds = ref([])
  const selectedFile = ref(null)
  const deletingSelectedFiles = ref(false)
  const moveTargetDatasetId = ref("")
  const movingSelectedFiles = ref(false)
  const uploadingFiles = ref(false)
  const uploadProgressPercent = ref(0)
  const uploadProgressText = ref("")

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
    selectedFileIds.value = []
    moveTargetDatasetId.value = ""
    selectedFile.value = null
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

    selectedDataset.value.name = editDatasetName.value
    selectedDataset.value.description = editDatasetDescription.value

    await loadDatasets()

  } catch (error) {
    console.error("Fehler beim Update:", error)
    errorMessage.value = "Dataset konnte nicht aktualisiert werden."
  } finally {
    savingDataset.value = false
  }
}


async function deleteFile(fileId) {
  const confirmed = window.confirm(
    "Really delete this file?"
  )

  if (!confirmed) {
    return
  }

  try {
    await axios.delete(`http://localhost:8000/files/${fileId}`)

    if (selectedDataset.value) {
      await selectDataset(selectedDataset.value.id)
    }

    await loadDatasets()
  } catch (error) {
    console.error("Fehler beim Löschen der Datei:", error)
    errorMessage.value = "Datei konnte nicht gelöscht werden."
  }
}


async function deleteDataset(datasetId) {
  const confirmed = window.confirm(
    "Really delete this dataset and all associated files?"
  )

  if (!confirmed) {
    return
  }

  try {
    await axios.delete(`http://localhost:8000/datasets/${datasetId}`)

    selectedDataset.value = null

    await loadDatasets()
  } catch (error) {
    console.error("Fehler beim Löschen des Datasets:", error)
    errorMessage.value = "Dataset konnte nicht gelöscht werden."
  }
}

function toggleFileSelection(fileId) {
  if (selectedFileIds.value.includes(fileId)) {
    selectedFileIds.value = selectedFileIds.value.filter((id) => id !== fileId)
  } else {
    selectedFileIds.value = [...selectedFileIds.value, fileId]
  }
}

function isFileSelected(fileId) {
  return selectedFileIds.value.includes(fileId)
}

function toggleSelectAllFiles() {
  if (!selectedDataset.value) return

  const allFileIds = selectedDataset.value.files.map((file) => file.id)

  if (selectedFileIds.value.length === allFileIds.length) {
    selectedFileIds.value = []
  } else {
    selectedFileIds.value = allFileIds
  }
}

async function deleteSelectedFiles() {
  if (!selectedDataset.value || selectedFileIds.value.length === 0) {
    return
  }

  const confirmed = window.confirm(
    `Really delete ${selectedFileIds.value.length} selected file(s)?`
  )

  if (!confirmed) {
    return
  }

  deletingSelectedFiles.value = true
  errorMessage.value = ""

  try {
    await axios.post("http://localhost:8000/files/bulk-delete", {
      file_ids: selectedFileIds.value,
    })

    selectedFileIds.value = []

    await selectDataset(selectedDataset.value.id)
    await loadDatasets()
  } catch (error) {
    console.error("Fehler beim Löschen ausgewählter Dateien:", error)
    errorMessage.value = "Ausgewählte Dateien konnten nicht gelöscht werden."
  } finally {
    deletingSelectedFiles.value = false
  }
}

async function moveSelectedFiles() {
  if (!selectedDataset.value || selectedFileIds.value.length === 0 || !moveTargetDatasetId.value) {
    return
  }

  const confirmed = window.confirm(
    `Really move ${selectedFileIds.value.length} selected file(s) to another dataset?`
  )

  if (!confirmed) {
    return
  }

  movingSelectedFiles.value = true
  errorMessage.value = ""

  try {
    await axios.post("http://localhost:8000/files/bulk-move", {
      file_ids: selectedFileIds.value,
      target_dataset_id: moveTargetDatasetId.value,
    })

    selectedFileIds.value = []
    moveTargetDatasetId.value = ""

    await selectDataset(selectedDataset.value.id)
    await loadDatasets()
  } catch (error) {
    console.error("Fehler beim Verschieben ausgewählter Dateien:", error)
    errorMessage.value = "Ausgewählte Dateien konnten nicht verschoben werden."
  } finally {
    movingSelectedFiles.value = false
  }
}


function openFilePicker() {
  const input = document.getElementById("dataset-file-upload")
  if (input) {
    input.click()
  }
}

async function handleFileUpload(event) {
  const files = Array.from(event.target.files || [])

  if (files.length === 0 || !selectedDataset.value) {
    return
  }

  uploadingFiles.value = true
  uploadProgressPercent.value = 0
  uploadProgressText.value = `Uploading 0 / ${files.length}`
  errorMessage.value = ""

  try {
    for (let index = 0; index < files.length; index++) {
      const file = files[index]
      const formData = new FormData()
      formData.append("uploaded_file", file)

      uploadProgressText.value = `Uploading ${index + 1} / ${files.length}: ${file.name}`

      const response = await axios.post(
        `http://localhost:8000/datasets/${selectedDataset.value.id}/upload`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          onUploadProgress: (progressEvent) => {
            const total = progressEvent.total || file.size || 1
            const fileProgress = Math.round((progressEvent.loaded / total) * 100)
            const overallProgress = Math.round(((index + fileProgress / 100) / files.length) * 100)
            uploadProgressPercent.value = overallProgress
          },
        }
      )

      const uploadedFile = response.data

      try {
        await axios.post(
          `http://localhost:8000/files/${uploadedFile.id}/previews/generate-trace-thumb`
        )
      } catch (previewError) {
        console.error("Preview-Generierung fehlgeschlagen:", previewError)
      }
    }

    await selectDataset(selectedDataset.value.id)
    await loadDatasets()
  } catch (error) {
    console.error("Upload fehlgeschlagen:", error)
    errorMessage.value = "Upload fehlgeschlagen"
  } finally {
    uploadingFiles.value = false
    uploadProgressText.value = ""
    uploadProgressPercent.value = 0
    event.target.value = ""
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

        <div v-else-if="selectedFile" class="file-detail">
          <button
            class="secondary-button small-button"
            @click="selectedFile = null"
          >
            ← Back to dataset
          </button>

          <h3>{{ selectedFile.filename }}</h3>
          <p class="file-meta">{{ selectedFile.object_key }}</p>

          <TracePreview
            v-if="selectedFile.preview"
            :preview="selectedFile.preview.preview_data"
            variant="detail"
            class="detail-trace-preview"
          />

          <p v-else class="empty-state">Keine Preview für dieses File vorhanden.</p>
        </div>

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

          <button
            class="danger-button small-button"
            @click="deleteDataset(selectedDataset.id)"
          >
            Delete Dataset
          </button>


          <h4>Files</h4>

          <div class="upload-section">
            <input
              id="dataset-file-upload"
              class="hidden-file-input"
              type="file"
              multiple
              @change="handleFileUpload"
            />

            <button
              class="primary-button small-button"
              @click="openFilePicker"
              :disabled="uploadingFiles"
            >
              {{ uploadingFiles ? "Uploading..." : "Upload file(s)" }}
            </button>
            <div v-if="uploadingFiles" class="upload-progress">
              <div class="upload-progress-text">{{ uploadProgressText }}</div>
              <div class="upload-progress-bar">
                <div
                  class="upload-progress-bar-fill"
                  :style="{ width: `${uploadProgressPercent}%` }"
                ></div>
              </div>
              <div class="upload-progress-percent">{{ uploadProgressPercent }}%</div>
            </div>
          </div>

          <div v-if="selectedDataset.files.length > 0" class="file-actions-bar">
            <label class="select-all-row">
              <input
                type="checkbox"
                :checked="selectedFileIds.length === selectedDataset.files.length"
                @change="toggleSelectAllFiles"
              />
      
              <span>Select all</span>
            </label>

            <div class="bulk-actions-group">
              <select
                v-model="moveTargetDatasetId"
                class="text-input move-select"
              >
                <option value="">Move to dataset...</option>
                <option
                  v-for="ds in datasets.filter((ds) => ds.id !== selectedDataset.id)"
                  :key="ds.id"
                  :value="ds.id"
                >
                  {{ ds.name }}
                </option>
              </select>

              <button
                class="secondary-button small-button"
                @click="moveSelectedFiles"
                :disabled="selectedFileIds.length === 0 || !moveTargetDatasetId || movingSelectedFiles"
              >
                {{ movingSelectedFiles ? "Moving..." : `Move selected (${selectedFileIds.length})` }}
              </button>
            </div>

            <button
              class="danger-button small-button"
              @click="deleteSelectedFiles"
              :disabled="selectedFileIds.length === 0 || deletingSelectedFiles"
            >
              {{ deletingSelectedFiles ? "Deleting..." : `Delete selected (${selectedFileIds.length})` }}
            </button>
          </div>

          <ul class="file-list">
            <li
              v-for="file in selectedDataset.files"
              :key="file.id"
              class="file-item clickable-file"
              @click="selectedFile = file"
            >
              <div class="file-top-row">
                <label class="file-checkbox-row">
                  <input
                    type="checkbox"
                    :checked="isFileSelected(file.id)"
                    @click.stop
                    @change="toggleFileSelection(file.id)"
                  />
                  <span class="file-name">{{ file.filename }}</span>
                </label>
              </div>

              <div class="file-meta">{{ file.object_key }}</div>

              <TracePreview
                v-if="file.preview"
                :preview="file.preview.preview_data"
                variant="thumb"
              />

              <div class="file-button-row">
                <button class="download-button small-button" @click.stop="downloadFile(file.id)">
                  Download
                </button>

                <button class="danger-button small-button" @click.stop="deleteFile(file.id)">
                  Delete
                </button>
              </div>
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

.secondary-button {
  padding: 0.7rem 1rem;
  border: none;
  border-radius: 10px;
  background: #6c757d;
  color: white;
  cursor: pointer;
  font-weight: 600;
}

.secondary-button:hover {
  background: #5a6268;
}

.secondary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.edit-dataset-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.danger-button {
  padding: 0.45rem 0.8rem;
  border: none;
  border-radius: 10px;
  background: #d9534f;
  color: white;
  cursor: pointer;
  font-weight: 600;
}

.danger-button:hover {
  background: #c63f3b;
}

.small-button {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
  border-radius: 8px;
}

.file-actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.bulk-actions-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.move-select {
  min-width: 180px;
  margin: 0;
}

.select-all-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
}

.file-top-row {
  display: flex;
  align-items: center;
  margin-bottom: 0.35rem;
}

.file-checkbox-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  cursor: pointer;
}

.file-button-row {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.upload-section {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.hidden-file-input {
  display: none;
}

.upload-progress {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 260px;
}

.upload-progress-text {
  font-size: 0.85rem;
  color: #555;
}

.upload-progress-bar {
  width: 100%;
  height: 10px;
  background: #e8ebf3;
  border-radius: 999px;
  overflow: hidden;
}

.upload-progress-bar-fill {
  height: 100%;
  background: #2f6fed;
  transition: width 0.15s ease;
}

.upload-progress-percent {
  font-size: 0.8rem;
  color: #666;
}

.clickable-file {
  cursor: pointer;
}

.clickable-file:hover {
  background: #f1f4ff;
  border-color: #d9e1ff;
}

.file-detail {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail-trace-preview {
  width: 100%;
}

</style>