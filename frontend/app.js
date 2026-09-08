// Fact Knowledge Layer - Core Application Logic
// Styled for Editorial Paper & Docket Aesthetic

// Global State
let allFacts = [];
let allDocs = [];
let allRels = [];
let network = null;
let currentShowcaseMode = 'dynamic';

// Helper: Escape HTML
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initDropzone();
    checkApiStatus();
    loadShowcaseCases();
    loadDocuments();
    loadFacts();
});

// -------------------------------------------------------------
// Navigation & Tab Switching
// -------------------------------------------------------------
function initNavigation() {
    // Check if any tab is hash-selected or default to cases
    const hash = window.location.hash.replace('#', '');
    if (hash && ['cases', 'graph', 'facts', 'ask', 'upload'].includes(hash)) {
        switchTab(hash);
    }
}

function switchTab(tabId) {
    // Update nav links
    document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
    const activeNav = document.getElementById('nav-' + tabId);
    if (activeNav) activeNav.classList.add('active');

    // Update section visibility
    document.querySelectorAll('section').forEach(sec => sec.classList.remove('active'));
    const targetSection = document.getElementById(tabId);
    if (targetSection) targetSection.classList.add('active');

    // Trigger graph layout if switched to graph tab
    if (tabId === 'graph') {
        setTimeout(renderKnowledgeGraph, 80);
    }
}

// -------------------------------------------------------------
// API Key Status & Settings
// -------------------------------------------------------------
async function checkApiStatus() {
    try {
        const res = await fetch('/api/config/status');
        const data = await res.json();
        const badgeText = document.getElementById('api-status-text');
        const badgeDot = document.getElementById('api-dot');

        if (badgeText && badgeDot) {
            if (data.has_gemini_key) {
                badgeText.innerText = 'Gemini Active';
                badgeDot.style.background = 'var(--green)';
            } else {
                badgeText.innerText = 'Offline Mode';
                badgeDot.style.background = 'var(--ochre)';
            }
        }
    } catch (e) {
        console.error('Failed to check API status:', e);
    }
}

function openSettingsModal() {
    const modal = document.getElementById('settings-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeSettingsModal() {
    const modal = document.getElementById('settings-modal');
    if (modal) modal.classList.add('hidden');
}

async function saveApiKey() {
    const input = document.getElementById('settings-api-key-input');
    const key = input ? input.value.trim() : '';
    if (!key) {
        alert('Please enter a valid Gemini API key.');
        return;
    }
    try {
        const res = await fetch('/api/config/key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: key })
        });
        const data = await res.json();
        alert(data.message || 'Key saved.');
        closeSettingsModal();
        checkApiStatus();
    } catch (e) {
        alert('Failed to save API key: ' + e.message);
    }
}

// -------------------------------------------------------------
// Showcase Cases (Docket Style)
// -------------------------------------------------------------
async function setShowcaseMode(mode) {
    currentShowcaseMode = mode;
    const btnDyn = document.getElementById('btn-mode-dynamic');
    const btnBench = document.getElementById('btn-mode-benchmark');
    if (btnDyn && btnBench) {
        if (mode === 'dynamic') {
            btnDyn.classList.add('active');
            btnBench.classList.remove('active');
        } else {
            btnDyn.classList.remove('active');
            btnBench.classList.add('active');
        }
    }
    await loadShowcaseCases();
}

async function loadShowcaseCases() {
    const container = document.getElementById('showcase-cards-container');
    if (!container) return;

    try {
        const res = await fetch(`/api/cases?mode=${currentShowcaseMode}`);
        const cases = await res.json();

        if (!cases || cases.length === 0) {
            container.innerHTML = '<div style="text-align:center;padding:36px;color:var(--ink-soft);">No showcase cases found.</div>';
            return;
        }

        container.innerHTML = cases.map(c => {
            let relClass = 'corroborate';
            let relSymbol = '≈';
            let relText = 'Corroborated';

            if (c.case_type === 'Corroboration') {
                relClass = 'corroborate';
                relSymbol = '≈';
                relText = 'Corroborated';
            } else if (c.case_type === 'Contradiction') {
                relClass = 'contradict';
                relSymbol = '≠';
                relText = 'Contradiction';
            } else if (c.case_type === 'Reconciled Contradiction') {
                relClass = 'reconciled';
                relSymbol = '≠*';
                relText = 'Reconciled by context';
            } else {
                relClass = 'failure';
                relSymbol = '—';
                relText = 'Extraction failure';
            }

            const isSingle = (c.case_type === 'Reasoning Failure Analysis') || !c.source_evidence_b || !c.source_evidence_b.document;
            const evA = c.source_evidence_a || {};
            const evB = c.source_evidence_b || {};

            const originTag = c.is_live_derived
                ? `<span class="docket-tag" style="color:var(--green);border-color:var(--green);">● Live Discovered</span>`
                : `<span class="docket-tag">Reference Benchmark</span>`;

            const edgeTag = c.fact_a_id
                ? `<span class="docket-tag" style="font-family:monospace;font-size:10.5px;">Edge: #${c.fact_a_id} ${c.fact_b_id ? `⟷ #${c.fact_b_id}` : ''}</span>`
                : '';

            return `
            <div class="docket-entry">
                <div class="docket-head">
                    <span class="docket-number">${c.case_number}</span>
                    <span class="docket-relation ${relClass}">${relText}</span>
                    ${originTag}
                    ${edgeTag}
                </div>
                <p class="docket-claim">${escapeHtml(c.title || c.summary)}</p>

                <div class="exhibits ${isSingle ? 'single-exhibit' : ''}">
                    <div class="exhibit">
                        <div class="exhibit-source">
                            <span>${escapeHtml(evA.document || 'Source filing')}</span>
                            <span>Page ${evA.page != null ? evA.page : '—'}</span>
                        </div>
                        <div class="exhibit-value">Stated: <b>${escapeHtml(evA.value || c.predicate_a || 'Reported figure')}</b></div>
                        <div class="exhibit-quote">"${escapeHtml(evA.quote || 'No excerpt available')}"</div>
                    </div>
                    ${!isSingle ? `
                    <div class="relation-symbol ${relClass}">${relSymbol}</div>
                    <div class="exhibit">
                        <div class="exhibit-source">
                            <span>${escapeHtml(evB.document || 'Source filing')}</span>
                            <span>Page ${evB.page != null ? evB.page : '—'}</span>
                        </div>
                        <div class="exhibit-value">Stated: <b>${escapeHtml(evB.value || c.predicate_b || 'Reported figure')}</b></div>
                        <div class="exhibit-quote">"${escapeHtml(evB.quote || 'No excerpt available')}"</div>
                    </div>
                    ` : ''}
                </div>

                <div class="docket-why">
                    <span>Why this matters / Reasoning:</span> ${escapeHtml(c.system_reasoning)}
                    ${c.resolution ? `<div style="margin-top:6px;"><span>Outcome:</span> ${escapeHtml(c.resolution)}</div>` : ''}
                </div>
            </div>
            `;
        }).join('');

    } catch (e) {
        container.innerHTML = `<div style="text-align:center;padding:24px;color:var(--rust);">Failed to load showcase cases: ${escapeHtml(e.message)}</div>`;
    }
}

// -------------------------------------------------------------
// Interactive Vis.js Knowledge Graph (Uncluttered & Editorial)
// -------------------------------------------------------------
async function renderKnowledgeGraph() {
    const loader = document.getElementById('graph-loader');
    if (loader) loader.style.display = 'flex';

    try {
        const [docsRes, factsRes, relsRes] = await Promise.all([
            fetch('/api/documents'),
            fetch('/api/facts'),
            fetch('/api/relationships')
        ]);

        allDocs = await docsRes.json();
        allFacts = await factsRes.json();
        allRels = await relsRes.json();

        // Populate side document list
        renderGraphDocList(allDocs, allFacts);

        const nodes = [];
        const edges = [];

        // Check active UI filters
        const docFilterVal = document.getElementById('graph-doc-filter')?.value || '';
        const relFilterVal = document.getElementById('graph-rel-filter')?.value || 'all';

        // 1. Determine which documents to show
        let visibleDocs = allDocs;
        if (docFilterVal) {
            const selectedDocId = parseInt(docFilterVal);
            visibleDocs = allDocs.filter(d => d.id === selectedDocId);
        }

        // Add Document Nodes: Dark ink boxes with ample padding
        visibleDocs.forEach(d => {
            const shortName = d.filename.replace('.pdf', '').replace(/_/g, ' ');
            nodes.push({
                id: 'DOC_' + d.id,
                label: shortName,
                color: {
                    background: '#23241F',
                    border: '#23241F',
                    highlight: { background: '#3B5D50', border: '#3B5D50' }
                },
                shape: 'box',
                margin: 10,
                font: { color: '#F6F6F1', size: 12, face: 'Public Sans', bold: true },
                borderWidth: 1.5,
                docData: d
            });
        });

        // 2. Filter & Deduplicate Facts to eliminate visual clutter
        const seenClaimKeys = new Set();
        const distinctFacts = [];
        for (const f of allFacts) {
            if (docFilterVal && f.document_id !== parseInt(docFilterVal)) {
                // If a document filter is selected, only allow facts that have a direct relationship with this doc
                const hasRelationToDoc = allRels.some(r => 
                    (r.fact_a_id === f.id || r.fact_b_id === f.id)
                );
                if (!hasRelationToDoc) continue;
            }

            const cleanSub = (f.subject || '').toLowerCase().trim();
            const cleanVal = (f.value || '').toLowerCase().trim();
            const dedupKey = `${f.document_id}::${cleanSub}::${cleanVal}`;
            if (!seenClaimKeys.has(dedupKey)) {
                seenClaimKeys.add(dedupKey);
                distinctFacts.push(f);
            }
        }

        // 3. Prioritize facts that participate in active relationships
        const relFactIds = new Set();
        allRels.forEach(r => {
            if (relFilterVal !== 'all' && r.rel_type !== relFilterVal) return;
            if (r.fact_a_id) relFactIds.add(r.fact_a_id);
            if (r.fact_b_id) relFactIds.add(r.fact_b_id);
        });

        const priorityFacts = distinctFacts.filter(f => relFactIds.has(f.id));
        const regularFacts = distinctFacts.filter(f => !relFactIds.has(f.id));

        // Display at most 18-20 facts at once to ensure a clean, breathable canvas
        const displayFacts = [
            ...priorityFacts.slice(0, 14),
            ...regularFacts.slice(0, docFilterVal ? 8 : 6)
        ];

        displayFacts.forEach(f => {
            let borderColor = '#A9AB99';
            if (f.category === 'Financial') borderColor = '#3B5D50';
            else if (f.category === 'Operational') borderColor = '#8A6524';
            else if (f.category === 'Governance') borderColor = '#8B3A2B';

            // Concise labels for clean reading
            const cleanSub = f.subject.length > 24 ? f.subject.slice(0, 22) + '…' : f.subject;
            const cleanVal = f.value.length > 20 ? f.value.slice(0, 18) + '…' : f.value;

            nodes.push({
                id: f.id,
                label: `${cleanSub}\n${cleanVal}`,
                color: {
                    background: '#F6F6F1',
                    border: borderColor,
                    highlight: { background: '#F7F2E1', border: '#23241F' }
                },
                shape: 'box',
                borderRadius: 5,
                margin: 8,
                font: { color: '#23241F', size: 10.5, face: 'Public Sans' },
                borderWidth: 1.5,
                factData: f
            });

            // Spoke edge from Document to Fact: subtle, soft opacity
            const docNodeExists = visibleDocs.some(d => d.id === f.document_id);
            if (docNodeExists) {
                edges.push({
                    id: `spoke_${f.id}`,
                    from: 'DOC_' + f.document_id,
                    to: f.id,
                    color: { color: '#CBCCBE', opacity: 0.45 },
                    dashes: [4, 4],
                    width: 1,
                    smooth: false,
                    arrows: ''
                });
            }
        });

        // 4. Cross-Document Relationship Links (Sparse, informative, NO arrow clutter)
        const validNodeIds = new Set(nodes.map(n => n.id));
        const seenPairs = new Set();
        const displayRels = [];

        for (const r of allRels) {
            if (relFilterVal !== 'all' && r.rel_type !== relFilterVal) continue;
            if (!validNodeIds.has(r.fact_a_id) || !validNodeIds.has(r.fact_b_id)) continue;

            const pairKey = [r.fact_a_id, r.fact_b_id].sort().join('::');
            if (seenPairs.has(pairKey)) continue; // Prevent redundant multiple edges
            seenPairs.add(pairKey);
            displayRels.push(r);
            if (displayRels.length >= 15) break; // Limit to 15 key relationships max
        }

        displayRels.forEach(r => {
            let color = '#3B5D50'; // corroboration
            let symbol = '≈ Corroborated';
            let dashes = false;
            if (r.rel_type === 'contradiction') {
                color = '#8B3A2B';
                symbol = '≠ Contradiction';
                dashes = [5, 4];
            } else if (r.rel_type === 'reconciled') {
                color = '#8A6524';
                symbol = '≠* Reconciled';
            }

            edges.push({
                id: 'rel_' + r.id,
                from: r.fact_a_id,
                to: r.fact_b_id,
                label: symbol,
                color: { color: color, highlight: color },
                font: {
                    color: color,
                    size: 9.5,
                    face: 'Public Sans',
                    background: '#F6F6F1',
                    strokeWidth: 2,
                    strokeColor: '#F6F6F1'
                },
                width: 2.2,
                dashes: dashes,
                arrows: '', // NO arrow clutter! Clean lines with centered labels
                smooth: { type: 'continuous', roundness: 0.15 },
                relData: r
            });
        });

        const container = document.getElementById('network-graph');
        if (!container) return;
        if (!window.vis) {
            if (loader) loader.innerHTML = `<span style="color:var(--ink-soft);">Loading visualization library...</span>`;
            return;
        }

        const data = {
            nodes: new vis.DataSet(nodes),
            edges: new vis.DataSet(edges)
        };

        // Physics: forceAtlas2Based with generous spacing and 100% overlap avoidance
        const options = {
            physics: {
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {
                    gravitationalConstant: -180,
                    centralGravity: 0.008,
                    springLength: 220,
                    springConstant: 0.05,
                    damping: 0.7,
                    avoidOverlap: 1.0
                },
                stabilization: {
                    enabled: true,
                    iterations: 75,
                    updateInterval: 25
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 100,
                zoomView: true,
                dragView: true
            }
        };

        if (network) {
            network.destroy();
            network = null;
        }

        network = new vis.Network(container, data, options);

        network.once('stabilizationIterationsDone', () => {
            if (loader) loader.style.display = 'none';
        });
        setTimeout(() => {
            if (loader) loader.style.display = 'none';
        }, 400);

        // Click interaction: inspect nodes and edges
        network.on('click', (params) => {
            const inspector = document.getElementById('graph-inspector');
            const inspTitle = document.getElementById('inspector-title');
            const inspBody = document.getElementById('inspector-body');

            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                if (nodeId.startsWith('DOC_')) {
                    const docId = parseInt(nodeId.replace('DOC_', ''));
                    const doc = allDocs.find(d => d.id === docId);
                    if (doc && inspector && inspTitle && inspBody) {
                        inspector.style.display = 'block';
                        inspTitle.innerText = doc.filename;
                        const docFactsCount = allFacts.filter(f => f.document_id === doc.id).length;
                        inspBody.innerHTML = `
                            <div style="font-size:12.5px;color:var(--ink-soft);margin-bottom:6px;">${doc.page_count} indexed pages · ${doc.status}</div>
                            <div style="font-size:13px;color:var(--ink);">Contains <b>${docFactsCount}</b> extracted atomic facts in the active ledger.</div>
                            <div style="margin-top:10px;">
                                <button class="evidence-link" onclick="filterByDocument('${escapeHtml(doc.filename)}')">Filter facts for this document →</button>
                            </div>
                        `;
                    }
                } else {
                    // Fact node
                    const fact = allFacts.find(f => f.id === nodeId);
                    if (fact && inspector && inspTitle && inspBody) {
                        inspector.style.display = 'block';
                        inspTitle.innerText = fact.subject;
                        inspBody.innerHTML = `
                            <div style="margin-bottom:6px;font-size:13px;"><b>Value:</b> <span style="font-weight:600;color:var(--ink);">${escapeHtml(fact.value)}</span></div>
                            <div style="margin-bottom:6px;font-size:12px;color:var(--ink-soft);">${escapeHtml(fact.document_name)} · Page ${fact.page_number}</div>
                            <div class="exhibit-quote" style="margin:8px 0 10px;font-size:12.5px;">"${escapeHtml(fact.exact_quote)}"</div>
                            <button class="evidence-link" onclick="openEvidenceModal('${fact.id}')">View full evidence →</button>
                        `;
                    }
                }
            } else if (params.edges.length > 0) {
                const edgeId = params.edges[0];
                if (edgeId.startsWith('rel_')) {
                    const relId = parseInt(edgeId.replace('rel_', ''));
                    const rel = allRels.find(r => r.id === relId);
                    if (rel && inspector && inspTitle && inspBody) {
                        inspector.style.display = 'block';
                        inspTitle.innerText = `${rel.rel_type.toUpperCase()}: ${rel.predicate_a}`;
                        inspBody.innerHTML = `
                            <div style="margin-bottom:8px;font-size:12.5px;color:var(--ink-soft);">${escapeHtml(rel.doc_a)} ⟷ ${escapeHtml(rel.doc_b)}</div>
                            <div class="exhibit-quote" style="margin:8px 0 10px;font-size:12.5px;">${escapeHtml(rel.reasoning)}</div>
                            <div style="font-size:12px;color:var(--ink-soft);">Confidence: ${(rel.confidence * 100).toFixed(0)}%</div>
                        `;
                    }
                }
            }
        });

        if (loader) loader.style.display = 'none';

    } catch (e) {
        if (loader) loader.innerHTML = `<span style="color:var(--rust);">Failed to load graph: ${escapeHtml(e.message)}</span>`;
    }
}

function renderGraphDocList(docs, facts) {
    const listContainer = document.getElementById('graph-doc-list');
    if (!listContainer) return;

    listContainer.innerHTML = docs.map(d => {
        const count = facts.filter(f => f.document_id === d.id).length;
        const shortName = d.filename.replace('.pdf', '').replace(/_/g, ' ');
        return `
        <div class="graph-doc-item" onclick="focusGraphDocument(${d.id})" title="Center graph on ${escapeHtml(shortName)}">
            <b>${escapeHtml(shortName)}</b>
            <span>${count} facts · ${d.page_count}p</span>
        </div>
        `;
    }).join('');
}

function focusGraphDocument(docId) {
    const select = document.getElementById('graph-doc-filter');
    if (select) {
        select.value = docId;
        renderKnowledgeGraph();
    } else if (network) {
        network.focus('DOC_' + docId, {
            scale: 1.1,
            animation: { duration: 600, easingFunction: 'easeInOutQuad' }
        });
    }
}

function resetGraphView() {
    const select = document.getElementById('graph-doc-filter');
    if (select) select.value = '';
    const relSelect = document.getElementById('graph-rel-filter');
    if (relSelect) relSelect.value = 'all';
    renderKnowledgeGraph();
}

function filterByDocument(docName) {
    switchTab('facts');
    const docSelect = document.getElementById('filter-doc');
    if (docSelect) {
        docSelect.value = docName;
        loadFacts();
    }
}

// -------------------------------------------------------------
// Fact Ledger Table
// -------------------------------------------------------------
async function loadFacts() {
    const tbody = document.getElementById('facts-table-body');
    const docSelect = document.getElementById('filter-doc');
    const catSelect = document.getElementById('filter-cat');
    const searchInput = document.getElementById('fact-search-input');
    const countLabel = document.getElementById('ledger-count');

    const doc = docSelect ? docSelect.value : '';
    const cat = catSelect ? catSelect.value : '';
    const q = searchInput ? searchInput.value.trim() : '';

    let url = '/api/facts?';
    if (doc) url += 'doc=' + encodeURIComponent(doc) + '&';
    if (cat) url += 'category=' + encodeURIComponent(cat) + '&';
    if (q) url += 'q=' + encodeURIComponent(q) + '&';

    try {
        const res = await fetch(url);
        allFacts = await res.json();

        if (countLabel) {
            countLabel.innerText = `Showing ${allFacts.length} grounded facts.`;
        }

        if (allFacts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:32px;color:var(--ink-soft);">No facts found matching criteria.</td></tr>';
            return;
        }

        tbody.innerHTML = allFacts.map(f => {
            return `
            <tr>
                <td class="claim-cell">
                    <b>${escapeHtml(f.subject)}</b>
                    <span>${escapeHtml(f.predicate)}</span>
                </td>
                <td><b>${escapeHtml(f.value)}</b></td>
                <td>
                    ${escapeHtml(f.temporal_period || '—')}
                    ${f.entity_scope ? `<span style="display:block;font-size:11.5px;color:var(--ink-soft);">${escapeHtml(f.entity_scope)}</span>` : ''}
                </td>
                <td class="doc-cell">
                    <b>${escapeHtml(f.document_name)}</b>
                    <span>Page ${f.page_number}</span>
                </td>
                <td style="text-align:right;white-space:nowrap;">
                    <button class="evidence-link" onclick="openEvidenceModal('${f.id}')">View quote →</button>
                </td>
            </tr>
            `;
        }).join('');

    } catch (e) {
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--rust);">Failed to load facts: ${escapeHtml(e.message)}</td></tr>`;
        }
    }
}

function handleFactSearch(e) {
    if (e.key === 'Enter' || e.target.value.length === 0 || e.target.value.length > 2) {
        loadFacts();
    }
}

// -------------------------------------------------------------
// Document List & Ingestion
// -------------------------------------------------------------
async function loadDocuments() {
    try {
        const res = await fetch('/api/documents');
        allDocs = await res.json();

        // Update Document dropdown in Fact Ledger
        const docSelect = document.getElementById('filter-doc');
        if (docSelect) {
            const currentVal = docSelect.value;
            let optionsHtml = '<option value="">All documents</option>';
            allDocs.forEach(d => {
                optionsHtml += `<option value="${escapeHtml(d.filename)}">${escapeHtml(d.filename)}</option>`;
            });
            docSelect.innerHTML = optionsHtml;
            docSelect.value = currentVal;
        }

        // Update Document dropdown in Graph filter
        const graphDocSelect = document.getElementById('graph-doc-filter');
        if (graphDocSelect) {
            const currentGraphVal = graphDocSelect.value;
            let optionsHtml = '<option value="">All Documents (Ecosystem)</option>';
            allDocs.forEach(d => {
                const shortName = d.filename.replace('.pdf', '').replace(/_/g, ' ');
                optionsHtml += `<option value="${d.id}">${escapeHtml(shortName)}</option>`;
            });
            graphDocSelect.innerHTML = optionsHtml;
            graphDocSelect.value = currentGraphVal;
        }

        // Update Document list in Upload tab
        const container = document.getElementById('doc-list-container');
        if (container) {
            container.innerHTML = allDocs.map(d => `
                <div class="docrow">
                    <div>
                        <b>${escapeHtml(d.filename)}</b>
                        <div><span>${d.page_count} pages · ${d.status}</span></div>
                    </div>
                    <div class="status">✓ Indexed</div>
                </div>
            `).join('');
        }

    } catch (e) {
        console.error('Failed to load documents:', e);
    }
}

function initDropzone() {
    const dropzone = document.getElementById('dropzone');
    if (!dropzone) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.style.borderColor = 'var(--ink)';
            dropzone.style.background = '#ECECE5';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.style.borderColor = 'var(--rule-strong)';
            dropzone.style.background = 'var(--paper-raised)';
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    }, false);
}

function handleFileSelected(event) {
    const file = event.target.files[0];
    if (file) {
        uploadFile(file);
    }
}

async function uploadFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please select a valid PDF file.');
        return;
    }

    const progressCard = document.getElementById('upload-progress-card');
    const bar = document.getElementById('upload-bar');
    const msg = document.getElementById('upload-message');
    const depthSelect = document.getElementById('upload-page-depth');

    if (progressCard) progressCard.style.display = 'block';
    if (bar) bar.style.width = '30%';
    if (msg) msg.innerText = `Uploading ${file.name} and extracting text...`;

    const depthVal = depthSelect ? depthSelect.value : '20';
    const formData = new FormData();
    formData.append('file', file);
    if (depthVal !== 'all') {
        formData.append('max_pages', parseInt(depthVal));
    }

    try {
        if (bar) bar.style.width = '60%';
        if (msg) msg.innerText = 'Extracting atomic claims and running incremental cross-reconciliation...';

        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Upload failed');
        }

        const data = await res.json();
        if (bar) bar.style.width = '100%';
        if (msg) {
            msg.innerHTML = `
                <div style="color:var(--green);font-weight:500;margin-bottom:4px;">
                    Successfully processed ${data.pages_processed} of ${data.total_pages} pages!
                </div>
                <div style="font-size:12.5px;color:var(--ink-soft);">
                    Extracted <b>${data.facts_extracted}</b> facts · Discovered <b>${data.new_relationships_discovered}</b> cross-document relationships.
                </div>
                ${data.truncation_note ? `<div style="font-size:11.5px;color:var(--ink-faint);margin-top:4px;">${data.truncation_note}</div>` : ''}
            `;
        }

        // Refresh all data
        await loadDocuments();
        await loadFacts();
        await loadShowcaseCases();

    } catch (e) {
        if (bar) {
            bar.style.width = '100%';
            bar.style.background = 'var(--rust)';
        }
        if (msg) {
            msg.innerHTML = `<span style="color:var(--rust);font-weight:500;">Error: ${escapeHtml(e.message)}</span>`;
        }
    }
}

// -------------------------------------------------------------
// Grounded Ask Engine
// -------------------------------------------------------------
function setAskQuery(query) {
    const input = document.getElementById('ask-input');
    if (input) {
        input.value = query;
        askQuestion();
    }
}

async function askQuestion() {
    const input = document.getElementById('ask-input');
    const query = input ? input.value.trim() : '';
    if (!query) return;

    const btn = document.getElementById('ask-btn');
    const loading = document.getElementById('ask-loading');
    const resultWrap = document.getElementById('ask-result-wrap');
    const ansText = document.getElementById('ask-answer-text');
    const sourcesList = document.getElementById('ask-sources-list');

    if (btn) btn.disabled = true;
    if (loading) loading.style.display = 'block';
    if (resultWrap) resultWrap.style.display = 'none';

    try {
        const res = await fetch('/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await res.json();

        // Format Markdown answer text
        let formatted = escapeHtml(data.answer || '');
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
        formatted = formatted.replace(/\*(.*?)\*/g, '<i>$1</i>');
        formatted = formatted.replace(/\n\n/g, '<br><br>');
        formatted = formatted.replace(/\n/g, '<br>');

        if (ansText) ansText.innerHTML = formatted;

        if (sourcesList) {
            if (data.grounded_facts && data.grounded_facts.length > 0) {
                sourcesList.innerHTML = data.grounded_facts.map((f, i) => `
                    <div class="ask-source">
                        <b>[${i + 1}]</b>
                        <div style="flex:1;">
                            <span style="color:var(--ink);font-weight:500;">${escapeHtml(f.subject)}: ${escapeHtml(f.value)}</span>
                            <span style="color:var(--ink-soft);margin-left:6px;">— ${escapeHtml(f.document_name)}, Page ${f.page_number}</span>
                            <button class="evidence-link" style="margin-left:8px;" onclick="openEvidenceModal('${f.id}')">View quote →</button>
                        </div>
                    </div>
                `).join('');
            } else {
                sourcesList.innerHTML = '<div style="font-size:13px;color:var(--ink-soft);">No direct atomic facts cited.</div>';
            }
        }

        if (resultWrap) resultWrap.style.display = 'block';

    } catch (e) {
        if (ansText) ansText.innerHTML = `<span style="color:var(--rust);">Query error: ${escapeHtml(e.message)}</span>`;
        if (resultWrap) resultWrap.style.display = 'block';
    } finally {
        if (loading) loading.style.display = 'none';
        if (btn) btn.disabled = false;
    }
}

// -------------------------------------------------------------
// Evidence Inspector Modal
// -------------------------------------------------------------
async function openEvidenceModal(factId) {
    let fact = allFacts.find(f => f.id === factId);
    if (!fact) {
        try {
            const res = await fetch('/api/facts/' + factId);
            fact = await res.json();
        } catch (e) {
            alert('Failed to load fact details: ' + e.message);
            return;
        }
    }

    const titleEl = document.getElementById('modal-fact-title');
    const predEl = document.getElementById('modal-fact-predicate');
    const valEl = document.getElementById('modal-fact-val');
    const periodEl = document.getElementById('modal-fact-period');
    const scopeEl = document.getElementById('modal-fact-scope');
    const locEl = document.getElementById('modal-fact-location');
    const quoteEl = document.getElementById('modal-fact-quote');

    if (titleEl) titleEl.innerText = fact.subject || 'Claim Evidence';
    if (predEl) predEl.innerText = fact.predicate || '—';
    if (valEl) valEl.innerText = fact.value || '—';
    if (periodEl) periodEl.innerText = (fact.unit ? fact.unit + ' · ' : '') + (fact.temporal_period || 'N/A');
    if (scopeEl) scopeEl.innerText = fact.entity_scope || 'Consolidated';
    if (locEl) locEl.innerText = `${fact.document_name} · Page ${fact.page_number}`;
    if (quoteEl) quoteEl.innerText = `"${fact.exact_quote || 'No excerpt recorded'}"`;

    const modal = document.getElementById('evidence-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeEvidenceModal() {
    const modal = document.getElementById('evidence-modal');
    if (modal) modal.classList.add('hidden');
}
