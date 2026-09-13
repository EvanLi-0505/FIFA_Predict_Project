<script setup>
import ModelManager from '../components/ModelManager.vue'
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>Model Management</h1>
      <p class="muted">
        Activating a model changes what live predictions use. Activating a dataset
        elsewhere does not — a model always predicts using the dataset it was
        actually trained on, so results stay reproducible.
      </p>
    </div>
    <ModelManager />
  </div>
</template>
