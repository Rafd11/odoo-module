// Helpdesk Dashboard JavaScript
(function() {
    'use strict';

    // Helper function to replace jQuery selector
    function $(selector) {
        if (typeof selector === 'string') {
            return document.querySelector(selector);
        }
        return selector;
    }

    // Helper function to get all elements
    function $$(selector) {
        return document.querySelectorAll(selector);
    }

    // Chart instances
    var ticketTrendChart = null;
    var stateDistributionChart = null;
    var priorityDistributionChart = null;
    var slaStatusChart = null;
    
    // Current filters
    var currentFilters = {
        date_from: null,
        date_to: null,
        team_id: null,
        state: null
    };
    
    // RPC helper
    function rpcQuery(route, params) {
        return new Promise(function(resolve, reject) {
            var csrfMeta = document.querySelector('meta[name="csrf-token"]');
            var csrfToken = csrfMeta ? csrfMeta.getAttribute('content') || '' : '';
            
            var xhr = new XMLHttpRequest();
            xhr.open('POST', route, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('X-CSRFToken', csrfToken);
            
            xhr.onload = function() {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        var result = JSON.parse(xhr.responseText);
                        if (result.result) {
                            resolve(result.result);
                        } else if (result.error) {
                            reject(new Error(result.error.message || 'RPC error'));
                        } else {
                            resolve(result);
                        }
                    } catch (e) {
                        reject(new Error('Invalid JSON response'));
                    }
                } else {
                    reject(new Error('Request failed with status: ' + xhr.status));
                }
            };
            
            xhr.onerror = function() {
                reject(new Error('Request failed'));
            };
            
            xhr.send(JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: params || {},
                id: Math.floor(Math.random() * 1000000)
            }));
        });
    }
    
    // Load Chart.js library
    function loadChartLibrary() {
        return new Promise(function(resolve, reject) {
            if (window.Chart) {
                resolve(window.Chart);
                return;
            }
            
            var script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
            script.onload = function() {
                resolve(window.Chart);
            };
            script.onerror = function() {
                reject(new Error('Failed to load Chart.js library'));
            };
            document.head.appendChild(script);
        });
    }
    
    var HelpdeskDashboard = {
        Chart: null,
        
        init: function() {
            var self = this;
            
            // Load Chart.js and initialize
            loadChartLibrary().then(function(Chart) {
                self.Chart = Chart;
                self.loadTeams();
                self.loadKPIs();
                self.setupEventListeners();
            }).catch(function(error) {
                console.error('Failed to initialize dashboard:', error);
                var overlay = $('#helpdesk-loading-overlay');
                if (overlay) overlay.style.display = 'none';
            });
        },
        
        setupEventListeners: function() {
            var self = this;
            
            var applyBtn = $('#btn-apply-filters');
            if (applyBtn) {
                applyBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    self.applyFilters();
                    return false;
                });
            }
            
            var resetBtn = $('#btn-reset-filters');
            if (resetBtn) {
                resetBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    self.resetFilters();
                    return false;
                });
            }
            
            var refreshBtn = $('#btn-refresh-dashboard');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    self.loadKPIs();
                    self.loadCharts();
                    return false;
                });
            }
        },
        
        loadTeams: function() {
            var self = this;
            rpcQuery('/helpdesk/dashboard/teams', {}).then(function(result) {
                if (result.success && result.data) {
                    // Populate team dropdown
                    var select = $('#filter-team');
                    if (select) {
                        select.innerHTML = '';
                        var allOption = document.createElement('option');
                        allOption.value = '';
                        allOption.textContent = 'All Teams';
                        select.appendChild(allOption);
                        
                        result.data.forEach(function(team) {
                            var option = document.createElement('option');
                            option.value = team.id;
                            option.textContent = team.name;
                            select.appendChild(option);
                        });
                    }
                }
            }).catch(function(error) {
                console.error('Error loading teams:', error);
            });
        },
        
        loadKPIs: function() {
            var self = this;
            var overlay = $('#helpdesk-loading-overlay');
            if (overlay) overlay.style.display = 'block';
            
            var params = {
                date_from: currentFilters.date_from || null,
                date_to: currentFilters.date_to || null,
                team_id: currentFilters.team_id || null,
                state: currentFilters.state || null
            };
            
            rpcQuery('/helpdesk/dashboard/kpis', params).then(function(result) {
                if (result.success && result.kpis) {
                    self.updateKPIs(result.kpis);
                    self.loadCharts();
                }
            }).catch(function(error) {
                console.error('Error loading KPIs:', error);
            }).finally(function() {
                if (overlay) overlay.style.display = 'none';
            });
        },
        
        updateKPIs: function(kpis) {
            var updateElement = function(id, value) {
                var el = $('#' + id);
                if (el) el.textContent = value || 0;
            };
            
            updateElement('total-tickets', kpis.total_tickets);
            updateElement('my-tickets', kpis.my_tickets);
            updateElement('unassigned', kpis.unassigned);
            updateElement('sla-risk', kpis.sla_at_risk);
            updateElement('today-tickets', kpis.today_tickets);
            updateElement('overdue-count', kpis.overdue_count);
            updateElement('resolved-today', kpis.resolved_today);
            updateElement('total-reminders', kpis.total_reminders);
            updateElement('pending-reminders', kpis.pending_reminders);
            updateElement('sent-reminders', kpis.sent_reminders);
            updateElement('upcoming-reminders', kpis.upcoming_reminders);
        },
        
        loadCharts: function() {
            var self = this;
            
            // Load ticket trend
            self.loadTicketTrend();
            
            // Load state distribution
            self.loadStateDistribution();
            
            // Load priority distribution
            self.loadPriorityDistribution();
            
            // Load SLA status
            self.loadSLAStatus();
        },
        
        loadTicketTrend: function() {
            var self = this;
            var params = {
                months: 12,
                team_id: currentFilters.team_id || null,
                state: currentFilters.state || null
            };
            
            rpcQuery('/helpdesk/dashboard/ticket-trend', params).then(function(result) {
                if (result.success && result.data) {
                    self.renderTicketTrendChart(result.data);
                }
            }).catch(function(error) {
                console.error('Error loading ticket trend:', error);
            });
        },
        
        loadStateDistribution: function() {
            var self = this;
            var params = {
                team_id: currentFilters.team_id || null
            };
            
            rpcQuery('/helpdesk/dashboard/state-distribution', params).then(function(result) {
                if (result.success && result.data) {
                    self.renderStateDistributionChart(result.data);
                }
            }).catch(function(error) {
                console.error('Error loading state distribution:', error);
            });
        },
        
        loadPriorityDistribution: function() {
            var self = this;
            var params = {
                team_id: currentFilters.team_id || null
            };
            
            rpcQuery('/helpdesk/dashboard/priority-distribution', params).then(function(result) {
                if (result.success && result.data) {
                    self.renderPriorityDistributionChart(result.data);
                }
            }).catch(function(error) {
                console.error('Error loading priority distribution:', error);
            });
        },
        
        loadSLAStatus: function() {
            var self = this;
            var params = {
                team_id: currentFilters.team_id || null
            };
            
            rpcQuery('/helpdesk/dashboard/sla-status', params).then(function(result) {
                if (result.success && result.data) {
                    self.renderSLAStatusChart(result.data);
                }
            }).catch(function(error) {
                console.error('Error loading SLA status:', error);
            });
        },
        
        renderTicketTrendChart: function(data) {
            var self = this;
            var ctx = document.getElementById('chart-ticket-trend');
            if (!ctx) return;
            
            if (ticketTrendChart) {
                ticketTrendChart.destroy();
            }
            
            ticketTrendChart = new self.Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Tickets Created',
                        data: data.values || [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true
                        }
                    }
                }
            });
        },
        
        renderStateDistributionChart: function(data) {
            var self = this;
            var ctx = document.getElementById('chart-state-distribution');
            if (!ctx) return;
            
            if (stateDistributionChart) {
                stateDistributionChart.destroy();
            }
            
            stateDistributionChart = new self.Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.values || [],
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(54, 162, 235, 0.8)',
                            'rgba(255, 206, 86, 0.8)',
                            'rgba(75, 192, 192, 0.8)',
                            'rgba(153, 102, 255, 0.8)',
                            'rgba(255, 159, 64, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        },
        
        renderPriorityDistributionChart: function(data) {
            var self = this;
            var ctx = document.getElementById('chart-priority-distribution');
            if (!ctx) return;
            
            if (priorityDistributionChart) {
                priorityDistributionChart.destroy();
            }
            
            priorityDistributionChart = new self.Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Tickets by Priority',
                        data: data.values || [],
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.8)',   // Low - Green
                            'rgba(255, 193, 7, 0.8)',   // Medium - Yellow
                            'rgba(253, 126, 20, 0.8)',   // High - Orange
                            'rgba(220, 53, 69, 0.8)'     // Urgent - Red
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        },
        
        renderSLAStatusChart: function(data) {
            var self = this;
            var ctx = document.getElementById('chart-sla-status');
            if (!ctx) return;
            
            if (slaStatusChart) {
                slaStatusChart.destroy();
            }
            
            slaStatusChart = new self.Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.values || [],
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.8)',   // Met - Green
                            'rgba(255, 193, 7, 0.8)',   // At Risk - Yellow
                            'rgba(220, 53, 69, 0.8)',   // Breached - Red
                            'rgba(108, 117, 125, 0.8)'   // No SLA - Gray
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        },
        
        applyFilters: function() {
            var self = this;
            
            // Read filter values from HTML input/select fields
            var dateFromEl = $('#filter-date-from');
            var dateToEl = $('#filter-date-to');
            var teamEl = $('#filter-team');
            var stateEl = $('#filter-state');
            
            currentFilters.date_from = dateFromEl ? dateFromEl.value || null : null;
            currentFilters.date_to = dateToEl ? dateToEl.value || null : null;
            currentFilters.team_id = teamEl ? teamEl.value || null : null;
            currentFilters.state = stateEl ? stateEl.value || null : null;
            
            // Reload KPIs and charts with new filters
            self.loadKPIs();
        },
        
        resetFilters: function() {
            var self = this;
            
            // Clear HTML input/select fields
            var dateFromEl = $('#filter-date-from');
            var dateToEl = $('#filter-date-to');
            var teamEl = $('#filter-team');
            var stateEl = $('#filter-state');
            
            if (dateFromEl) dateFromEl.value = '';
            if (dateToEl) dateToEl.value = '';
            if (teamEl) teamEl.value = '';
            if (stateEl) stateEl.value = '';
            
            // Reset filter object
            currentFilters = {
                date_from: null,
                date_to: null,
                team_id: null,
                state: null
            };
            
            // Reload KPIs with cleared filters
            self.loadKPIs();
        }
    };
    
    // Initialize dashboard when DOM is ready
    function initDashboard() {
        if (typeof HelpdeskDashboard !== 'undefined') {
            HelpdeskDashboard.init();
        }
    }
    
    // Use multiple initialization methods to ensure it works in Odoo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(initDashboard, 1000);
        });
    } else if (document.readyState === 'interactive' || document.readyState === 'complete') {
        setTimeout(initDashboard, 1000);
    }
    
    // Also try to initialize when page is fully loaded
    window.addEventListener('load', function() {
        setTimeout(initDashboard, 500);
    });
    
    // Export for global access
    window.HelpdeskDashboard = HelpdeskDashboard;
    
})();
