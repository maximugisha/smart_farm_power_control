/**
 * Chart utilities for Smart Farm Power Control System
 */

// Chart color palette
const CHART_COLORS = {
    blue: '#3498db',
    red: '#e74c3c',
    green: '#2ecc71',
    orange: '#f39c12',
    purple: '#9b59b6',
    teal: '#1abc9c',
    darkOrange: '#d35400',
    darkBlue: '#34495e',
    lightBlue: '#85c1e9',
    lightRed: '#f1948a',
    lightGreen: '#82e0aa',
    lightOrange: '#f8c471'
};

// Transparent versions of colors
const CHART_COLORS_TRANSPARENT = {
    blue: 'rgba(52, 152, 219, 0.2)',
    red: 'rgba(231, 76, 60, 0.2)',
    green: 'rgba(46, 204, 113, 0.2)',
    orange: 'rgba(243, 156, 18, 0.2)',
    purple: 'rgba(155, 89, 182, 0.2)',
    teal: 'rgba(26, 188, 156, 0.2)',
    darkOrange: 'rgba(211, 84, 0, 0.2)',
    darkBlue: 'rgba(52, 73, 94, 0.2)'
};

// Color sequences for charts with multiple datasets
const CHART_COLOR_SEQUENCE = [
    CHART_COLORS.blue,
    CHART_COLORS.red,
    CHART_COLORS.green,
    CHART_COLORS.orange,
    CHART_COLORS.purple,
    CHART_COLORS.teal,
    CHART_COLORS.darkOrange,
    CHART_COLORS.darkBlue
];

// Transparent color sequences
const CHART_COLOR_SEQUENCE_TRANSPARENT = [
    CHART_COLORS_TRANSPARENT.blue,
    CHART_COLORS_TRANSPARENT.red,
    CHART_COLORS_TRANSPARENT.green,
    CHART_COLORS_TRANSPARENT.orange,
    CHART_COLORS_TRANSPARENT.purple,
    CHART_COLORS_TRANSPARENT.teal,
    CHART_COLORS_TRANSPARENT.darkOrange,
    CHART_COLORS_TRANSPARENT.darkBlue
];

/**
 * Create a power usage line chart
 * @param {string} canvasId - Canvas element ID
 * @param {object} data - Chart data
 * @param {object} options - Additional chart options
 * @returns {Chart} Chart instance
 */
function createPowerUsageChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Power (Watts)'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Time'
                }
            }
        },
        plugins: {
            tooltip: {
                mode: 'index',
                intersect: false,
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += formatWatts(context.parsed.y);
                        }
                        return label;
                    }
                }
            },
            legend: {
                position: 'top',
            }
        }
    };

    // Merge default options with provided options
    const chartOptions = { ...defaultOptions, ...options };

    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: chartOptions
    });
}

/**
 * Create an energy consumption bar chart
 * @param {string} canvasId - Canvas element ID
 * @param {object} data - Chart data
 * @param {object} options - Additional chart options
 * @returns {Chart} Chart instance
 */
function createEnergyConsumptionChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Energy (kWh)'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Date'
                }
            }
        },
        plugins: {
            tooltip: {
                mode: 'index',
                intersect: false,
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += context.parsed.y.toFixed(2) + ' kWh';
                        }
                        return label;
                    }
                }
            },
            legend: {
                position: 'top',
            }
        }
    };

    // Merge default options with provided options
    const chartOptions = { ...defaultOptions, ...options };

    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: chartOptions
    });
}

/**
 * Create a power distribution pie/doughnut chart
 * @param {string} canvasId - Canvas element ID
 * @param {object} data - Chart data
 * @param {object} options - Additional chart options
 * @param {boolean} isDoughnut - Whether to create a doughnut chart
 * @returns {Chart} Chart instance
 */
function createPowerDistributionChart(canvasId, data, options = {}, isDoughnut = true) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const label = context.label || '';
                        const value = context.raw || 0;
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = ((value / total) * 100).toFixed(1);
                        return `${label}: ${value.toFixed(1)} W (${percentage}%)`;
                    }
                }
            },
            legend: {
                position: 'right',
            }
        }
    };

    // Merge default options with provided options
    const chartOptions = { ...defaultOptions, ...options };

    return new Chart(ctx, {
        type: isDoughnut ? 'doughnut' : 'pie',
        data: data,
        options: chartOptions
    });
}

/**
 * Create a device comparison bar chart
 * @param {string} canvasId - Canvas element ID
 * @param {object} data - Chart data
 * @param {object} options - Additional chart options
 * @returns {Chart} Chart instance
 */
function createDeviceComparisonChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y', // Horizontal bar chart
        scales: {
            x: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Power (Watts)'
                }
            }
        },
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.x !== null) {
                            label += formatWatts(context.parsed.x);
                        }
                        return label;
                    }
                }
            },
            legend: {
                display: false
            }
        }
    };

    // Merge default options with provided options
    const chartOptions = { ...defaultOptions, ...options };

    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: chartOptions
    });
}

/**
 * Create a cost analysis line chart
 * @param {string} canvasId - Canvas element ID
 * @param {object} data - Chart data
 * @param {object} options - Additional chart options
 * @returns {Chart} Chart instance
 */
function createCostAnalysisChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Cost ($)'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Date'
                }
            }
        },
        plugins: {
            tooltip: {
                mode: 'index',
                intersect: false,
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += '$' + context.parsed.y.toFixed(2);
                        }
                        return label;
                    }
                }
            },
            legend: {
                position: 'top',
            }
        }
    };

    // Merge default options with provided options
    const chartOptions = { ...defaultOptions, ...options };

    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: chartOptions
    });
}

/**
 * Update chart data and redraw
 * @param {Chart} chart - Chart instance
 * @param {Array} labels - New labels
 * @param {Array} datasets - New datasets
 */
function updateChartData(chart, labels, datasets) {
    chart.data.labels = labels;
    chart.data.datasets = datasets;
    chart.update();
}

/**
 * Format watts with appropriate unit
 * @param {number} watts - Value in watts
 * @returns {string} Formatted value
 */
function formatWatts(watts) {
    if (watts >= 1000) {
        return (watts / 1000).toFixed(2) + ' kW';
    }
    return watts.toFixed(1) + ' W';
}

/**
 * Create a combo chart with both bar and line
 * @param {string} canvasId - Canvas element ID
 * @param {object} data - Chart data
 * @param {object} options - Additional chart options
 * @returns {Chart} Chart instance
 */
function createEnergyPriceComboChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                position: 'left',
                title: {
                    display: true,
                    text: 'Energy (kWh)'
                }
            },
            y1: {
                beginAtZero: true,
                position: 'right',
                grid: {
                    drawOnChartArea: false,
                },
                title: {
                    display: true,
                    text: 'Cost ($)'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Date'
                }
            }
        },
        plugins: {
            tooltip: {
                mode: 'index',
                intersect: false
            },
            legend: {
                position: 'top',
            }
        }
    };

    // Merge default options with provided options
    const chartOptions = { ...defaultOptions, ...options };

    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: chartOptions
    });
}