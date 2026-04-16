<script setup>
import Card from 'primevue/card'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'

defineProps({
  datasets: {
    type: Array,
    required: true,
  },
  loadingDatasets: {
    type: Boolean,
    required: true,
  },
  errorMessage: {
    type: String,
    required: true,
  },
  newDatasetName: {
    type: String,
    required: true,
  },
  newDatasetDescription: {
    type: String,
    required: true,
  },
  creatingDataset: {
    type: Boolean,
    required: true,
  },
})

const emit = defineEmits([
  'update:newDatasetName',
  'update:newDatasetDescription',
  'create-dataset',
  'select-dataset',
])
</script>

<template>
  <Card class="panel-card">
    <template #title>Datasets</template>
    <template #content>
      <div class="panel-content">
        <p v-if="loadingDatasets">Loading datasets ...</p>
        <p v-if="errorMessage">{{ errorMessage }}</p>

        <div class="create-dataset-form">
          <InputText
            :model-value="newDatasetName"
            placeholder="Dataset name"
            class="text-input"
            @update:model-value="emit('update:newDatasetName', $event)"
          />

          <Textarea
            :model-value="newDatasetDescription"
            placeholder="Description"
            class="text-input textarea-input"
            @update:model-value="emit('update:newDatasetDescription', $event)"
          />

          <Button
            :label="creatingDataset ? 'Creating...' : 'Create Dataset'"
            :loading="creatingDataset"
            :disabled="creatingDataset"
            @click="emit('create-dataset')"
          />
        </div>

        <ul class="dataset-list">
          <li
            v-for="ds in datasets"
            :key="ds.id"
            class="dataset-item"
            @click="emit('select-dataset', ds.id)"
          >
            <div class="dataset-name">{{ ds.name }}</div>
            <div class="dataset-meta">
              {{ ds.file_count }} files
            </div>
          </li>
        </ul>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.panel-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.create-dataset-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.dataset-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.dataset-item {
  background: #fafbff;
  border: 1px solid #e8ebf3;
  border-radius: 14px;
  padding: 0.9rem 1rem;
  margin-bottom: 0.9rem;
  transition: all 0.15s ease;
  cursor: pointer;
}

.dataset-item:hover {
  background: #f1f4ff;
  border-color: #d9e1ff;
  transform: translateY(-1px);
}

.dataset-name {
  font-weight: 600;
  margin-bottom: 0.35rem;
  font-size: 1rem;
}

.dataset-meta {
  font-size: 0.9rem;
  color: #666;
}

.text-input {
  width: 100%;
  box-sizing: border-box;
}

.textarea-input {
  min-height: 90px;
  resize: vertical;
}
</style>