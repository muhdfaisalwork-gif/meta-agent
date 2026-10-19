function showBanner(msg) {
    const b = document.getElementById('status-banner');
    const t = document.getElementById('status-banner-text');
    if (b && t) {
        t.textContent = msg;
        b.classList.remove('hidden');
    }
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
    const target = document.getElementById(`tab-${tabId}`);
    if (target) target.classList.remove('hidden');

    document.querySelectorAll('.sidebar-btn').forEach(btn => {
        btn.classList.remove('bg-dark-700', 'border', 'border-dark-600', 'text-slate-100');
        btn.classList.add('text-slate-400');
    });
    const activeBtn = document.getElementById(`tab-btn-${tabId}`);
    if (activeBtn) {
        activeBtn.classList.add('bg-dark-700', 'border', 'border-dark-600', 'text-slate-100');
        activeBtn.classList.remove('text-slate-400');
    }

    if (tabId === 'sheet') loadSheetRows();
    if (tabId === 'comments') loadCommentsLog();
    if (tabId === 'brain') loadBrainData();
    if (tabId === 'seo') {
        loadSeoAudit();
        loadLaunchPack();
    }
}

async function loadSeoAudit() {
    try {
        const res = await fetch('/api/seo/audit');
        const data = await res.json();
        document.getElementById('seo-score-val').textContent = `${data.score}/100`;
        document.getElementById('seo-grade-badge').textContent = `Grade ${data.grade}`;
        document.getElementById('seo-gh-cmd').textContent = data.gh_cli_command || '';
        const box = document.getElementById('seo-checklist-box');
        box.innerHTML = (data.checklist || []).map(item => `
            <div class="flex items-center justify-between bg-dark-900 border border-dark-700 px-3.5 py-2 rounded-xl">
                <div>
                    <strong class="text-slate-200">${item.item}</strong>
                    <span class="text-slate-400 ml-2">${item.note}</span>
                </div>
                <span class="px-2 py-0.5 rounded-full text-[11px] font-mono ${item.status === 'pass' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'}">${item.status.toUpperCase()}</span>
            </div>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}

async function installCommunityFiles() {
    const res = await fetch('/api/seo/install-community-files', { method: 'POST' });
    const data = await res.json();
    showBanner(data.message);
    loadSeoAudit();
}

async function applyOptimizedReadme() {
    const res = await fetch('/api/seo/optimize-readme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apply: true })
    });
    const data = await res.json();
    showBanner(`Optimized README.md written to disk (${data.byte_count} bytes)!`);
    loadSeoAudit();
}

async function loadLaunchPack() {
    const channel = document.getElementById('seo-launch-channel').value;
    const res = await fetch('/api/seo/launch-pack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel })
    });
    const data = await res.json();
    document.getElementById('seo-launch-output').textContent = (data.packs && data.packs[channel]) || '';
}

async function loadSystemStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();

        const igOk = data.auth?.instagram_authenticated;
        const fbOk = data.auth?.facebook_authenticated;
        document.getElementById('ig-auth-dot').className = `w-2 h-2 rounded-full ${igOk ? 'bg-emerald-400' : 'bg-amber-400'}`;
        document.getElementById('ig-auth-label').textContent = igOk ? 'Connected' : 'Local Mode';
        document.getElementById('fb-auth-dot').className = `w-2 h-2 rounded-full ${fbOk ? 'bg-emerald-400' : 'bg-amber-400'}`;
        document.getElementById('fb-auth-label').textContent = fbOk ? 'Connected' : 'Local Mode';

        document.getElementById('active-llm-badge').textContent = `${data.llm?.active_provider}/${data.llm?.current_model}`;

        const g = data.guardrails || {};
        document.getElementById('stat-reels-cap').textContent = `${g.reels_published_today || 0} / ${g.max_reels_per_day || 5}`;
        document.getElementById('stat-comments-cap').textContent = `${g.comments_posted_today || 0} / ${g.max_comments_per_session || 20}`;

        const ms = data.master_sheet || {};
        document.getElementById('card-total-videos').textContent = ms.total_videos || 0;
        document.getElementById('card-downloaded-videos').textContent = ms.downloaded || 0;
        document.getElementById('card-ready-videos').textContent = ms.ready_to_post || 0;
        document.getElementById('card-published-videos').textContent = ms.published || 0;
    } catch (e) {
        console.error('Status check failed:', e);
    }
}

async function loadMusicLibrary() {
    try {
        const res = await fetch('/api/music');
        const data = await res.json();
        const selects = document.querySelectorAll('.music-select');
        selects.forEach(sel => {
            sel.innerHTML = '';
            (data.tracks || []).forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.name;
                opt.textContent = `${t.name} (${t.size_kb} KB)`;
                sel.appendChild(opt);
            });
        });
    } catch (e) {
        console.error(e);
    }
}

async function loadSheetRows() {
    try {
        const res = await fetch('/api/sheet');
        const data = await res.json();
        const tbody = document.getElementById('sheet-table-body');
        const rows = data.rows || [];
        if (rows.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="py-8 text-center text-slate-400">No saved videos in sheet yet. Click "Run Full Autonomous Cycle" or go to "02 Saved & yt-dlp" to extract!</td></tr>`;
            return;
        }
        tbody.innerHTML = rows.map(r => {
            const badgeColor = r.repost_status === 'Published'
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                : (r.repost_status === 'Ready to Post' ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' : 'bg-amber-500/20 text-amber-300 border-amber-500/30');
            const mp4File = (r.ready_mp4_path || r.local_mp4_path || '').split(/[\\/]/).pop();
            return `
                <tr class="hover:bg-dark-700/40 transition">
                    <td class="py-3 px-4 font-mono font-bold text-slate-300">#${r.id}</td>
                    <td class="py-3 px-4 font-semibold">${r.platform}</td>
                    <td class="py-3 px-4 max-w-xs truncate" title="${(r.video_name_hook || '').replace(/"/g, '&quot;')}">${r.video_name_hook}</td>
                    <td class="py-3 px-4 font-mono text-slate-400">${r.creator_handle}</td>
                    <td class="py-3 px-4 text-purple-300">${r.music_used}</td>
                    <td class="py-3 px-4 font-mono text-slate-400 text-[11px]">${mp4File || 'N/A'}</td>
                    <td class="py-3 px-4"><span class="px-2.5 py-0.5 rounded-full text-[11px] border ${badgeColor}">${r.repost_status}</span></td>
                    <td class="py-3 px-4 space-x-1.5">
                        <button onclick="quickMixRow(${r.id})" class="bg-purple-600/30 hover:bg-purple-600 text-purple-200 px-2.5 py-1 rounded-lg text-[11px] transition">Mix MP3</button>
                        <button onclick="quickPublishRow(${r.id}, '${r.platform}')" class="bg-emerald-600/30 hover:bg-emerald-600 text-emerald-200 px-2.5 py-1 rounded-lg text-[11px] transition">Publish</button>
                    </td>
                </tr>
            `;
        }).join('');
        loadSystemStatus();
    } catch (e) {
        console.error(e);
    }
}

async function quickMixRow(videoId) {
    showBanner(`Mixing Video #${videoId} with local MP3 (20% original / 85% music) via FFmpeg...`);
    const res = await fetch('/api/mixer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: 'a', video_id: videoId })
    });
    const data = await res.json();
    showBanner(`Mixed Video #${videoId} -> ${data.output_path || data.message}`);
    loadSheetRows();
}

async function quickPublishRow(videoId, platform) {
    showBanner(`Publishing Video #${videoId} to ${platform}...`);
    const res = await fetch('/api/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform, video_id: videoId })
    });
    const data = await res.json();
    showBanner(`${platform} Publish Complete! Posted URL: ${data.posted_url || data.message}`);
    loadSheetRows();
}

async function extractSingleUrl() {
    const url = document.getElementById('extract-url-input').value.trim() || 'https://www.instagram.com/reel/C8CustomMetaReel/';
    const platform = document.getElementById('extract-platform-select').value;
    showBanner(`Extracting ${url} via yt-dlp and updating saved_videos_log.xlsx...`);
    const res = await fetch('/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, platform })
    });
    const data = await res.json();
    showBanner(`Extracted & Downloaded! Added Row #${data.record?.id || ''} to saved_videos_log.xlsx.`);
    switchTab('sheet');
}

async function scrapeSavedCollection(platform) {
    showBanner(`Running 02_saved_extractor.py for ${platform}...`);
    const res = await fetch('/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform, max_items: 3 })
    });
    const data = await res.json();
    showBanner(`Processed ${data.processed_count || 0} saved videos into saved_videos_log.xlsx!`);
    switchTab('sheet');
}

async function runScenarioA() {
    const videoId = parseInt(document.getElementById('mix-a-video-id').value || '1', 10);
    const mp3Name = document.getElementById('mix-a-mp3').value;
    showBanner(`Running Scenario A (20% Video Audio + 85% ${mp3Name})...`);
    const res = await fetch('/api/mixer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: 'a', video_id: videoId, mp3_name: mp3Name })
    });
    const data = await res.json();
    showBanner(`Scenario A Complete: ${data.output_path || data.message}`);
    loadSheetRows();
}

async function runScenarioB() {
    const hookText = document.getElementById('mix-b-hook').value;
    const mp3Name = document.getElementById('mix-b-mp3').value;
    showBanner(`Rendering 15s 1080x1920 9:16 Reel from visual card + ${mp3Name}...`);
    const res = await fetch('/api/mixer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: 'b', hook_text: hookText, mp3_name: mp3Name, duration_sec: 15 })
    });
    const data = await res.json();
    showBanner(`Scenario B 15s Reel Created: ${data.output_path || data.message}`);
    loadSystemStatus();
}

async function runScenarioC() {
    const videoId = parseInt(document.getElementById('mix-c-video-id').value || '1', 10);
    const song = document.getElementById('mix-c-song').value;
    const res = await fetch('/api/mixer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: 'c', video_id: videoId, native_song: song })
    });
    const data = await res.json();
    showBanner(`Flagged Row #${videoId} with ${data.music_used}!`);
    loadSheetRows();
}

async function draftMetaCaption() {
    const topic = document.getElementById('pub-topic').value;
    const platform = document.getElementById('pub-platform').value;
    showBanner(`Drafting 82-Rule Humanized ${platform} caption...`);
    const res = await fetch('/api/caption/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic_or_title: topic, platform })
    });
    const data = await res.json();
    document.getElementById('pub-caption-box').value = data.caption || '';
    showBanner(`Caption generated via ${data.provider}/${data.model_used} (AI Tells: ${data.audit?.ai_tell_count || 0}).`);
}

async function publishReel(platform) {
    const videoId = parseInt(document.getElementById('pub-video-id').value || '1', 10);
    const caption = document.getElementById('pub-caption-box').value;
    showBanner(`Running ${platform} UI Publisher for Row #${videoId}...`);
    const res = await fetch('/api/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform, video_id: videoId, caption })
    });
    const data = await res.json();
    document.getElementById('pub-execution-log').textContent = JSON.stringify(data, null, 2);
    showBanner(`${platform} Reel Published! Sheet updated.`);
    loadSystemStatus();
}

async function runCommentEngine(mode) {
    const platform = document.getElementById('com-platform').value;
    const author = document.getElementById('com-author').value;
    const commentText = document.getElementById('com-incoming').value;
    const hashtag = document.getElementById('com-hashtag').value;
    showBanner(`Running Phase 5 Comment Engine (${mode}) on ${platform}...`);
    await fetch('/api/comments/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            platform,
            mode,
            author_name: author,
            comment_text: commentText,
            hashtag_or_topic: hashtag
        })
    });
    showBanner(`Comment action completed with 50-90ms human typing simulation!`);
    loadCommentsLog();
    loadSystemStatus();
}

async function loadCommentsLog() {
    const res = await fetch('/api/comments/log');
    const data = await res.json();
    const container = document.getElementById('comments-log-list');
    const list = data.comments || [];
    if (list.length === 0) {
        container.innerHTML = `<div class="text-slate-500">No comments logged yet.</div>`;
        return;
    }
    container.innerHTML = list.map(c => `
        <div class="bg-dark-900 border border-dark-700 p-3.5 rounded-xl flex flex-col gap-1">
            <div class="flex items-center justify-between">
                <span class="font-semibold text-cyan-300">[${c.platform} // ${c.mode}] ${c.author_name || ''}</span>
                <span class="text-[11px] text-slate-500 font-mono">${c.created_at}</span>
            </div>
            ${c.comment_text ? `<div class="text-slate-400">Incoming: "${c.comment_text}"</div>` : ''}
            <div class="text-emerald-300 font-medium">Agent Typed: "${c.reply_text}"</div>
        </div>
    `).join('');
}

async function loadBrainData() {
    const res = await fetch('/api/brain');
    const data = await res.json();
    const grid = document.getElementById('brain-receipts-grid');
    grid.innerHTML = (data.story_bank || []).map(s => `
        <div class="bg-dark-800 border border-dark-700 p-4 rounded-2xl space-y-1.5">
            <div class="flex items-center justify-between">
                <span class="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full font-mono">${s.category}</span>
                <span class="text-xs text-slate-400 font-mono">${s.year_or_date}</span>
            </div>
            <h4 class="font-bold text-sm text-white">${s.title}</h4>
            <p class="text-xs text-slate-300">${s.detail}</p>
            <div class="text-xs text-amber-300 font-mono pt-1">Receipt: ${s.metrics_receipts}</div>
        </div>
    `).join('');
}

async function launchInteractiveBrowser() {
    const res = await fetch('/api/auth/launch-browser', { method: 'POST' });
    const data = await res.json();
    showBanner(data.message);
}

async function savePlatformCookies() {
    const ig = document.getElementById('cookie-ig-sessionid').value.trim();
    const fbC = document.getElementById('cookie-fb-cuser').value.trim();
    const fbXs = document.getElementById('cookie-fb-xs').value.trim();
    const res = await fetch('/api/auth/cookies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ig_sessionid: ig || null, fb_c_user: fbC || null, fb_xs: fbXs || null })
    });
    const data = await res.json();
    showBanner(data.message);
    loadSystemStatus();
}

async function runFullAutoCycle() {
    showBanner('Running Full Autonomous Cycle (02 Extract -> 03 FFmpeg Mix -> 04 IG Publish & Reply -> 05 FB Publish & Reply)...');
    const res = await fetch('/api/auto-cycle', { method: 'POST' });
    const data = await res.json();
    showBanner(`Autonomous Cycle Complete! Extracted: ${data.step_1_saved_extraction?.processed_count}, Mixed: ${data.step_2_media_music_mixer?.mixed_count}, Published IG & FB Reels!`);
    loadSheetRows();
}

document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    loadSystemStatus();
    loadMusicLibrary();
    loadSheetRows();
});
