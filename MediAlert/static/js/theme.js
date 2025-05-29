document.addEventListener('DOMContentLoaded', () => {
    const themeToggler = document.getElementById('theme-toggler');
    if (!themeToggler) return; // Si no hay botón en la página, no hace nada

    const htmlElement = document.documentElement;
    const themeIcon = themeToggler.querySelector('i.bi');

    // Función para establecer el tema y guardarlo
    const setTheme = (theme) => {
        htmlElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);

        // Actualizar el ícono del botón
        if (theme === 'dark') {
            themeIcon.classList.remove('bi-sun-fill');
            themeIcon.classList.add('bi-moon-stars-fill');
        } else {
            themeIcon.classList.remove('bi-moon-stars-fill');
            themeIcon.classList.add('bi-sun-fill');
        }
    };

    // Al cargar la página, aplicar el tema guardado o el preferido por el sistema
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);

    // Evento de clic para cambiar el tema
    themeToggler.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-bs-theme');
        setTheme(currentTheme === 'dark' ? 'light' : 'dark');
    });
});