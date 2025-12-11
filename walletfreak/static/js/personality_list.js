let currentQuestion = 0;
const userAnswers = {};
// Track votes for each personality
const personalityVotes = {};

function loadQuestion() {
    const q = questions[currentQuestion];
    const progress = (currentQuestion / questions.length) * 100;

    document.getElementById('question-counter').textContent = `QUESTION ${q.stage} OF ${questions.length}`;
    document.getElementById('progress-percent').textContent = `${Math.round(progress)}% COMPLETE`;
    document.getElementById('progress-bar').style.width = `${progress}%`;
    document.getElementById('question-text').textContent = q.question;
    document.getElementById('question-subtitle').textContent = q.subtitle;

    const container = document.getElementById('options-container');
    container.innerHTML = '';

    // Always use 3 columns for answer choices
    container.style.gridTemplateColumns = 'repeat(3, 1fr)';

    q.options.forEach((option, idx) => {
        const div = document.createElement('div');
        div.className = 'quiz-option';
        div.dataset.id = option.id;
        // Store personalities this option maps to
        div.dataset.personalities = JSON.stringify(option.personalities || []);

        div.innerHTML = `
            <span class="text">${option.text}</span>
            <div class="checkmark">
                <span class="material-icons" style="font-size: 16px; color: #2563EB;">check</span>
            </div>
        `;

        // Determine if multi-select based on max_selections
        const isMulti = q.max_selections !== 1;
        div.onclick = () => selectOption(div, isMulti, q.max_selections);
        container.appendChild(div);
    });

    // Hide Continue button initially
    document.getElementById('continue-btn').style.display = 'none';

    // Update button text for last question
    const btn = document.getElementById('continue-btn');
    btn.textContent = currentQuestion === questions.length - 1 ? 'Reveal Match →' : 'Continue →';

    // Show/hide back button
    const backBtn = document.getElementById('back-btn');
    if (currentQuestion > 0) {
        backBtn.style.display = 'block';
    } else {
        backBtn.style.display = 'none';
    }
}

function selectOption(element, multiSelect, maxSelect) {
    const container = document.getElementById('options-container');
    const selected = container.querySelectorAll('.quiz-option.selected');

    if (multiSelect) {
        if (element.classList.contains('selected')) {
            element.classList.remove('selected');
        } else {
            if (maxSelect && selected.length >= maxSelect) {
                // Don't allow more than max
                return;
            }
            element.classList.add('selected');
        }
    } else {
        selected.forEach(el => el.classList.remove('selected'));
        element.classList.add('selected');
    }

    // Show/hide continue button based on selection
    const hasSelection = container.querySelectorAll('.quiz-option.selected').length > 0;
    const continueBtn = document.getElementById('continue-btn');
    if (hasSelection) {
        continueBtn.style.display = 'block';
    } else {
        continueBtn.style.display = 'none';
    }
}

function nextQuestion() {
    const container = document.getElementById('options-container');
    const selected = container.querySelectorAll('.quiz-option.selected');

    // Tally votes
    selected.forEach(el => {
        const associatedPersonalities = JSON.parse(el.dataset.personalities);
        associatedPersonalities.forEach(slug => {
            personalityVotes[slug] = (personalityVotes[slug] || 0) + 1;
        });
    });

    currentQuestion++;

    if (currentQuestion < questions.length) {
        loadQuestion();
    } else {
        showLoading();
    }
}

function previousQuestion() {
    if (currentQuestion > 0) {
        // We don't easily untally votes here without complex state tracking.
        // For simplicity in this version, we'll just reset votes and restart quiz if they go back?
        // Or better: just decrement currentQuestion and re-render. 
        // The votes are tallied on "next", so if we go back we should ideally untally.
        // But since we re-tally on "next", we can just clear votes and re-calculate everything from scratch?
        // No, that's hard because we don't store history.

        // Let's just restart for now if they go back, or just accept that "back" is visual only?
        // Actually, let's just not support back button logic fully for the vote tallying in this quick implementation
        // unless we store answers per stage.

        // Correct approach: Store answers per stage, tally at the end.
        // But to keep it simple and consistent with previous code structure:
        currentQuestion--;
        loadQuestion();
        // Note: This implementation is slightly buggy on "back" regarding votes. 
        // Ideally we should refactor to store selections and calculate result at the end.
        // Given the constraints, I will assume forward-only flow is primary.
    }
}

// Refactored to store answers and calculate at end
const stageSelections = {}; // stage_index -> [list of personalities from selected options]

// Override nextQuestion to store selections
nextQuestion = function () {
    const container = document.getElementById('options-container');
    const selected = container.querySelectorAll('.quiz-option.selected');

    const currentStageVotes = [];
    selected.forEach(el => {
        const associatedPersonalities = JSON.parse(el.dataset.personalities);
        currentStageVotes.push(...associatedPersonalities);
    });

    stageSelections[currentQuestion] = currentStageVotes;

    currentQuestion++;

    if (currentQuestion < questions.length) {
        loadQuestion();
    } else {
        showLoading();
    }
}

// Override previousQuestion
previousQuestion = function () {
    if (currentQuestion > 0) {
        currentQuestion--;
        loadQuestion();
        // We don't need to restore visual selection state here because loadQuestion clears it.
        // If we wanted to restore, we'd need to save option IDs.
        // For now, "Back" just lets you re-answer the previous question.
    }
}

function showLoading() {
    document.getElementById('quiz-container').style.display = 'none';
    document.getElementById('loading-container').style.display = 'block';

    // Simulate loading with fun messages
    const messages = [
        { title: "Analyzing your preferences...", subtitle: "Crunching the multipliers" },
        { title: "Calculating your vibe...", subtitle: "Consulting the credit card oracle" },
        { title: "Finding your match...", subtitle: "Almost there!" }
    ];

    let msgIndex = 0;
    const interval = setInterval(() => {
        msgIndex++;
        if (msgIndex < messages.length) {
            document.getElementById('loading-title').textContent = messages[msgIndex].title;
            document.getElementById('loading-subtitle').textContent = messages[msgIndex].subtitle;
        }
    }, 1000);

    // Show results after 3 seconds
    setTimeout(() => {
        clearInterval(interval);
        calculateAndShowResults();
    }, 3000);
}

function calculateAndShowResults() {
    // Tally all votes from all stages
    const finalVotes = {};
    Object.values(stageSelections).forEach(stageVotes => {
        stageVotes.forEach(slug => {
            finalVotes[slug] = (finalVotes[slug] || 0) + 1;
        });
    });

    // Find personality with max votes
    let bestMatchSlug = null;
    let maxVotes = -1;

    for (const [slug, votes] of Object.entries(finalVotes)) {
        if (votes > maxVotes) {
            maxVotes = votes;
            bestMatchSlug = slug;
        }
    }

    // Fallback if no votes (shouldn't happen)
    if (!bestMatchSlug && personalities.length > 0) {
        bestMatchSlug = personalities[0].slug;
    }

    const bestMatch = personalities.find(p => p.slug === bestMatchSlug) || personalities[0];

    showResults(bestMatch);
}

function showResults(personality) {
    document.getElementById('loading-container').style.display = 'none';
    document.getElementById('results-container').style.display = 'block';

    // Update progress to 100%
    document.getElementById('progress-bar').style.width = '100%';

    // Display personality info
    // Use a default icon if none (we don't have icons in the new data yet, maybe add them?)
    // For now, just use a generic one or try to map based on slug
    let icon = '🎯';
    if (personality.slug.includes('jetsetter') || personality.slug.includes('travel')) icon = '✈️';
    if (personality.slug.includes('freak')) icon = '🤑';
    if (personality.slug.includes('foodie')) icon = '🍔';
    if (personality.slug.includes('cash')) icon = '💵';

    // document.getElementById('result-icon').textContent = icon;

    const img = document.getElementById('result-image');
    if (img) {
        img.src = `${PERSONALITY_IMAGES_PATH}${personality.slug}.png`;
        img.alt = personality.name;
    }
    document.getElementById('result-name').textContent = personality.name;
    document.getElementById('result-description').textContent = personality.description;
    // Use slug for URL
    document.getElementById('view-stack-btn').href = `/personalities/${personality.slug}/`;
}

function resetQuiz() {
    currentQuestion = 0;
    for (const key in stageSelections) delete stageSelections[key];

    document.getElementById('results-container').style.display = 'none';
    document.getElementById('quiz-container').style.display = 'block';

    loadQuestion();
}

// Load first question on page load
loadQuestion();

// Carousel Navigation
function scrollCarousel(direction) {
    const container = document.getElementById('personalities-carousel');
    const scrollAmount = 400; // Approximate width of card + gap

    if (direction === -1) {
        container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
    } else {
        container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
}
