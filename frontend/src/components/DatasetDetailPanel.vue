<script setup>
import { ref } from 'vue'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import ProgressBar from 'primevue/progressbar'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import TracePreview from './TracePreview.vue'

const showDatasetMeta = ref(false)
const showFileMeta    = ref(false)

defineProps({
  loadingDatasetDetail: Boolean,
  selectedDataset: Object,
  editDatasetName: String,
  editDatasetDescription: String,
  editDatasetNotes: String,
  savingDataset: Boolean,
  uploadingFiles: Boolean,
  uploadProgressText: String,
  uploadProgressPercent: Number,
  uploadMetadataSuggestions: Array,
  applyingUploadMetadata: Boolean,
  selectedFileIds: Array,
  moveTargetDatasetId: String,
  moveTargetDatasetOptions: Array,
  movingSelectedFiles: Boolean,
  deletingSelectedFiles: Boolean,
  bulkMeasurementDateDraft: String,
  bulkExcitationPowerDraft: [String, Number],
  bulkObjectiveDraft: String,
  savingBulkMetadata: Boolean,
})

const emit = defineEmits([
  'update:editDatasetName',
  'update:editDatasetDescription',
  'update:editDatasetNotes',
  'update:moveTargetDatasetId',
  'update:bulkMeasurementDateDraft',
  'update:bulkExcitationPowerDraft',
  'update:bulkObjectiveDraft',
  'update-dataset',
  'delete-dataset',
  'open-file-picker',
  'handle-file-upload',
  'apply-upload-metadata-suggestions',
  'dismiss-upload-metadata-suggestions',
  'toggle-select-all-files',
  'move-selected-files',
  'copy-selected-files',
  'delete-selected-files',
  'update-selected-metadata',
  'open-file-detail',
  'toggle-file-selection',
  'download-file',
  'delete-file',
])

function isFileSelected(selectedFileIds, fileId) {
  return selectedFileIds.includes(fileId)
}

function formatMeasurementDate(value) {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return date.toLocaleDateString('de-DE', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

function formatExcitationPower(value) {
  if (value == null || value === '') return null
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue)) return null
  return `${Number.isInteger(numericValue) ? numericValue : numericValue.toFixed(2)} µW`
}

function fileMetadataItems(file) {
  const measurementDate  = formatMeasurementDate(file.measurement_date)
  const excitationPower  = formatExcitationPower(file.excitation_power)

  return [
    measurementDate  ? { icon: 'pi pi-calendar', label: measurementDate  } : null,
    excitationPower  ? { icon: 'pi pi-bolt',      label: excitationPower  } : null,
    file.objective   ? { icon: 'pi pi-search',    label: file.objective   } : null,
  ].filter(Boolean)
}
</script>

<template>
  <section class="dataset-detail-panel">
    <div class="panel-content">

      <!-- Loading -->
      <div v-if="loadingDatasetDetail" class="loading-state">
        <Message severity="info" :closable="false">Loading dataset …</Message>
        <ProgressBar mode="indeterminate" class="loading-progress" />
      </div>

      <div v-else-if="selectedDataset" class="dataset-workspace">

        <!-- ── Dataset Metadata ──────────────────────────────────── -->
        <div class="section-block">
          <button class="section-toggle" @click="showDatasetMeta = !showDatasetMeta">
            <i class="pi pi-database section-toggle-icon"></i>
            <span>Dataset Metadata</span>
            <i :class="['pi section-chevron', showDatasetMeta ? 'pi-chevron-up' : 'pi-chevron-down']"></i>
          </button>

          <div v-if="showDatasetMeta" class="section-body">
            <div class="form-grid">
              <label class="field">
                <span>Name</span>
                <InputText
                  :model-value="editDatasetName"
                  placeholder="Dataset name"
                  @update:model-value="emit('update:editDatasetName', $event)"
                />
              </label>

              <label class="field field--wide">
                <span>Description</span>
                <Textarea
                  :model-value="editDatasetDescription"
                  auto-resize
                  rows="3"
                  placeholder="Description"
                  @update:model-value="emit('update:editDatasetDescription', $event)"
                />
              </label>

              <label class="field field--wide">
                <span>Notes</span>
                <Textarea
                  :model-value="editDatasetNotes"
                  auto-resize
                  rows="3"
                  placeholder="Dataset notes"
                  @update:model-value="emit('update:editDatasetNotes', $event)"
                />
              </label>
            </div>

            <div class="form-actions">
              <Button
                label="Save changes"
                icon="pi pi-save"
                :loading="savingDataset"
                :disabled="savingDataset"
                @click="emit('update-dataset')"
              />
              <Button
                label="Delete Dataset"
                icon="pi pi-trash"
                severity="danger"
                variant="outlined"
                @click="emit('delete-dataset', selectedDataset.id)"
              />
            </div>
          </div>
        </div>

        <!-- ── Bulk File Metadata ────────────────────────────────── -->
        <div v-if="selectedDataset.files.length > 0" class="section-block">
          <button class="section-toggle" @click="showFileMeta = !showFileMeta">
            <i class="pi pi-tags section-toggle-icon"></i>
            <span>Bulk File Metadata</span>
            <i :class="['pi section-chevron', showFileMeta ? 'pi-chevron-up' : 'pi-chevron-down']"></i>
          </button>

          <div v-if="showFileMeta" class="section-body">
            <div class="bulk-metadata-panel">
              <label class="field">
                <span>Measurement date</span>
                <InputText
                  :model-value="bulkMeasurementDateDraft"
                  type="datetime-local"
                  @update:model-value="emit('update:bulkMeasurementDateDraft', $event)"
                />
              </label>

              <label class="field">
                <span>Power (µW)</span>
                <InputNumber
                  :model-value="bulkExcitationPowerDraft === '' ? null : Number(bulkExcitationPowerDraft)"
                  :min="0"
                  :min-fraction-digits="0"
                  :max-fraction-digits="3"
                  placeholder="Power (µW)"
                  @update:model-value="emit('update:bulkExcitationPowerDraft', $event ?? '')"
                />
              </label>

              <label class="field">
                <span>Objective</span>
                <InputText
                  :model-value="bulkObjectiveDraft"
                  placeholder="Objective"
                  @update:model-value="emit('update:bulkObjectiveDraft', $event)"
                />
              </label>

              <Button
                label="Set for selected"
                icon="pi pi-tags"
                :loading="savingBulkMetadata"
                :disabled="selectedFileIds.length === 0 || savingBulkMetadata"
                @click="emit('update-selected-metadata')"
              />
            </div>
          </div>
        </div>

        <!-- ── Upload header ─────────────────────────────────────── -->
        <div class="section-header-row">
          <div class="section-header-title">
            <i class="pi pi-folder-open"></i>
            <span>Files</span>
            <span class="file-count-badge">{{ selectedDataset.files.length }}</span>
          </div>
          <div class="section-header-actions">
            <input
              id="dataset-file-upload"
              class="hidden-file-input"
              type="file"
              multiple
              @change="emit('handle-file-upload', $event)"
            />
            <Button
              label="Upload"
              icon="pi pi-upload"
              size="small"
              :loading="uploadingFiles"
              :disabled="uploadingFiles"
              @click="emit('open-file-picker')"
            />
          </div>
        </div>

        <!-- Upload progress -->
        <div v-if="uploadingFiles" class="upload-progress">
          <div class="upload-progress-text">{{ uploadProgressText }}</div>
          <ProgressBar :value="uploadProgressPercent" />
        </div>

        <!-- Upload metadata detection -->
        <Message
          v-if="uploadMetadataSuggestions.length > 0"
          severity="info"
          :closable="false"
          class="upload-detection-panel"
        >
          <div class="upload-detection-header">
            <strong>Detected metadata for uploaded files</strong>
            <div class="upload-detection-actions">
              <Button
                label="Apply"
                icon="pi pi-check"
                size="small"
                :loading="applyingUploadMetadata"
                :disabled="applyingUploadMetadata"
                @click="emit('apply-upload-metadata-suggestions')"
              />
              <Button
                label="Dismiss"
                icon="pi pi-times"
                size="small"
                severity="secondary"
                variant="outlined"
                :disabled="applyingUploadMetadata"
                @click="emit('dismiss-upload-metadata-suggestions')"
              />
            </div>
          </div>

          <div class="upload-detection-list">
            <div
              v-for="suggestion in uploadMetadataSuggestions"
              :key="suggestion.fileId"
              class="upload-detection-item"
            >
              <span class="upload-detection-filename">{{ suggestion.filename }}</span>
              <Tag v-if="suggestion.measurement_date" :value="`Date: ${suggestion.measurement_date}`" severity="secondary" rounded />
              <Tag v-if="suggestion.excitation_power != null" :value="`Power: ${suggestion.excitation_power} µW`" severity="secondary" rounded />
            </div>
          </div>
        </Message>

        <!-- ── Bulk controls ──────────────────────────────────────── -->
        <div v-if="selectedDataset.files.length > 0" class="file-list-controls">
          <div class="file-list-controls-left">
            <label class="select-all-row">
              <Checkbox
                binary
                :model-value="selectedFileIds.length === selectedDataset.files.length"
                @update:model-value="emit('toggle-select-all-files')"
              />
              <span>Select all</span>
            </label>
            <Tag :value="`${selectedFileIds.length} selected`" severity="secondary" rounded />
          </div>

          <div class="file-list-controls-right">
            <Select
              :model-value="moveTargetDatasetId"
              :options="moveTargetDatasetOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Target dataset"
              class="move-select"
              @update:model-value="emit('update:moveTargetDatasetId', $event)"
            />
            <Button
              icon="pi pi-arrow-right"
              aria-label="Move selected"
              title="Move selected"
              size="small"
              severity="secondary"
              rounded
              :loading="movingSelectedFiles"
              :disabled="selectedFileIds.length === 0 || !moveTargetDatasetId || movingSelectedFiles"
              @click="emit('move-selected-files')"
            />
            <Button
              icon="pi pi-copy"
              aria-label="Copy selected"
              title="Copy selected"
              size="small"
              severity="secondary"
              variant="outlined"
              rounded
              :disabled="selectedFileIds.length === 0 || !moveTargetDatasetId"
              @click="emit('copy-selected-files')"
            />
            <Button
              icon="pi pi-trash"
              aria-label="Delete selected"
              title="Delete selected"
              size="small"
              severity="danger"
              variant="outlined"
              rounded
              :loading="deletingSelectedFiles"
              :disabled="selectedFileIds.length === 0 || deletingSelectedFiles"
              @click="emit('delete-selected-files')"
            />
          </div>
        </div>

        <!-- ── File list ──────────────────────────────────────────── -->
        <div v-if="selectedDataset.files.length > 0" class="file-list">
          <article
            v-for="file in selectedDataset.files"
            :key="file.id"
            class="file-row"
            :class="{ 'file-row--selected': isFileSelected(selectedFileIds, file.id) }"
            :title="file.object_key"
            @click="emit('open-file-detail', file)"
          >
            <!-- Header: checkbox · filename · metadata · actions -->
            <div class="file-row-header">
              <label class="file-check" @click.stop>
                <Checkbox
                  binary
                  :model-value="isFileSelected(selectedFileIds, file.id)"
                  @update:model-value="emit('toggle-file-selection', file.id)"
                />
              </label>

              <div class="file-row-info">
                <div class="file-row-top">
                  <span class="file-name">{{ file.filename }}</span>
                  <div v-if="file.tags?.length" class="file-tags-inline">
                    <Tag
                      v-for="tag in file.tags"
                      :key="tag.id"
                      :value="tag.name"
                      severity="info"
                      rounded
                    />
                  </div>
                </div>
                <div class="file-metadata-strip">
                  <span
                    v-for="item in fileMetadataItems(file)"
                    :key="`${file.id}-${item.label}`"
                    class="metadata-chip"
                  >
                    <i :class="item.icon"></i>
                    {{ item.label }}
                  </span>
                  <span v-if="fileMetadataItems(file).length === 0" class="metadata-chip metadata-chip--empty">
                    No metadata
                  </span>
                </div>
              </div>

              <div class="file-row-actions" @click.stop>
                <Button
                  icon="pi pi-download"
                  aria-label="Download"
                  title="Download"
                  size="small"
                  severity="secondary"
                  variant="text"
                  rounded
                  @click="emit('download-file', file.id)"
                />
                <Button
                  icon="pi pi-trash"
                  aria-label="Delete"
                  title="Delete"
                  size="small"
                  severity="danger"
                  variant="text"
                  rounded
                  @click="emit('delete-file', file.id)"
                />
              </div>
            </div>

            <!-- Previews: trace (wider) + ACF -->
            <div class="file-row-previews">
              <div class="preview-col preview-col--trace">
                <TracePreview
                  v-if="file.tracePreview"
                  :preview="file.tracePreview.preview_data"
                  variant="thumb"
                />
                <div v-else class="thumb-empty">
                  <i class="pi pi-chart-line"></i>
                </div>
              </div>
              <div class="preview-col preview-col--acf">
                <TracePreview
                  v-if="file.acfPreview"
                  :preview="file.acfPreview.preview_data"
                  variant="thumb"
                  x-scale="logarithmic"
                  :y-min="1"
                />
                <div v-else class="thumb-empty">
                  <i class="pi pi-wave-pulse"></i>
                </div>
              </div>
            </div>
          </article>
        </div>

        <Message v-if="selectedDataset.files.length === 0" severity="secondary" :closable="false">
          This dataset contains no files yet.
        </Message>
      </div>

      <Message v-else severity="secondary" :closable="false">
        Select a dataset to view its files.
      </Message>
    </div>
  </section>
</template>

<style scoped>
/* ── Layout ─────────────────────────────────────────────────────── */
.panel-content,
.dataset-workspace,
.loading-state,
.upload-progress,
.upload-detection-list,
.file-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.dataset-workspace {
  max-width: 1080px;
}

.loading-progress {
  height: 0.3rem;
}

/* ── Form grids ──────────────────────────────────────────────────── */
.form-grid,
.bulk-metadata-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  align-items: end;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--p-text-muted-color);
}

.field--wide {
  grid-column: 1 / -1;
}

.form-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding-top: 0.25rem;
}

/* ── Custom collapsible sections ─────────────────────────────────── */
.section-block {
  border: 1px solid var(--p-content-border-color);
  border-radius: 10px;
  overflow: hidden;
}

.section-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.7rem 1rem;
  background: color-mix(in srgb, var(--p-content-background) 97%, var(--p-text-color) 3%);
  border: none;
  cursor: pointer;
  text-align: left;
  color: var(--p-text-color);
  font-size: 0.88rem;
  font-weight: 600;
  font-family: inherit;
  transition: background 0.12s ease;
}

.section-toggle:hover {
  background: color-mix(in srgb, var(--p-content-background) 92%, var(--p-text-color) 8%);
}

.section-toggle-icon {
  color: var(--p-primary-color);
  font-size: 0.9rem;
}

.section-chevron {
  margin-left: auto;
  font-size: 0.72rem;
  color: var(--p-text-muted-color);
}

.section-body {
  padding: 1rem;
  border-top: 1px solid var(--p-content-border-color);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* ── Section header row (replaces Toolbar) ───────────────────────── */
.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.4rem 0;
  border-bottom: 1px solid var(--p-content-border-color);
}

.section-header-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--p-text-muted-color);
}

.file-count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  font-size: 0.72rem;
  font-weight: 700;
  background: color-mix(in srgb, var(--p-primary-color) 12%, transparent);
  color: var(--p-primary-color);
  border: 1px solid color-mix(in srgb, var(--p-primary-color) 22%, transparent);
}

.section-header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* ── Bulk file controls ──────────────────────────────────────────── */
.file-list-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding: 0.35rem 0;
}

.file-list-controls-left,
.file-list-controls-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.select-all-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
}

.move-select {
  width: 180px;
}

/* ── Upload ──────────────────────────────────────────────────────── */
.hidden-file-input {
  display: none;
}

.upload-progress-text {
  color: var(--p-text-muted-color);
  font-size: 0.85rem;
}

.upload-detection-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.upload-detection-actions {
  display: flex;
  gap: 0.5rem;
}

.upload-detection-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.upload-detection-filename {
  font-weight: 600;
  font-size: 0.88rem;
}

/* ── File list ───────────────────────────────────────────────────── */
.file-list {
  gap: 0.45rem;
}

.file-row {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--p-content-border-color);
  border-radius: 8px;
  background: var(--p-content-background);
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.13s ease, box-shadow 0.13s ease;
  min-width: 0;
}

.file-row:hover {
  border-color: color-mix(in srgb, var(--p-primary-color) 55%, transparent);
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}

.file-row--selected {
  border-color: var(--p-primary-color);
  box-shadow: inset 3px 0 0 var(--p-primary-color);
}

/* ── Row header ──────────────────────────────────────────────────── */
.file-row-header {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.55rem 0.75rem 0.55rem 0.65rem;
}

.file-check {
  display: flex;
  align-items: center;
  cursor: pointer;
  flex: 0 0 auto;
}

.file-row-info {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.file-row-top {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  min-width: 0;
}

.file-name {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--p-text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-tags-inline {
  display: flex;
  gap: 0.3rem;
  flex-wrap: wrap;
}

.file-metadata-strip {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.metadata-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.76rem;
  font-weight: 500;
  color: var(--p-text-muted-color);
  padding: 0.15rem 0.45rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: 5px;
  background: color-mix(in srgb, var(--p-content-background) 94%, var(--p-text-color) 6%);
  white-space: nowrap;
}

.metadata-chip i {
  font-size: 0.72rem;
  opacity: 0.75;
}

.metadata-chip--empty {
  opacity: 0.5;
}

.file-row-actions {
  display: flex;
  gap: 0.2rem;
  align-items: center;
  flex: 0 0 auto;
  opacity: 0;
  transition: opacity 0.13s ease;
}

.file-row:hover .file-row-actions {
  opacity: 1;
}

/* ── Row previews (full-width below header) ──────────────────────── */
.file-row-previews {
  display: grid;
  grid-template-columns: 3fr 2fr;
  border-top: 1px solid var(--p-content-border-color);
  overflow: hidden;
}

.preview-col {
  height: 110px;
  overflow: hidden;
  background: var(--p-surface-ground);
  display: flex;
  align-items: stretch;
}

.preview-col--acf {
  border-left: 1px solid var(--p-content-border-color);
}

.thumb-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--p-text-muted-color);
  opacity: 0.3;
  font-size: 1.1rem;
}

/* ── Deep overrides ──────────────────────────────────────────────── */
:deep(.p-inputtext),
:deep(.p-textarea),
:deep(.p-inputnumber),
:deep(.p-inputnumber-input),
:deep(.p-select) {
  width: 100%;
}

:deep(.preview-col .trace-preview-wrapper--thumb) {
  height: 110px;
  width: 100%;
}

@media (max-width: 900px) {
  .file-list-controls {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 600px) {
  .file-row-previews {
    grid-template-columns: 1fr;
  }

  .preview-col {
    height: 80px;
  }

  :deep(.preview-col .trace-preview-wrapper--thumb) {
    height: 80px;
  }

  .preview-col--acf {
    display: none;
  }
}
</style>
