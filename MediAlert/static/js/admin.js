document.addEventListener('DOMContentLoaded', async () => {
    // --- Verificación de Sesión ---
    try {
        const response = await fetch('/api/session_check');
        if (!response.ok) {
            // Si la respuesta no es OK (ej. 401), redirige al login
            throw new Error('Sesión no válida o expirada.');
        }
        const data = await response.json();
        if (data.rol !== 'admin') {
            throw new Error('Acceso denegado. Se requiere rol de administrador.');
        }
        // Si todo está bien, actualiza el nombre del admin
        document.getElementById('admin-name').textContent = data.nombre;
    } catch (e) {
        console.error("Error en la verificación de sesión:", e.message);
        window.location.href = '/login.html'; // Redirige al login si hay cualquier error
        return; // Detiene la ejecución del script
    }

    // --- Navegación SPA (Single Page Application) ---
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    const views = document.querySelectorAll('.view-content');

    function showView(viewId) {
        views.forEach(view => view.style.display = 'none');
        const currentView = document.getElementById(viewId);
        if (currentView) {
            currentView.style.display = 'block';
        }

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.dataset.view === viewId) {
                link.classList.add('active');
            }
        });
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const viewId = e.currentTarget.dataset.view;
            showView(viewId);
            
            if (viewId === 'view-clientes') loadClientes();
            if (viewId === 'view-medicamentos') loadMedicamentos();
        });
    });

    // --- Carga de Datos (con manejo de errores) ---
    async function loadClientes() {
        try {
            const response = await fetch('/api/admin/clientes');
            if (!response.ok) throw new Error(`Error del servidor: ${response.status}`);
            
            const clientes = await response.json();
            const tableBody = document.getElementById('clientes-table-body');
            
            if (!tableBody) {
                console.error("Error: No se encontró el elemento #clientes-table-body");
                return;
            }

            tableBody.innerHTML = ''; // Limpiar tabla antes de llenar
            if (clientes.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No hay clientes registrados.</td></tr>';
            } else {
                clientes.forEach(c => {
                    tableBody.innerHTML += `<tr>
                        <td>${c.nombre}</td>
                        <td>${c.cedula}</td>
                        <td>${c.email}</td>
                        <td>
                            <button class="btn btn-sm btn-info">Editar</button> 
                            <button class="btn btn-sm btn-danger">Eliminar</button>
                        </td>
                    </tr>`;
                });
            }
        } catch (error) {
            console.error("No se pudieron cargar los clientes:", error);
            const tableBody = document.getElementById('clientes-table-body');
            if (tableBody) {
                 tableBody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">Error al cargar datos. Revisa la consola.</td></tr>`;
            }
        }
    }

    async function loadMedicamentos() {
        try {
            const response = await fetch('/api/admin/medicamentos');
            if (!response.ok) throw new Error(`Error del servidor: ${response.status}`);

            const medicamentos = await response.json();
            const tableBody = document.getElementById('medicamentos-table-body');

            if (!tableBody) {
                console.error("Error: No se encontró el elemento #medicamentos-table-body");
                return;
            }
            
            tableBody.innerHTML = ''; // Limpiar tabla
            if (medicamentos.length === 0) {
                 tableBody.innerHTML = '<tr><td colspan="3" class="text-center">No hay medicamentos registrados.</td></tr>';
            } else {
                medicamentos.forEach(m => {
                    tableBody.innerHTML += `<tr>
                        <td>${m.nombre}</td>
                        <td>${m.descripcion}</td>
                        <td>
                            <button class="btn btn-sm btn-info">Editar</button> 
                            <button class="btn btn-sm btn-danger">Eliminar</button>
                        </td>
                    </tr>`;
                });
            }
        } catch (error) {
            console.error("No se pudieron cargar los medicamentos:", error);
             const tableBody = document.getElementById('medicamentos-table-body');
            if (tableBody) {
                tableBody.innerHTML = `<tr><td colspan="3" class="text-center text-danger">Error al cargar datos. Revisa la consola.</td></tr>`;
            }
        }
    }

    // --- Lógica de Configuración y Cierre de Sesión ---
    document.getElementById('logout-btn').addEventListener('click', async () => {
        await fetch('/api/logout', { method: 'POST' });
        window.location.href = '/login.html';
    });
    // (Aquí va la lógica del formulario de contraseña que ya tenías)

    // --- Carga Inicial ---
    showView('view-clientes'); // Muestra la vista de clientes por defecto
    loadClientes();
});