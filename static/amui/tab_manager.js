/**
 * TabManager - Gestión de tabs para múltiples apps abiertas
 * Amachine ERP
 *
 * OPTIMIZACIÓN DE RENDIMIENTO:
 * - Tabs inactivas se "pausan" (HTML guardado en memoria, DOM limpiado)
 * - Solo la tab activa tiene contenido renderizado
 * - Máximo 8 tabs abiertas
 * - Auto-cierre de tabs antiguas
 */

class TabManager {
    constructor(options = {}) {
        this.maxTabs = options.maxTabs || 8;
        this.tabs = []; // [{id, name, icon, url, content, active, loaded, paused, cachedHTML}]
        this.tabsContainer = options.tabsContainer || document.getElementById('appTabs');
        this.contentContainer = options.contentContainer || document.getElementById('tabContent');
        this.homeTabId = options.homeTabId || 'launcher-home';
        this.onTabChange = options.onTabChange || null;
        this.dtmplUrl = options.dtmplUrl || '/io/dtmpl/';

        // Restaurar tabs de sessionStorage
        this.restoreTabs();

        // Bind de eventos
        this.bindEvents();
    }

    /**
     * Abre una nueva tab o activa una existente
     */
    openTab(app) {
        // Si ya existe, solo activar
        const existing = this.tabs.find(t => t.id === app.app_name);
        if (existing) {
            this.switchTab(app.app_name);
            return;
        }

        // Pausar la tab activa actual antes de cambiar
        const currentActive = this.tabs.find(t => t.active);
        if (currentActive && currentActive.id !== this.homeTabId) {
            this.pauseTab(currentActive.id);
        }

        // Desactivar todas las tabs
        this.tabs.forEach(t => t.active = false);

        // Si alcanzó el máximo, cerrar la más antigua (excepto home)
        if (this.tabs.length >= this.maxTabs) {
            const oldestTab = this.tabs.find(t => t.id !== this.homeTabId);
            if (oldestTab) {
                this.closeTab(oldestTab.id, false);
            }
        }

        // Crear nueva tab
        const tab = {
            id: app.app_name,
            name: app.friendly_name,
            icon: app.icon || 'mdi mdi-application',
            url: app.url,
            active: true,
            loaded: false,
            paused: false,
            cachedHTML: null
        };

        this.tabs.push(tab);
        this.renderTabs();
        this.loadTabContent(tab);
        this.saveTabs();
    }

    /**
     * Cierra una tab
     */
    closeTab(tabId, render = true) {
        const index = this.tabs.findIndex(t => t.id === tabId);
        if (index === -1) return;

        // No permitir cerrar home
        if (tabId === this.homeTabId) return;

        const wasActive = this.tabs[index].active;

        // Remover contenido del DOM
        const pane = document.getElementById(`tab-pane-${tabId}`);
        if (pane) pane.remove();

        // Limpiar cache
        this.tabs[index].cachedHTML = null;

        this.tabs.splice(index, 1);

        // Si era activa, activar home o la última
        if (wasActive) {
            if (this.tabs.length > 0) {
                const homeTab = this.tabs.find(t => t.id === this.homeTabId);
                if (homeTab) {
                    homeTab.active = true;
                } else {
                    this.tabs[this.tabs.length - 1].active = true;
                }
            }
        }

        if (render) {
            this.renderTabs();
            this.showActiveContent();
        }

        this.saveTabs();
    }

    /**
     * Cambia a una tab específica
     */
    switchTab(tabId) {
        const tab = this.tabs.find(t => t.id === tabId);
        if (!tab) return;

        // Pausar la tab activa actual
        const currentActive = this.tabs.find(t => t.active);
        if (currentActive && currentActive.id !== tabId && currentActive.id !== this.homeTabId) {
            this.pauseTab(currentActive.id);
        }

        // Activar la nueva tab
        this.tabs.forEach(t => t.active = (t.id === tabId));

        // Si la tab estaba pausada, restaurarla
        if (tab.paused && tab.cachedHTML) {
            this.resumeTab(tabId);
        }

        this.renderTabs();
        this.showActiveContent();

        // Callback opcional
        if (this.onTabChange) {
            this.onTabChange(tab);
        }

        this.saveTabs();
    }

    /**
     * OPTIMIZACIÓN: Pausa una tab (guarda HTML en memoria, limpia DOM)
     * Esto detiene todos los scripts, intervals, event listeners de esa tab
     */
    pauseTab(tabId) {
        const tab = this.tabs.find(t => t.id === tabId);
        if (!tab || tab.id === this.homeTabId || tab.paused) return;

        const pane = document.getElementById(`tab-pane-${tabId}`);
        if (!pane) return;

        // Guardar el HTML actual en memoria
        tab.cachedHTML = pane.innerHTML;
        tab.paused = true;

        // Limpiar el DOM (esto mata todos los scripts/intervals)
        pane.innerHTML = `
            <div class="tab-paused" style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; color: #718096;">
                <i class="mdi mdi-pause-circle-outline" style="font-size: 48px; opacity: 0.5;"></i>
                <p style="margin-top: 16px;">Tab pausada para optimizar rendimiento</p>
            </div>
        `;

        console.log(`[TabManager] Tab "${tab.name}" pausada`);
    }

    /**
     * OPTIMIZACIÓN: Restaura una tab pausada
     */
    resumeTab(tabId) {
        const tab = this.tabs.find(t => t.id === tabId);
        if (!tab || !tab.paused || !tab.cachedHTML) return;

        const pane = document.getElementById(`tab-pane-${tabId}`);
        if (!pane) return;

        // Restaurar el HTML
        pane.innerHTML = tab.cachedHTML;

        // Re-ejecutar scripts
        this.executeScripts(pane);

        tab.paused = false;
        // Mantener cachedHTML por si se vuelve a pausar

        console.log(`[TabManager] Tab "${tab.name}" restaurada`);
    }

    /**
     * Renderiza las tabs en el contenedor
     */
    renderTabs() {
        if (!this.tabsContainer) return;

        this.tabsContainer.innerHTML = '';

        // Tab de Home siempre primero
        const homeTab = this.tabs.find(t => t.id === this.homeTabId);
        if (homeTab) {
            this.tabsContainer.appendChild(this.createTabElement(homeTab, false));
        }

        // Resto de tabs
        this.tabs.filter(t => t.id !== this.homeTabId).forEach(tab => {
            this.tabsContainer.appendChild(this.createTabElement(tab, true));
        });
    }

    /**
     * Crea el elemento HTML de una tab
     */
    createTabElement(tab, closeable = true) {
        const tabEl = document.createElement('div');
        tabEl.className = `app-tab ${tab.active ? 'active' : ''}`;
        tabEl.dataset.tabId = tab.id;

        const isHome = tab.id === this.homeTabId;

        tabEl.innerHTML = `
            <span class="tab-icon"><i class="${isHome ? 'mdi mdi-home' : tab.icon}"></i></span>
            <span class="tab-name">${isHome ? 'Inicio' : tab.name}</span>
            ${closeable ? `<button class="tab-close" data-tab-id="${tab.id}"><i class="mdi mdi-close"></i></button>` : ''}
        `;

        // Click para activar
        tabEl.addEventListener('click', (e) => {
            if (!e.target.closest('.tab-close')) {
                this.switchTab(tab.id);
            }
        });

        // Click en cerrar
        const closeBtn = tabEl.querySelector('.tab-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.closeTab(tab.id);
            });
        }

        return tabEl;
    }

    /**
     * Muestra el contenido de la tab activa
     */
    showActiveContent() {
        if (!this.contentContainer) return;

        const activeTab = this.tabs.find(t => t.active);
        if (!activeTab) return;

        // Ocultar todos los panes
        const panes = this.contentContainer.querySelectorAll('.tab-pane');
        panes.forEach(p => p.classList.remove('active'));

        // Mostrar pane activo
        const activePane = document.getElementById(`tab-pane-${activeTab.id}`);
        if (activePane) {
            activePane.classList.add('active');
        }
    }

    /**
     * Carga el contenido de una tab desde el servidor
     */
    async loadTabContent(tab) {
        if (!this.contentContainer) return;

        // Crear pane si no existe
        let pane = document.getElementById(`tab-pane-${tab.id}`);
        if (!pane) {
            pane = document.createElement('div');
            pane.id = `tab-pane-${tab.id}`;
            pane.className = 'tab-pane';
            this.contentContainer.appendChild(pane);
        }

        // Mostrar loading
        pane.innerHTML = `
            <div class="tab-loading">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p>Cargando ${tab.name}...</p>
            </div>
        `;
        pane.classList.add('active');

        try {
            // Cargar contenido via dtmpl (GET con parámetros)
            const params = new URLSearchParams();
            params.append('tmpl', tab.url);

            const response = await axios.get(`${this.dtmplUrl}?${params.toString()}`);

            // Insertar contenido
            pane.innerHTML = response.data;

            // Ejecutar scripts del contenido
            this.executeScripts(pane);

            tab.loaded = true;
            tab.paused = false;
            tab.cachedHTML = response.data; // Guardar para restauración futura

        } catch (error) {
            console.error('Error cargando tab:', error);
            pane.innerHTML = `
                <div class="tab-error">
                    <i class="mdi mdi-alert-circle text-danger" style="font-size: 48px;"></i>
                    <h4>Error al cargar</h4>
                    <p>${error.message || 'No se pudo cargar el contenido'}</p>
                    <button class="btn btn-primary" onclick="tabManager.reloadTab('${tab.id}')">
                        <i class="mdi mdi-refresh"></i> Reintentar
                    </button>
                </div>
            `;
        }
    }

    /**
     * Recarga el contenido de una tab
     */
    reloadTab(tabId) {
        const tab = this.tabs.find(t => t.id === tabId);
        if (tab) {
            tab.loaded = false;
            tab.paused = false;
            tab.cachedHTML = null;
            this.loadTabContent(tab);
        }
    }

    /**
     * Ejecuta los scripts del contenido cargado
     */
    executeScripts(container) {
        const scripts = container.querySelectorAll('script');
        scripts.forEach(oldScript => {
            const newScript = document.createElement('script');

            // Copiar atributos
            Array.from(oldScript.attributes).forEach(attr => {
                newScript.setAttribute(attr.name, attr.value);
            });

            // Copiar contenido
            newScript.textContent = oldScript.textContent;

            // Reemplazar
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });
    }

    /**
     * Guarda el estado de tabs en sessionStorage
     */
    saveTabs() {
        const tabsData = this.tabs.map(t => ({
            id: t.id,
            name: t.name,
            icon: t.icon,
            url: t.url,
            active: t.active
            // No guardamos cachedHTML ni paused (se regenera)
        }));
        sessionStorage.setItem('amachine_tabs', JSON.stringify(tabsData));
    }

    /**
     * Restaura tabs desde sessionStorage
     */
    restoreTabs() {
        try {
            const saved = sessionStorage.getItem('amachine_tabs');
            if (saved) {
                const tabsData = JSON.parse(saved);
                // Solo restaurar si hay datos válidos
                if (Array.isArray(tabsData) && tabsData.length > 0) {
                    this.tabs = tabsData.map(t => ({
                        ...t,
                        loaded: false,
                        paused: false,
                        cachedHTML: null
                    }));
                }
            }
        } catch (e) {
            console.warn('Error restaurando tabs:', e);
        }
    }

    /**
     * Inicializa la tab de home
     */
    initHomeTab() {
        // Verificar si ya existe home
        const homeExists = this.tabs.find(t => t.id === this.homeTabId);
        if (!homeExists) {
            this.tabs.unshift({
                id: this.homeTabId,
                name: 'Inicio',
                icon: 'mdi mdi-home',
                url: null,
                active: true,
                loaded: true,
                paused: false,
                cachedHTML: null
            });
        }
        this.renderTabs();
        this.showActiveContent();
    }

    /**
     * Obtiene la tab activa
     */
    getActiveTab() {
        return this.tabs.find(t => t.active);
    }

    /**
     * Cierra todas las tabs excepto home
     */
    closeAllTabs() {
        const tabsToClose = this.tabs.filter(t => t.id !== this.homeTabId).map(t => t.id);
        tabsToClose.forEach(id => this.closeTab(id, false));

        // Activar home
        const homeTab = this.tabs.find(t => t.id === this.homeTabId);
        if (homeTab) {
            homeTab.active = true;
        }

        this.renderTabs();
        this.showActiveContent();
        this.saveTabs();
    }

    /**
     * Obtiene estadísticas de rendimiento
     */
    getStats() {
        return {
            totalTabs: this.tabs.length,
            activeTabs: this.tabs.filter(t => !t.paused).length,
            pausedTabs: this.tabs.filter(t => t.paused).length,
            loadedTabs: this.tabs.filter(t => t.loaded).length,
            maxTabs: this.maxTabs
        };
    }

    /**
     * Bind de eventos globales
     */
    bindEvents() {
        // Ctrl+W para cerrar tab activa
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'w') {
                e.preventDefault();
                const activeTab = this.getActiveTab();
                if (activeTab && activeTab.id !== this.homeTabId) {
                    this.closeTab(activeTab.id);
                }
            }
        });
    }
}

// Exportar globalmente
window.TabManager = TabManager;
