<template>
  <div class="app-shell">
    <div
      v-if="sidebarOpen"
      class="sidebar-overlay"
      aria-hidden="true"
      @click="closeSidebar"
    ></div>

    <aside id="app-sidebar" class="sidebar" :class="{ open: sidebarOpen, collapsed: isCollapsed }">
      <div class="sidebar-brand">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 8l-9-5-9 5 9 5 9-5z" />
            <path d="M3 8v8l9 5 9-5V8" />
            <path d="M12 13v8" />
          </svg>
        </span>
        <div class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <nav class="sidebar-nav" :aria-label="t('nav.primaryNavigation')">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :title="isCollapsed ? item.label : null"
          :active-class="item.path === '/' ? '' : 'active'"
          exact-active-class="active"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path v-for="d in item.icon" :key="d" :d="d" />
          </svg>
          <!-- Visually hidden (not removed) when collapsed so the link keeps its accessible name. -->
          <span class="nav-label" :class="{ 'visually-hidden': isCollapsed }">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- Collapse toggle is desktop/tablet only; the <768px drawer always shows the full sidebar. -->
      <div v-if="!isMobile" class="sidebar-toggle-wrap">
        <button
          class="collapse-toggle"
          type="button"
          :aria-label="isCollapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
          :title="isCollapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
          aria-controls="app-sidebar"
          :aria-expanded="!isCollapsed"
          @click="toggleCollapsed"
        >
          <svg class="nav-icon collapse-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M15 6l-6 6 6 6" />
          </svg>
          <span class="collapse-label">{{ t('nav.collapse') }}</span>
        </button>
      </div>

      <div class="sidebar-footer">
        <LanguageSwitcher :collapsed="isCollapsed" />
        <ProfileMenu
          :collapsed="isCollapsed"
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="shell-main">
      <header class="topbar">
        <button
          class="menu-button"
          type="button"
          :aria-label="sidebarOpen ? t('nav.closeNavigation') : t('nav.openNavigation')"
          aria-controls="app-sidebar"
          :aria-expanded="sidebarOpen"
          @click="sidebarOpen = !sidebarOpen"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1 class="topbar-title">{{ pageTitle }}</h1>
      </header>

      <FilterBar />

      <main class="content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])
    const route = useRoute()
    const sidebarOpen = ref(false)

    const navItems = computed(() => [
      { path: '/', label: t('nav.overview'), icon: ['M3 3h8v8H3z', 'M13 3h8v5h-8z', 'M13 10h8v11h-8z', 'M3 13h8v8H3z'] },
      { path: '/inventory', label: t('nav.inventory'), icon: ['M21 8l-9-5-9 5 9 5 9-5z', 'M3 8v8l9 5 9-5V8', 'M12 13v8'] },
      { path: '/orders', label: t('nav.orders'), icon: ['M6 3h12v18l-3-2-3 2-3-2-3 2z', 'M9 8h6', 'M9 12h6'] },
      { path: '/spending', label: t('nav.finance'), icon: ['M3 7h18v12H3z', 'M3 11h18', 'M7 15h3'] },
      { path: '/demand', label: t('nav.demandForecast'), icon: ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'] },
      { path: '/reports', label: t('nav.reports'), icon: ['M6 3h9l4 4v14H6z', 'M14 3v5h5', 'M9 13h7', 'M9 17h5'] }
    ])

    // Top bar title reuses the nav labels so it stays translated.
    const pageTitle = computed(() => {
      const match = navItems.value.find(item => item.path === route.path)
      return match ? match.label : t('nav.companyName')
    })

    // ---- Collapsed (icons-only) sidebar ----
    const STORAGE_KEY = 'sidebar-collapsed'
    const readStored = () => {
      try {
        const v = localStorage.getItem(STORAGE_KEY)
        return v === 'collapsed' ? true : v === 'expanded' ? false : null
      } catch (e) {
        return null // storage blocked (private mode etc.)
      }
    }
    const storedCollapsed = ref(readStored()) // null = no stored preference

    const hasMatchMedia = typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    const mqDesktop = hasMatchMedia ? window.matchMedia('(min-width: 1024px)') : null
    const mqTablet = hasMatchMedia ? window.matchMedia('(min-width: 768px)') : null
    const isDesktop = ref(mqDesktop ? mqDesktop.matches : true)
    const isMobile = ref(mqTablet ? !mqTablet.matches : false)
    const onDesktopChange = (e) => { isDesktop.value = e.matches }
    const onTabletChange = (e) => { isMobile.value = !e.matches }

    // Below 768px the drawer always shows the full labelled sidebar.
    // Otherwise a stored choice wins; with no choice, 768-1023px defaults to the rail
    // and >=1024px defaults to expanded.
    const isCollapsed = computed(() => {
      if (isMobile.value) return false
      if (storedCollapsed.value !== null) return storedCollapsed.value
      return !isDesktop.value
    })

    const toggleCollapsed = () => {
      storedCollapsed.value = !isCollapsed.value
      try {
        localStorage.setItem(STORAGE_KEY, storedCollapsed.value ? 'collapsed' : 'expanded')
      } catch (e) {
        // Preference just won't persist.
      }
    }

    const closeSidebar = () => {
      sidebarOpen.value = false
    }

    // The drawer overlays the page on small screens, so navigating must dismiss it.
    watch(() => route.path, closeSidebar)

    // Growing past 768px turns the drawer into the in-flow rail, so drop its open state.
    watch(isMobile, (mobile) => { if (!mobile) closeSidebar() })

    const onKeydown = (event) => {
      if (event.key === 'Escape') closeSidebar()
    }

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(() => {
      loadTasks()
      window.addEventListener('keydown', onKeydown)
      if (mqDesktop) mqDesktop.addEventListener('change', onDesktopChange)
      if (mqTablet) mqTablet.addEventListener('change', onTabletChange)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('keydown', onKeydown)
      if (mqDesktop) mqDesktop.removeEventListener('change', onDesktopChange)
      if (mqTablet) mqTablet.removeEventListener('change', onTabletChange)
    })

    return {
      t,
      navItems,
      pageTitle,
      sidebarOpen,
      isCollapsed,
      isMobile,
      toggleCollapsed,
      closeSidebar,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ---------- Shell ---------- */
.app-shell {
  display: flex;
  min-height: 100vh;
}

.shell-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.sidebar {
  position: sticky;
  top: 0;
  flex-shrink: 0;
  width: var(--sidebar-width);
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-sidebar-bg);
  color: var(--color-sidebar-text);
  /* Above the sticky top bar and filter bar; overflow stays visible so footer dropdowns are not clipped. */
  z-index: 200;
  transition: width 0.2s ease;
}

.sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--topbar-height);
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--color-sidebar-border);
  flex-shrink: 0;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: var(--color-sidebar-text-active);
  flex-shrink: 0;
}

.brand-mark svg {
  width: 20px;
  height: 20px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-sidebar-text-active);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  font-size: var(--text-xs);
  color: var(--color-sidebar-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-3);
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 40px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-sidebar-text);
  font-size: var(--text-sm);
  font-weight: 500;
  text-decoration: none;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background: var(--color-sidebar-item-hover);
  color: var(--color-sidebar-text-active);
}

.nav-item.active {
  background: var(--color-sidebar-item-active);
  color: var(--color-sidebar-text-active);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: calc(-1 * var(--space-3));
  top: var(--space-2);
  bottom: var(--space-2);
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--color-primary);
}

.nav-item:focus-visible,
.collapse-toggle:focus-visible,
.menu-button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.sidebar-toggle-wrap {
  padding: 0 var(--space-3) var(--space-3);
  flex-shrink: 0;
}

.collapse-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  height: 40px;
  padding: 0 var(--space-3);
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-sidebar-text);
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.collapse-toggle:hover {
  background: var(--color-sidebar-item-hover);
  color: var(--color-sidebar-text-active);
}

.collapse-chevron {
  transition: transform 0.2s ease;
}

.sidebar.collapsed .collapse-chevron {
  transform: rotate(180deg);
}

/* Standard screen-reader-only utility: hidden visually, still in the accessibility tree. */
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}

/* Rail: icons centered, text hidden. */
.sidebar.collapsed .brand-text,
.sidebar.collapsed .collapse-label {
  display: none;
}

.sidebar.collapsed .sidebar-brand {
  justify-content: center;
  padding: 0;
}

.sidebar.collapsed .nav-item,
.sidebar.collapsed .collapse-toggle {
  justify-content: center;
  padding: 0;
}

.nav-label,
.collapse-label {
  white-space: nowrap;
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .collapse-chevron {
    transition: none;
  }
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
  border-top: 1px solid var(--color-sidebar-border);
  flex-shrink: 0;
}

.sidebar-overlay {
  display: none;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--topbar-height);
  padding: 0 var(--space-5);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.topbar-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.menu-button {
  display: none;
  align-items: center;
  justify-content: center;
  width: var(--control-height);
  height: var(--control-height);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
}

.menu-button:hover {
  background: var(--color-bg);
}

.menu-button svg {
  width: 20px;
  height: 20px;
}

.content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-5);
}

/* Below 768px the sidebar becomes an off-canvas drawer (768-1023px uses the icon rail). */
@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    box-shadow: var(--shadow-lg);
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.5);
    z-index: 150;
  }

  .menu-button {
    display: flex;
  }

}

@media (max-width: 1023px) {
  .topbar {
    padding: 0 var(--space-4);
  }

  .content {
    padding: var(--space-4);
  }
}

/* ---------- Global content classes (shared by all views) ---------- */
.page-header {
  margin-bottom: var(--space-5);
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-1);
  letter-spacing: -0.02em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--color-text);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.stat-card.warning .stat-value {
  color: var(--color-warning);
}

.stat-card.success .stat-value {
  color: var(--color-success);
}

.stat-card.danger .stat-value {
  color: var(--color-danger);
}

.stat-card.info .stat-value {
  color: var(--color-primary);
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--color-bg);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-3);
  font-weight: 600;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  height: 48px;
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-bg);
}

.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

/* Status color mapping unchanged from the previous design. */
.badge.success,
.badge.increasing {
  background: #d1fae5;
  color: #065f46;
}

.badge.warning,
.badge.medium {
  background: #fed7aa;
  color: #92400e;
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: #fecaca;
  color: #991b1b;
}

.badge.info,
.badge.low {
  background: #dbeafe;
  color: #1e40af;
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.loading {
  text-align: center;
  padding: var(--space-7);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-sm);
}
</style>
