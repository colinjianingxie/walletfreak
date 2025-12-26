let currentTab = 0;
const totalTabs = 3;

function switchTab(index) {
    currentTab = index;

    // Update Buttons
    document.querySelectorAll('.tab-btn').forEach((btn, i) => {
        if (i === index) {
            btn.classList.remove('tab-btn-inactive');
            btn.classList.add('tab-btn-active');
        } else {
            btn.classList.remove('tab-btn-active');
            btn.classList.add('tab-btn-inactive');
        }
    });

    // Update Text
    document.querySelectorAll('.carousel-content-block').forEach((block, i) => {
        if (i === index) {
            block.style.display = 'block';
            // Trigger animation
            block.classList.remove('slide-in-text');
            void block.offsetWidth; // trigger reflow
            block.classList.add('slide-in-text');
        } else {
            block.style.display = 'none';
        }
    });

    // Update Visual
    document.querySelectorAll('.carousel-visual-block').forEach((block, i) => {
        if (i === index) {
            block.style.display = 'block';
            // Trigger animation
            block.classList.remove('animate-in');
            void block.offsetWidth; // trigger reflow
            block.classList.add('animate-in');
        } else {
            block.style.display = 'none';
        }
    });
}

function travelTab(direction) {
    let newIndex = currentTab + direction;
    if (newIndex < 0) newIndex = totalTabs - 1;
    if (newIndex >= totalTabs) newIndex = 0;
    switchTab(newIndex);
}
