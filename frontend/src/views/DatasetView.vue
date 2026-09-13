<script setup>
import DatasetManager from '../components/DatasetManager.vue'
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>Dataset Management</h1>
      <p class="muted">
        The built-in dataset is read-only and can never be edited, overwritten, or
        deleted. Uploading a CSV always creates a new version — it never touches an
        existing one.
      </p>
    </div>
    <DatasetManager />
  </div>
</template>
