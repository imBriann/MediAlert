document.addEventListener('DOMContentLoaded', () => {
    // Selecciona todos los elementos que pueden cambiar de sección (enlaces, botones)
    const navTriggers = document.querySelectorAll('[data-target]');
    const contentSections = document.querySelectorAll('.content-section');
    const sidebarLinks = document.querySelectorAll('.sidebar .nav-link[data-target]');

    const showSection = (targetId) => {
        // Oculta todas las secciones de contenido
        contentSections.forEach(section => {
            section.classList.add('d-none');
        });

        // Muestra solo la sección deseada
        const targetSection = document.getElementById(targetId);
        if (targetSection) {
            targetSection.classList.remove('d-none');
        }

        // Actualiza el estado "active" en la barra lateral
        sidebarLinks.forEach(link => {
            link.classList.remove('active');
            if (link.dataset.target === targetId) {
                link.classList.add('active');
            }
        });
    };

    // Agrega el evento de clic a cada activador de navegación
    navTriggers.forEach(trigger => {
        trigger.addEventListener('click', (event) => {
            event.preventDefault(); // Evita que el enlace recargue la página
            const targetId = trigger.dataset.target;
            showSection(targetId);
            // Actualiza el hash en la URL para poder compartir el enlace
            window.location.hash = targetId.replace('section-', '');
        });
    });

    // Revisa si la URL tiene un hash al cargar la página
    const initialHash = window.location.hash.substring(1);
    if (initialHash) {
        showSection('section-' + initialHash);
    } else {
        // Si no hay hash, muestra la primera sección (alertas) y márcala como activa
        showSection('section-alertas');
    }
});