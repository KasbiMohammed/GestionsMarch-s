/**
 * Application JavaScript principale
 * Gestion des Marchés Publics - Communes Territoriales Marocaines
 */

// Configuration globale
const App = {
    apiBaseUrl: '/api',
    currentUserId: null,
    currentMarketId: null,
    
    // Initialisation
    init: function() {
        this.setupEventListeners();
        this.checkAuthentication();
        this.loadNotifications();
    },
    
    // Configuration des écouteurs d'événements
    setupEventListeners: function() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', this.handleNavigation);
        });
        
        // Formulaires
        document.querySelectorAll('form[data-ajax="true"]').forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit);
        });
        
        // Boutons d'action
        document.querySelectorAll('[data-action]').forEach(button => {
            button.addEventListener('click', this.handleAction);
        });
    },
    
    // Vérification de l'authentification
    checkAuthentication: function() {
        const token = this.getCookie('access_token');
        if (!token && !window.location.pathname.includes('/login')) {
            window.location.href = '/';
        }
    },
    
    // Gestion de la navigation
    handleNavigation: function(e) {
        const href = this.getAttribute('href');
        if (href && href !== '#' && !href.startsWith('http')) {
            e.preventDefault();
            // Navigation SPA si nécessaire
            window.location.href = href;
        }
    },
    
    // Gestion des soumissions de formulaire
    handleFormSubmit: async function(e) {
        e.preventDefault();
        
        const form = this;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Conversion des nombres
        for (const key in data) {
            if (data[key] && !isNaN(data[key])) {
                data[key] = parseFloat(data[key]);
            }
        }
        
        const url = form.action || `${App.apiBaseUrl}${form.dataset.endpoint}`;
        const method = form.method || 'POST';
        
        const button = form.querySelector('button[type="submit"]');
        const originalText = button.innerHTML;
        
        App.showLoading(button);
        
        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${App.getCookie('access_token')}`
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                App.showNotification('Opération réussie', 'success');
                
                // Callback de succès si défini
                if (form.dataset.successCallback) {
                    window[form.dataset.successCallback](result);
                }
                
                // Reset du formulaire
                form.reset();
                
                // Fermeture de la modale si dans une modale
                const modal = form.closest('.modal');
                if (modal) {
                    bootstrap.Modal.getInstance(modal).hide();
                }
            } else {
                App.showNotification(result.detail || 'Erreur lors de l\'opération', 'danger');
            }
        } catch (error) {
            App.showNotification('Erreur de connexion au serveur', 'danger');
        } finally {
            App.hideLoading(button, originalText);
        }
    },
    
    // Gestion des actions
    handleAction: async function(e) {
        const action = this.dataset.action;
        const endpoint = this.dataset.endpoint;
        const method = this.dataset.method || 'POST';
        
        if (action === 'delete') {
            if (!confirm('Êtes-vous sûr de vouloir supprimer cet élément ?')) {
                return;
            }
        }
        
        const originalText = this.innerHTML;
        App.showLoading(this);
        
        try {
            const response = await fetch(`${App.apiBaseUrl}${endpoint}`, {
                method: method,
                headers: {
                    'Authorization': `Bearer ${App.getCookie('access_token')}`
                }
            });
            
            if (response.ok) {
                App.showNotification('Opération réussie', 'success');
                
                // Callback de succès si défini
                if (this.dataset.successCallback) {
                    window[this.dataset.successCallback]();
                }
            } else {
                const result = await response.json();
                App.showNotification(result.detail || 'Erreur lors de l\'opération', 'danger');
            }
        } catch (error) {
            App.showNotification('Erreur de connexion au serveur', 'danger');
        } finally {
            App.hideLoading(this, originalText);
        }
    },
    
    // Chargement des notifications
    loadNotifications: async function () {

    const response = await fetch(
        `${this.apiBaseUrl}/dashboard/notifications`,
        {
            headers: {
                Authorization: `Bearer ${App.getCookie("access_token")}`
            }
        }
    );

    const data = await response.json();

    this.updateNotificationBadge(data.unread_count);
    this.displayNotifications(data.notifications);
    
    },
    
    // Mise à jour du badge de notification
    updateNotificationBadge: function(count) {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline' : 'none';
        }
    },
    
    // Affichage des notifications
    displayNotifications: function(notifications) {
        const container = document.querySelector('.notifications-dropdown');
        if (container) {
            container.innerHTML = notifications.map(n => `
                <a class="dropdown-item" href="${n.link || '#'}">
                    <div class="d-flex">
                        <div class="flex-shrink-0">
                            <i class="bi bi-${n.icon || 'bell'}"></i>
                        </div>
                        <div class="flex-grow-1 ms-2">
                            <p class="small mb-0">${n.message}</p>
                            <small class="text-muted">${this.formatDateTime(n.created_at)}</small>
                        </div>
                    </div>
                </a>
            `).join('');
        }
    },
    
    // Utilitaires
    getCookie: function(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },
    
    setCookie: function(name, value, days = 30) {
        const expires = new Date();
        expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
    },
    
    deleteCookie: function(name) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/`;
    },
    
    formatDate: function(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleDateString('fr-FR');
    },
    
    formatDateTime: function(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleString('fr-FR');
    },
    
    formatAmount: function(amount) {
        if (!amount) return '0,00 MAD';
        return new Intl.NumberFormat('fr-MA', {
            style: 'currency',
            currency: 'MAD'
        }).format(amount);
    },
    
    showLoading: function(element) {
        element.dataset.originalText = element.innerHTML;
        element.innerHTML = '<span class="loading-spinner"></span> Chargement...';
        element.disabled = true;
    },
    
    hideLoading: function(element) {
        element.innerHTML = element.dataset.originalText || element.innerHTML;
        element.disabled = false;
        delete element.dataset.originalText;
    },
    
    showNotification: function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    },
    
    // API helpers
    api: {
        get: async function(endpoint) {
            const response = await fetch(`${App.apiBaseUrl}${endpoint}`, {
                headers: {
                    'Authorization': `Bearer ${App.getCookie('access_token')}`
                }
            });
            return response.json();
        },
        
        post: async function(endpoint, data) {
            const response = await fetch(`${App.apiBaseUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${App.getCookie('access_token')}`
                },
                body: JSON.stringify(data)
            });
            return response.json();
        },
        
        put: async function(endpoint, data) {
            const response = await fetch(`${App.apiBaseUrl}${endpoint}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${App.getCookie('access_token')}`
                },
                body: JSON.stringify(data)
            });
            return response.json();
        },
        
        delete: async function(endpoint) {
            const response = await fetch(`${App.apiBaseUrl}${endpoint}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${App.getCookie('access_token')}`
                }
            });
            return response.json();
        }
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    App.init();
});

// Export pour utilisation globale
window.App = App;
