// ===== VARIABILI GLOBALI =====
let isOnline = navigator.onLine;
let installPrompt = null;

// ===== INIZIALIZZAZIONE =====
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkOnlineStatus();
    setupPWA();
});

// ===== FUNZIONI PRINCIPALI =====
function initializeApp() {
    console.log('🚗 MasterWash App inizializzata');
    
    // Gestione orientamento mobile
    if (window.screen && window.screen.orientation) {
        window.screen.orientation.lock('portrait').catch(() => {
            // Silently fail if orientation lock is not supported
        });
    }
    
    // Prevenzione zoom accidentale su iOS
    document.addEventListener('gesturestart', function (e) {
        e.preventDefault();
    });
    
    // Auto-dismiss flash messages
    setTimeout(function() {
        const flashMessages = document.querySelectorAll('.flash');
        flashMessages.forEach(flash => {
            if (flash.style.display !== 'none') {
                flash.style.animation = 'slideOut 0.3s ease-in forwards';
                setTimeout(() => flash.remove(), 300);
            }
        });
    }, 5000);
}

function setupEventListeners() {
    // Menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', toggleMenu);
    }
    
    // Gestione tasti globali
    document.addEventListener('keydown', handleGlobalKeyPress);
    
    // Touch gestures per mobile
    setupTouchGestures();
    
    // Gestione form per prevenire doppi submit
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
    
    // Auto-focus su input visibili
    const visibleInputs = document.querySelectorAll('input[type="text"]:not([style*="display: none"]), input[type="tel"]:not([style*="display: none"])');
    if (visibleInputs.length > 0) {
        visibleInputs[0].focus();
    }
}

function setupTouchGestures() {
    let startX = 0;
    let startY = 0;
    
    document.addEventListener('touchstart', function(e) {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
    }, { passive: true });
    
    document.addEventListener('touchend', function(e) {
        const endX = e.changedTouches[0].clientX;
        const endY = e.changedTouches[0].clientY;
        
        const deltaX = endX - startX;
        const deltaY = endY - startY;
        
        // Swipe da sinistra per aprire menu
        if (deltaX > 50 && Math.abs(deltaY) < 100 && startX < 50) {
            toggleMenu();
        }
        
        // Swipe da destra per chiudere menu
        if (deltaX < -50 && Math.abs(deltaY) < 100 && startX > window.innerWidth - 50) {
            const navMenu = document.getElementById('navMenu');
            if (navMenu && navMenu.classList.contains('active')) {
                toggleMenu();
            }
        }
    }, { passive: true });
}

// ===== GESTIONE MENU =====
function toggleMenu() {
    const navMenu = document.getElementById('navMenu');
    if (navMenu) {
        navMenu.classList.toggle('active');
        
        // Feedback vibrazione
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        // Gestione focus trap quando menu aperto
        if (navMenu.classList.contains('active')) {
            trapFocus(navMenu);
        }
    }
}

function trapFocus(element) {
    const focusableElements = element.querySelectorAll(
        'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
    );
    const firstFocusableElement = focusableElements[0];
    const lastFocusableElement = focusableElements[focusableElements.length - 1];
    
    element.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                if (document.activeElement === firstFocusableElement) {
                    lastFocusableElement.focus();
                    e.preventDefault();
                }
            } else {
                if (document.activeElement === lastFocusableElement) {
                    firstFocusableElement.focus();
                    e.preventDefault();
                }
            }
        }
    });
}

// ===== GESTIONE TASTIERA =====
function handleGlobalKeyPress(e) {
    // ESC per chiudere menu/modal
    if (e.key === 'Escape') {
        const navMenu = document.getElementById('navMenu');
        if (navMenu && navMenu.classList.contains('active')) {
            toggleMenu();
            return;
        }
        
        // Chiudi eventuali modal o overlay
        const overlay = document.querySelector('.loading-overlay.active');
        if (overlay) {
            hideLoading();
            return;
        }
        
        // Pulisci campi di input attivi
        if (document.activeElement && document.activeElement.tagName === 'INPUT') {
            document.activeElement.value = '';
        }
    }
    
    // F5 per refresh (solo in development)
    if (e.key === 'F5' && window.location.hostname === 'localhost') {
        e.preventDefault();
        window.location.reload();
    }
    
    // Ctrl/Cmd + K per focus su ricerca
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="search"], input[placeholder*="cerca"], input[placeholder*="ricerca"]');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }
}

// ===== GESTIONE FORM =====
function handleFormSubmit(e) {
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
    
    if (submitBtn) {
        // Disabilita il pulsante per prevenire doppi submit
        submitBtn.disabled = true;
        
        // Mostra loading se form richiede tempo
        if (form.dataset.loading !== 'false') {
            showLoading('Elaborazione...');
        }
        
        // Riabilita il pulsante dopo timeout di sicurezza
        setTimeout(() => {
            submitBtn.disabled = false;
            hideLoading();
        }, 10000);
    }
    
    // Feedback vibrazione su submit
    if (navigator.vibrate) {
        navigator.vibrate(100);
    }
}

// ===== LOADING OVERLAY =====
function showLoading(text = 'Caricamento...') {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        const loadingText = overlay.querySelector('.loading-text');
        if (loadingText) {
            loadingText.textContent = text;
        }
        overlay.classList.add('active');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// ===== GESTIONE CONNETTIVITÀ =====
function checkOnlineStatus() {
    window.addEventListener('online', function() {
        isOnline = true;
        showNotification('Connessione ripristinata', 'success');
        console.log('🌐 Connessione online');
    });
    
    window.addEventListener('offline', function() {
        isOnline = false;
        showNotification('Connessione persa - Modalità offline', 'warning');
        console.log('📴 Connessione offline');
    });
}

// ===== NOTIFICHE =====
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `flash flash-${type}`;
    notification.innerHTML = `
        <span class="flash-icon">${getNotificationIcon(type)}</span>
        <span class="flash-message">${message}</span>
        <button class="flash-close" onclick="this.parentElement.remove()">✕</button>
    `;
    
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Auto-remove
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideOut 0.3s ease-in forwards';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
    }
    
    // Click to dismiss
    notification.addEventListener('click', () => notification.remove());
    
    return notification;
}

function getNotificationIcon(type) {
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    return icons[type] || 'ℹ️';
}

// ===== PWA SETUP =====
function setupPWA() {
    // Gestione install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        installPrompt = e;
        showInstallButton();
    });
    
    // Gestione install success
    window.addEventListener('appinstalled', () => {
        showNotification('App installata con successo!', 'success');
        hideInstallButton();
        installPrompt = null;
    });
    
    // Update disponibile
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            showNotification('Aggiornamento disponibile - Ricarica la pagina', 'info', 10000);
        });
    }
}

function showInstallButton() {
    // Crea o mostra pulsante di installazione
    let installBtn = document.getElementById('installBtn');
    if (!installBtn) {
        installBtn = document.createElement('button');
        installBtn.id = 'installBtn';
        installBtn.className = 'btn btn-primary install-btn';
        installBtn.innerHTML = '📱 Installa App';
        installBtn.addEventListener('click', installApp);
        
        // Aggiungi al header o footer
        const header = document.querySelector('.header-right');
        if (header) {
            header.appendChild(installBtn);
        }
    }
    installBtn.style.display = 'block';
}

function hideInstallButton() {
    const installBtn = document.getElementById('installBtn');
    if (installBtn) {
        installBtn.style.display = 'none';
    }
}

async function installApp() {
    if (!installPrompt) return;
    
    const result = await installPrompt.prompt();
    console.log('Install prompt result:', result);
    
    installPrompt = null;
    hideInstallButton();
}

// ===== UTILITY FUNCTIONS =====
function formatCurrency(amount) {
    return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount);
}

function formatDate(date, options = {}) {
    const defaultOptions = {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    };
    return new Intl.DateTimeFormat('it-IT', { ...defaultOptions, ...options }).format(new Date(date));
}

function formatTime(date) {
    return new Intl.DateTimeFormat('it-IT', {
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ===== API HELPERS =====
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    };
    
    // Aggiungi CSRF token se presente
    const csrfToken = document.querySelector('input[name="csrf_token"]');
    if (csrfToken && (options.method === 'POST' || options.method === 'PUT' || options.method === 'DELETE')) {
        defaultOptions.headers['X-CSRFToken'] = csrfToken.value;
    }
    
    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return await response.text();
        }
    } catch (error) {
        console.error('API Request failed:', error);
        if (!isOnline) {
            showNotification('Operazione non disponibile offline', 'warning');
        } else {
            showNotification('Errore di connessione', 'error');
        }
        throw error;
    }
}

// ===== FORM VALIDATION HELPERS =====
function validateRequired(input) {
    const value = input.value.trim();
    if (!value) {
        showFieldError(input, 'Questo campo è obbligatorio');
        return false;
    }
    clearFieldError(input);
    return true;
}

function validatePhone(input) {
    const phone = input.value.replace(/\s+/g, '').replace(/[\-\+]/g, '');
    const phoneRegex = /^(3\d{9}|0\d{8,10})$/;
    
    if (!phoneRegex.test(phone)) {
        showFieldError(input, 'Inserisci un numero di telefono valido');
        return false;
    }
    clearFieldError(input);
    return true;
}

function validateLicensePlate(input) {
    const plate = input.value.toUpperCase().replace(/\s+/g, '');
    const plateRegex = /^[A-Z]{2}\d{3}[A-Z]{1,2}$/;
    
    if (!plateRegex.test(plate)) {
        showFieldError(input, 'Inserisci una targa italiana valida (es. AB123CD)');
        return false;
    }
    clearFieldError(input);
    input.value = plate; // Normalizza il formato
    return true;
}

function validateNFC(input) {
    const nfc = input.value.toUpperCase().trim();
    const nfcRegex = /^[A-Z0-9]{8}$/;
    
    if (!nfcRegex.test(nfc)) {
        showFieldError(input, 'Il codice NFC deve essere di 8 caratteri alfanumerici');
        return false;
    }
    clearFieldError(input);
    input.value = nfc; // Normalizza il formato
    return true;
}

function showFieldError(input, message) {
    clearFieldError(input);
    
    input.classList.add('error');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    
    input.parentNode.appendChild(errorDiv);
}

function clearFieldError(input) {
    input.classList.remove('error');
    const existingError = input.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

// ===== STORAGE HELPERS =====
function setLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.warn('LocalStorage not available:', error);
    }
}

function getLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.warn('LocalStorage read error:', error);
        return defaultValue;
    }
}

function removeLocalStorage(key) {
    try {
        localStorage.removeItem(key);
    } catch (error) {
        console.warn('LocalStorage remove error:', error);
    }
}

// ===== ANIMATION HELPERS =====
function animateElement(element, animation, duration = 300) {
    return new Promise((resolve) => {
        element.style.animation = `${animation} ${duration}ms ease-in-out`;
        setTimeout(() => {
            element.style.animation = '';
            resolve();
        }, duration);
    });
}

function slideIn(element, direction = 'left') {
    return animateElement(element, `slideIn${direction.charAt(0).toUpperCase() + direction.slice(1)}`);
}

function slideOut(element, direction = 'left') {
    return animateElement(element, `slideOut${direction.charAt(0).toUpperCase() + direction.slice(1)}`);
}

function fadeIn(element) {
    return animateElement(element, 'fadeIn');
}

function fadeOut(element) {
    return animateElement(element, 'fadeOut');
}

// ===== EXPORT FUNCTIONS =====
window.MasterWash = {
    showLoading,
    hideLoading,
    showNotification,
    toggleMenu,
    apiRequest,
    validateRequired,
    validatePhone,
    validateLicensePlate,
    validateNFC,
    formatCurrency,
    formatDate,
    formatTime,
    debounce,
    throttle,
    setLocalStorage,
    getLocalStorage,
    removeLocalStorage,
    animateElement,
    slideIn,
    slideOut,
    fadeIn,
    fadeOut
};

// ===== GLOBAL ERROR HANDLER =====
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    if (!isOnline) {
        showNotification('Errore: verifica la connessione', 'error');
    }
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    e.preventDefault();
});

console.log('🚗 MasterWash JavaScript loaded successfully');