document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-btn');
    const topicInput = document.getElementById('topic');
    const styleSelect = document.getElementById('style');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const historyList = document.getElementById('history-list');

    // Elements for results
    const ideasList = document.getElementById('ideas-list');
    const postTextElem = document.getElementById('post_text');
    const titlesList = document.getElementById('titles-list');
    const titlesTextElem = document.getElementById('titles_text');
    const hashtagsTextElem = document.getElementById('hashtags_text');

    // Helper function to fill and show results
    const displayResults = (data) => {
        // Fill ideas
        ideasList.innerHTML = data.ideas.map(idea => `<li>${idea}</li>`).join('');
        
        // Fill post
        postTextElem.textContent = data.post_text;
        
        // Fill titles
        titlesList.innerHTML = data.titles.map(t => `<li>${t}</li>`).join('');
        titlesTextElem.textContent = data.titles.join('\n');
        
        // Fill hashtags
        hashtagsTextElem.textContent = data.hashtags;

        // Show results and scroll to them
        results.classList.remove('hidden');
        results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    const fetchHistory = async () => {
        try {
            const res = await fetch('/api/history');
            const history = await res.json();
            historyList.innerHTML = '';
            history.forEach(item => {
                const div = document.createElement('div');
                div.className = 'history-item fade-in';
                div.innerHTML = `
                    <h4>${item.topic}</h4>
                    <p>${item.created_at}</p>
                `;
                div.onclick = () => {
                    displayResults(item);
                };
                historyList.appendChild(div);
            });
        } catch (err) {
            console.error('Error fetching history:', err);
        }
    };

    fetchHistory();

    const generate = async () => {
        const topic = topicInput.value.trim();
        const style = styleSelect.value;

        if (!topic) {
            alert('Пожалуйста, введите тему!');
            return;
        }

        // UI state
        generateBtn.disabled = true;
        loading.classList.remove('hidden');
        results.classList.add('hidden');

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic, style })
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Use our new helper to display the new generation
            displayResults(data);
            fetchHistory(); // Refresh history

        } catch (err) {
            alert('Ошибка: ' + err.message);
            console.error(err);
        } finally {
            generateBtn.disabled = false;
            loading.classList.add('hidden');
        }
    };

    generateBtn.addEventListener('click', generate);

    // Global copy function
    window.copyText = (elementId) => {
        const element = document.getElementById(elementId);
        if (!element) return;
        const text = element.textContent;
        navigator.clipboard.writeText(text).then(() => {
            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = 'Скопировано!';
            btn.style.color = '#10b981'; 
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.color = '';
            }, 2000);
        }).catch(err => {
            console.error('Could not copy text: ', err);
        });
    };
});
