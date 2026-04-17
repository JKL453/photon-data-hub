<script setup>
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Divider from 'primevue/divider'
import Fieldset from 'primevue/fieldset'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import ProgressBar from 'primevue/progressbar'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import Toolbar from 'primevue/toolbar'
import TracePreview from './TracePreview.vue'

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

  return date.toLocaleDateString('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

function formatExcitationPower(value) {
  if (value == null || value === '') return null

  const numericValue = Number(value)
  if (!Number.isFinite(numericValue)) return null

  return `${Number.isInteger(numericValue) ? numericValue : numericValue.toFixed(2)} µW`
}

function fileMetadataItems(file) {
  const measurementDate = formatMeasurementDate(file.measurement_date)
  const excitationPower = formatExcitationPower(file.excitation_power)

  return [
    measurementDate ? { icon: 'pi pi-calendar', label: measurementDate } : null,
    excitationPower ? { icon: 'pi pi-bolt', label: excitationPower } : null,
    file.objective ? { icon: 'pi pi-search', label: file.objective } : null,
  ].filter(Boolean)
}
</script>

<template>
  <section class="dataset-detail-panel">
    <div class="panel-content">
      <div v-if="loadingDatasetDetail" class="loading-state">
        <Message severity="info" :closable="false">Dataset-Details werden geladen ...</Message>
        <ProgressBar mode="indeterminate" class="loading-progress" />
      </div>

      <div v-else-if="selectedDataset" class="dataset-workspace">
          <Fieldset legend="Dataset Metadata" toggleable collapsed>
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
          </Fieldset>

          <Fieldset v-if="selectedDataset.files.length > 0" legend="File Metadata" toggleable collapsed>
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
                label="Set metadata"
                icon="pi pi-tags"
                :loading="savingBulkMetadata"
                :disabled="selectedFileIds.length === 0 || savingBulkMetadata"
                @click="emit('update-selected-metadata')"
              />
            </div>
          </Fieldset>

          <Toolbar class="section-toolbar">
            <template #start>
              <div class="toolbar-title">
                <i class="pi pi-upload"></i>
                <span>Upload</span>
              </div>
            </template>

            <template #end>
              <input
                id="dataset-file-upload"
                class="hidden-file-input"
                type="file"
                multiple
                @change="emit('handle-file-upload', $event)"
              />

              <Button
                label="Upload files"
                icon="pi pi-upload"
                size="small"
                :loading="uploadingFiles"
                :disabled="uploadingFiles"
                @click="emit('open-file-picker')"
              />
            </template>
          </Toolbar>

          <div v-if="uploadingFiles" class="upload-progress">
            <div class="upload-progress-text">{{ uploadProgressText }}</div>
            <ProgressBar :value="uploadProgressPercent" />
          </div>

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
                  label="Apply detected metadata"
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
                <Tag
                  v-if="suggestion.measurement_date"
                  :value="`Date: ${suggestion.measurement_date}`"
                  severity="secondary"
                  rounded
                />
                <Tag
                  v-if="suggestion.excitation_power != null"
                  :value="`Power: ${suggestion.excitation_power} µW`"
                  severity="secondary"
                  rounded
                />
              </div>
            </div>
          </Message>

          <Toolbar v-if="selectedDataset.files.length > 0" class="bulk-toolbar">
            <template #start>
              <div class="bulk-toolbar-row">
                <label class="select-all-row">
                  <Checkbox
                    binary
                    :model-value="selectedFileIds.length === selectedDataset.files.length"
                    @update:model-value="emit('toggle-select-all-files')"
                  />
                  <span>Select all</span>
                </label>
                <Tag :value="`${selectedFileIds.length} selected`" severity="secondary" rounded />
                <div class="bulk-toolbar-actions">
                  <Select
                    :model-value="moveTargetDatasetId"
                    :options="moveTargetDatasetOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Target"
                    class="move-select"
                    @update:model-value="emit('update:moveTargetDatasetId', $event)"
                  />

                  <Button
                    icon="pi pi-arrow-right"
                    aria-label="Move selected files"
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
                    aria-label="Copy selected files"
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
                    aria-label="Delete selected files"
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
            </template>
          </Toolbar>

          <div v-if="selectedDataset.files.length > 0" class="file-list">
            <article
              v-for="file in selectedDataset.files"
              :key="file.id"
              class="file-row"
              :class="{ 'file-row--selected': isFileSelected(selectedFileIds, file.id) }"
              :title="file.object_key"
              @click="emit('open-file-detail', file)"
            >
              <div class="file-row-meta">
                <div class="file-row-titlebar">
                  <label class="file-checkbox-row">
                    <Checkbox
                      binary
                      :model-value="isFileSelected(selectedFileIds, file.id)"
                      @click.stop
                      @update:model-value="emit('toggle-file-selection', file.id)"
                    />
                    <span class="file-name">{{ file.filename }}</span>
                  </label>

                  <div class="file-row-actions">
                    <Button
                      icon="pi pi-download"
                      aria-label="Download file"
                      title="Download"
                      size="small"
                      severity="secondary"
                      variant="outlined"
                      rounded
                      @click.stop="emit('download-file', file.id)"
                    />
                    <Button
                      icon="pi pi-trash"
                      aria-label="Delete file"
                      title="Delete"
                      size="small"
                      severity="danger"
                      variant="outlined"
                      rounded
                      @click.stop="emit('delete-file', file.id)"
                    />
                  </div>
                </div>

                <div class="file-row-summary">
                  <div class="file-metadata-strip">
                    <span
                      v-for="item in fileMetadataItems(file)"
                      :key="`${file.id}-${item.icon}-${item.label}`"
                      class="metadata-chip"
                    >
                      <i :class="item.icon"></i>
                      {{ item.label }}
                    </span>
                    <span
                      v-if="fileMetadataItems(file).length === 0"
                      class="metadata-chip metadata-chip--empty"
                    >
                      <i class="pi pi-info-circle"></i>
                      No metadata
                    </span>
                  </div>

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
              </div>

              <div class="file-row-previews">
                <div class="preview-panel preview-panel--trace">
                  <div class="preview-label">Time Trace</div>
                  <TracePreview
                    v-if="file.tracePreview"
                    :preview="file.tracePreview.preview_data"
                    variant="thumb"
                  />
                  <div v-else class="empty-preview">
                    <i class="pi pi-chart-line"></i>
                    <span>No trace preview</span>
                  </div>
                </div>

                <div class="preview-panel preview-panel--acf">
                  <div class="preview-label">ACF</div>
                  <TracePreview
                    v-if="file.acfPreview"
                    :preview="file.acfPreview.preview_data"
                    variant="thumb"
                    x-scale="logarithmic"
                    :y-min="1"
                  />
                  <div v-else class="empty-preview">
                    <i class="pi pi-wave-pulse"></i>
                    <span>No ACF preview</span>
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
.form-actions,
.select-all-row,
.bulk-actions,
.bulk-toolbar-row,
.file-checkbox-row,
.file-row-titlebar,
.upload-detection-header,
.upload-detection-item,
.toolbar-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.upload-detection-header {
  justify-content: space-between;
  flex-wrap: wrap;
}

.file-row-titlebar {
  justify-content: space-between;
  flex-wrap: wrap;
}

.file-row-summary {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: space-between;
}

.select-all-row {
  flex: 0 0 auto;
  white-space: nowrap;
}

.bulk-toolbar-row .p-tag,
.bulk-toolbar-row .p-button {
  flex: 0 0 auto;
}

.panel-content,
.dataset-workspace,
.loading-state,
.upload-progress,
.upload-detection-list,
.file-list,
.file-row-meta {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.loading-progress {
  height: 0.35rem;
}

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
  gap: 0.4rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
}

.field--wide {
  grid-column: 1 / -1;
}

.form-actions,
.bulk-actions,
.file-row-actions,
.upload-detection-actions,
.file-tags-inline {
  flex-wrap: wrap;
}

.section-toolbar,
.bulk-toolbar {
  border-radius: 8px;
}

.bulk-toolbar {
  margin-top: 0.25rem;
}

.hidden-file-input {
  display: none;
}

.upload-progress-text,
.file-meta,
.metadata-chip {
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
  word-break: break-word;
}

.metadata-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
}

.file-metadata-strip {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.metadata-chip {
  padding: 0.2rem 0.45rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: 8px;
  background: color-mix(in srgb, var(--p-content-background) 92%, var(--p-text-color) 8%);
  line-height: 1.2;
}

.metadata-chip--empty {
  opacity: 0.7;
}

.upload-detection-actions,
.file-tags-inline {
  display: flex;
  gap: 0.5rem;
}

.upload-detection-item {
  justify-content: flex-start;
  flex-wrap: wrap;
}

.upload-detection-filename,
.file-name {
  font-weight: 600;
  word-break: break-word;
}

.bulk-actions {
  justify-content: flex-end;
}

.bulk-toolbar-row {
  flex-wrap: nowrap;
  width: 100%;
  overflow: visible;
}

.bulk-toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
  flex: 0 1 auto;
  min-width: 0;
}

.move-select {
  width: 180px;
  max-width: 180px;
  flex: 0 1 180px;
  min-width: 140px;
}

.file-row {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  padding: 1rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: 8px;
  background: var(--p-content-background);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.file-row:hover {
  border-color: var(--p-primary-color);
  box-shadow: var(--p-card-shadow);
}

.file-row--selected {
  border-color: var(--p-primary-color);
  background: color-mix(in srgb, var(--p-content-background) 92%, var(--p-primary-color) 8%);
  box-shadow: inset 4px 0 0 var(--p-primary-color);
}

.file-row-previews {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(180px, 240px);
  gap: 1rem;
  min-width: 0;
}

.preview-panel {
  min-width: 0;
  padding: 0.25rem 0;
  border: none;
  background: transparent;
  display: flex;
  flex-direction: column;
}

.preview-panel--trace {
  min-height: 220px;
}

.preview-panel--acf {
  align-self: stretch;
  min-height: 220px;
  overflow: hidden;
}

.preview-label {
  margin-bottom: 0.5rem;
  color: var(--p-text-muted-color);
  font-size: 0.85rem;
  font-weight: 700;
}

.empty-preview {
  min-height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--p-text-muted-color);
  border: 1px dashed var(--p-content-border-color);
  border-radius: 8px;
  font-size: 0.85rem;
}

.empty-preview i {
  font-size: 1.25rem;
}

.file-row-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

:deep(.section-toolbar .p-toolbar-end),
:deep(.bulk-toolbar .p-toolbar-start),
:deep(.bulk-toolbar .p-toolbar-end) {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

:deep(.bulk-toolbar .p-toolbar-start) {
  width: 100%;
  flex-wrap: nowrap;
  overflow: visible;
}

:deep(.section-toolbar),
:deep(.bulk-toolbar) {
  padding: 0.55rem 0.75rem;
}

:deep(.bulk-toolbar) {
  min-height: 2.75rem;
  padding: 0.35rem 0.75rem;
}

:deep(.bulk-toolbar .p-toolbar-start),
:deep(.bulk-toolbar .p-toolbar-end) {
  gap: 0.5rem;
}

:deep(.bulk-toolbar .p-button) {
  width: 2rem;
  height: 2rem;
  padding: 0;
}

:deep(.bulk-toolbar .p-select) {
  min-height: 2rem;
  max-width: 180px;
  min-width: 140px;
}

:deep(.bulk-toolbar .p-select-label) {
  padding-block: 0.2rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.bulk-toolbar .p-tag) {
  padding-block: 0.15rem;
}

:deep(.p-fieldset) {
  border-radius: 8px;
}

:deep(.p-inputtext),
:deep(.p-textarea),
:deep(.p-inputnumber),
:deep(.p-inputnumber-input),
:deep(.p-select) {
  width: 100%;
}

:deep(.preview-panel--trace .trace-preview-wrapper--thumb) {
  height: 180px;
}

:deep(.preview-panel--acf .trace-preview-wrapper--thumb) {
  height: 180px;
}

@media (max-width: 1200px) {
  .file-row-actions {
    justify-content: flex-end;
  }
}

@media (max-width: 900px) {
  .bulk-toolbar-row {
    flex-wrap: wrap;
  }

  .bulk-toolbar-actions {
    margin-left: 0;
    flex-wrap: wrap;
  }

  :deep(.bulk-toolbar .p-toolbar-start) {
    flex-wrap: wrap;
  }
}

@media (max-width: 760px) {
  .file-row-previews {
    grid-template-columns: 1fr;
  }

  .preview-panel--acf {
    max-height: none;
  }
}
</style>
