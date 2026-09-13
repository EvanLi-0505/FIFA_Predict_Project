import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import PredictionView from '../views/PredictionView.vue'
import DatasetView from '../views/DatasetView.vue'
import ModelView from '../views/ModelView.vue'
import HistoryView from '../views/HistoryView.vue'
import DashboardView from '../views/DashboardView.vue'
import TeamExplorerView from '../views/TeamExplorerView.vue'
import SettingsView from '../views/SettingsView.vue'

// Both the Web edition and the Desktop edition (pywebview pointed at
// http://127.0.0.1:PORT/, served by the same FastAPI app — see
// desktop_app/main.py) load this over plain HTTP, same-origin as the API,
// so there is no `file://` base-path concern and both can use normal
// HTML5 history-mode routing. (An earlier Electron-based desktop build
// loaded the frontend via `file://` and needed hash-based routing to
// work around that; it doesn't apply anymore.)
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/predict', name: 'predict', component: PredictionView },
    { path: '/datasets', name: 'datasets', component: DatasetView },
    { path: '/models', name: 'models', component: ModelView },
    { path: '/history', name: 'history', component: HistoryView },
    { path: '/dashboard', name: 'dashboard', component: DashboardView },
    { path: '/teams', name: 'teams', component: TeamExplorerView },
    { path: '/settings', name: 'settings', component: SettingsView },
  ],
})

export default router
