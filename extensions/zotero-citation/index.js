/**
 * Zotero Web API Integration
 */

const SEARCH_DEBOUNCE_MS = 500;
let searchTimeout = null;

const elements = {
    search: document.getElementById('search'),
    results: document.getElementById('results'),
    status: document.getElementById('status'),
    loader: document.getElementById('loader'),
    empty: document.getElementById('empty-state'),
    settingsPanel: document.getElementById('settings-panel'),
    toggleSettings: document.getElementById('toggle-settings'),
    saveSettings: document.getElementById('save-settings'),
    cancelSettings: document.getElementById('cancel-settings'),
    userId: document.getElementById('zotero-userid'),
    apiKey: document.getElementById('zotero-apikey'),
    mainUI: document.getElementById('main-ui'),
    popout: document.getElementById('popout-btn')
};

const channel = new BroadcastChannel("dociere-extensions");

// Initial Load
function init() {
    const userId = localStorage.getItem('zotero_userid');
    const apiKey = localStorage.getItem('zotero_apikey');
    
    if (userId && apiKey) {
        elements.userId.value = userId;
        elements.apiKey.value = apiKey;
        elements.status.innerText = "Zotero Web API ready";
        elements.status.style.color = "#10b981";
        elements.mainUI.style.opacity = "1";
    } else {
        elements.status.innerText = "Please configure your API settings";
        elements.status.style.color = "#f59e0b";
        elements.settingsPanel.style.display = "block";
        elements.mainUI.style.opacity = "0.3";
    }

    // If already in a popout, hide the popout button
    if (window.parent === window) {
        elements.popout.style.display = "none";
    }
}

// Popout Handler
elements.popout.onclick = () => {
    console.log("[Zotero Extension] Popout button clicked!");
    if (window.parent !== window) {
        console.log("[Zotero Extension] Sending dociere:popout to parent");
        window.parent.postMessage({
            type: 'dociere:popout',
            payload: { 
                id: 'zotero-citation',
                title: 'Zotero Citation Manager',
                url: window.location.href
            }
        }, '*');
    } else {
        console.log("[Zotero Extension] Already in standalone window, ignoring popout click.");
    }
};

// Settings Handlers
elements.toggleSettings.onclick = () => {
    const isVisible = elements.settingsPanel.style.display === "block";
    elements.settingsPanel.style.display = isVisible ? "none" : "block";
};

elements.cancelSettings.onclick = () => {
    elements.settingsPanel.style.display = "none";
};

elements.saveSettings.onclick = () => {
    const userId = elements.userId.value.trim();
    const apiKey = elements.apiKey.value.trim();
    
    if (!userId || !apiKey) {
        alert("Please enter both User ID and API Key");
        return;
    }
    
    localStorage.setItem('zotero_userid', userId);
    localStorage.setItem('zotero_apikey', apiKey);
    
    elements.settingsPanel.style.display = "none";
    elements.mainUI.style.opacity = "1";
    init();
};

// Search Logic
async function performSearch(query) {
    if (!query.trim()) {
        elements.results.innerHTML = '';
        elements.empty.style.display = 'block';
        elements.loader.style.display = 'none';
        return;
    }

    const userId = localStorage.getItem('zotero_userid');
    const apiKey = localStorage.getItem('zotero_apikey');
    
    if (!userId || !apiKey) return;

    elements.empty.style.display = 'none';
    elements.loader.style.display = 'block';

    try {
        const response = await fetch('/api/zotero/web', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: userId,
                apiKey: apiKey,
                endpoint: "items",
                params: {
                    q: query,
                    itemType: "-attachment || -note", // only real items
                    limit: 10
                }
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.message || "API Error");
        }

        const items = await response.json();
        elements.status.innerText = "Zotero Web API ready";
        elements.status.style.color = "#10b981";
        displayResults(items);
    } catch (err) {
        console.error("Search error:", err);
        elements.results.innerHTML = '';
        elements.status.innerText = `Search failed: ${err.message}`;
        elements.status.style.color = "#ef4444";
    } finally {
        elements.loader.style.display = 'none';
    }
}

function displayResults(items) {
    elements.results.innerHTML = '';
    
    if (items.length === 0) {
        elements.results.innerHTML = '<li class="empty-state">No matching items found</li>';
        return;
    }

    items.forEach(item => {
        const data = item.data;
        const li = document.createElement('li');
        li.className = 'result-item';
        
        const title = data.title || "Untitled";
        const authors = data.creators ? data.creators.map(c => c.lastName || c.name).join(', ') : "Unknown Author";
        const date = data.date ? data.date.substring(0, 4) : "-";
        
        // Extract Citekey from 'extra' field (Standard for Better BibTeX users)
        // Format is often "Citation Key: [key]"
        let citekey = item.key; // fallback to Zotero internal key
        if (data.extra) {
            const match = data.extra.match(/Citation Key:\s*([^\s\n\r]+)/);
            if (match) citekey = match[1];
        }

        li.innerHTML = `
            <span class="title">${title}</span>
            <div class="metadata">
                <span>${authors} (${date})</span>
                <span class="citekey">${citekey}</span>
            </div>
        `;
        
        li.onclick = () => insertCitation(citekey);
        elements.results.appendChild(li);
    });
}

function insertCitation(citeKey) {
    const message = {
        type: 'dociere:insert',
        payload: { text: `\\cite{${citeKey}}` }
    };
    
    // Send to iframe parent if it exists
    if (window.parent !== window) {
        window.parent.postMessage(message, '*');
    }
    
    // Also send via BroadcastChannel for popped-out windows
    channel.postMessage(message);

    // Show toast
    const infoMessage = {
        type: 'dociere:show-info',
        payload: { message: `Inserted: ${citeKey}` }
    };
    
    if (window.parent !== window) {
        window.parent.postMessage(infoMessage, '*');
    }
    channel.postMessage(infoMessage);
}

// Event Listeners
elements.search.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => performSearch(e.target.value), SEARCH_DEBOUNCE_MS);
});

// Start
init();
