/* ── Influencer Analytics Dashboard — Frontend JS ── */

const API_BASE = window.location.origin + '/api/v1';

let currentGrowthChart = null;

// ── Navigation ───────────────────────────────────
function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const el = document.getElementById(`page-${page}`);
    if (el) el.classList.add('active');
    const nav = document.getElementById(`nav-${page}`);
    if (nav) nav.classList.add('active');
}

document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
        const page = btn.dataset.page;
        showPage(page);
        if (page === 'dashboard') loadDashboard();
    });
});

// ── Format Numbers ───────────────────────────────
function fmt(n) {
    if (n === null || n === undefined) return '0';
    if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B';
    if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
    return n.toLocaleString();
}

// ── Health Check ─────────────────────────────────
async function checkHealth() {
    const dot = document.querySelector('.status-dot');
    const text = document.querySelector('.status-text');
    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        dot.className = 'status-dot online';
        text.textContent = data.youtube_configured ? 'API Connected' : 'API Key Missing';
    } catch {
        dot.className = 'status-dot offline';
        text.textContent = 'API Offline';
    }
}

// ── Dashboard ────────────────────────────────────
async function loadDashboard() {
    try {
        const res = await fetch(`${API_BASE}/dashboard`);
        const data = await res.json();

        document.getElementById('stat-profiles').textContent = data.total_profiles || 0;
        document.getElementById('stat-videos').textContent = fmt(data.total_videos || 0);
        document.getElementById('stat-comments').textContent = fmt(data.total_comments || 0);

        const grid = document.getElementById('profiles-grid');
        if (!data.profiles || data.profiles.length === 0) {
            grid.innerHTML = `<div class="empty-state glass"><div class="empty-icon">🔍</div><h3>No channels tracked yet</h3><p>Add a YouTube channel to get started</p><button class="btn btn-primary" onclick="showPage('collect')">Add Channel</button></div>`;
            return;
        }

        grid.innerHTML = data.profiles.map(p => `
            <div class="profile-card glass" onclick="loadProfile(${p.id})">
                <div class="profile-card-header">
                    ${p.profile_image_url
                        ? `<img class="profile-avatar" src="${p.profile_image_url}" alt="${p.display_name}">`
                        : `<div class="profile-avatar-placeholder">${(p.display_name || '?')[0]}</div>`}
                    <div class="profile-info">
                        <h3>${p.display_name || p.username}</h3>
                        <span class="handle">@${p.username}</span>
                    </div>
                </div>
                <div class="profile-stats">
                    <div class="profile-stat"><div class="profile-stat-value">${fmt(p.subscribers)}</div><div class="profile-stat-label">Subscribers</div></div>
                    <div class="profile-stat"><div class="profile-stat-value">${fmt(p.total_views)}</div><div class="profile-stat-label">Views</div></div>
                    <div class="profile-stat"><div class="profile-stat-value">${fmt(p.video_count)}</div><div class="profile-stat-label">Videos</div></div>
                </div>
            </div>
        `).join('');

        const compareSelect = document.getElementById('compare-select');
        if (compareSelect) {
            compareSelect.innerHTML = data.profiles.map(p => `<option value="${p.id}">${p.display_name || p.username}</option>`).join('');
        }
    } catch (e) { console.error('Dashboard load error:', e); }
}

// ── Collect Channel ──────────────────────────────
async function collectChannel() {
    const url = document.getElementById('channel-url').value.trim();
    if (!url) return;

    const btn = document.getElementById('btn-collect');
    const progress = document.getElementById('collect-progress');
    const result = document.getElementById('collect-result');
    const fill = document.getElementById('progress-fill');
    const text = document.getElementById('progress-text');

    btn.disabled = true;
    btn.querySelector('.btn-text').style.display = 'none';
    btn.querySelector('.btn-loader').style.display = 'inline';
    progress.style.display = 'block';
    result.style.display = 'none';

    // Animate progress
    let pct = 0;
    const interval = setInterval(() => {
        pct = Math.min(pct + Math.random() * 8, 90);
        fill.style.width = pct + '%';
        if (pct < 20) text.textContent = 'Resolving channel...';
        else if (pct < 40) text.textContent = 'Fetching channel data...';
        else if (pct < 60) text.textContent = 'Collecting videos...';
        else if (pct < 80) text.textContent = 'Analyzing comments & sentiment...';
        else text.textContent = 'Calculating metrics...';
    }, 500);

    try {
        const res = await fetch(`${API_BASE}/collect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });
        clearInterval(interval);
        fill.style.width = '100%';

        const data = await res.json();
        if (res.ok) {
            text.textContent = 'Collection complete!';
            result.style.display = 'block';
            result.className = 'collect-result result-success';
            result.innerHTML = `<strong>✅ ${data.message}</strong><br><span style="color:var(--text-secondary);">${data.videos_collected} videos · ${data.comments_collected} comments collected</span><br><button class="btn btn-primary" style="margin-top:12px" onclick="loadProfile(${data.profile_id})">View Profile →</button>`;
        } else {
            text.textContent = 'Collection failed';
            result.style.display = 'block';
            result.className = 'collect-result result-error';
            result.innerHTML = `<strong>❌ Error:</strong> ${data.detail || 'Unknown error'}`;
        }
    } catch (e) {
        clearInterval(interval);
        result.style.display = 'block';
        result.className = 'collect-result result-error';
        result.innerHTML = `<strong>❌ Network error:</strong> ${e.message}`;
    }

    btn.disabled = false;
    btn.querySelector('.btn-text').style.display = 'inline';
    btn.querySelector('.btn-loader').style.display = 'none';
}

// ── Profile Detail ───────────────────────────────
async function loadProfile(id) {
    showPage('profile');
    document.getElementById('nav-profile').style.display = 'flex';
    const content = document.getElementById('profile-content');
    content.innerHTML = '<p style="color:var(--text-secondary)">Loading profile...</p>';

    try {
        const [profile, posts, growth, engagement, hashtags, sentiment, score, topViews, topComments, categories, anomalies] = await Promise.all([
            fetch(`${API_BASE}/profiles/${id}`).then(r => r.json()),
            fetch(`${API_BASE}/profiles/${id}/posts?limit=20`).then(r => r.json()),
            fetch(`${API_BASE}/profiles/${id}/growth`).then(r => r.json()),
            fetch(`${API_BASE}/profiles/${id}/engagement`).then(r => r.json()),
            fetch(`${API_BASE}/profiles/${id}/hashtags`).then(r => r.json()),
            fetch(`${API_BASE}/profiles/${id}/sentiment`).then(r => r.json()),
            fetch(`${API_BASE}/profiles/${id}/score`).then(r => r.json()),
            fetch(`${API_BASE}/profiles/${id}/posts?limit=10&sort_by=views`).then(r => r.json()),
            fetch(`${API_BASE}/profiles/${id}/posts?limit=10&sort_by=comments_count`).then(r => r.json()),
            fetch(`${API_BASE}/profiles/${id}/categories`).then(r => r.json()),
            fetch(`${API_BASE}/profiles/${id}/anomalies`).then(r => r.json()),
        ]);

        window.currentProfileGrowth = growth; // Save for rendering chart when tab becomes active
        window.currentProfileCategories = categories; // Save for category chart

        const tierClass = (score.tier || 'new').toLowerCase().replace(' ', '-');

        content.innerHTML = `
            <!-- Header -->
            <div class="profile-detail-header glass">
                ${profile.profile_image_url ? `<img class="profile-detail-avatar" src="${profile.profile_image_url}" alt="">` : `<div class="profile-avatar-placeholder" style="width:96px;height:96px;font-size:36px;">${(profile.display_name||'?')[0]}</div>`}
                <div class="profile-detail-info">
                    <h2>${profile.display_name || profile.username} <span class="tier-badge tier-${tierClass}">${score.tier}</span></h2>
                    <div class="handle">@${profile.username} · ${profile.platform}</div>
                    <div class="bio">${(profile.bio || '').substring(0, 200)}</div>
                </div>
            </div>

            ${anomalies.fake_follower_risk === 'High' ? `
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px; margin-bottom: 24px; display: flex; align-items: flex-start; gap: 12px;">
                <div style="font-size: 24px;">⚠️</div>
                <div>
                    <h3 style="color: #fca5a5; margin-bottom: 4px; font-size: 16px; margin-top: 0;">High Fake Follower Risk Detected</h3>
                    <ul style="color: rgba(255,255,255,0.8); margin: 0; padding-left: 20px; font-size: 14px;">
                        ${anomalies.fake_follower_flags.map(f => `<li>${f}</li>`).join('')}
                    </ul>
                </div>
            </div>
            ` : ''}

            <!-- KPIs -->
            <div class="kpi-grid">
                <div class="kpi-card glass"><div class="kpi-value gradient">${fmt(profile.subscribers)}</div><div class="kpi-label">Subscribers</div></div>
                <div class="kpi-card glass"><div class="kpi-value gradient">${fmt(profile.total_views)}</div><div class="kpi-label">Total Views</div></div>
                <div class="kpi-card glass"><div class="kpi-value gradient">${fmt(profile.video_count)}</div><div class="kpi-label">Videos</div></div>
                <div class="kpi-card glass"><div class="kpi-value gradient">${score.overall_score}</div><div class="kpi-label">Influence Score</div></div>
                <div class="kpi-card glass"><div class="kpi-value gradient">${engagement.length ? engagement[0].engagement_rate.toFixed(2) + '%' : 'N/A'}</div><div class="kpi-label">Engagement Rate</div></div>
            </div>

            <!-- Tabs -->
            <div class="tabs">
                <button class="tab active" onclick="switchTab('tab-videos', this)">Videos</button>
                <button class="tab" onclick="switchTab('tab-top-videos', this)">Top Videos</button>
                <button class="tab" onclick="switchTab('tab-growth', this)">Growth</button>
                <button class="tab" onclick="switchTab('tab-sentiment', this)">Sentiment</button>
                <button class="tab" onclick="switchTab('tab-hashtags', this)">Hashtags</button>
                <button class="tab" onclick="switchTab('tab-categories', this)">Categories</button>
                <button class="tab" onclick="switchTab('tab-score', this)">Score</button>
                <button class="tab" onclick="switchTab('tab-insights', this)">Insights 🚀</button>
            </div>

            <!-- Videos Tab -->
            <div class="tab-content active" id="tab-videos">
                <div class="section">
                    <h3 class="section-title">Recent Videos</h3>
                    <div style="overflow-x:auto;">
                        <table class="data-table">
                            <thead><tr><th></th><th>Title</th><th>Views</th><th>Likes</th><th>Comments</th><th>Type</th><th>Engagement</th></tr></thead>
                            <tbody>${posts.map(p => `<tr>
                                <td>${p.thumbnail_url ? `<img class="video-thumb" src="${p.thumbnail_url}" alt="">` : ''}</td>
                                <td><a href="${p.url}" target="_blank" style="color:var(--text-primary)">${p.title.substring(0,60)}${p.title.length > 60 ? '...' : ''}</a></td>
                                <td>${fmt(p.views)}</td><td>${fmt(p.likes)}</td><td>${fmt(p.comments_count)}</td>
                                <td><span style="text-transform:capitalize">${p.content_type || 'video'}</span></td>
                                <td>${p.engagement_rate ? p.engagement_rate.toFixed(2) + '%' : 'N/A'}</td>
                            </tr>`).join('')}</tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Top Videos Tab -->
            <div class="tab-content" id="tab-top-videos">
                <div class="section" style="display: flex; gap: 24px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 300px;">
                        <h3 class="section-title">Top 10 by Views</h3>
                        <div class="glass" style="padding: 16px;">
                            ${topViews.map((p, i) => `
                                <div style="display: flex; gap: 12px; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--border-glass);">
                                    <div style="font-size: 20px; font-weight: 800; color: var(--accent-primary); width: 24px;">${i+1}</div>
                                    ${p.thumbnail_url ? `<img src="${p.thumbnail_url}" style="width: 60px; height: 34px; border-radius: 4px; object-fit: cover;">` : ''}
                                    <div style="flex: 1; overflow: hidden;">
                                        <div style="font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"><a href="${p.url}" target="_blank" style="color:var(--text-primary)">${p.title}</a></div>
                                        <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">👁️ ${fmt(p.views)} views</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div style="flex: 1; min-width: 300px;">
                        <h3 class="section-title">Top 10 by Comments</h3>
                        <div class="glass" style="padding: 16px;">
                            ${topComments.map((p, i) => `
                                <div style="display: flex; gap: 12px; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--border-glass);">
                                    <div style="font-size: 20px; font-weight: 800; color: var(--accent-primary); width: 24px;">${i+1}</div>
                                    ${p.thumbnail_url ? `<img src="${p.thumbnail_url}" style="width: 60px; height: 34px; border-radius: 4px; object-fit: cover;">` : ''}
                                    <div style="flex: 1; overflow: hidden;">
                                        <div style="font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"><a href="${p.url}" target="_blank" style="color:var(--text-primary)">${p.title}</a></div>
                                        <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">💬 ${fmt(p.comments_count)} comments</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Growth Tab -->
            <div class="tab-content" id="tab-growth">
                <div class="section">
                    <h3 class="section-title">Subscriber Growth</h3>
                    <div class="glass" style="padding: 24px; height: 400px; position: relative;">
                        <canvas id="growthChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Sentiment Tab -->
            <div class="tab-content" id="tab-sentiment">
                <div class="section">
                    <h3 class="section-title">Comment Sentiment Analysis</h3>
                    <div class="glass" style="padding:24px;">
                        <div class="sentiment-bar-container">
                            <div class="sentiment-segment sentiment-positive" style="width:${sentiment.positive_pct || 0}%">${sentiment.positive_pct ? sentiment.positive_pct.toFixed(0) + '%' : ''}</div>
                            <div class="sentiment-segment sentiment-neutral" style="width:${sentiment.neutral_pct || 0}%">${sentiment.neutral_pct ? sentiment.neutral_pct.toFixed(0) + '%' : ''}</div>
                            <div class="sentiment-segment sentiment-negative" style="width:${sentiment.negative_pct || 0}%">${sentiment.negative_pct ? sentiment.negative_pct.toFixed(0) + '%' : ''}</div>
                        </div>
                        <div class="sentiment-legend">
                            <div class="legend-item"><div class="legend-dot" style="background:var(--success)"></div>Positive: ${sentiment.positive_count || 0}</div>
                            <div class="legend-item"><div class="legend-dot" style="background:var(--warning)"></div>Neutral: ${sentiment.neutral_count || 0}</div>
                            <div class="legend-item"><div class="legend-dot" style="background:var(--danger)"></div>Negative: ${sentiment.negative_count || 0}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Hashtags Tab -->
            <div class="tab-content" id="tab-hashtags">
                <div class="section">
                    <h3 class="section-title">Top Hashtags</h3>
                    <div class="hashtag-cloud">${hashtags.map(h => `<span class="hashtag-tag">#${h.tag}<span class="freq">×${h.frequency}</span></span>`).join('')}</div>
                    ${hashtags.length === 0 ? '<p style="color:var(--text-muted)">No hashtags found in video titles/descriptions.</p>' : ''}
                </div>
            </div>

            <!-- Categories Tab -->
            <div class="tab-content" id="tab-categories">
                <div class="section">
                    <h3 class="section-title">Content Categories</h3>
                    <div class="glass" style="padding: 24px; height: 400px; position: relative; display: flex; justify-content: center;">
                        <canvas id="categoryChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Score Tab -->
            <div class="tab-content" id="tab-score">
                <div class="section">
                    <h3 class="section-title">Influence Score Breakdown</h3>
                    <div class="score-container glass">
                        <div class="score-circle" style="--score:${score.overall_score}">
                            <span class="score-number">${score.overall_score}</span>
                        </div>
                        <div class="score-breakdown">
                            ${Object.entries(score.breakdown || {}).map(([k, v]) => `
                                <div class="score-factor">
                                    <span class="score-factor-label">${k.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                                    <div class="score-factor-bar"><div class="score-factor-fill" style="width:${v.score}%"></div></div>
                                    <span class="score-factor-value">${v.score}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Insights Tab -->
            <div class="tab-content" id="tab-insights">
                <div class="section" style="display: flex; gap: 24px; flex-wrap: wrap;">
                    
                    <div style="flex: 1; min-width: 300px;">
                        <h3 class="section-title">🚀 Viral Spikes Detected</h3>
                        ${anomalies.viral_posts.length === 0 ? '<p style="color:var(--text-muted)">No recent viral posts detected against the baseline.</p>' : ''}
                        <div style="display: flex; flex-direction: column; gap: 16px;">
                            ${anomalies.viral_posts.map(p => `
                                <div class="glass" style="padding: 16px; border-left: 4px solid var(--success);">
                                    <h4 style="margin: 0 0 8px 0; color: var(--text-primary); font-size: 15px;"><a href="https://youtube.com/watch?v=${p.video_id}" target="_blank" style="color: inherit; text-decoration: none;">${p.title}</a></h4>
                                    <div style="display: flex; gap: 16px; font-size: 13px;">
                                        <div style="color: var(--success); font-weight: 600;">🔥 ${p.multiplier}x Multiplier</div>
                                        <div style="color: var(--text-secondary);">Actual Views: <span style="color: var(--text-primary);">${fmt(p.views)}</span></div>
                                        <div style="color: var(--text-secondary);">Expected: <span style="color: var(--text-primary);">${fmt(p.expected_views)}</span></div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <div style="flex: 1; min-width: 300px;">
                        <h3 class="section-title">📊 Follower Growth Anomalies</h3>
                        ${anomalies.suspicious_growth_spikes.length === 0 ? '<p style="color:var(--text-muted)">No mathematically improbable growth spikes detected.</p>' : ''}
                        <div style="display: flex; flex-direction: column; gap: 16px;">
                            ${anomalies.suspicious_growth_spikes.map(s => `
                                <div class="glass" style="padding: 16px; border-left: 4px solid var(--warning);">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                        <span style="font-weight: 600; color: var(--text-primary);">${new Date(s.date).toLocaleDateString()}</span>
                                        <span style="background: rgba(245, 158, 11, 0.2); color: #fcd34d; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">+${s.percentage_jump}% Jump</span>
                                    </div>
                                    <div style="color: var(--text-secondary); font-size: 13px;">
                                        Jumped from <strong style="color: var(--text-primary);">${fmt(s.old_subscribers)}</strong> to <strong style="color: var(--text-primary);">${fmt(s.new_subscribers)}</strong> in a single day.
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <div style="flex: 1; min-width: 300px;">
                        <h3 class="section-title">📉 Follower Drops</h3>
                        ${(anomalies.follower_drops || []).length === 0 ? '<p style="color:var(--text-muted)">No significant follower drops detected.</p>' : ''}
                        <div style="display: flex; flex-direction: column; gap: 16px;">
                            ${(anomalies.follower_drops || []).map(d => `
                                <div class="glass" style="padding: 16px; border-left: 4px solid var(--danger);">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                        <span style="font-weight: 600; color: var(--text-primary);">${new Date(d.date).toLocaleDateString()}</span>
                                        <span style="background: rgba(239, 68, 68, 0.2); color: #fca5a5; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">▼ ${d.percentage_drop}% Drop</span>
                                    </div>
                                    <div style="color: var(--text-secondary); font-size: 13px;">
                                        Dropped from <strong style="color: var(--text-primary);">${fmt(d.old_subscribers)}</strong> to <strong style="color: var(--text-primary);">${fmt(d.new_subscribers)}</strong> — lost <strong style="color: #fca5a5;">${fmt(d.lost_count)}</strong> subscribers.
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                </div>
            </div>
        `;
    } catch (e) {
        content.innerHTML = `<div class="collect-result result-error"><strong>Error loading profile:</strong> ${e.message}</div>`;
    }

    // We now render the chart inside switchTab() when the Growth tab becomes active.
    // This fixes a Chart.js bug where it renders at 0x0 size if the container has display:none.
}

function renderGrowthChart(growthData) {
    const ctx = document.getElementById('growthChart');
    if (!ctx) return;
    
    if (currentGrowthChart) {
        currentGrowthChart.destroy();
    }
    
    if (!growthData || growthData.length === 0) {
        return;
    }
    
    let chartData = [...growthData];
    if (chartData.length === 1) {
        // Create a dummy point 24h ago to draw a flat line instead of a single dot
        const dummy = { ...chartData[0] };
        dummy.timestamp = new Date(new Date(dummy.timestamp).getTime() - 86400000).toISOString();
        chartData.unshift(dummy);
    }

    // Sort by timestamp ascending
    const sorted = chartData.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    const labels = sorted.map(d => {
        const date = new Date(d.timestamp);
        return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    });
    
    const data = sorted.map(d => d.subscribers);

    currentGrowthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Subscribers',
                data: data,
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#0a0e1a',
                pointBorderColor: '#6366f1',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.9)',
                    titleFont: { size: 14, family: "'Inter', sans-serif" },
                    bodyFont: { size: 14, family: "'Inter', sans-serif" },
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return fmt(context.raw) + ' Subscribers';
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
                    ticks: { color: '#94a3b8', font: { family: "'Inter', sans-serif" } }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
                    ticks: {
                        color: '#94a3b8',
                        font: { family: "'Inter', sans-serif" },
                        callback: function(value) { return fmt(value); }
                    }
                }
            }
        }
    });
}

function switchTab(tabId, btn) {
    btn.closest('.tabs').querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    const parent = btn.closest('.page');
    parent.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    parent.querySelector(`#${tabId}`).classList.add('active');

    // Render chart only when the tab becomes visible to prevent 0x0 size bugs
    if (tabId === 'tab-growth' && window.currentProfileGrowth) {
        renderGrowthChart(window.currentProfileGrowth);
    }
    if (tabId === 'tab-categories' && window.currentProfileCategories) {
        renderCategoryChart(window.currentProfileCategories);
    }
}

function clearProfileState() {
    currentProfileGrowth = null;
    currentProfileCategories = null;
}

// ── Competitive Analysis ───────────────────────────
let compareEngagementChart = null;
let compareSovChart = null;

async function runComparison() {
    const select = document.getElementById('compare-select');
    const selectedOptions = Array.from(select.selectedOptions).map(opt => parseInt(opt.value));
    
    if (selectedOptions.length < 2) {
        alert('Please select at least 2 influencers to compare.');
        return;
    }
    if (selectedOptions.length > 5) {
        alert('Please select maximum 5 influencers for a clean comparison.');
        return;
    }

    const btn = document.getElementById('btn-run-compare');
    btn.textContent = 'Analyzing...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/compare`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_ids: selectedOptions })
        });
        const data = await res.json();
        
        document.getElementById('compare-results').style.display = 'flex';
        renderCompareTable(data);
        renderCompareCharts(data);

    } catch (e) {
        console.error('Comparison error:', e);
        alert('Failed to run comparison.');
    } finally {
        btn.textContent = 'Analyze';
        btn.disabled = false;
    }
}

function renderCompareTable(data) {
    const head = document.getElementById('compare-table-head');
    const body = document.getElementById('compare-table-body');
    
    head.innerHTML = `<th style="padding: 12px; color: var(--text-secondary);">Metric</th>` + data.profiles.map(p => `<th style="padding: 12px;">${p.display_name}</th>`).join('');
    
    const rows = [
        { label: 'Subscribers', key: 'subscribers', fmt: fmt },
        { label: 'Total Views', key: 'total_views', fmt: fmt },
        { label: 'Videos', key: 'video_count', fmt: fmt },
        { label: 'Engagement Rate', key: 'engagement_rate', fmt: v => v.toFixed(2) + '%' },
        { label: 'Influence Score', key: 'influence_score', fmt: v => v.toFixed(1) }
    ];

    body.innerHTML = rows.map(r => `
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
            <td style="padding: 12px; color: var(--text-secondary);">${r.label}</td>
            ${data.profiles.map(p => `<td style="padding: 12px; font-weight: 500;">${r.fmt(p[r.key])}</td>`).join('')}
        </tr>
    `).join('');
}

function renderCompareCharts(data) {
    const colors = [
        'rgba(99, 102, 241, 0.8)', // Indigo
        'rgba(236, 72, 153, 0.8)', // Pink
        'rgba(16, 185, 129, 0.8)', // Emerald
        'rgba(245, 158, 11, 0.8)', // Amber
        'rgba(139, 92, 246, 0.8)'  // Violet
    ];

    // Engagement Chart
    const engCtx = document.getElementById('compareEngagementChart');
    if (compareEngagementChart) compareEngagementChart.destroy();

    compareEngagementChart = new Chart(engCtx, {
        type: 'bar',
        data: {
            labels: data.profiles.map(p => p.display_name),
            datasets: [
                {
                    type: 'line',
                    label: 'Niche Benchmark',
                    data: data.profiles.map(() => data.benchmark_engagement_rate),
                    borderColor: 'rgba(255, 255, 255, 0.6)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                },
                {
                    type: 'bar',
                    label: 'Engagement Rate (%)',
                    data: data.profiles.map(p => p.engagement_rate),
                    backgroundColor: data.profiles.map((_, i) => colors[i % colors.length]),
                    borderWidth: 1,
                    borderColor: data.profiles.map((_, i) => colors[i % colors.length].replace('0.8', '1'))
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: 'rgba(255, 255, 255, 0.7)' } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            if (ctx.dataset.type === 'line') return `Benchmark: ${ctx.raw.toFixed(2)}%`;
                            return `Engagement: ${ctx.raw.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: 'rgba(255, 255, 255, 0.5)' } },
                x: { grid: { display: false }, ticks: { color: 'rgba(255, 255, 255, 0.5)' } }
            }
        }
    });

    // SOV Stacked Bar Chart
    const sovCtx = document.getElementById('compareSovChart');
    if (compareSovChart) compareSovChart.destroy();

    const labels = data.sov_data.map(d => d.tag);
    const datasets = data.profiles.map((p, i) => {
        return {
            label: p.display_name,
            data: data.sov_data.map(d => d.distribution[p.profile_id] || 0),
            backgroundColor: colors[i % colors.length]
        };
    });

    compareSovChart = new Chart(sovCtx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: 'rgba(255, 255, 255, 0.7)' } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.raw}%`
                    }
                }
            },
            scales: {
                x: { stacked: true, grid: { display: false }, ticks: { color: 'rgba(255, 255, 255, 0.5)' } },
                y: { stacked: true, max: 100, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: 'rgba(255, 255, 255, 0.5)', callback: v => v + '%' } }
            }
        }
    });
}

let currentCategoryChart = null;

function renderCategoryChart(categoryData) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;
    
    if (currentCategoryChart) {
        currentCategoryChart.destroy();
    }
    
    if (!categoryData || categoryData.length === 0) {
        return;
    }
    
    const labels = categoryData.map(d => d.category);
    const data = categoryData.map(d => d.percentage);
    
    // Generate some vibrant colors for the pie chart
    const bgColors = [
        'rgba(99, 102, 241, 0.8)', // Indigo
        'rgba(236, 72, 153, 0.8)', // Pink
        'rgba(16, 185, 129, 0.8)', // Emerald
        'rgba(245, 158, 11, 0.8)', // Amber
        'rgba(139, 92, 246, 0.8)', // Violet
        'rgba(59, 130, 246, 0.8)', // Blue
        'rgba(239, 68, 68, 0.8)',  // Red
        'rgba(20, 184, 166, 0.8)', // Teal
        'rgba(249, 115, 22, 0.8)'  // Orange
    ];
    const borderColors = bgColors.map(c => c.replace('0.8', '1'));

    currentCategoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: bgColors,
                borderColor: borderColors,
                borderWidth: 2,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#94a3b8', font: { family: "'Inter', sans-serif" } }
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.9)',
                    titleFont: { size: 14, family: "'Inter', sans-serif" },
                    bodyFont: { size: 14, family: "'Inter', sans-serif" },
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.raw + '%';
                        }
                    }
                }
            },
            cutout: '65%'
        }
    });
}

// ── Init ─────────────────────────────────────────
checkHealth();
loadDashboard();

// Enter key support
document.getElementById('channel-url').addEventListener('keydown', e => {
    if (e.key === 'Enter') collectChannel();
});
