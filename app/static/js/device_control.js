/**
 * Device control functionality for Smart Farm Power Control System
 */

// Device control namespace
const DeviceControl = {
    /**
     * Toggle device power state
     * @param {number} deviceId - Device ID
     * @param {boolean} currentState - Current power state (true = on, false = off)
     * @param {Function} successCallback - Success callback
     * @param {Function} errorCallback - Error callback
     */
    togglePower: function(deviceId, currentState, successCallback, errorCallback) {
        // Prepare API request
        const newState = !currentState;

        fetch(`/dashboard/api/device/${deviceId}/control`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + getToken()
            },
            body: JSON.stringify({
                command: 'power',
                value: newState
            })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    if (errorCallback) errorCallback(data.error);
                    return;
                }

                if (successCallback) successCallback(data, newState);
            })
            .catch(error => {
                console.error('Error:', error);
                if (errorCallback) errorCallback('Failed to control device. Please try again.');
            });
    },

    /**
     * Send custom command to device
     * @param {number} deviceId - Device ID
     * @param {string} command - Command name
     * @param {any} value - Command value
     * @param {Function} successCallback - Success callback
     * @param {Function} errorCallback - Error callback
     */
    sendCommand: function(deviceId, command, value, successCallback, errorCallback) {
        fetch(`/dashboard/api/device/${deviceId}/control`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + getToken()
            },
            body: JSON.stringify({
                command: command,
                value: value
            })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    if (errorCallback) errorCallback(data.error);
                    return;
                }

                if (successCallback) successCallback(data);
            })
            .catch(error => {
                console.error('Error:', error);
                if (errorCallback) errorCallback('Failed to send command. Please try again.');
            });
    },

    /**
     * Get device details
     * @param {number} deviceId - Device ID
     * @param {Function} successCallback - Success callback
     * @param {Function} errorCallback - Error callback
     */
    getDeviceDetails: function(deviceId, successCallback, errorCallback) {
        fetch(`/api/devices/${deviceId}`, {
            headers: {
                'Authorization': 'Bearer ' + getToken()
            }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    if (errorCallback) errorCallback(data.error);
                    return;
                }

                if (successCallback) successCallback(data.device);
            })
            .catch(error => {
                console.error('Error:', error);
                if (errorCallback) errorCallback('Failed to get device details. Please try again.');
            });
    },

    /**
     * Get device power statistics
     * @param {number} deviceId - Device ID
     * @param {string} period - Time period (day, week, month)
     * @param {Function} successCallback - Success callback
     * @param {Function} errorCallback - Error callback
     */
    getDevicePowerStats: function(deviceId, period, successCallback, errorCallback) {
        fetch(`/api/power/devices/${deviceId}?period=${period}`, {
            headers: {
                'Authorization': 'Bearer ' + getToken()
            }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    if (errorCallback) errorCallback(data.error);
                    return;
                }

                if (successCallback) successCallback(data);
            })
            .catch(error => {
                console.error('Error:', error);
                if (errorCallback) errorCallback('Failed to get power statistics. Please try again.');
            });
    },

    /**
     * Format device status with proper badge class
     * @param {string} status - Device status
     * @returns {string} HTML badge element
     */
    formatStatusBadge: function(status) {
        let badgeClass = 'bg-secondary';

        switch (status.toLowerCase()) {
            case 'online':
                badgeClass = 'bg-success';
                break;
            case 'offline':
                badgeClass = 'bg-secondary';
                break;
            case 'error':
                badgeClass = 'bg-danger';
                break;
            case 'warning':
                badgeClass = 'bg-warning';
                break;
        }

        return `<span class="badge ${badgeClass}">${status}</span>`;
    },

    /**
     * Format power state indicator
     * @param {boolean} state - Power state
     * @returns {string} HTML formatted state
     */
    formatPowerState: function(state) {
        if (state) {
            return '<span class="text-success">ON</span>';
        } else {
            return '<span class="text-secondary">OFF</span>';
        }
    },

    /**
     * Create power toggle button
     * @param {number} deviceId - Device ID
     * @param {boolean} currentState - Current power state
     * @returns {string} HTML button element
     */
    createPowerButton: function(deviceId, currentState) {
        const btnClass = currentState ? 'btn-danger' : 'btn-success';
        const btnText = currentState ? 'Turn Off' : 'Turn On';

        return `
            <button class="btn btn-sm ${btnClass} toggle-power" 
                    data-device-id="${deviceId}" 
                    data-current-state="${currentState ? 'on' : 'off'}">
                <i class="fas fa-power-off"></i> ${btnText}
            </button>
        `;
    },

    /**
     * Initialize all device control buttons on a page
     */
    initControls: function() {
        // Power toggle buttons
        document.querySelectorAll('.toggle-power').forEach(button => {
            button.addEventListener('click', function() {
                const deviceId = this.getAttribute('data-device-id');
                const currentState = this.getAttribute('data-current-state') === 'on';

                // Disable button and show spinner
                this.disabled = true;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

                DeviceControl.togglePower(
                    deviceId,
                    currentState,
                    // Success callback
                    (data, newState) => {
                        // Update button
                        this.disabled = false;
                        this.setAttribute('data-current-state', newState ? 'on' : 'off');

                        if (newState) {
                            this.classList.remove('btn-success');
                            this.classList.add('btn-danger');
                            this.innerHTML = '<i class="fas fa-power-off"></i> Turn Off';
                        } else {
                            this.classList.remove('btn-danger');
                            this.classList.add('btn-success');
                            this.innerHTML = '<i class="fas fa-power-off"></i> Turn On';
                        }

                        // Update device status in UI if elements exist
                        const statusBadge = document.querySelector(`#device-row-${deviceId} .status-badge`);
                        if (statusBadge) {
                            statusBadge.outerHTML = DeviceControl.formatStatusBadge(data.status);
                        }

                        const powerState = document.querySelector(`#device-row-${deviceId} .power-state`);
                        if (powerState) {
                            powerState.outerHTML = DeviceControl.formatPowerState(newState);
                        }
                    },
                    // Error callback
                    (errorMsg) => {
                        this.disabled = false;
                        this.innerHTML = `<i class="fas fa-power-off"></i> ${currentState ? 'Turn Off' : 'Turn On'}`;
                        alert(errorMsg);
                    }
                );
            });
        });

        // Custom command buttons
        document.querySelectorAll('.custom-command').forEach(button => {
            button.addEventListener('click', function() {
                const deviceId = this.getAttribute('data-device-id');
                const command = this.getAttribute('data-command');
                const value = this.getAttribute('data-value');

                // Disable button and show spinner
                this.disabled = true;
                const originalContent = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

                DeviceControl.sendCommand(
                    deviceId,
                    command,
                    value,
                    // Success callback
                    (data) => {
                        this.disabled = false;
                        this.innerHTML = originalContent;

                        if (data.message) {
                            showAlert(data.message, 'success');
                        }
                    },
                    // Error callback
                    (errorMsg) => {
                        this.disabled = false;
                        this.innerHTML = originalContent;
                        alert(errorMsg);
                    }
                );
            });
        });
    },

    /**
     * Create and render device card
     * @param {object} device - Device data
     * @param {string} containerId - Container element ID
     */
    renderDeviceCard: function(device, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const powerClass = getPowerClass(device.current_power, device.max_power);
        const lastUpdated = device.last_updated ? formatDateTime(device.last_updated) : 'Never';

        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4 mb-4';
        card.innerHTML = `
            <div class="card h-100" id="device-card-${device.id}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="card-title mb-0">${device.name}</h5>
                    ${DeviceControl.formatStatusBadge(device.status)}
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <small class="text-muted">Device ID: ${device.device_id}</small>
                    </div>
                    <div class="mb-3">
                        <p class="mb-1">Type: ${device.device_type}</p>
                        <p class="mb-1">Location: ${device.location || 'N/A'}</p>
                        <p class="mb-0">Power State: <span class="power-state">${DeviceControl.formatPowerState(device.power_state)}</span></p>
                    </div>
                    <div class="d-flex align-items-center mb-3">
                        <div class="power-meter flex-grow-1">
                            <div class="progress" style="height: 10px;">
                                <div class="progress-bar ${powerClass}" role="progressbar" 
                                     style="width: ${(device.current_power / device.max_power * 100) || 0}%"></div>
                            </div>
                            <div class="d-flex justify-content-between">
                                <small class="text-muted">0W</small>
                                <small class="text-muted">${formatWatts(device.max_power)}</small>
                            </div>
                        </div>
                        <div class="ms-3">
                            <h4 class="mb-0 ${powerClass}">${formatWatts(device.current_power)}</h4>
                        </div>
                    </div>
                </div>
                <div class="card-footer">
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">Last updated: ${lastUpdated}</small>
                        ${DeviceControl.createPowerButton(device.id, device.power_state)}
                    </div>
                </div>
            </div>
        `;

        container.appendChild(card);
    }
};

// Initialize device controls when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    DeviceControl.initControls();
});