// Gorgona-One Generated Script
console.log("⚡ Gorgona-One Cyber System Initialized");

function triggerAction(actionName) {
    alert("Модуль [" + actionName + "] успешно активирован через ядро Gorgona-One AI!");
}

// Interactive cards tilt effect
document.querySelectorAll('.cyber-card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        card.style.setProperty('--mouse-x', `${x}px`);
        card.style.setProperty('--mouse-y', `${y}px`);
    });
});
