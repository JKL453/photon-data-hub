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
  const editDatasetNotes = ref("")
  const fileNotesDraft = ref("")
  const savingFileNotes = ref(false)
  const selectedFileIds = ref([])
  const selectedFile = ref(null)
  const deletingSelectedFiles = ref(false)
  const moveTargetDatasetId = ref("")
  const movingSelectedFiles = ref(false)
  const uploadingFiles = ref(false)
  const uploadProgressPercent = ref(0)
  const uploadProgressText = ref("")
  const selectedDetailBinWidthMs = ref(10)
  const fileDetailTrace = ref(null)
  const loadingFileDetailTrace = ref(false)
  const selectedDetailView = ref("trace")
  const fileAcfTrace = ref(null)
  const loadingFileAcfTrace = ref(false)
  const acfBinsPerDec = ref(30)
  const acfLagMinExp = ref(0)
  const acfLagMaxExp = ref(7)
  const acfCutPoints = ref(50)
  const acfTauMinUs = ref(5)
  const acfTauMaxUs = ref(0)
  const newTagName = ref("")
async function loadFileTags(fileId) {
  try {
    const response = await axios.get(`http://localhost:8000/files/${fileId}/tags`)
    return response.data
  } catch (error) {
    console.error(`Tags could not be loaded for file ${fileId}:`, error)
    return []
  }
}

async function addTagToFile(file) {
  const tagName = newTagName.value.trim()
  if (!tagName) return

  try {
    const tagResponse = await axios.post("http://localhost:8000/tags", {
      name: tagName,
    })

    await axios.post(
      `http://localhost:8000/files/${file.id}/tags/${tagResponse.data.id}`
    )

    const alreadyAssigned = (file.tags || []).some((tag) => tag.id === tagResponse.data.id)
    if (!alreadyAssigned) {
      file.tags = [...(file.tags || []), tagResponse.data]
    }

    newTagName.value = ""
  } catch (error) {
    console.error("Tag could not be added:", error)
    errorMessage.value = "Tag konnte nicht hinzugefügt werden."
  }
}

async function removeTagFromFile(file, tag) {
  try {
    await axios.delete(`http://localhost:8000/files/${file.id}/tags/${tag.id}`)
    file.tags = (file.tags || []).filter((t) => t.id !== tag.id)
  } catch (error) {
    console.error("Tag could not be removed:", error)
    errorMessage.value = "Tag konnte nicht entfernt werden."
  }
}


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

  async function loadTraceThumbPreview(fileId) {
    try {
      const previewResponse = await axios.get(
        `http://localhost:8000/files/${fileId}/previews/trace_thumb`
      )

      return previewResponse.data
    } catch (error) {
      try {
        await axios.post(
          `http://localhost:8000/files/${fileId}/previews/generate-trace-thumb`
        )

        const previewResponse = await axios.get(
          `http://localhost:8000/files/${fileId}/previews/trace_thumb`
        )

        return previewResponse.data
      } catch (retryError) {
        console.error(`Preview could not be loaded or generated for file ${fileId}:`, retryError)
        return null
      }
    }
  }


  async function loadAcfThumbPreview(fileId) {
  try {
    const previewResponse = await axios.get(
      `http://localhost:8000/files/${fileId}/previews/acf_thumb`
    )

    return previewResponse.data
  } catch (error) {
    try {
      await axios.post(
        `http://localhost:8000/files/${fileId}/previews/generate-acf-thumb`
      )

      const previewResponse = await axios.get(
        `http://localhost:8000/files/${fileId}/previews/acf_thumb`
      )

      return previewResponse.data
    } catch (retryError) {
      console.error(`ACF preview could not be loaded or generated for file ${fileId}:`, retryError)
      return null
    }
  }
}

function sortDatasetFiles(files) {
  return [...files].sort((a, b) => {
    const aTime = a.created_at ? new Date(a.created_at).getTime() : NaN
    const bTime = b.created_at ? new Date(b.created_at).getTime() : NaN

    const aHasValidTime = Number.isFinite(aTime)
    const bHasValidTime = Number.isFinite(bTime)

    if (aHasValidTime && bHasValidTime && aTime !== bTime) {
      return aTime - bTime
    }

    return (a._listOrder ?? 0) - (b._listOrder ?? 0)
  })
}

  async function selectDataset(datasetId) {
  loadingDatasetDetail.value = true
  errorMessage.value = ""

  try {
    const response = await axios.get(`http://localhost:8000/datasets/${datasetId}`)
    const dataset = response.data

    const filesWithPreviews = await Promise.all(
      dataset.files.map(async (file, index) => {
        const tracePreview = await loadTraceThumbPreview(file.id)
        const acfPreview = await loadAcfThumbPreview(file.id)
        const tags = await loadFileTags(file.id)

        return {
          ...file,
          tracePreview,
          acfPreview,
          tags,
          _listOrder: index,
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
    fileDetailTrace.value = null
    fileAcfTrace.value = null
    selectedDetailView.value = "trace"
  } catch (error) {
    console.error("Fehler beim Laden des Dataset-Details:", error)
    errorMessage.value = "Dataset-Details konnten nicht geladen werden."
  } finally {
    loadingDatasetDetail.value = false
  }
  editDatasetName.value = selectedDataset.value.name
  editDatasetDescription.value = selectedDataset.value.description
  editDatasetNotes.value = selectedDataset.value.notes || ""
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
        notes: editDatasetNotes.value,
      }
    )

    selectedDataset.value.name = editDatasetName.value
    selectedDataset.value.description = editDatasetDescription.value
    selectedDataset.value.notes = editDatasetNotes.value

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


async function copySelectedFiles() {
  if (!selectedDataset.value || selectedFileIds.value.length === 0 || !moveTargetDatasetId.value) {
    return
  }

  const confirmed = window.confirm(
    `Copy ${selectedFileIds.value.length} file(s) to another dataset?`
  )

  if (!confirmed) return

  try {
    await axios.post("http://localhost:8000/files/bulk-copy", {
      file_ids: selectedFileIds.value,
      target_dataset_id: moveTargetDatasetId.value,
    })

    await selectDataset(selectedDataset.value.id)
    await loadDatasets()
  } catch (error) {
    console.error("Copy failed:", error)
    errorMessage.value = "Files could not be copied."
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


async function loadFileDetailTrace(fileId) {
  loadingFileDetailTrace.value = true
  errorMessage.value = ""

  try {
    const response = await axios.get(
      `http://localhost:8000/files/${fileId}/trace-detail`,
      {
        params: {
          bin_width_ms: selectedDetailBinWidthMs.value,
          max_points: 5000,
        },
      }
    )

    fileDetailTrace.value = response.data
  } catch (error) {
    console.error("Fehler beim Laden des Detail-Traces:", error)
    errorMessage.value = "Detail-Trace konnte nicht geladen werden."
  } finally {
    loadingFileDetailTrace.value = false
  }
}


async function openFileDetail(file) {
  selectedFile.value = file
  selectedDetailView.value = "trace"
  fileAcfTrace.value = null
  fileNotesDraft.value = file.notes || ""
  await loadFileDetailTrace(file.id)
}

async function saveFileNotes() {
  if (!selectedFile.value) return

  savingFileNotes.value = true
  errorMessage.value = ""

  try {
    const response = await axios.patch(
      `http://localhost:8000/files/${selectedFile.value.id}`,
      {
        notes: fileNotesDraft.value,
      }
    )

    selectedFile.value.notes = response.data.notes

    if (selectedDataset.value) {
      const fileIndex = selectedDataset.value.files.findIndex(
        (file) => file.id === selectedFile.value.id
      )

      if (fileIndex !== -1) {
        selectedDataset.value.files[fileIndex].notes = response.data.notes

      }
    }
  } catch (error) {
    console.error("Fehler beim Speichern der File-Notizen:", error)
    errorMessage.value = "File-Notizen konnten nicht gespeichert werden."
  } finally {
    savingFileNotes.value = false
  }
}


async function switchDetailView(view) {
  if (!selectedFile.value) return

  selectedDetailView.value = view

  if (view === "trace") {
    await loadFileDetailTrace(selectedFile.value.id)
  }

  if (view === "acf") {
    await loadFileAcfTrace(selectedFile.value.id)
  }
}


async function loadFileAcfTrace(fileId) {
  loadingFileAcfTrace.value = true
  errorMessage.value = ""

  try {
    const response = await axios.get(
      `http://localhost:8000/files/${fileId}/acf-detail`,
      {
        params: {
          bins_per_dec: acfBinsPerDec.value,
          lag_min_exp: acfLagMinExp.value,
          lag_max_exp: acfLagMaxExp.value,
          cut_points: acfCutPoints.value,
          tau_min_s: acfTauMinUs.value > 0 ? acfTauMinUs.value * 1e-6 : null,
          tau_max_s: acfTauMaxUs.value > 0 ? acfTauMaxUs.value * 1e-6 : null,
        },
      }
    )

    console.log("ACF response from backend:", response.data)
    fileAcfTrace.value = response.data
  } catch (error) {
    console.error("Fehler beim Laden der ACF/CCF:", error)
    errorMessage.value = "ACF/CCF konnte nicht geladen werden."
  } finally {
    loadingFileAcfTrace.value = false
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
            @click="selectedFile = null; fileDetailTrace = null; fileAcfTrace = null"
          >
            ← Back to dataset
          </button>

          <h3>{{ selectedFile.filename }}</h3>
          <p class="file-meta">{{ selectedFile.object_key }}</p>
          <div class="file-notes-section">
            <label class="notes-label" for="file-notes-textarea">File notes</label>
            <textarea
              id="file-notes-textarea"
              v-model="fileNotesDraft"
              class="text-input textarea-input"
              placeholder="Add notes for this file"
            ></textarea>
            <button
              class="secondary-button small-button save-notes-button"
              @click="saveFileNotes"
              :disabled="savingFileNotes"
            >
              {{ savingFileNotes ? "Saving..." : "Save notes" }}
            </button>
          </div>

          <div class="file-tags" v-if="selectedFile.tags?.length">
            <span
              v-for="tag in selectedFile.tags"
              :key="tag.id"
              class="tag-pill removable-tag"
              @click="removeTagFromFile(selectedFile, tag)"
              title="Remove tag"
            >
              {{ tag.name }} ×
            </span>
          </div>

          <div class="tag-input-row">
            <input
              v-model="newTagName"
              type="text"
              placeholder="Add tag"
              class="text-input"
              @keyup.enter="addTagToFile(selectedFile)"
            />
            <button
              class="secondary-button small-button"
              @click="addTagToFile(selectedFile)"
            >
              Add tag
            </button>
          </div>

          <div class="detail-view-toggle">
            <button
              class="secondary-button small-button"
              :class="{'active-toggle': selectedDetailView === 'trace' }"
              @click="switchDetailView('trace')"
            >
              Trace
            </button>

            <button
              class="secondary-button small-button"
              :class="{'active-toggle': selectedDetailView === 'acf' }"
              @click="switchDetailView('acf')"
            >
              ACF
            </button>
          </div>

          <div v-if="selectedDetailView === 'trace'" class="detail-controls">
            <label for="bin-width-select">Bin width:</label>
            <select
              id="bin-width-select"
              v-model.number="selectedDetailBinWidthMs"
              class="text-input"
              @change="loadFileDetailTrace(selectedFile.id)"
            >
              <option :value="1">1 ms</option>
              <option :value="5">5 ms</option>
              <option :value="10">10 ms</option>
              <option :value="50">50 ms</option>
              <option :value="100">100 ms</option>
            </select>
          </div>

          <div v-if="selectedDetailView === 'acf'" class="detail-controls detail-controls-grid">
            <label>
              Bins/dec
              <input v-model.number="acfBinsPerDec" type="number" min="1" class="text-input" />
            </label>

            <label>
              Lag min exp
              <input v-model.number="acfLagMinExp" type="number" class="text-input" />
            </label>

            <label>
              Lag max exp
              <input v-model.number="acfLagMaxExp" type="number" class="text-input" />
            </label>

            <label>
              Cut points
              <input v-model.number="acfCutPoints" type="number" min="0" class="text-input" />
            </label>

            <label>
              τ min (µs)
              <input v-model.number="acfTauMinUs" type="number" min="0" step="0.1" class="text-input" />
            </label>

            <label>
              τ max (µs, 0 = none)
              <input v-model.number="acfTauMaxUs" type="number" min="0" step="0.1" class="text-input" />
            </label>

            <button
              class="secondary-button small-button"
              @click="loadFileAcfTrace(selectedFile.id)"
              :disabled="loadingFileAcfTrace"
            >
              {{ loadingFileAcfTrace ? "Loading..." : "Update ACF" }}
            </button>
          </div>


          <TracePreview
            v-if="selectedDetailView === 'trace' && fileDetailTrace"
            :preview="fileDetailTrace"
            variant="detail"
          />

          <TracePreview
            v-else-if="selectedDetailView === 'acf' && fileAcfTrace"
            :preview="fileAcfTrace"
            variant="detail"
          />

          <p v-else-if="selectedDetailView === 'trace' && loadingFileDetailTrace" class="empty-state">
            Lade Detail-Trace ...
          </p>

          <p v-else-if="selectedDetailView === 'acf' && loadingFileAcfTrace" class="empty-state">
            Lade ACF/CCF ...
          </p>

          <p v-else class="empty-state">Keine Daten für diese Ansicht vorhanden.</p>
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
            <textarea
              v-model="editDatasetNotes"
              class="text-input textarea-input"
              placeholder="Dataset notes"
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

            <div class="bulk-actions-panel">
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
                  {{ movingSelectedFiles ? "Moving..." : "Move selected" }}
                </button>

                <button
                  class="secondary-button small-button"
                  @click="copySelectedFiles"
                  :disabled="selectedFileIds.length === 0 || !moveTargetDatasetId"
                >
                  Copy selected
                </button>

                <button
                  class="danger-button small-button"
                  @click="deleteSelectedFiles"
                  :disabled="selectedFileIds.length === 0 || deletingSelectedFiles"
                >
                  {{ deletingSelectedFiles ? "Deleting..." : "Delete selected" }}
                </button>
              </div>

              <div class="selected-files-info">
                {{ selectedFileIds.length }} file(s) selected
              </div>
            </div>
          </div>

          <ul class="file-list">
            <li
              v-for="file in selectedDataset.files"
              :key="file.id"
              class="file-item clickable-file"
              @click="openFileDetail(file)"
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

              <div class="file-tags-inline" v-if="file.tags?.length">
                <span
                  v-for="tag in file.tags"
                  :key="tag.id"
                  class="tag-pill"
                >
                  {{ tag.name }}
                </span>
              </div>

              <div class="preview-stack">
                <div class="preview-block">
                  <div class="preview-label">Trace</div>
                  <TracePreview
                    v-if="file.tracePreview"
                    :preview="file.tracePreview.preview_data"
                    variant="thumb"
                  />
                </div>

                <div class="preview-block preview-block--acf">
                  <div class="preview-label">ACF</div>
                  <TracePreview
                    v-if="file.acfPreview"
                    :preview="file.acfPreview.preview_data"
                    variant="thumb"
                  />
                </div>
              </div>

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

.bulk-actions-panel {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.selected-files-info {
  font-size: 0.9rem;
  color: #666;
  white-space: nowrap;
  align-self: flex-start;
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

.detail-view-toggle {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.active-toggle {
  background: #2f6fed;
}

.detail-controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  align-items: end;
}

.detail-controls-grid label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.preview-stack {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 0.6rem;
  align-items: start;
}

.preview-block {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.preview-block--acf {
  max-width: 220px;
}

.preview-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #666;
}

.file-tags,
.file-tags-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.file-tags-inline {
  margin-top: 0.5rem;
}

.tag-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: #eef2ff;
  color: #445;
  font-size: 0.75rem;
  font-weight: 600;
}

.removable-tag {
  cursor: pointer;
}

.removable-tag:hover {
  background: #e0e7ff;
}

.tag-input-row {
  display: flex;
  gap: 0.6rem;
  align-items: center;
}

.tag-input-row .text-input {
  max-width: 220px;
}

.file-notes-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.notes-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #555;
}

.save-notes-button {
  align-self: flex-start;
}

</style>