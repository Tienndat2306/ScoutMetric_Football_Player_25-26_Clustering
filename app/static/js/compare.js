(function () {
    const STORAGE_KEY = 'scoutmetric:lastClusterResult';
    const excludedKeys = new Set([
        'id',
        'Player',
        'Team',
        'League',
        'Primary Position',
        'Cluster',
        'Cluster_Confidence'
    ]);

    const categoryConfig = [
        {
            name: 'Shooting',
            icon: 'target',
            patterns: [
                /goal/i,
                /\bxg\b/i,
                /xg/i,
                /shot/i,
                /finishing/i,
                /touches in opposition box/i
            ]
        },
        {
            name: 'Passing',
            icon: 'conversion_path',
            patterns: [
                /assist/i,
                /\bxa\b/i,
                /pass/i,
                /long ball/i,
                /chance/i,
                /cross/i,
                /build-up/i
            ]
        },
        {
            name: 'Possession',
            icon: 'motion_photos_auto',
            patterns: [
                /touch/i,
                /dribbl/i,
                /duel/i,
                /aerial/i,
                /recover/i,
                /possession/i,
                /fouls won/i,
                /dispossessed/i,
                /minutes played/i
            ]
        },
        {
            name: 'Defending',
            icon: 'shield',
            patterns: [
                /defen/i,
                /tackle/i,
                /interception/i,
                /blocked/i,
                /clearance/i,
                /clean sheet/i,
                /conceded/i,
                /against/i,
                /dribbled past/i,
                /ball winning/i
            ]
        },
        {
            name: 'Discipline',
            icon: 'gavel',
            patterns: [
                /card/i,
                /foul/i,
                /penalt/i
            ]
        }
    ];

    const compositeDefinitions = [
        {
            key: 'Expected Output',
            formula: 'Non-penalty xG + Expected assists (xA)',
            dependencies: ['Non-penalty xG', 'Expected assists (xA)']
        },
        {
            key: 'Ball Winning Actions',
            formula: 'Tackles + Interceptions + Recoveries + Duels won',
            dependencies: ['Tackles', 'Interceptions', 'Recoveries', 'Duels won']
        },
        {
            key: 'Finishing',
            formula: 'Non-penalty xG + Shots',
            dependencies: ['Non-penalty xG', 'Shots']
        },
        {
            key: 'Build-up',
            formula: 'Touches + Chances created',
            dependencies: ['Touches', 'Chances created']
        },
        {
            key: 'Defending',
            formula: 'Tackles + Blocked shots + Interceptions + Duels won',
            dependencies: ['Tackles', 'Blocked shots', 'Interceptions', 'Duels won']
        }
    ];

    let clusterResult = null;
    let players = [];
    let metricKeys = [];
    let groupedMetrics = [];
    let selectedOne = null;
    let selectedTwo = null;
    let radarChart = null;

    const $ = (id) => document.getElementById(id);
    const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
    const numberValue = (value) => {
        const numeric = Number(value);
        return Number.isFinite(numeric) ? numeric : 0;
    };

    const escapeHtml = (value) => String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');

    const initials = (name) => String(name || '')
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map(part => part[0]?.toUpperCase() || '')
        .join('') || '--';

    const displayCluster = (player) => {
        if (!player) return 'Cluster --';
        return Number(player.Cluster) === -1 ? 'Noise' : `Cluster ${player.Cluster}`;
    };

    const playerLabel = (player) => {
        if (!player) return '';
        return `${player.Player}${player.Team ? ` - ${player.Team}` : ''}`;
    };

    const isNumericMetric = (rows, key) => (
        !excludedKeys.has(key) && rows.some(row => Number.isFinite(Number(row[key])))
    );

    const getMetricKeys = (rows) => {
        if (!rows.length) return [];
        return Object.keys(rows[0]).filter(key => isNumericMetric(rows, key));
    };

    const metricMax = (key) => Math.max(1, ...players.map(player => numberValue(player[key])));
    const normalizedMetric = (player, key) => clamp((numberValue(player?.[key]) / metricMax(key)) * 100, 0, 100);

    const positionZoneMap = {
        'Goalkeeper': { left: 50, top: 88 },
        'Center-back': { left: 50, top: 72, pairOffset: 12 },
        'Left-back': { left: 20, top: 68 },
        'Right-back': { left: 80, top: 68 },
        'Left Wing Back': { left: 22, top: 58 },
        'Right Wing Back': { left: 78, top: 58 },
        'Defensive Midfielder': { left: 50, top: 58 },
        'Central Midfielder': { left: 50, top: 48 },
        'Left Midfielder': { left: 28, top: 44 },
        'Right Midfielder': { left: 72, top: 44 },
        'Attacking Midfielder': { left: 50, top: 34 },
        'Left Winger': { left: 24, top: 26 },
        'Right Winger': { left: 76, top: 26 },
        'Striker': { left: 50, top: 16 }
    };

    const pitchZoneForPlayer = (player, fallbackTop) => (
        positionZoneMap[player?.['Primary Position']] || { left: 50, top: fallbackTop }
    );

    const separateOverlappingZones = (oneZone, twoZone) => {
        const isOverlapping = Math.abs(oneZone.left - twoZone.left) < 4
            && Math.abs(oneZone.top - twoZone.top) < 4;

        if (!isOverlapping) return [oneZone, twoZone];

        const pairOffset = Math.max(oneZone.pairOffset || 10, twoZone.pairOffset || 10);

        return [
            {
                left: clamp(oneZone.left - pairOffset, 12, 88),
                top: oneZone.top
            },
            {
                left: clamp(twoZone.left + pairOffset, 12, 88),
                top: twoZone.top
            }
        ];
    };

    const categoryForMetric = (key) => (
        categoryConfig.find(category => category.patterns.some(pattern => pattern.test(key)))
        || categoryConfig.find(category => category.name === 'Possession')
    );

    const buildMetricGroups = () => {
        const groups = categoryConfig.map(category => ({
            ...category,
            metrics: []
        }));

        metricKeys.forEach(key => {
            const category = categoryForMetric(key);
            const group = groups.find(item => item.name === category.name);
            if (group) group.metrics.push(key);
        });

        return groups;
    };

    const categoryScore = (player, group) => {
        if (!player || !group.metrics.length) return 0;
        const total = group.metrics.reduce((sum, key) => sum + normalizedMetric(player, key), 0);
        return total / group.metrics.length;
    };

    const compositeForPlayer = (player) => {
        if (!player) return { label: 'Composite', value: null, formula: 'Select a player' };

        const direct = compositeDefinitions.find(definition => Number.isFinite(Number(player[definition.key])));
        if (direct) {
            return {
                label: direct.key,
                value: numberValue(player[direct.key]),
                formula: direct.formula
            };
        }

        const computed = compositeDefinitions.find(definition =>
            definition.dependencies.every(key => Number.isFinite(Number(player[key])))
        );
        if (computed) {
            return {
                label: computed.key,
                value: computed.dependencies.reduce((sum, key) => sum + numberValue(player[key]), 0),
                formula: computed.formula
            };
        }

        const groupsWithMetrics = groupedMetrics.filter(group => group.metrics.length);
        const average = groupsWithMetrics.length
            ? groupsWithMetrics.reduce((sum, group) => sum + categoryScore(player, group), 0) / groupsWithMetrics.length
            : null;

        return {
            label: 'Composite',
            value: average,
            formula: 'Average normalized category score'
        };
    };

    const findPlayer = (query) => {
        const normalized = String(query || '').trim().toLowerCase();
        if (!normalized) return null;
        return players.find(player => playerLabel(player).toLowerCase() === normalized)
            || players.find(player => String(player.Player || '').toLowerCase() === normalized)
            || players.find(player => String(player.Player || '').toLowerCase().includes(normalized));
    };

    const updateText = (id, value) => {
        const element = $(id);
        if (element) element.innerText = value;
    };

    const updatePlayerCard = (slot, player) => {
        const prefix = slot === 1 ? 'player-one' : 'player-two';
        const composite = compositeForPlayer(player);
        const value = composite.value;

        updateText(`${prefix}-initials`, initials(player?.Player));
        updateText(`${prefix}-name`, player?.Player || 'Select a player');
        updateText(`${prefix}-meta`, player
            ? `${displayCluster(player)}${player.Team ? ` - ${player.Team}` : ''}${player.League ? ` - ${player.League}` : ''}`
            : 'Cluster and team details'
        );
        updateText(`${prefix}-score`, value === null ? '--' : value.toFixed(2));
        updateText(`${prefix}-formula`, `${composite.label}: ${composite.formula}`);
        updateText(`${prefix}-confidence`, Number.isFinite(Number(player?.Cluster_Confidence))
            ? `${(Number(player.Cluster_Confidence) * 100).toFixed(1)}% cluster confidence`
            : 'Cluster confidence not available'
        );
        updateText(`${prefix}-marker-initials`, initials(player?.Player));
        updateText(`${prefix}-marker-label`, player?.Player || `Player ${slot}`);
        updateText(`${prefix}-legend`, player?.Player || `Player ${slot}`);
        updateText(`${prefix}-radar-label`, player?.Player || `Player ${slot}`);
        updateText(`${prefix}-breakdown-label`, player?.Player || `Player ${slot}`);
    };

    const updatePitchMarkers = () => {
        const oneZone = pitchZoneForPlayer(selectedOne, 33);
        const twoZone = pitchZoneForPlayer(selectedTwo, 50);
        const [visibleOneZone, visibleTwoZone] = separateOverlappingZones(oneZone, twoZone);

        const update = (markerId, zone) => {
            const marker = $(markerId);
            if (!marker) return;
            const left = zone.left;
            const top = zone.top;
            marker.style.left = `${clamp(left, 12, 88)}%`;
            marker.style.top = `${clamp(top, 12, 88)}%`;
        };

        update('player-one-marker', visibleOneZone);
        update('player-two-marker', visibleTwoZone);
    };

    const updateRelatedPlayers = () => {
        const container = $('related-player-list');
        const description = $('related-description');
        if (!container || !description) return;

        if (!selectedOne) {
            container.innerHTML = '';
            description.innerText = 'Players from the same cluster appear here after selecting a primary player.';
            return;
        }

        const related = players
            .filter(player => String(player.Cluster) === String(selectedOne.Cluster) && player.Player !== selectedOne.Player)
            .slice(0, 12);

        description.innerText = `${related.length} shown from ${displayCluster(selectedOne)}. Use search to compare with another cluster.`;
        container.innerHTML = related.map(player => `
            <button type="button"
                    class="related-player-btn px-3 py-2 rounded-lg border border-violet-100 bg-violet-50 text-xs font-semibold text-violet-700 hover:bg-violet-100"
                    data-player="${escapeHtml(player.Player)}">
                ${escapeHtml(player.Player)}
            </button>
        `).join('');

        container.querySelectorAll('.related-player-btn').forEach(button => {
            button.addEventListener('click', () => {
                selectedTwo = players.find(player => player.Player === button.dataset.player) || selectedTwo;
                $('comparison-player-search').value = playerLabel(selectedTwo);
                render();
            });
        });
    };

    const updateRadarChart = () => {
        const canvas = $('comparison-radar-chart');
        if (!canvas || !groupedMetrics.length) return;

        const radarGroups = groupedMetrics.filter(group => group.metrics.length);
        const labels = radarGroups.map(group => group.name);
        const dataOne = radarGroups.map(group => selectedOne ? categoryScore(selectedOne, group) : 0);
        const dataTwo = radarGroups.map(group => selectedTwo ? categoryScore(selectedTwo, group) : 0);

        if (radarChart) radarChart.destroy();
        radarChart = new Chart(canvas.getContext('2d'), {
            type: 'radar',
            data: {
                labels,
                datasets: [
                    {
                        label: selectedOne?.Player || 'Player 1',
                        data: dataOne,
                        borderColor: '#7c3aed',
                        backgroundColor: 'rgba(124, 58, 237, 0.16)',
                        pointBackgroundColor: '#7c3aed',
                        borderWidth: 2
                    },
                    {
                        label: selectedTwo?.Player || 'Player 2',
                        data: dataTwo,
                        borderColor: '#ba1a1a',
                        backgroundColor: 'rgba(186, 26, 26, 0.12)',
                        pointBackgroundColor: '#ba1a1a',
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            afterLabel: item => {
                                const group = radarGroups[item.dataIndex];
                                return `${group.metrics.length} metrics`;
                            },
                            label: item => `${item.dataset.label}: ${Number(item.raw).toFixed(1)}%`
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        min: 0,
                        max: 100,
                        ticks: { display: false, backdropColor: 'transparent' },
                        grid: { color: '#e2e8f0' },
                        angleLines: { color: '#e2e8f0' },
                        pointLabels: { font: { size: 12, weight: '600' } }
                    }
                }
            }
        });
    };

    const metricRow = (key) => {
        const oneValue = selectedOne ? Math.max(0, numberValue(selectedOne[key])) : 0;
        const twoValue = selectedTwo ? Math.max(0, numberValue(selectedTwo[key])) : 0;
        const total = oneValue + twoValue;
        const oneShare = total > 0 ? (oneValue / total) * 100 : 50;
        const twoShare = total > 0 ? (twoValue / total) * 100 : 50;
        return `
            <div class="group cursor-default">
                <div class="flex justify-between gap-3 text-[11px] font-bold mb-1 uppercase text-slate-400 group-hover:text-primary transition-colors">
                    <span class="min-w-0 break-words">${escapeHtml(key)}</span>
                    <div class="flex shrink-0 gap-2">
                        <span class="text-primary">${selectedOne ? numberValue(selectedOne[key]).toFixed(2) : '--'}</span>
                        <span class="text-error">${selectedTwo ? numberValue(selectedTwo[key]).toFixed(2) : '--'}</span>
                    </div>
                </div>
                <div class="flex justify-between text-[10px] font-semibold mb-1">
                    <span class="text-primary">${oneShare.toFixed(0)}%</span>
                    <span class="text-error">${twoShare.toFixed(0)}%</span>
                </div>
                <div class="relative flex h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div class="h-full bg-primary" style="width:${oneShare}%"></div>
                    <div class="h-full bg-error/50" style="width:${twoShare}%"></div>
                </div>
            </div>
        `;
    };

    const updateMetricBreakdown = () => {
        const grid = $('metric-breakdown-grid');
        if (!grid) return;

        grid.innerHTML = groupedMetrics.map(group => `
            <div>
                <div class="flex items-center gap-2 mb-4">
                    <span class="material-symbols-outlined text-primary text-sm">${group.icon}</span>
                    <h4 class="text-label-caps font-bold text-slate-500 uppercase tracking-widest">
                        ${group.name}
                        <span class="text-slate-300">(${group.metrics.length})</span>
                    </h4>
                </div>
                <div class="space-y-4">
                    ${group.metrics.length ? group.metrics.map(metricRow).join('') : '<p class="text-xs text-slate-400">No numeric metrics.</p>'}
                </div>
            </div>
        `).join('');
    };

    const render = () => {
        updatePlayerCard(1, selectedOne);
        updatePlayerCard(2, selectedTwo);
        updatePitchMarkers();
        updateRelatedPlayers();
        updateRadarChart();
        updateMetricBreakdown();
    };

    const init = () => {
        const raw = localStorage.getItem(STORAGE_KEY);
        clusterResult = raw ? JSON.parse(raw) : null;
        players = Array.isArray(clusterResult?.data) ? clusterResult.data : [];
        metricKeys = getMetricKeys(players);
        groupedMetrics = buildMetricGroups();

        if (!players.length || !metricKeys.length) {
            $('compare-empty-state')?.classList.remove('hidden');
            return;
        }

        const contextParts = [
            clusterResult.description,
            clusterResult.cluster_count ? `${clusterResult.cluster_count} clusters` : null,
            clusterResult.params?.algorithm
        ].filter(Boolean);
        updateText('compare-context', contextParts.join(' - '));

        const datalist = $('player-options');
        datalist.innerHTML = players.map(player => `<option value="${escapeHtml(playerLabel(player))}"></option>`).join('');

        selectedOne = players[0];
        selectedTwo = players.find(player => String(player.Cluster) === String(selectedOne.Cluster) && player.Player !== selectedOne.Player)
            || players[1]
            || players[0];

        $('primary-player-search').value = playerLabel(selectedOne);
        $('comparison-player-search').value = playerLabel(selectedTwo);

        $('primary-player-search').addEventListener('change', (event) => {
            selectedOne = findPlayer(event.target.value) || selectedOne;
            event.target.value = playerLabel(selectedOne);
            if (selectedTwo?.Player === selectedOne?.Player) {
                selectedTwo = players.find(player => player.Player !== selectedOne.Player) || selectedOne;
                $('comparison-player-search').value = playerLabel(selectedTwo);
            }
            render();
        });

        $('comparison-player-search').addEventListener('change', (event) => {
            selectedTwo = findPlayer(event.target.value) || selectedTwo;
            event.target.value = playerLabel(selectedTwo);
            render();
        });

        render();
    };

    document.addEventListener('DOMContentLoaded', () => {
        try {
            init();
        } catch (error) {
            console.error('Compare page initialization failed:', error);
            $('compare-empty-state')?.classList.remove('hidden');
        }
    });
})();
