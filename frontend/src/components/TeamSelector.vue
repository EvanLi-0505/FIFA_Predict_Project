<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

// Custom combobox, NOT a native <input list>/<datalist> pair. Datalist
// popups are rendered by the OS/browser as a native control that web
// content cannot restyle or attach scroll handling to — on the packaged
// Windows desktop build, users found the popup did not respond to mouse
// wheel scrolling at all (a known Chromium/Electron limitation with
// <datalist>, not something fixable with CSS). This component renders its
// own dropdown as a plain scrollable <ul>, so mouse wheel, trackpad, and
// touch scrolling all work exactly like any other scrollable element.

const model = defineModel({ type: String, default: '' })

const props = defineProps({
  label: { type: String, required: true },
  teams: { type: Array, default: () => [] },
  listId: { type: String, required: true },
  placeholder: { type: String, default: 'Type or pick a team' },
})

const query = ref(model.value)
const isOpen = ref(false)
const highlightedIndex = ref(-1)
const rootEl = ref(null)
const listEl = ref(null)

watch(model, (value) => {
  if (value !== query.value) query.value = value
})

const filteredTeams = computed(() => {
  const needle = query.value.trim().toLowerCase()
  if (!needle) return props.teams
  return props.teams.filter((team) => team.toLowerCase().includes(needle))
})

function open() {
  isOpen.value = true
  highlightedIndex.value = filteredTeams.value.findIndex((t) => t === model.value)
}

function close() {
  isOpen.value = false
  highlightedIndex.value = -1
}

function handleInput(event) {
  query.value = event.target.value
  model.value = event.target.value
  isOpen.value = true
  highlightedIndex.value = 0
}

function selectTeam(team) {
  model.value = team
  query.value = team
  close()
}

function moveHighlight(delta) {
  if (!isOpen.value) {
    open()
    return
  }
  const count = filteredTeams.value.length
  if (count === 0) return
  const next = highlightedIndex.value + delta
  highlightedIndex.value = ((next % count) + count) % count
  nextTick(() => {
    listEl.value?.children[highlightedIndex.value]?.scrollIntoView({ block: 'nearest' })
  })
}

function confirmHighlighted() {
  if (isOpen.value && highlightedIndex.value >= 0) {
    selectTeam(filteredTeams.value[highlightedIndex.value])
  } else {
    close()
  }
}

function handleClickOutside(event) {
  if (rootEl.value && !rootEl.value.contains(event.target)) close()
}

document.addEventListener('mousedown', handleClickOutside)
onBeforeUnmount(() => document.removeEventListener('mousedown', handleClickOutside))
</script>

<template>
  <div ref="rootEl" class="combobox field">
    <label v-if="label" :for="listId">{{ label }}</label>
    <input
      :id="listId"
      type="text"
      :value="query"
      :placeholder="placeholder"
      autocomplete="off"
      role="combobox"
      aria-haspopup="listbox"
      :aria-expanded="isOpen"
      @input="handleInput"
      @focus="open"
      @keydown.down.prevent="moveHighlight(1)"
      @keydown.up.prevent="moveHighlight(-1)"
      @keydown.enter.prevent="confirmHighlighted"
      @keydown.esc="close"
    />
    <ul v-if="isOpen && filteredTeams.length" ref="listEl" class="dropdown" role="listbox">
      <li
        v-for="(team, index) in filteredTeams"
        :key="team"
        role="option"
        :class="{ highlighted: index === highlightedIndex, selected: team === model }"
        @mousedown.prevent="selectTeam(team)"
        @mouseenter="highlightedIndex = index"
      >
        {{ team }}
      </li>
    </ul>
    <p v-else-if="isOpen && query" class="no-matches muted">No matching team — you can still use this as free text.</p>
  </div>
</template>

<style scoped>
.combobox {
  position: relative;
}

.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 20;
  margin: 4px 0 0;
  padding: 4px;
  list-style: none;
  max-height: 240px;
  overflow-y: auto;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
}

.dropdown li {
  padding: 7px 10px;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
}

.dropdown li.highlighted {
  background: var(--color-primary);
  color: white;
}

.dropdown li.selected:not(.highlighted) {
  color: var(--color-primary);
  font-weight: 600;
}

.no-matches {
  position: absolute;
  top: 100%;
  left: 0;
  margin: 4px 0 0;
  font-size: 0.8rem;
}
</style>
