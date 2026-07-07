document.addEventListener('DOMContentLoaded', () => {
    const positionSelect = document.getElementById('position-select');
    const leagueSelect = document.getElementById('league-select');
    const criteriaSelect = document.getElementById('criteria-select');
    const algoSelect = document.getElementById('algo-select');
    const kMethodSelect = document.getElementById('k-method-select');
    const kInput = document.getElementById('k-value');
    const loadDataBtn = document.getElementById('load-data-btn');
    const runClusteringBtn = document.getElementById('run-clustering-btn');
    const downloadChartBtn = document.getElementById('download-chart-btn');
    const moreActionsBtn = document.getElementById('more-actions-btn');
    const moreActionsMenu = document.getElementById('more-actions-menu');
    const compareActionLink = document.getElementById('compare-action-link');
    const chartDescription = document.getElementById('chart-description');
    const charts = window.ScoutMetricCharts;
    let defaultKMethods = [];
    let canDownloadClusterChart = false;

    if (!positionSelect || !leagueSelect || !criteriaSelect || !algoSelect || !kMethodSelect || !runClusteringBtn) {
        return;
    }

    if (!charts) {
        console.error('ScoutMetricCharts is not loaded. Check script order in base.html.');
        if (chartDescription) chartDescription.innerText = 'Chart module could not be loaded.';
        return;
    }

    const fillSelect = (element, values) => {
        if (!element) return;
        element.innerHTML = values.map(value => `<option value="${value}">${value}</option>`).join('');
    };

    const getSelectedParams = () => ({
        position: positionSelect?.value,
        league: leagueSelect?.value,
        criteria: criteriaSelect?.value,
        algorithm: algoSelect?.value,
        k_method: kMethodSelect?.value,
        k: kInput?.value
    });

    const setManualKState = (disabled) => {
        if (!kInput) return;
        kInput.disabled = disabled;
        kInput.classList.toggle('bg-slate-200', disabled);
        kInput.classList.toggle('opacity-50', disabled);
    };

    const setKMethodState = (disabled) => {
        if (!kMethodSelect) return;
        kMethodSelect.disabled = disabled;
        kMethodSelect.parentElement?.classList.toggle('opacity-50', disabled);
    };

    const setDownloadChartState = (enabled) => {
        canDownloadClusterChart = enabled;
        if (!downloadChartBtn) return;
        downloadChartBtn.disabled = !enabled;
        if (compareActionLink) {
            compareActionLink.classList.toggle('pointer-events-none', !enabled);
            compareActionLink.classList.toggle('opacity-40', !enabled);
            compareActionLink.title = enabled
                ? 'Compare clustered players'
                : 'Run clustering before comparing players';
        }
    };

    const buildChartFilename = () => {
        const params = getSelectedParams();
        const safeParts = [
            params.position,
            params.league,
            params.criteria,
            params.algorithm
        ].filter(Boolean).map(part => String(part)
            .trim()
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '')
        ).filter(Boolean);

        return `${safeParts.join('_') || 'player-clustering'}_chart.png`;
    };

    const handleUILogic = () => {
        if (!algoSelect || !kMethodSelect || !kInput) return;

        setKMethodState(false);
        setManualKState(false);

        if (algoSelect.value === 'GMM') {
            fillSelect(kMethodSelect, ['BIC']);
            kMethodSelect.value = 'BIC';
            setKMethodState(true);
            setManualKState(true);
            return;
        }

        if (defaultKMethods.length && kMethodSelect.options.length === 1 && kMethodSelect.value === 'BIC') {
            fillSelect(kMethodSelect, defaultKMethods);
        }

        if (algoSelect.value === 'DBSCAN') {
            setKMethodState(true);
            setManualKState(true);
            return;
        }

        setManualKState(kMethodSelect.value !== 'Manual');
    };

    const loadKEvaluationCharts = async () => {
        const params = getSelectedParams();
        if (!params.position || !params.league || !params.criteria) return;

        const response = await fetch('/api/k_evaluation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        const result = await response.json();

        if (result.status !== 'success') {
            console.warn(result.message || 'Unable to compute K-evaluation charts.');
            return;
        }

        charts.renderMetricChart('elbow-chart', 'elbow', result.data.elbow);
        charts.renderMetricChart('silhouette-chart', 'silhouette', result.data.silhouette);
        charts.renderMetricChart('gmm-evaluation-chart', 'gmm', result.data.gmm);
    };

    const loadCriteriaOptions = async () => {
        const position = positionSelect.value;
        criteriaSelect.innerHTML = '<option value="">Loading...</option>';

        if (!position) {
            criteriaSelect.innerHTML = '<option value="">Select position</option>';
            return;
        }

        const response = await fetch(`/get_criteria_options/${position}`);
        const criteria = await response.json();
        fillSelect(criteriaSelect, criteria);
    };

    const loadPreviewData = async () => {
        const params = getSelectedParams();
        if (!params.position || !params.league || !params.criteria) return;

        const response = await fetch('/api/load_raw_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        const result = await response.json();

        if (result.status !== 'success') {
            chartDescription.innerText = result.message || 'Unable to load data.';
            setDownloadChartState(false);
            return;
        }

        chartDescription.innerText = result.description;
        charts.renderScatterChart(result.data, { showClusters: false });
        charts.resetClusterSummary();
        setDownloadChartState(false);
        await loadKEvaluationCharts();
    };

    const setClusteringLoading = (isLoading) => {
        if (!runClusteringBtn) return;
        runClusteringBtn.disabled = isLoading;
        const buttonText = runClusteringBtn.querySelector('.btn-text');
        if (buttonText) buttonText.innerText = isLoading ? 'Processing...' : 'Cluster';
    };

    const runClustering = async () => {
        const params = getSelectedParams();
        if (!params.position || !params.league || !params.criteria || !params.algorithm) return;

        setClusteringLoading(true);
        setDownloadChartState(false);

        try {
            const response = await fetch('/api/cluster', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });
            const result = await response.json();

            if (result.status !== 'success') {
                chartDescription.innerText = result.message || 'Unable to run clustering.';
                setDownloadChartState(false);
                return;
            }

            const roundedMinutes = result.min_minutes_threshold
                ? Math.round(result.min_minutes_threshold)
                : null;
            const minutesText = roundedMinutes ? ` with more than ${roundedMinutes} minutes played` : '';

            chartDescription.innerText = `${result.description}${minutesText} - Clusters: ${result.cluster_count}`;
            charts.renderScatterChart(result.data, {
                showClusters: true,
                metricKeys: result.selected_features || []
            });
            setDownloadChartState(true);
            localStorage.setItem('scoutmetric:lastClusterResult', JSON.stringify({
                params,
                description: result.description,
                cluster_count: result.cluster_count,
                selected_features: result.selected_features || [],
                component_features: result.component_features || [],
                cluster_components: result.cluster_components || [],
                data: result.data || [],
                saved_at: new Date().toISOString()
            }));

            if (Number(result.cluster_count) >= 5) {
                charts.hideClusterRadarChart();
            } else {
                charts.renderClusterRadarChart(result.component_features, result.cluster_components);
            }

            charts.renderClusterSummary(result.data, result.selected_features || []);
            charts.renderClusterEvaluation(result.evaluation);
            charts.renderClusterHeatmap(result.component_features, result.cluster_components);
        } finally {
            setClusteringLoading(false);
        }
    };

    const init = async () => {
        const response = await fetch('/api/get_params');
        const params = await response.json();

        fillSelect(positionSelect, params.positions);
        fillSelect(leagueSelect, params.leagues);
        fillSelect(algoSelect, params.algorithms);
        fillSelect(kMethodSelect, params.k_methods);
        defaultKMethods = params.k_methods || [];

        await loadCriteriaOptions();
        handleUILogic();
        await loadPreviewData();
    };

    positionSelect.addEventListener('change', async () => {
        await loadCriteriaOptions();
        await loadPreviewData();
    });
    leagueSelect.addEventListener('change', loadPreviewData);
    criteriaSelect.addEventListener('change', loadPreviewData);
    loadDataBtn.addEventListener('click', loadPreviewData);
    runClusteringBtn.addEventListener('click', runClustering);
    downloadChartBtn?.addEventListener('click', () => {
        if (!canDownloadClusterChart) return;
        charts.downloadMainChart(buildChartFilename());
    });
    moreActionsBtn?.addEventListener('click', (event) => {
        event.stopPropagation();
        moreActionsMenu?.classList.toggle('hidden');
        moreActionsBtn.setAttribute('aria-expanded', String(!moreActionsMenu?.classList.contains('hidden')));
    });
    document.addEventListener('click', () => {
        moreActionsMenu?.classList.add('hidden');
        moreActionsBtn?.setAttribute('aria-expanded', 'false');
    });
    algoSelect.addEventListener('change', async () => {
        handleUILogic();
        setDownloadChartState(false);
        await loadKEvaluationCharts();
    });
    kMethodSelect.addEventListener('change', async () => {
        handleUILogic();
        setDownloadChartState(false);
        await loadKEvaluationCharts();
    });

    init().catch(error => {
        console.error('Init error:', error);
        chartDescription.innerText = 'Interface initialization failed.';
    });
});
