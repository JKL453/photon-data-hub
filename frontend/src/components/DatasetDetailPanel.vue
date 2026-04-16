<script setup>
import Card from 'primevue/card'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
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
</script>

<template>
  <Card class="panel-card">
    <template #title>Dataset Details</template>
    <template #content>
      <div class="panel-content">
        <p v-if="loadingDatasetDetail">Dataset-Details werden geladen ...</p>

        <div v-else-if="selectedDataset">
          <div class="edit-dataset-form">
            <InputText
              :model-value="editDatasetName"
              class="text-input"
              placeholder="Dataset name"
              @update:model-value="emit('update:editDatasetName', $event)"
            />

            <Textarea
              :model-value="editDatasetDescription"
              class="text-input textarea-input"
              placeholder="Description"
              @update:model-value="emit('update:editDatasetDescription', $event)"
            />
            <Textarea
              :model-value="editDatasetNotes"
              class="text-input textarea-input"
              placeholder="Dataset notes"
              @update:model-value="emit('update:editDatasetNotes', $event)"
            />

            <Button
              class="primary-button"
              :label="savingDataset ? 'Saving...' : 'Save changes'"
              :loading="savingDataset"
              :disabled="savingDataset"
              @click="emit('update-dataset')"
            />
          </div>

          <Button
            class="danger-button small-button"
            label="Delete Dataset"
            @click="emit('delete-dataset', selectedDataset.id)"
          />

          <h4>Files</h4>

          <div class="upload-section">
            <input
              id="dataset-file-upload"
              class="hidden-file-input"
              type="file"
              multiple
              @change="$emit('handle-file-upload', $event)"
            />

            <Button
              class="primary-button small-button"
              :label="uploadingFiles ? 'Uploading...' : 'Upload file(s)'"
              :loading="uploadingFiles"
              :disabled="uploadingFiles"
              @click="emit('open-file-picker')"
            />
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

          <div v-if="uploadMetadataSuggestions.length > 0" class="upload-detection-panel">
            <div class="upload-detection-header">
              <strong>Detected metadata for uploaded files</strong>
              <div class="upload-detection-actions">
                <Button
                  class="secondary-button small-button"
                  :label="applyingUploadMetadata ? 'Applying...' : 'Apply detected metadata'"
                  :loading="applyingUploadMetadata"
                  :disabled="applyingUploadMetadata"
                  @click="emit('apply-upload-metadata-suggestions')"
                />
                <Button
                  class="secondary-button small-button"
                  label="Dismiss"
                  :disabled="applyingUploadMetadata"
                  @click="emit('dismiss-upload-metadata-suggestions')"
                />
              </div>
            </div>

            <ul class="upload-detection-list">
              <li
                v-for="suggestion in uploadMetadataSuggestions"
                :key="suggestion.fileId"
                class="upload-detection-item"
              >
                <div class="upload-detection-filename">{{ suggestion.filename }}</div>
                <div class="upload-detection-meta">
                  <span v-if="suggestion.measurement_date">
                    Date: {{ suggestion.measurement_date }}
                  </span>
                  <span v-if="suggestion.excitation_power != null">
                    Power: {{ suggestion.excitation_power }} µW
                  </span>
                </div>
              </li>
            </ul>
          </div>

          <div v-if="selectedDataset.files.length > 0" class="file-actions-bar">
            <label class="select-all-row">
              <input
                type="checkbox"
                :checked="selectedFileIds.length === selectedDataset.files.length"
                @change="emit('toggle-select-all-files')"
              />
              <span>Select all</span>
            </label>

            <div class="bulk-actions-panel">
              <div class="bulk-actions-group">
                <Select
                  :model-value="moveTargetDatasetId"
                  :options="moveTargetDatasetOptions"
                  optionLabel="label"
                  optionValue="value"
                  placeholder="Move to dataset..."
                  class="text-input move-select"
                  @update:model-value="emit('update:moveTargetDatasetId', $event)"
                />

                <Button
                  class="secondary-button small-button"
                  :label="movingSelectedFiles ? 'Moving...' : 'Move selected'"
                  :loading="movingSelectedFiles"
                  :disabled="selectedFileIds.length === 0 || !moveTargetDatasetId || movingSelectedFiles"
                  @click="emit('move-selected-files')"
                />

                <Button
                  class="secondary-button small-button"
                  label="Copy selected"
                  :disabled="selectedFileIds.length === 0 || !moveTargetDatasetId"
                  @click="emit('copy-selected-files')"
                />

                <Button
                  class="danger-button small-button"
                  :label="deletingSelectedFiles ? 'Deleting...' : 'Delete selected'"
                  :loading="deletingSelectedFiles"
                  :disabled="selectedFileIds.length === 0 || deletingSelectedFiles"
                  @click="emit('delete-selected-files')"
                />
              </div>

              <div class="bulk-metadata-panel">
                <input
                  :value="bulkMeasurementDateDraft"
                  type="datetime-local"
                  class="text-input"
                  placeholder="Measurement date"
                  @input="emit('update:bulkMeasurementDateDraft', $event.target.value)"
                />

                <input
                  :value="bulkExcitationPowerDraft"
                  type="number"
                  step="0.1"
                  min="0"
                  class="text-input"
                  placeholder="Power (µW)"
                  @input="emit('update:bulkExcitationPowerDraft', $event.target.value)"
                />

                <input
                  :value="bulkObjectiveDraft"
                  type="text"
                  class="text-input"
                  placeholder="Objective"
                  @input="emit('update:bulkObjectiveDraft', $event.target.value)"
                />

                <Button
                  class="secondary-button small-button"
                  :label="savingBulkMetadata ? 'Saving...' : 'Set metadata'"
                  :loading="savingBulkMetadata"
                  :disabled="selectedFileIds.length === 0 || savingBulkMetadata"
                  @click="emit('update-selected-metadata')"
                />
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
              @click="emit('open-file-detail', file)"
            >
              <div class="file-top-row">
                <label class="file-checkbox-row">
                  <input
                    type="checkbox"
                    :checked="isFileSelected(selectedFileIds, file.id)"
                    @click.stop
                    @change="emit('toggle-file-selection', file.id)"
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
                <Button
                  class="download-button small-button"
                  label="Download"
                  @click.stop="emit('download-file', file.id)"
                />
                <Button
                  class="danger-button small-button"
                  label="Delete"
                  @click.stop="emit('delete-file', file.id)"
                />
              </div>
            </li>
          </ul>

          <p v-if="selectedDataset.files.length === 0" class="empty-state">
            This dataset contains no files yet.
          </p>
        </div>

        <p v-else class="empty-state">Select a dataset to view its files.</p>
      </div>
    </template>
  </Card>
</template>