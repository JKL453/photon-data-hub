<script setup>

  import { ref, onMounted, computed } from "vue"
  import axios from "axios"

  import DatasetDetailPanel from "./components/DatasetDetailPanel.vue"
  import FileDetailPanel from "./components/FileDetailPanel.vue"

  import Button from 'primevue/button'
  import Breadcrumb from 'primevue/breadcrumb'
  import Card from 'primevue/card'
  import Divider from 'primevue/divider'
  import Message from "primevue/message"
  import PanelMenu from "primevue/panelmenu"
  import ProgressSpinner from 'primevue/progressspinner'
  import Tag from 'primevue/tag'
  import Toolbar from "primevue/toolbar"




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
  const sidebarCollapsed = ref(false)

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

  const selectedDatasetFileCount = computed(() => selectedDataset.value?.files?.length || 0)

  const breadcrumbItems = computed(() => {
    const items = [
      {
        label: "Datasets",
        icon: "pi pi-database",
        command: () => {
          selectedFile.value = null
        },
      },
    ]

    if (selectedDataset.value) {
      items.push({
        label: selectedDataset.value.name,
        icon: "pi pi-folder-open",
        command: () => {
          selectedFile.value = null
        },
      })
    }

    if (selectedFile.value) {
      items.push({
        label: selectedFile.value.filename,
        icon: "pi pi-file",
      })
    }

    return items
  })

  const workspaceTitle = computed(() => {
    if (selectedFile.value) return selectedFile.value.filename
    if (selectedDataset.value) return selectedDataset.value.name
    return "Photon Data Hub"
  })

  const workspaceSubtitle = computed(() => {
    if (selectedFile.value) return selectedDataset.value?.name || "Selected dataset"
    if (selectedDataset.value) return selectedDataset.value.description || "No description available."
    return "Choose a dataset from the navigation."
  })

  const menuItems = computed(() => [
  {
    label: "Datasets",
    icon: "pi pi-database",
    items: datasets.value.map((ds) => ({
      label: ds.name,
      icon: selectedDataset.value?.id === ds.id ? "pi pi-folder-open" : "pi pi-folder",
      command: () => selectDataset(ds.id),
    })),
  },
])

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

  if (selectedDataset.value) {
    editDatasetName.value = selectedDataset.value.name
    editDatasetDescription.value = selectedDataset.value.description
    editDatasetNotes.value = selectedDataset.value.notes || ""
  }
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

function closeFileDetail() {
  selectedFile.value = null
  fileDetailTrace.value = null
  fileAcfTrace.value = null
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


<template>
  <div
    class="app-shell"
    :class="{ 'app-shell--sidebar-collapsed': sidebarCollapsed }"
  >
    <aside class="app-sidebar">
      <div class="brand-block">
        <div class="brand-icon-wrap">
          <i class="pi pi-sparkles brand-icon"></i>
        </div>
        <div v-if="!sidebarCollapsed" class="brand-copy">
          <div class="brand-title">Photon Data Hub</div>
          <div class="brand-subtitle">TCSPC Platform</div>
        </div>
        <Button
          class="sidebar-toggle"
          :icon="sidebarCollapsed ? 'pi pi-angle-right' : 'pi pi-angle-left'"
          severity="secondary"
          variant="text"
          rounded
          :aria-label="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          @click="sidebarCollapsed = !sidebarCollapsed"
        />
      </div>

      <Divider v-if="!sidebarCollapsed" class="sidebar-divider" />

      <Card v-if="!sidebarCollapsed" class="sidebar-card">
        <template #title>
          <div class="card-title-row">
            <span>Navigation</span>
            <Tag :value="datasets.length" severity="info" rounded />
          </div>
        </template>
        <template #content>
          <ProgressSpinner
            v-if="loadingDatasets"
            class="sidebar-spinner"
            stroke-width="4"
            aria-label="Loading datasets"
          />
          <PanelMenu v-else :model="menuItems" class="dataset-menu" />
        </template>
      </Card>

      <Card v-if="!sidebarCollapsed" class="sidebar-card sidebar-info-card">
        <template #title>Workspace</template>
        <template #content>
          <div class="sidebar-meta-list">
            <Tag
              :value="selectedDataset ? `${selectedDatasetFileCount} files` : 'No dataset selected'"
              :severity="selectedDataset ? 'success' : 'secondary'"
              rounded
            />
            <span v-if="selectedDataset" class="sidebar-selected-name">
              {{ selectedDataset.name }}
            </span>
          </div>
        </template>
      </Card>

      <div v-else class="sidebar-rail">
        <Button
          icon="pi pi-database"
          severity="secondary"
          variant="text"
          rounded
          :title="`${datasets.length} datasets`"
          @click="sidebarCollapsed = false"
        />
        <Button
          v-if="selectedDataset"
          icon="pi pi-folder-open"
          severity="secondary"
          variant="text"
          rounded
          :title="selectedDataset.name"
          @click="sidebarCollapsed = false"
        />
      </div>
    </aside>

    <main class="app-main">
      <Toolbar class="main-toolbar">
        <template #start>
          <Breadcrumb :model="breadcrumbItems" class="app-breadcrumb" />
        </template>

        <template #end>
          <Tag
            v-if="selectedDataset"
            :value="`${selectedDatasetFileCount} files`"
            severity="secondary"
            rounded
          />
          <Button
            label="Reload"
            icon="pi pi-refresh"
            variant="outlined"
            :loading="loadingDatasets || loadingDatasetDetail"
            @click="selectedDataset ? selectDataset(selectedDataset.id) : loadDatasets()"
          />
        </template>
      </Toolbar>

      <Message v-if="errorMessage" severity="error" class="app-message" closable>
        {{ errorMessage }}
      </Message>

      <Card class="workspace-shell">
        <template #title>
          <div class="workspace-header">
            <div class="workspace-heading">
              <h1 class="workspace-title">{{ workspaceTitle }}</h1>
              <p class="workspace-subtitle">{{ workspaceSubtitle }}</p>
            </div>

            <Button
              v-if="selectedFile"
              label="Back to dataset"
              icon="pi pi-arrow-left"
              variant="outlined"
              @click="closeFileDetail"
            />
          </div>
        </template>

        <template #content>
          <div v-if="!selectedDataset" class="empty-state-content">
            <i class="pi pi-database empty-icon"></i>
            <h2>Select a dataset</h2>
            <p>Choose a dataset from the navigation to view files and metadata.</p>
          </div>

          <div v-else-if="selectedFile" class="workspace-body workspace-body--file">
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
              @back="closeFileDetail"
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
          </div>

          <div v-else class="workspace-body">
            <DatasetDetailPanel
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
              @handle-file-upload="handleFileUpload"
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
        </template>
      </Card>
    </main>
  </div>
</template>


<style scoped>
.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  background: var(--p-surface-100);
  color: var(--p-text-color);
  transition: grid-template-columns 0.18s ease;
}

.app-shell--sidebar-collapsed {
  grid-template-columns: 76px minmax(0, 1fr);
}

.app-sidebar {
  background: var(--p-surface-0);
  color: var(--p-text-color);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  border-right: 1px solid var(--p-surface-200);
  min-width: 0;
}

.app-shell--sidebar-collapsed .app-sidebar {
  padding: 0.75rem 0.5rem;
  align-items: center;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.1rem 0 0.25rem;
}

.app-shell--sidebar-collapsed .brand-block {
  flex-direction: column;
  gap: 0.5rem;
}

.brand-copy {
  min-width: 0;
  flex: 1;
}

.brand-icon-wrap {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: var(--p-primary-50);
  border: 1px solid var(--p-primary-100);
  flex: 0 0 auto;
}

.brand-icon {
  font-size: 1.25rem;
  color: var(--p-primary-color);
}

.brand-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--p-text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  font-size: 0.82rem;
  color: var(--p-text-muted-color);
}

.sidebar-toggle {
  margin-left: auto;
  flex: 0 0 auto;
}

.app-shell--sidebar-collapsed .sidebar-toggle {
  margin-left: 0;
}

.sidebar-divider {
  margin: 0;
}

.card-title-row,
.sidebar-meta-list {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.sidebar-meta-list {
  align-items: flex-start;
  flex-direction: column;
}

.sidebar-selected-name {
  color: var(--p-text-muted-color);
  font-weight: 600;
  word-break: break-word;
}

.sidebar-spinner {
  width: 2rem;
  height: 2rem;
}

.sidebar-card {
  border-radius: 8px;
  border: 1px solid var(--p-surface-200);
  overflow: hidden;
  box-shadow: none;
  background: var(--p-surface-50);
}

.sidebar-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding-top: 0.25rem;
}

.app-main {
  padding: 1.25rem clamp(1rem, 2vw, 2.5rem) 2rem;
  min-width: 0;
}

.main-toolbar,
.app-message {
  margin-bottom: 1rem;
}

.workspace-shell {
  border-radius: 8px;
  border: 1px solid var(--p-surface-200);
  box-shadow: var(--p-card-shadow);
  background: var(--p-content-background);
}

.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
}

.workspace-heading {
  min-width: 0;
}

.workspace-title {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  color: var(--p-text-color);
  overflow-wrap: anywhere;
}

.workspace-subtitle {
  margin: 0.35rem 0 0;
  color: var(--p-text-muted-color);
  font-size: 1rem;
  overflow-wrap: anywhere;
}

.workspace-body {
  min-width: 0;
}

.workspace-body--file {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 440px);
  gap: 1.25rem;
  align-items: start;
}

.empty-state-content {
  min-height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  text-align: center;
  color: var(--p-text-muted-color);
}

.empty-icon {
  font-size: 2rem;
  color: var(--p-primary-color);
}

:deep(.main-toolbar .p-toolbar-end) {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}

:deep(.app-breadcrumb) {
  padding: 0;
  border: none;
  background: transparent;
}

:deep(.dataset-menu .p-panelmenu-panel) {
  background: transparent;
  border: none;
}

:deep(.dataset-menu .p-panelmenu-header-link) {
  background: transparent;
  color: var(--p-text-color);
  border-radius: 8px;
  padding: 0.8rem 0.9rem;
}

:deep(.dataset-menu .p-panelmenu-header-link:hover) {
  background: var(--p-surface-100);
}

:deep(.dataset-menu .p-panelmenu-content) {
  background: transparent;
  border: none;
  padding-top: 0.35rem;
}

:deep(.dataset-menu .p-menuitem-link) {
  color: var(--p-text-muted-color);
  border-radius: 8px;
  padding: 0.7rem 0.8rem;
}

:deep(.dataset-menu .p-menuitem-link:hover) {
  background: var(--p-surface-100);
  color: var(--p-text-color);
}

:deep(.sidebar-card .p-card-body) {
  padding: 1rem;
}

:deep(.sidebar-card .p-card) {
  background: transparent;
}

:deep(.workspace-shell .p-card-body) {
  padding: clamp(1rem, 1.5vw, 1.75rem);
}

:deep(.workspace-shell .p-card-title) {
  margin-bottom: 1rem;
}

:deep(.p-tag) {
  font-weight: 600;
}

@media (max-width: 1200px) {
  .workspace-body--file {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .app-sidebar {
    border-right: none;
    border-bottom: 1px solid var(--p-surface-200);
  }

  .app-main {
    padding: 1rem;
  }

  .workspace-title {
    font-size: 1.6rem;
  }
}
</style>
