// Helpdesk Team Dashboard JavaScript
(function() {
    'use strict';
    
    // Helper function to replace jQuery selector
    function $(selector) {
        if (typeof selector === 'string') {
            return document.querySelector(selector);
        }
        return selector;
    }
    
    // Current filters
    var currentFilters = {
        date_from: null,
        date_to: null,
        team_id: null
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
    
    var HelpdeskTeamDashboard = {
        init: function() {
            var self = this;
            
            self.loadTeams();
            self.loadKPIs();
            self.setupEventListeners();
        },
        
        setupEventListeners: function() {
            var self = this;
            
            var applyBtn = $('#btn-apply-team-filters');
            if (applyBtn) {
                applyBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    self.applyFilters();
                    return false;
                });
            }
            
            var resetBtn = $('#btn-reset-team-filters');
            if (resetBtn) {
                resetBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    self.resetFilters();
                    return false;
                });
            }
            
            var refreshBtn = $('#btn-refresh-team-dashboard');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    self.loadKPIs();
                    return false;
                });
            }
        },
        
        loadTeams: function() {
            var self = this;
            
            rpcQuery('/helpdesk/dashboard/teams', {}).then(function(result) {
                if (result.success && result.data) {
                    var select = $('#team-filter-team');
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
                console.error('Failed to load teams:', error);
            });
        },
        
        loadKPIs: function() {
            var self = this;
            
            self.showLoadingOverlay();
            
            var params = {
                date_from: currentFilters.date_from || null,
                date_to: currentFilters.date_to || null,
                team_id: currentFilters.team_id || null
            };
            
            rpcQuery('/helpdesk/team/dashboard/kpis', params).then(function(result) {
                if (result.success && result.kpis) {
                    self.updateKPIs(result.kpis);
                    self.updateTeamPerformanceTable(result.kpis.team_performance || []);
                } else {
                    console.error('Failed to load KPIs:', result.error);
                }
                self.hideLoadingOverlay();
            }).catch(function(error) {
                console.error('Failed to load KPIs:', error);
                self.hideLoadingOverlay();
            });
        },
        
        updateKPIs: function(kpis) {
            var updateElement = function(id, value) {
                var el = $('#' + id);
                if (el) el.textContent = value || 0;
            };
            
            updateElement('total-teams', kpis.total_teams);
            updateElement('active-teams', kpis.active_teams);
            updateElement('total-team-tickets', kpis.total_team_tickets);
            updateElement('open-team-tickets', kpis.open_team_tickets);
            updateElement('today-team-tickets', kpis.today_team_tickets);
            updateElement('team-sla-at-risk', kpis.team_sla_at_risk);
        },
        
        updateTeamPerformanceTable: function(teamPerformance) {
            var tbody = $('#team-performance-tbody');
            if (!tbody) return;
            
            tbody.innerHTML = '';
            
            if (teamPerformance.length === 0) {
                var row = document.createElement('tr');
                var cell = document.createElement('td');
                cell.colSpan = 6;
                cell.className = 'text-center';
                cell.textContent = 'No team data available';
                row.appendChild(cell);
                tbody.appendChild(row);
                return;
            }
            
            teamPerformance.forEach(function(team) {
                var row = document.createElement('tr');
                
                var teamNameCell = document.createElement('td');
                var teamNameStrong = document.createElement('strong');
                teamNameStrong.textContent = team.team_name || 'N/A';
                teamNameCell.appendChild(teamNameStrong);
                row.appendChild(teamNameCell);
                
                var leaderCell = document.createElement('td');
                leaderCell.textContent = team.team_leader || 'N/A';
                row.appendChild(leaderCell);
                
                var memberCell = document.createElement('td');
                memberCell.textContent = team.member_count || 0;
                row.appendChild(memberCell);
                
                var totalCell = document.createElement('td');
                totalCell.textContent = team.total_tickets || 0;
                row.appendChild(totalCell);
                
                var openCell = document.createElement('td');
                var openBadge = document.createElement('span');
                openBadge.className = 'badge badge-warning';
                openBadge.textContent = team.open_tickets || 0;
                openCell.appendChild(openBadge);
                row.appendChild(openCell);
                
                var resolvedCell = document.createElement('td');
                var resolvedBadge = document.createElement('span');
                resolvedBadge.className = 'badge badge-success';
                resolvedBadge.textContent = team.resolved_tickets || 0;
                resolvedCell.appendChild(resolvedBadge);
                row.appendChild(resolvedCell);
                
                tbody.appendChild(row);
            });
        },
        
        applyFilters: function() {
            var dateFromEl = $('#team-filter-date-from');
            var dateToEl = $('#team-filter-date-to');
            var teamEl = $('#team-filter-team');
            
            currentFilters.date_from = dateFromEl ? dateFromEl.value || null : null;
            currentFilters.date_to = dateToEl ? dateToEl.value || null : null;
            currentFilters.team_id = teamEl ? teamEl.value || null : null;
            
            this.loadKPIs();
        },
        
        resetFilters: function() {
            var dateFromEl = $('#team-filter-date-from');
            var dateToEl = $('#team-filter-date-to');
            var teamEl = $('#team-filter-team');
            
            if (dateFromEl) dateFromEl.value = '';
            if (dateToEl) dateToEl.value = '';
            if (teamEl) teamEl.value = '';
            
            currentFilters = {
                date_from: null,
                date_to: null,
                team_id: null
            };
            
            this.loadKPIs();
        },
        
        showLoadingOverlay: function() {
            var overlay = $('#team-loading-overlay');
            if (overlay) overlay.style.display = 'block';
        },
        
        hideLoadingOverlay: function() {
            var overlay = $('#team-loading-overlay');
            if (overlay) overlay.style.display = 'none';
        }
    };
    
    // Initialize dashboard when DOM is ready
    function initDashboard() {
        if (typeof HelpdeskTeamDashboard !== 'undefined') {
            HelpdeskTeamDashboard.init();
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(initDashboard, 500);
        });
    } else if (document.readyState === 'interactive' || document.readyState === 'complete') {
        setTimeout(initDashboard, 500);
    }
    
    // Export for global access
    window.HelpdeskTeamDashboard = HelpdeskTeamDashboard;
    
})();
