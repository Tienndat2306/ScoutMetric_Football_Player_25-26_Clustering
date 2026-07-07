(function () {
    const clusterColors = [
        '#7c3aed', '#14b8a6', '#d97706', '#2563eb', '#dc2626',
        '#059669', '#9333ea', '#475569', '#db2777', '#0891b2'
    ];

    const isFiniteNumeric = (value) => Number.isFinite(Number(value));

    const numericFeatureKeys = (rows, preferredKeys = []) => {
        if (!rows.length) return [];
        const numericKeys = Object.keys(rows[0]).filter(key =>
            !['id', 'Player', 'Team', 'League', 'Primary Position', 'Cluster', 'Cluster_Confidence'].includes(key) &&
            rows.some(row => isFiniteNumeric(row[key]))
        );
        const preferredNumericKeys = preferredKeys.filter(key => numericKeys.includes(key));
        return [...preferredNumericKeys, ...numericKeys.filter(key => !preferredNumericKeys.includes(key))];
    };

    const renderScatterChart = (players, options = {}) => {
        const canvas = document.getElementById('main-chart');
        const chartDescription = document.getElementById('chart-description');
        if (!canvas || !players.length) return;

        const keys = numericFeatureKeys(players, options.metricKeys || []);
        if (keys.length < 2) {
            if (chartDescription) {
                chartDescription.innerText = 'At least two numeric features are required to draw the scatter chart.';
            }
            return;
        }

        const [xKey, yKey] = keys;
        const grouped = new Map();

        players.forEach(player => {
            if (!isFiniteNumeric(player[xKey]) || !isFiniteNumeric(player[yKey])) return;
            const cluster = options.showClusters ? String(player.Cluster) : 'Preview';
            if (!grouped.has(cluster)) grouped.set(cluster, []);
            grouped.get(cluster).push({
                x: Number(player[xKey]),
                y: Number(player[yKey]),
                playerName: player.Player,
                team: player.Team,
                cluster: player.Cluster,
                confidence: player.Cluster_Confidence
            });
        });

        const datasets = Array.from(grouped.entries()).map(([cluster, data]) => ({
            label: options.showClusters ? `Cluster ${cluster}` : 'Player',
            data,
            backgroundColor: options.showClusters
                ? clusterColors[Math.abs(Number(cluster)) % clusterColors.length] || '#111827'
                : '#94a3b8',
            pointRadius: 5,
            pointHoverRadius: 7
        })).filter(dataset => dataset.data.length);

        if (!datasets.length) {
            if (chartDescription) {
                chartDescription.innerText = 'No valid numeric player values are available for the selected chart axes.';
            }
            return;
        }

        if (window.myChart) window.myChart.destroy();

        window.myChart = new Chart(canvas.getContext('2d'), {
            type: 'scatter',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const p = context.raw;
                                return `${p.playerName}${p.team ? ` - ${p.team}` : ''}`;
                            },
                            footer: (context) => {
                                const p = context[0].raw;
                                const clusterText = options.showClusters ? `\nCluster: ${p.cluster}` : '';
                                const confidenceText = Number.isFinite(Number(p.confidence))
                                    ? `\nConfidence: ${(Number(p.confidence) * 100).toFixed(1)}%`
                                    : '';
                                return `${xKey}: ${p.x.toFixed(2)}\n${yKey}: ${p.y.toFixed(2)}${clusterText}${confidenceText}`;
                            }
                        }
                    },
                    legend: { display: true }
                },
                scales: {
                    x: {
                        title: { display: true, text: xKey, font: { weight: 'bold' } },
                        grid: { color: '#f1f5f9' }
                    },
                    y: {
                        title: { display: true, text: yKey, font: { weight: 'bold' } },
                        grid: { color: '#f1f5f9' }
                    }
                }
            }
        });
    };

    const downloadMainChart = (filename = 'player-clustering-chart.png') => {
        const canvas = document.getElementById('main-chart');
        if (!canvas || !window.myChart) return false;

        const exportCanvas = document.createElement('canvas');
        exportCanvas.width = canvas.width;
        exportCanvas.height = canvas.height;

        const context = exportCanvas.getContext('2d');
        context.fillStyle = '#ffffff';
        context.fillRect(0, 0, exportCanvas.width, exportCanvas.height);
        context.drawImage(canvas, 0, 0);

        const link = document.createElement('a');
        link.href = exportCanvas.toDataURL('image/png');
        link.download = filename;
        link.click();
        return true;
    };

    const renderMetricChart = (canvasId, chartKey, config) => {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !config?.k_values?.length) return;

        const chartNameMap = {
            elbow: 'elbowChart',
            silhouette: 'silhouetteChart',
            gmm: 'gmmEvaluationChart'
        };
        const chartName = chartNameMap[chartKey] || `${chartKey}Chart`;
        const optimalK = config.optimal_k;
        const metricLabel = config.metric_name || (chartKey === 'elbow' ? 'Inertia' : 'Silhouette Score');
        const colorMap = {
            elbow: '#7c3aed',
            silhouette: '#14b8a6',
            gmm: '#2563eb'
        };
        const chartColor = colorMap[chartKey] || '#2563eb';
        const gmmTitle = document.getElementById('gmm-evaluation-title');

        if (chartKey === 'gmm' && gmmTitle) {
            gmmTitle.innerText = `GMM ${metricLabel} - Optimal K: ${optimalK}`;
        }

        if (window[chartName]) window[chartName].destroy();

        window[chartName] = new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: config.k_values,
                datasets: [{
                    label: metricLabel,
                    data: config.scores,
                    borderColor: chartColor,
                    backgroundColor: chartColor,
                    tension: 0.25,
                    pointRadius: config.k_values.map(k => k === optimalK ? 6 : 4),
                    pointHoverRadius: 7,
                    pointBackgroundColor: config.k_values.map(k => k === optimalK ? '#dc2626' : chartColor)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: items => `K = ${items[0].label}`,
                            label: item => `${item.dataset.label}: ${Number(item.raw).toFixed(4)}`
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: 'K', font: { weight: 'bold' } },
                        grid: { color: '#f8fafc' }
                    },
                    y: {
                        title: {
                            display: true,
                            text: chartKey === 'elbow' ? 'Inertia' : metricLabel,
                            font: { weight: 'bold' }
                        },
                        grid: { color: '#f1f5f9' }
                    }
                }
            }
        });
    };

    const resetClusterSummary = () => {
        const bars = document.getElementById('cluster-summary-bars');
        const table = document.getElementById('cluster-summary-table');
        const xHeader = document.getElementById('cluster-table-x-header');
        const yHeader = document.getElementById('cluster-table-y-header');
        const benchmark = document.getElementById('cluster-average-benchmark');
        const radarDescription = document.getElementById('cluster-radar-description');
        const radarSection = document.getElementById('cluster-radar-section');
        const heatmapSection = document.getElementById('cluster-heatmap-section');
        const heatmap = document.getElementById('cluster-heatmap');
        const heatmapDescription = document.getElementById('cluster-heatmap-description');
        const evaluationSection = document.getElementById('cluster-evaluation-section');
        const evaluationMetrics = document.getElementById('cluster-evaluation-metrics');
        const evaluationDescription = document.getElementById('cluster-evaluation-description');

        if (bars) bars.innerHTML = '<p class="text-sm text-slate-500">No clustering result yet.</p>';
        if (table) {
            table.innerHTML = '<tr><td class="px-4 py-3 text-slate-500" colspan="3">No clustering result yet.</td></tr>';
        }
        if (xHeader) xHeader.innerText = 'Average X-axis';
        if (yHeader) yHeader.innerText = 'Average Y-axis';
        if (benchmark) benchmark.innerText = 'No cluster average available yet.';
        if (radarDescription) radarDescription.innerText = 'No clustering result yet.';
        if (radarSection) radarSection.classList.add('hidden');
        if (heatmapSection) heatmapSection.classList.add('hidden');
        if (heatmap) heatmap.innerHTML = '';
        if (heatmapDescription) heatmapDescription.innerText = 'No clustering result yet.';
        if (evaluationSection) evaluationSection.classList.add('hidden');
        if (evaluationMetrics) evaluationMetrics.innerHTML = '';
        if (evaluationDescription) evaluationDescription.innerText = 'No clustering result yet.';
        if (window.clusterRadarChart) {
            window.clusterRadarChart.destroy();
            window.clusterRadarChart = null;
        }
    };

    const renderClusterSummary = (players, preferredKeys = []) => {
        const bars = document.getElementById('cluster-summary-bars');
        const table = document.getElementById('cluster-summary-table');
        const xHeader = document.getElementById('cluster-table-x-header');
        const yHeader = document.getElementById('cluster-table-y-header');
        const benchmark = document.getElementById('cluster-average-benchmark');
        if (!bars || !table || !players.length) return;

        const keys = numericFeatureKeys(players, preferredKeys);
        if (keys.length < 2) {
            resetClusterSummary();
            return;
        }

        const [xKey, yKey] = keys;
        if (xHeader) xHeader.innerText = `Average ${xKey}`;
        if (yHeader) yHeader.innerText = `Average ${yKey}`;
        const overallAvgX = players.reduce((sum, row) => sum + Number(row[xKey]), 0) / players.length;
        const overallAvgY = players.reduce((sum, row) => sum + Number(row[yKey]), 0) / players.length;

        if (benchmark) {
            benchmark.innerHTML = `
                <div class="flex flex-col gap-1">
                    <span>AVERAGE ${xKey.toUpperCase()}: ${overallAvgX.toFixed(2)}</span>
                    <span>AVERAGE ${yKey.toUpperCase()}: ${overallAvgY.toFixed(2)}</span>
                </div>
            `;
        }

        const grouped = new Map();
        players.forEach(player => {
            const cluster = String(player.Cluster);
            if (!grouped.has(cluster)) grouped.set(cluster, []);
            grouped.get(cluster).push(player);
        });

        const clusterEntries = Array.from(grouped.entries()).sort((a, b) => Number(a[0]) - Number(b[0]));
        const total = players.length;

        bars.innerHTML = clusterEntries.map(([cluster, rows]) => {
            const percentage = total ? (rows.length / total) * 100 : 0;
            const color = clusterColors[Math.abs(Number(cluster)) % clusterColors.length] || '#111827';
            const label = cluster === '-1' ? 'Noise' : `Cluster ${cluster}`;

            return `
                <div class="space-y-2">
                    <div class="flex justify-between gap-4 text-xs font-bold uppercase">
                        <span style="color:${color}">${label}</span>
                        <span class="text-slate-500">${rows.length} players (${percentage.toFixed(1)}%)</span>
                    </div>
                    <div class="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                        <div class="h-full rounded-full" style="width:${percentage}%; background:${color}"></div>
                    </div>
                </div>
            `;
        }).join('');

        table.innerHTML = clusterEntries.map(([cluster, rows], index) => {
            const color = clusterColors[Math.abs(Number(cluster)) % clusterColors.length] || '#111827';
            const label = cluster === '-1' ? 'Noise' : `Cluster ${cluster}`;
            const avgX = rows.reduce((sum, row) => sum + Number(row[xKey]), 0) / rows.length;
            const avgY = rows.reduce((sum, row) => sum + Number(row[yKey]), 0) / rows.length;
            const diffX = avgX - overallAvgX;
            const diffY = avgY - overallAvgY;
            const borderClass = index === clusterEntries.length - 1 ? '' : 'border-b border-slate-50';
            const formatDiff = value => {
                const sign = value >= 0 ? '+' : '';
                const textColor = value >= 0 ? 'text-emerald-600' : 'text-rose-600';
                return `<span class="${textColor} text-xs font-semibold">(${sign}${value.toFixed(2)})</span>`;
            };

            return `
                <tr class="${borderClass}">
                    <td class="px-4 py-3 font-semibold" style="color:${color}">${label}</td>
                    <td class="px-4 py-3">${avgX.toFixed(2)} ${formatDiff(diffX)}</td>
                    <td class="px-4 py-3">${avgY.toFixed(2)} ${formatDiff(diffY)}</td>
                </tr>
            `;
        }).join('');
    };

    const formatMetricValue = (metric) => {
        const value = Number(metric.value);
        if (!Number.isFinite(value)) return 'N/A';
        if (metric.key === 'noise_ratio') return `${(value * 100).toFixed(1)}%`;
        if (Math.abs(value) >= 1000) return value.toFixed(0);
        if (Math.abs(value) >= 100) return value.toFixed(1);
        return value.toFixed(3);
    };

    const percentileColor = (percentile) => {
        if (percentile >= 80) return '#059669';
        if (percentile >= 55) return '#2563eb';
        if (percentile >= 35) return '#d97706';
        return '#dc2626';
    };

    const renderClusterEvaluation = (evaluation) => {
        const section = document.getElementById('cluster-evaluation-section');
        const metricsContainer = document.getElementById('cluster-evaluation-metrics');
        const description = document.getElementById('cluster-evaluation-description');

        if (!section || !metricsContainer || !evaluation?.metrics?.length) {
            if (section) section.classList.add('hidden');
            return;
        }

        section.classList.remove('hidden');

        const noiseText = evaluation.noise_count
            ? `Noise: ${evaluation.noise_count} (${(Number(evaluation.noise_ratio || 0) * 100).toFixed(1)}%).`
            : 'No noise.';

        if (description) {
            description.innerText = `${evaluation.algorithm}: ${evaluation.cluster_count} clusters. ${noiseText} Percentile 100 is best among reference configurations.`;
        }

        const metricCards = evaluation.metrics.map(metric => {
            const percentile = Number(metric.percentile);
            const safePercentile = Number.isFinite(percentile) ? Math.max(0, Math.min(100, percentile)) : 0;
            const color = percentileColor(safePercentile);
            const direction = metric.higher_is_better ? 'Higher is better' : 'Lower is better';
            const percentileText = Number.isFinite(percentile) ? `${safePercentile.toFixed(1)}%` : 'N/A';

            return `
                <div class="border border-slate-100 rounded-lg p-4 bg-white">
                    <div class="flex items-start justify-between gap-3">
                        <div>
                            <h5 class="text-sm font-bold text-slate-800">${metric.label}</h5>
                            <p class="text-xs text-slate-500 mt-1">${direction}</p>
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-bold text-slate-900">${formatMetricValue(metric)}</div>
                            <div class="text-xs font-semibold" style="color:${color}">P${percentileText}</div>
                        </div>
                    </div>
                    <div class="mt-4 h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
                        <div class="h-full rounded-full" style="width:${safePercentile}%; background:${color}"></div>
                    </div>
                </div>
            `;
        }).join('');

        metricsContainer.innerHTML = metricCards;
    };

    const hexToRgba = (hex, alpha) => {
        const value = hex.replace('#', '');
        const r = parseInt(value.substring(0, 2), 16);
        const g = parseInt(value.substring(2, 4), 16);
        const b = parseInt(value.substring(4, 6), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    };

    const renderClusterRadarChart = (componentFeatures, clusterComponents) => {
        const radarSection = document.getElementById('cluster-radar-section');
        const canvas = document.getElementById('cluster-radar-chart');
        const description = document.getElementById('cluster-radar-description');
        if (componentFeatures?.length < 3) {
            if (window.clusterRadarChart) {
                window.clusterRadarChart.destroy();
                window.clusterRadarChart = null;
            }
            if (radarSection) radarSection.classList.add('hidden');
            return;
        }

        if (!canvas || !componentFeatures?.length || !clusterComponents?.length) {
            if (description) description.innerText = 'No component data available for radar chart.';
            if (radarSection) radarSection.classList.add('hidden');
            return;
        }

        if (radarSection) radarSection.classList.remove('hidden');

        const sortedClusters = [...clusterComponents].sort((a, b) => Number(a.cluster) - Number(b.cluster));
        const featureMaxValues = Object.fromEntries(
            componentFeatures.map(feature => {
                const maxValue = Math.max(
                    ...sortedClusters.map(item => Number(item.averages?.[feature] || 0))
                );
                return [feature, maxValue || 1];
            })
        );

        const datasets = sortedClusters.map(item => {
            const color = clusterColors[Math.abs(Number(item.cluster)) % clusterColors.length] || '#111827';
            const label = Number(item.cluster) === -1 ? 'Noise' : `Cluster ${item.cluster}`;
            const rawValues = componentFeatures.map(feature => Number(item.averages?.[feature] || 0));

            return {
                label,
                data: componentFeatures.map((feature, index) => (rawValues[index] / featureMaxValues[feature]) * 100),
                rawValues,
                borderColor: color,
                backgroundColor: hexToRgba(color, 0.12),
                pointBackgroundColor: color,
                pointBorderColor: '#ffffff',
                pointRadius: 3,
                borderWidth: 2
            };
        });

        if (window.clusterRadarChart) window.clusterRadarChart.destroy();

        window.clusterRadarChart = new Chart(canvas.getContext('2d'), {
            type: 'radar',
            data: {
                labels: componentFeatures,
                datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 12, font: { size: 11 } }
                    },
                    tooltip: {
                        callbacks: {
                            label: item => {
                                const rawValue = item.dataset.rawValues[item.dataIndex];
                                return `${item.dataset.label}: ${rawValue.toFixed(2)} (${Number(item.raw).toFixed(1)}%)`;
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        min: 0,
                        max: 100,
                        ticks: {
                            backdropColor: 'transparent',
                            font: { size: 20 },
                            callback: value => `${value}%`
                        },
                        pointLabels: {
                            font: { size: 11 }
                        },
                        grid: { color: '#e2e8f0' },
                        angleLines: { color: '#e2e8f0' }
                    }
                }
            }
        });

        if (description) {
            description.innerText = 'Radar chart is normalized to 0-100 per attribute.';
        }
    };

    const normalizedComponentData = (componentFeatures, clusterComponents) => {
        const sortedClusters = [...clusterComponents].sort((a, b) => Number(a.cluster) - Number(b.cluster));
        const featureMaxValues = Object.fromEntries(
            componentFeatures.map(feature => {
                const maxValue = Math.max(...sortedClusters.map(item => Number(item.averages?.[feature] || 0)));
                return [feature, maxValue || 1];
            })
        );

        return sortedClusters.map(item => ({
            cluster: item.cluster,
            count: item.count,
            values: Object.fromEntries(componentFeatures.map(feature => {
                const raw = Number(item.averages?.[feature] || 0);
                return [feature, {
                    raw,
                    normalized: (raw / featureMaxValues[feature]) * 100
                }];
            }))
        }));
    };

    const heatmapCellColor = (value) => {
        const clamped = Math.max(0, Math.min(100, value));
        const alpha = 0.1 + (clamped / 100) * 0.78;
        return `rgba(124, 58, 237, ${alpha})`;
    };

    const renderClusterHeatmap = (componentFeatures, clusterComponents) => {
        const section = document.getElementById('cluster-heatmap-section');
        const container = document.getElementById('cluster-heatmap');
        const description = document.getElementById('cluster-heatmap-description');

        if (!componentFeatures?.length || !clusterComponents?.length) {
            if (section) section.classList.add('hidden');
            if (container) container.innerHTML = '';
            return;
        }

        if (!section || !container) return;

        const rows = normalizedComponentData(componentFeatures, clusterComponents);
        section.classList.remove('hidden');

        const headerCells = componentFeatures.map(feature => `
            <th class="px-3 py-3 text-left text-[11px] font-semibold uppercase text-slate-500 whitespace-nowrap">${feature}</th>
        `).join('');

        const bodyRows = rows.map(row => {
            const label = Number(row.cluster) === -1 ? 'Noise' : `Cluster ${row.cluster}`;
            const cells = componentFeatures.map(feature => {
                const value = row.values[feature];
                const textColor = value.normalized >= 62 ? '#ffffff' : '#1e293b';

                return `
                    <td class="px-3 py-3 text-xs font-semibold text-center whitespace-nowrap"
                        style="background:${heatmapCellColor(value.normalized)}; color:${textColor}"
                        title="${feature}: ${value.raw.toFixed(2)} (${value.normalized.toFixed(1)}%)">
                        ${value.normalized.toFixed(0)}
                    </td>
                `;
            }).join('');

            return `
                <tr class="border-b border-slate-100 last:border-b-0">
                    <th class="px-3 py-3 text-left text-xs font-bold text-slate-700 whitespace-nowrap">${label}<span class="ml-1 text-slate-400">(${row.count})</span></th>
                    ${cells}
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <table class="min-w-full border-collapse overflow-hidden rounded-lg">
                <thead>
                    <tr class="bg-slate-50 border-b border-slate-100">
                        <th class="px-3 py-3 text-left text-[11px] font-semibold uppercase text-slate-500 whitespace-nowrap">Cluster</th>
                        ${headerCells}
                    </tr>
                </thead>
                <tbody>${bodyRows}</tbody>
            </table>
        `;

        if (description) {
            description.innerText = 'Darker cells indicate higher normalized values per attribute on a 0-100 scale.';
        }
    };

    const hideClusterRadarChart = () => {
        const radarSection = document.getElementById('cluster-radar-section');
        if (window.clusterRadarChart) {
            window.clusterRadarChart.destroy();
            window.clusterRadarChart = null;
        }
        if (radarSection) radarSection.classList.add('hidden');
    };

    window.ScoutMetricCharts = {
        renderScatterChart,
        downloadMainChart,
        renderMetricChart,
        resetClusterSummary,
        renderClusterSummary,
        renderClusterEvaluation,
        renderClusterRadarChart,
        renderClusterHeatmap,
        hideClusterRadarChart
    };
})();
