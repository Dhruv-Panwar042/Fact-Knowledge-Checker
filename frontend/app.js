// State
let allFacts = [];
let allDocs = [];
let allRels = [];
let network = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    fetchStats();
    loadShowcaseCases();
    loadDocuments();
    loadFacts();
    checkApiStatus();
});

// Tab Navigation
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active', 'text-indigo-400', 'bg-indigo-500/10', 'border-indigo-500/30');
        btn.classList.add('text-slate-400', 'border-transparent');
    });

    const activeBtn = document.getElementById(	ab-btn-);
    if (activeBtn) {
        activeBtn.classList.add('active', 'text-indigo-400', 'bg-indigo-500/10', 'border-indigo-500/30');
        activeBtn.classList.remove('text-slate-400', 'border-transparent');
    }

    document.querySelectorAll('.tab-content').forEach(sec => sec.classList.add('hidden'));
    const target = document.getElementById(	ab-);
    if (target) {
        target.classList.remove('hidden');
    }

    lucide.createIcons();

    if (tabId === 'graph') {
        setTimeout(renderKnowledgeGraph, 100);
    }
}

// Fetch System Stats
async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('stat-docs').innerText = data.documents;
        document.getElementById('stat-facts').innerText = data.facts;
        document.getElementById('stat-corrob').innerText = data.corroborations;
        document.getElementById('stat-contra').innerText = data.contradictions;
        document.getElementById('stat-reconciled').innerText = data.reconciled;
    } catch (e) {
        console.error('Failed to load stats:', e);
    }
}

// Check API Key Status
async function checkApiStatus() {
    try {
        const res = await fetch('/api/config/status');
        const data = await res.json();
        const badge = document.getElementById('api-status-text');
        if (data.has_gemini_key) {
            badge.innerText = ${data.model} (Ready);
        } else {
            badge.innerText = 'Offline Heuristic Mode';
        }
    } catch (e) {
        console.error(e);
    }
}

// Load Superjoin 4 Mandatory Cases
async function loadShowcaseCases() {
    const container = document.getElementById('showcase-cards-container');
    try {
        const res = await fetch('/api/cases');
        const cases = await res.json();

        container.innerHTML = cases.map(c => {
            let badgeClass = 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
            let icon = 'sparkles';
            if (c.case_type === 'Corroboration') {
                badgeClass = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
                icon = 'check-circle-2';
            } else if (c.case_type === 'Contradiction') {
                badgeClass = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
                icon = 'alert-triangle';
            } else if (c.case_type === 'Reconciled Contradiction') {
                badgeClass = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
                icon = 'scale';
            } else if (c.case_type === 'Reasoning Failure Analysis') {
                badgeClass = 'bg-purple-500/10 text-purple-400 border-purple-500/30';
                icon = 'wrench';
            }

            const evA = c.source_evidence_a || {};
            const evB = c.source_evidence_b || {};

            return 
            <div class="glass-card rounded-2xl p-6 border border-slate-800 space-y-5">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                    <div class="flex items-center space-x-3">
                        <span class="px-3 py-1 rounded-full text-xs font-bold border flex items-center space-x-1.5 ">
                            <i data-lucide="" class="w-3.5 h-3.5"></i>
                            <span></span>
                        </span>
                        <h3 class="text-base font-bold text-white"></h3>
                    </div>
                    <span class="text-xs text-slate-500 font-mono">Case #</span>
                </div>

                <p class="text-sm text-slate-300"></p>

                <!-- Side by Side Evidence Comparison -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-slate-900/80 rounded-xl p-4 border border-slate-800/80 space-y-2">
                        <div class="flex items-center justify-between text-xs">
                            <span class="font-semibold text-indigo-400 flex items-center space-x-1">
                                <i data-lucide="file" class="w-3.5 h-3.5"></i>
                                <span class="truncate max-w-[200px]"></span>
                            </span>
                            <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[11px]">Page </span>
                        </div>
                        <div class="p-3 bg-slate-950/60 rounded-lg border border-slate-800/60 text-xs italic font-serif text-slate-200 leading-relaxed">
                            ""
                        </div>
                    </div>

                    <div class="bg-slate-900/80 rounded-xl p-4 border border-slate-800/80 space-y-2">
                        <div class="flex items-center justify-between text-xs">
                            <span class="font-semibold text-purple-400 flex items-center space-x-1">
                                <i data-lucide="file" class="w-3.5 h-3.5"></i>
                                <span class="truncate max-w-[200px]"></span>
                            </span>
                            <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[11px]">Page </span>
                        </div>
                        <div class="p-3 bg-slate-950/60 rounded-lg border border-slate-800/60 text-xs italic font-serif text-slate-200 leading-relaxed">
                            ""
                        </div>
                    </div>
                </div>

                <!-- System Reasoning -->
                <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                    <div class="flex items-center space-x-2 text-xs font-semibold text-slate-300">
                        <i data-lucide="cpu" class="w-4 h-4 text-indigo-400"></i>
                        <span>System Reasoning & Reconciliation:</span>
                    </div>
                    <p class="text-xs text-slate-300 leading-relaxed whitespace-pre-line"></p>
                </div>

                <!-- Resolution Badge -->
                <div class="flex items-center space-x-2 text-xs pt-1">
                    <span class="font-semibold text-slate-400">Outcome:</span>
                    <span class="text-slate-200 bg-slate-800/90 px-3 py-1 rounded-lg border border-slate-700/60"></span>
                </div>
            </div>
            ;
        }).join('');

        lucide.createIcons();
    } catch (e) {
        container.innerHTML = <div class="p-6 text-center text-rose-400">Failed to load showcase cases: </div>;
    }
}

// Load Facts Table
async function loadFacts() {
    const tbody = document.getElementById('facts-table-body');
    const doc = document.getElementById('filter-doc').value;
    const cat = document.getElementById('filter-cat').value;
    const q = document.getElementById('fact-search-input').value;

    let url = /api/facts?;
    if (doc) url += doc=&;
    if (cat) url += category=&;
    if (q) url += q=&;

    try {
        const res = await fetch(url);
        allFacts = await res.json();

        if (allFacts.length === 0) {
            tbody.innerHTML = <tr><td colspan="7" class="text-center py-8 text-slate-500">No facts found matching criteria.</td></tr>;
            return;
        }

        tbody.innerHTML = allFacts.map(f => {
            let catColor = 'bg-slate-800 text-slate-300';
            if (f.category === 'Financial') catColor = 'bg-blue-500/10 text-blue-400 border border-blue-500/30';
            else if (f.category === 'Operational') catColor = 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30';
            else if (f.category === 'Governance') catColor = 'bg-purple-500/10 text-purple-400 border border-purple-500/30';
            else if (f.category === 'Strategy') catColor = 'bg-amber-500/10 text-amber-400 border border-amber-500/30';

            return 
            <tr class="hover:bg-slate-900/60 transition-colors">
                <td class="px-4 py-3 font-mono text-[11px] text-indigo-300"></td>
                <td class="px-4 py-3">
                    <div class="font-medium text-slate-200 truncate max-w-[170px]" title=""></div>
                    <div class="text-[11px] text-slate-500">Page </div>
                </td>
                <td class="px-4 py-3">
                    <span class="px-2 py-0.5 rounded text-[10px] font-semibold "></span>
                </td>
                <td class="px-4 py-3">
                    <div class="font-semibold text-slate-200"></div>
                    <div class="text-slate-400 text-[11px]"></div>
                </td>
                <td class="px-4 py-3 font-bold text-white"></td>
                <td class="px-4 py-3">
                    <div class="text-slate-300 font-medium"></div>
                    <div class="text-[10px] text-slate-500"></div>
                </td>
                <td class="px-4 py-3 text-right">
                    <button onclick="openEvidenceModal('')" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-indigo-600 text-slate-200 hover:text-white transition-all text-xs inline-flex items-center space-x-1">
                        <i data-lucide="eye" class="w-3.5 h-3.5"></i>
                        <span>Inspect</span>
                    </button>
                </td>
            </tr>
            ;
        }).join('');

        lucide.createIcons();
    } catch (e) {
        tbody.innerHTML = <tr><td colspan="7" class="text-center py-6 text-rose-400">Failed to load facts: </td></tr>;
    }
}

function handleFactSearch(e) {
    if (e.key === 'Enter' || e.target.value.length === 0 || e.target.value.length > 2) {
        loadFacts();
    }
}

// Load Document List
async function loadDocuments() {
    const container = document.getElementById('doc-list-container');
    try {
        const res = await fetch('/api/documents');
        allDocs = await res.json();
        container.innerHTML = allDocs.map(d => 
            <div class="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
                <div class="flex items-center space-x-3">
                    <div class="p-2 rounded-lg bg-blue-500/10 text-blue-400"><i data-lucide="file-text" class="w-4 h-4"></i></div>
                    <div>
                        <div class="font-medium text-slate-200"></div>
                        <div class="text-[11px] text-slate-500"> pages · </div>
                    </div>
                </div>
                <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-semibold border border-emerald-500/20">Indexed</span>
            </div>
        ).join('');
        lucide.createIcons();
    } catch (e) {
        console.error(e);
    }
}

// Evidence Inspector Modal
async function openEvidenceModal(factId) {
    let fact = allFacts.find(f => f.id === factId);
    if (!fact) {
        try {
            const res = await fetch(/api/facts/);
            fact = await res.json();
        } catch (e) {
            alert('Failed to load fact details');
            return;
        }
    }

    document.getElementById('modal-fact-title').innerText = fact.subject;
    document.getElementById('modal-fact-predicate').innerText = fact.predicate;
    document.getElementById('modal-fact-val').innerText = fact.value;
    document.getElementById('modal-fact-unit').innerText = fact.unit || 'Standard';
    document.getElementById('modal-fact-period').innerText = fact.temporal_period || 'N/A';
    document.getElementById('modal-fact-scope').innerText = fact.entity_scope || 'Consolidated';
    document.getElementById('modal-fact-location').innerText = ${fact.document_name} · Page ;
    document.getElementById('modal-fact-quote').innerText = "";

    document.getElementById('evidence-modal').classList.remove('hidden');
    lucide.createIcons();
}

function closeEvidenceModal() {
    document.getElementById('evidence-modal').classList.add('hidden');
}

// Settings Modal
function openSettingsModal() {
    document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettingsModal() {
    document.getElementById('settings-modal').classList.add('hidden');
}

async function saveApiKey() {
    const key = document.getElementById('settings-api-key-input').value.trim();
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
        alert(data.message);
        closeSettingsModal();
        checkApiStatus();
    } catch (e) {
        alert('Failed to save API key: ' + e);
    }
}

// Query / Ask the Knowledge Layer
function setQuery(q) {
    document.getElementById('query-input').value = q;
    submitQuery();
}

async function submitQuery() {
    const input = document.getElementById('query-input');
    const query = input.value.trim();
    if (!query) return;

    const btn = document.getElementById('query-btn');
    const outBox = document.getElementById('query-output-box');
    const ansText = document.getElementById('answer-text');
    const countBadge = document.getElementById('answer-source-count');
    const factsContainer = document.getElementById('grounded-facts-container');

    btn.disabled = true;
    btn.innerHTML = <i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>Analyzing...</span>;
    lucide.createIcons();

    outBox.classList.remove('hidden');
    ansText.innerHTML = <p class="text-slate-400 italic">Synthesizing verified cross-document facts...</p>;

    try {
        const res = await fetch('/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await res.json();

        ansText.innerHTML = marked.parse(data.answer);
        countBadge.innerText = ${data.grounded_facts ? data.grounded_facts.length : 0} citations;

        if (data.grounded_facts && data.grounded_facts.length > 0) {
            factsContainer.innerHTML = data.grounded_facts.map(f => 
                <div class="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80 flex items-center justify-between text-xs">
                    <div>
                        <span class="font-bold text-slate-200"></span>: <span class="text-indigo-300 font-semibold"></span>
                        <span class="text-slate-500 ml-2">(, p. )</span>
                    </div>
                    <button onclick="openEvidenceModal('')" class="text-indigo-400 hover:text-indigo-300 font-medium ml-2 underline">Inspect</button>
                </div>
            ).join('');
        } else {
            factsContainer.innerHTML = <p class="text-xs text-slate-500">No direct atomic facts cited.</p>;
        }
    } catch (e) {
        ansText.innerHTML = <p class="text-rose-400">Query error: </p>;
    } finally {
        btn.disabled = false;
        btn.innerHTML = <i data-lucide="send" class="w-4 h-4"></i><span>Query</span>;
        lucide.createIcons();
    }
}

// PDF Upload Handler
async function handleFileSelected(event) {
    const file = event.target.files[0];
    if (!file) return;

    const progressCard = document.getElementById('upload-progress-card');
    const filenameEl = document.getElementById('upload-filename');
    const bar = document.getElementById('upload-bar');
    const msg = document.getElementById('upload-message');

    filenameEl.innerText = file.name;
    progressCard.classList.remove('hidden');
    bar.style.width = '35%';
    msg.innerText = 'Uploading and extracting pages...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        bar.style.width = '65%';
        msg.innerText = 'Extracting atomic facts and cross-reconciling relationships...';

        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Upload failed');
        }

        const data = await res.json();
        bar.style.width = '100%';
        msg.innerHTML = <span class="text-emerald-400 font-medium">Successfully processed  pages! Extracted  facts and updated knowledge graph.</span>;

        // Refresh stats and components
        fetchStats();
        loadDocuments();
        loadFacts();
        loadShowcaseCases();

        setTimeout(() => {
            switchTab('explorer');
        }, 1200);

    } catch (e) {
        bar.classList.remove('bg-indigo-500');
        bar.classList.add('bg-rose-500');
        msg.innerHTML = <span class="text-rose-400">Error: </span>;
    }
}

// Vis.js Interactive Knowledge Graph
async function renderKnowledgeGraph() {
    const loader = document.getElementById('graph-loader');
    loader.classList.remove('hidden');

    try {
        const [docsRes, factsRes, relsRes] = await Promise.all([
            fetch('/api/documents'),
            fetch('/api/facts'),
            fetch('/api/relationships')
        ]);

        const docs = await docsRes.json();
        const facts = await factsRes.json();
        const rels = await relsRes.json();

        const nodes = [];
        const edges = [];

        // Document Nodes
        docs.forEach(d => {
            nodes.push({
                id: DOC_,
                label: d.filename.replace('.pdf', ''),
                color: { background: '#1E293B', border: '#3B82F6', highlight: { background: '#3B82F6', border: '#60A5FA' } },
                shape: 'box',
                font: { color: '#F8FAFC', size: 13, bold: true },
                margin: 10,
                borderWidth: 2
            });
        });

        // Fact Nodes (sample up to 25 to avoid visual clutter)
        const displayFacts = facts.slice(0, 20);
        displayFacts.forEach(f => {
            let bgColor = '#1E1B4B';
            let borderColor = '#6366F1';
            if (f.category === 'Operational') { bgColor = '#064E3B'; borderColor = '#10B981'; }
            if (f.category === 'Governance') { bgColor = '#3B0764'; borderColor = '#A855F7'; }

            nodes.push({
                id: f.id,
                label: ${f.subject}
,
                color: { background: bgColor, border: borderColor },
                shape: 'ellipse',
                font: { color: '#E2E8F0', size: 11 },
                borderWidth: 1.5,
                factData: f
            });

            // Edge from Doc to Fact
            if (f.document_id) {
                edges.push({
                    from: DOC_,
                    to: f.id,
                    color: { color: '#334155', opacity: 0.6 },
                    dashes: true,
                    width: 1
                });
            }
        });

        // Relationship Edges
        rels.forEach(r => {
            let color = '#10B981'; // Corroboration
            let dashes = false;
            if (r.rel_type === 'contradiction') {
                color = '#F43F5E';
                dashes = [5, 5];
            } else if (r.rel_type === 'reconciled') {
                color = '#F59E0B';
            }

            edges.push({
                id: r.id,
                from: r.fact_a_id,
                to: r.fact_b_id,
                label: r.rel_type.toUpperCase(),
                color: { color: color, highlight: color },
                font: { color: color, size: 9, strokeWidth: 2, strokeColor: '#0B0F19' },
                width: 2.5,
                dashes: dashes,
                arrows: 'to, from',
                smooth: { type: 'curvedCW', roundness: 0.2 }
            });
        });

        const container = document.getElementById('network-graph');
        const data = {
            nodes: new vis.DataSet(nodes),
            edges: new vis.DataSet(edges)
        };

        const options = {
            physics: {
                stabilization: false,
                barnesHut: {
                    springLength: 140,
                    avoidOverlap: 0.2
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 100
            }
        };

        network = new vis.Network(container, data, options);

        network.on('click', (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                if (nodeId.startsWith('FACT-')) {
                    openEvidenceModal(nodeId);
                }
            }
        });

        loader.classList.add('hidden');
    } catch (e) {
        loader.innerHTML = <span class="text-rose-400">Failed to load graph: </span>;
    }
}

function resetGraphView() {
    if (network) {
        network.fit();
    }
}
