<script setup>
import { ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import DisclaimerGate from './components/DisclaimerGate.vue'

// Deliberately NOT persisted (no localStorage) — by request, the disclaimer
// must be re-read and re-accepted every time the app is opened, not just
// once per browser.
const disclaimerAccepted = ref(false)

function acceptDisclaimer() {
  disclaimerAccepted.value = true
}
</script>

<template>
  <DisclaimerGate v-if="!disclaimerAccepted" @accept="acceptDisclaimer" />

  <template v-else>
    <header class="app-nav">
      <div class="app-nav-inner">
        <RouterLink to="/" class="brand">FIFA Prediction</RouterLink>
        <nav>
          <RouterLink to="/">Home</RouterLink>
          <RouterLink to="/predict">Predict</RouterLink>
          <RouterLink to="/datasets">Datasets</RouterLink>
          <RouterLink to="/models">Models</RouterLink>
          <RouterLink to="/history">History</RouterLink>
          <RouterLink to="/dashboard">Dashboard</RouterLink>
          <RouterLink to="/teams">Teams</RouterLink>
          <RouterLink to="/settings">Settings</RouterLink>
        </nav>
      </div>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
  </template>
</template>

<style scoped>
.app-nav {
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  position: sticky;
  top: 0;
  z-index: 10;
}

.app-nav-inner {
  max-width: 960px;
  margin: 0 auto;
  padding: 14px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.brand {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--color-text);
  text-decoration: none;
}

nav {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

nav a {
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 0.92rem;
  font-weight: 500;
  padding: 4px 0;
  border-bottom: 2px solid transparent;
}

nav a:hover {
  color: var(--color-text);
}

nav a.router-link-exact-active {
  color: var(--color-text);
  border-bottom-color: var(--color-primary);
}

.app-main {
  flex: 1;
}
</style>
