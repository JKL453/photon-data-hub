<script setup>

  import { ref, onMounted, computed } from "vue"
  import axios from "axios"

  import DatasetSidebar from "./components/DatasetSidebar.vue"
  import DatasetDetailPanel from "./components/DatasetDetailPanel.vue"
  import FileDetailPanel from "./components/FileDetailPanel.vue"
  import TracePreview from "./components/TracePreview.vue"

  import Button from 'primevue/button'
  import Card from 'primevue/card'
  import InputText from 'primevue/inputtext'
  import Textarea from 'primevue/textarea'
  import Select from 'primevue/select'




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
  const fileMeasurementDateDraft = ref("")
  const fileExcitationPowerDraft = ref("")
  const fileObjectiveDraft = ref("")
  const bulkMeasurementDateDraft = ref("")
  const bulkExcitationPowerDraft = ref("")
  const bulkObjectiveDraft = ref("")
  const savingBulkMetadata = ref(false)
  const uploadMetadataSuggestions = ref([])
  const applyingUploadMetadata = ref(false)
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

  const detailBinWidthOptions = [
    { label: '1 ms', value: 1 },
    { label: '5 ms', value: 5 },
    { label: '10 ms', value: 10 },
    { label: '50 ms', value: 50 },
    { label: '100 ms', value: 100 },
  ]

  const moveTargetDatasetOptions = computed(() => {
    if (!selectedDataset.value) return []

    return datasets.value
      .filter((ds) => ds.id !== selectedDataset.value.id)
      .map((ds) => ({
        label: ds.name,
        value: ds.id,
      }))
  })
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



function formatLastModifiedForDatetimeLocal(lastModifiedMs) {
  if (!lastModifiedMs) return ""

  const date = new Date(lastModifiedMs)
  if (Number.isNaN(date.getTime())) return ""

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  const hours = String(date.getHours()).padStart(2, "0")
  const minutes = String(date.getMinutes()).padStart(2, "0")

  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function formatApiDatetimeForInput(value) {
  if (!value) return ""

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return typeof value === "string" ? value.slice(0, 16) : ""
  }

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  const hours = String(date.getHours()).padStart(2, "0")
  const minutes = String(date.getMinutes()).padStart(2, "0")

  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function convertDatetimeLocalToApiValue(value) {
  if (!value) return null

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toISOString()
}

function parseExcitationPowerFromFilename(filename) {
  if (!filename) return null

  const patterns = [
    { pattern: /(\d+(?:[\.,]\d+)?)\s*(?:uW|µW)(?=[^a-zA-Z]|$)/i, factor: 1 },
    { pattern: /(\d+(?:[\.,]\d+)?)\s*(?:mW)(?=[^a-zA-Z]|$)/i, factor: 1000 },
    { pattern: /(\d+(?:[\.,]\d+)?)\s*(?:W)(?=[^a-zA-Z]|$)/i, factor: 1000000 },
  ]

  for (const { pattern, factor } of patterns) {
    const match = filename.match(pattern)
    if (!match) continue

    const rawValue = match[1].replace(",", ".")
    const value = Number(rawValue)

    if (Number.isFinite(value)) {
      return value * factor
    }
  }

  return null
}

function buildDetectedMetadataSuggestion(uploadedFileId, browserFile) {
  const detectedMeasurementDate = formatLastModifiedForDatetimeLocal(browserFile.lastModified)
  const detectedExcitationPower = parseExcitationPowerFromFilename(browserFile.name)

  if (!detectedMeasurementDate && detectedExcitationPower == null) {
    return null
  }

  return {
    fileId: uploadedFileId,
    filename: browserFile.name,
    measurement_date: detectedMeasurementDate || null,
    excitation_power: detectedExcitationPower,
  }
}

async function applyUploadMetadataSuggestions() {
  if (uploadMetadataSuggestions.value.length === 0) {
    return
  }

  applyingUploadMetadata.value = true
  errorMessage.value = ""

  try {
    await Promise.all(
      uploadMetadataSuggestions.value.map((suggestion) =>
        axios.patch(`http://localhost:8000/files/${suggestion.fileId}`, {
          measurement_date: convertDatetimeLocalToApiValue(suggestion.measurement_date),
          excitation_power: suggestion.excitation_power,
        })
      )
    )

    uploadMetadataSuggestions.value = []

    if (selectedDataset.value) {
      await selectDataset(selectedDataset.value.id)
    }
  } catch (error) {
    console.error("Detected metadata could not be applied:", error)
    errorMessage.value = "Erkannte Metadaten konnten nicht übernommen werden."
  } finally {
    applyingUploadMetadata.value = false
  }
}

async function updateSelectedMetadata() {
  if (!selectedDataset.value || selectedFileIds.value.length === 0) {
    return
  }

  savingBulkMetadata.value = true
  errorMessage.value = ""

  try {
    await axios.post("http://localhost:8000/files/bulk-update-metadata", {
      file_ids: selectedFileIds.value,
      measurement_date: convertDatetimeLocalToApiValue(bulkMeasurementDateDraft.value),
      excitation_power:
        bulkExcitationPowerDraft.value === ""
          ? null
          : Number(bulkExcitationPowerDraft.value),
      objective: bulkObjectiveDraft.value || null,
    })

    await selectDataset(selectedDataset.value.id)
  } catch (error) {
    console.error("Fehler beim Bulk-Update der Metadaten:", error)
    errorMessage.value = "Metadaten konnten nicht gesammelt gesetzt werden."
  } finally {
    savingBulkMetadata.value = false
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
    const detectedSuggestions = []
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

      const suggestion = buildDetectedMetadataSuggestion(uploadedFile.id, file)
      if (suggestion) {
        detectedSuggestions.push(suggestion)
      }

      try {
        await axios.post(
          `http://localhost:8000/files/${uploadedFile.id}/previews/generate-trace-thumb`
        )
      } catch (previewError) {
        console.error("Preview-Generierung fehlgeschlagen:", previewError)
      }
    }

    uploadMetadataSuggestions.value = detectedSuggestions

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
  fileMeasurementDateDraft.value = formatApiDatetimeForInput(file.measurement_date)
  fileExcitationPowerDraft.value = file.excitation_power ?? ""
  fileObjectiveDraft.value = file.objective || ""
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
        measurement_date: convertDatetimeLocalToApiValue(fileMeasurementDateDraft.value),
        excitation_power:
          fileExcitationPowerDraft.value === "" ? null : Number(fileExcitationPowerDraft.value),
        objective: fileObjectiveDraft.value || null,
      }
    )

    selectedFile.value.notes = response.data.notes
    selectedFile.value.measurement_date = response.data.measurement_date
    selectedFile.value.excitation_power = response.data.excitation_power
    selectedFile.value.objective = response.data.objective

    if (selectedDataset.value) {
      const fileIndex = selectedDataset.value.files.findIndex(
        (file) => file.id === selectedFile.value.id
      )

      if (fileIndex !== -1) {
        selectedDataset.value.files[fileIndex].notes = response.data.notes
        selectedDataset.value.files[fileIndex].measurement_date = response.data.measurement_date
        selectedDataset.value.files[fileIndex].excitation_power = response.data.excitation_power
        selectedDataset.value.files[fileIndex].objective = response.data.objective
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


// --------------------------------------------------------------------------------
// -------------------------------- TEMPLATE --------------------------------------
// --------------------------------------------------------------------------------


<template>
  <div class="page">
    <h1>Photon Data Hub</h1>

    <div class="layout" :class="{ 'layout--file-selected': selectedFile }">
      <DatasetSidebar
        :datasets="datasets"
        :loading-datasets="loadingDatasets"
        :error-message="errorMessage"
        :new-dataset-name="newDatasetName"
        :new-dataset-description="newDatasetDescription"
        :creating-dataset="creatingDataset"
        @update:new-dataset-name="newDatasetName = $event"
        @update:new-dataset-description="newDatasetDescription = $event"
        @create-dataset="createDataset"
        @select-dataset="selectDataset"
      />

      <template v-if="selectedFile">
        <FileDetailPanel
          :selected-file="selectedFile"
          :new-tag-name="newTagName"
          :file-notes-draft="fileNotesDraft"
          :file-measurement-date-draft="fileMeasurementDateDraft"
          :file-excitation-power-draft="fileExcitationPowerDraft"
          :file-objective-draft="fileObjectiveDraft"
          :saving-file-notes="savingFileNotes"
          :selected-detail-view="selectedDetailView"
          :selected-detail-bin-width-ms="selectedDetailBinWidthMs"
          :detail-bin-width-options="detailBinWidthOptions"
          :file-detail-trace="fileDetailTrace"
          :file-acf-trace="fileAcfTrace"
          :loading-file-detail-trace="loadingFileDetailTrace"
          :loading-file-acf-trace="loadingFileAcfTrace"
          :acf-bins-per-dec="acfBinsPerDec"
          :acf-lag-min-exp="acfLagMinExp"
          :acf-lag-max-exp="acfLagMaxExp"
          :acf-cut-points="acfCutPoints"
          :acf-tau-min-us="acfTauMinUs"
          :acf-tau-max-us="acfTauMaxUs"
          @back="selectedFile = null; fileDetailTrace = null; fileAcfTrace = null"
          @update:new-tag-name="newTagName = $event"
          @add-tag="addTagToFile"
          @remove-tag="removeTagFromFile"
          @update:file-notes-draft="fileNotesDraft = $event"
          @update:file-measurement-date-draft="fileMeasurementDateDraft = $event"
          @update:file-excitation-power-draft="fileExcitationPowerDraft = $event"
          @update:file-objective-draft="fileObjectiveDraft = $event"
          @save-notes="saveFileNotes"
          @switch-detail-view="switchDetailView"
          @update:selected-detail-bin-width-ms="selectedDetailBinWidthMs = $event"
          @load-detail-trace="loadFileDetailTrace"
          @load-acf-trace="loadFileAcfTrace"
          @update:acf-bins-per-dec="acfBinsPerDec = $event"
          @update:acf-lag-min-exp="acfLagMinExp = $event"
          @update:acf-lag-max-exp="acfLagMaxExp = $event"
          @update:acf-cut-points="acfCutPoints = $event"
          @update:acf-tau-min-us="acfTauMinUs = $event"
          @update:acf-tau-max-us="acfTauMaxUs = $event"
        />
      </template>

      <DatasetDetailPanel
        v-else
        :loading-dataset-detail="loadingDatasetDetail"
        :selected-dataset="selectedDataset"
        :edit-dataset-name="editDatasetName"
        :edit-dataset-description="editDatasetDescription"
        :edit-dataset-notes="editDatasetNotes"
        :saving-dataset="savingDataset"
        :uploading-files="uploadingFiles"
        :upload-progress-text="uploadProgressText"
        :upload-progress-percent="uploadProgressPercent"
        :upload-metadata-suggestions="uploadMetadataSuggestions"
        :applying-upload-metadata="applyingUploadMetadata"
        :selected-file-ids="selectedFileIds"
        :move-target-dataset-id="moveTargetDatasetId"
        :move-target-dataset-options="moveTargetDatasetOptions"
        :moving-selected-files="movingSelectedFiles"
        :deleting-selected-files="deletingSelectedFiles"
        :bulk-measurement-date-draft="bulkMeasurementDateDraft"
        :bulk-excitation-power-draft="bulkExcitationPowerDraft"
        :bulk-objective-draft="bulkObjectiveDraft"
        :saving-bulk-metadata="savingBulkMetadata"
        @update:edit-dataset-name="editDatasetName = $event"
        @update:edit-dataset-description="editDatasetDescription = $event"
        @update:edit-dataset-notes="editDatasetNotes = $event"
        @update:moveTargetDatasetId="moveTargetDatasetId = $event"
        @update:bulkMeasurementDateDraft="bulkMeasurementDateDraft = $event"
        @update:bulkExcitationPowerDraft="bulkExcitationPowerDraft = $event"
        @update:bulkObjectiveDraft="bulkObjectiveDraft = $event"
        @update-dataset="updateDataset"
        @delete-dataset="deleteDataset"
        @open-file-picker="openFilePicker"
        @apply-upload-metadata-suggestions="applyUploadMetadataSuggestions"
        @dismiss-upload-metadata-suggestions="uploadMetadataSuggestions = []"
        @toggle-select-all-files="toggleSelectAllFiles"
        @move-selected-files="moveSelectedFiles"
        @copy-selected-files="copySelectedFiles"
        @delete-selected-files="deleteSelectedFiles"
        @update-selected-metadata="updateSelectedMetadata"
        @open-file-detail="openFileDetail"
        @toggle-file-selection="toggleFileSelection"
        @download-file="downloadFile"
        @delete-file="deleteFile"
      />
    </div>
  </div>
</template>


<style scoped>
.page {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 1.5rem 2rem;
  font-family: Arial, sans-serif;
  background: #f6f7fb;
  min-height: 100vh;
  color: #222;
  box-sizing: border-box;
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
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 1.5rem;
  align-items: start;
  width: 100%;
}

.layout--file-selected {
  grid-template-columns: 300px minmax(0, 1.5fr) minmax(420px, 0.95fr);
}

.panel-card--side-detail {
  min-width: 0;
}

.panel-card {
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
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

.bulk-metadata-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.6rem;
  align-items: end;
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

.upload-detection-panel {
  margin-bottom: 1rem;
  padding: 0.85rem 1rem;
  border: 1px solid #d9deea;
  border-radius: 12px;
  background: #fafbff;
}

.upload-detection-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.upload-detection-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.upload-detection-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.upload-detection-item {
  padding: 0.55rem 0.7rem;
  border: 1px solid #e8ebf3;
  border-radius: 10px;
  background: white;
}

.upload-detection-filename {
  font-weight: 600;
  margin-bottom: 0.2rem;
}

.upload-detection-meta {
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
  color: #555;
  font-size: 0.9rem;
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


.file-detail-main-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
}


.sub-card {
  border-radius: 14px;
}

.file-analysis-card {
  min-width: 0;
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

.file-metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}

.file-metadata-grid label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.notes-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #555;
}

.save-notes-button {
  align-self: flex-start;
}

/* --- PrimeVue compact control adjustments --- */
:deep(.p-inputtext),
:deep(.p-select),
:deep(.p-button) {
  font-size: 0.9rem;
}

:deep(.p-inputtext),
:deep(.p-select) {
  min-height: 50px;
}

:deep(.p-inputtext) {
  padding-top: 0.45rem;
  padding-bottom: 0.45rem;
}

:deep(.p-select) {
  height: 50px;
}

:deep(.p-select .p-select-label) {
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
  display: flex;
  align-items: center;
}

:deep(.p-select .p-select-trigger) {
  width: 2rem;
}

:deep(.p-button.small-button) {
  padding: 0.3rem 0.6rem;
}

@media (max-width: 900px) {
  .layout,
  .layout--file-selected {
    grid-template-columns: 1fr;
  }
}
</style>