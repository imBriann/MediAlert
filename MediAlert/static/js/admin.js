// Espera a que todo el HTML esté cargado antes de ejecutar el script
document.addEventListener('DOMContentLoaded', () => {

    // --- Verificación de Sesión ---
    // Función autoejecutable para chequear la sesión al cargar la página
    (async () => {
        try {
            const response = await fetch('/api/session_check');
            if (!response.ok) throw new Error('Sesión no válida o expirada.');
            const data = await response.json();
            if (data.rol !== 'admin') throw new Error('Acceso denegado.');
            document.getElementById('admin-name').textContent = data.nombre;
            // Si la sesión es válida, carga la vista inicial
            showView('view-clientes');
        } catch (e) {
            console.error("Error en la verificación de sesión:", e.message);
            window.location.href = '/login.html';
        }
    })();

    // --- Instancias de Modales (importante obtenerlas después de que el DOM cargue) ---
    const clienteModalEl = document.getElementById('clienteModal');
    const clienteModal = clienteModalEl ? new bootstrap.Modal(clienteModalEl) : null;
    
    const medicamentoModalEl = document.getElementById('medicamentoModal');
    const medicamentoModal = medicamentoModalEl ? new bootstrap.Modal(medicamentoModalEl) : null;


    // --- Navegación SPA y Delegación de Eventos ---
    const mainContent = document.querySelector('main');

    // Escuchador de eventos principal para TODOS los clics
    document.body.addEventListener('click', async (e) => {
        const target = e.target;
        const button = target.closest('button, a'); // Busca el botón o enlace más cercano

        if (!button) return; // Si no se hizo clic en un botón o enlace, no hace nada

        // --- Navegación Sidebar ---
        if (button.matches('.sidebar .nav-link')) {
            e.preventDefault();
            const viewId = button.dataset.view;
            if (viewId) showView(viewId);
        }

        // --- Cierre de Sesión ---
        if (button.matches('#logout-btn')) {
            await fetch('/api/logout', { method: 'POST' });
            window.location.href = '/login.html';
        }

        // --- Botones "Agregar" ---
        if (button.matches('#btn-add-cliente')) {
            openClienteModal();
        }
        if (button.matches('#btn-add-medicamento')) {
            openMedicamentoModal();
        }

        // --- Botones de Acción en Tablas (Editar/Eliminar) ---
        if (button.matches('.btn-edit-cliente')) {
            const id = button.dataset.id;
            openClienteModal(id);
        }
        if (button.matches('.btn-delete-cliente')) {
            const id = button.dataset.id;
            if (confirm('¿Estás seguro de que quieres eliminar este cliente?')) {
                await fetch(`/api/admin/clientes/${id}`, { method: 'DELETE' });
                loadClientes();
            }
        }
        if (button.matches('.btn-edit-medicamento')) {
            const id = button.dataset.id;
            // Pasamos los datos directamente desde el botón para no hacer otra llamada a la API
            const nombre = button.dataset.nombre;
            const descripcion = button.dataset.descripcion;
            openMedicamentoModal(id, { nombre, descripcion });
        }
        if (button.matches('.btn-delete-medicamento')) {
            const id = button.dataset.id;
            if (confirm('¿Estás seguro de que quieres eliminar este medicamento? Se eliminarán las alertas asociadas.')) {
                await fetch(`/api/admin/medicamentos/${id}`, { method: 'DELETE' });
                loadMedicamentos();
            }
        }
    });

    // --- Manejo de Formularios ---
    document.getElementById('clienteForm').addEventListener('submit', handleClienteSubmit);
    document.getElementById('medicamentoForm').addEventListener('submit', handleMedicamentoSubmit);


    // --- Funciones de Carga de Vistas ---
    function showView(viewId) {
        document.querySelectorAll('.view-content').forEach(view => view.style.display = 'none');
        const currentView = document.getElementById(viewId);
        if (currentView) {
            currentView.style.display = 'block';
        }

        document.querySelectorAll('.sidebar .nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.view === viewId) link.classList.add('active');
        });

        // Cargar datos según la vista
        switch (viewId) {
            case 'view-clientes': loadClientes(); break;
            case 'view-medicamentos': loadMedicamentos(); break;
            case 'view-alertas': loadAlertas(); break;
            case 'view-auditoria': loadAuditoria(); break;
        }
    }

    // --- Funciones de Carga de Datos ---
    async function loadClientes() {
        const response = await fetch('/api/admin/clientes');
        const clientes = await response.json();
        const tableBody = document.getElementById('clientes-table-body');
        tableBody.innerHTML = '';
        if (clientes.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No hay clientes registrados.</td></tr>';
        } else {
            clientes.forEach(c => {
                tableBody.innerHTML += `
                    <tr>
                        <td>${c.nombre}</td>
                        <td>${c.cedula}</td>
                        <td>${c.email}</td>
                        <td>
                            <button class="btn btn-sm btn-info btn-edit-cliente" data-id="${c.id}"><i class="bi bi-pencil-square"></i> Editar</button>
                            <button class="btn btn-sm btn-danger btn-delete-cliente" data-id="${c.id}"><i class="bi bi-trash"></i> Eliminar</button>
                        </td>
                    </tr>`;
            });
        }
    }

    async function loadMedicamentos() {
        const response = await fetch('/api/admin/medicamentos');
        const medicamentos = await response.json();
        const tableBody = document.getElementById('medicamentos-table-body');
        tableBody.innerHTML = '';
        medicamentos.forEach(m => {
            tableBody.innerHTML += `
                <tr>
                    <td>${m.nombre}</td>
                    <td>${m.descripcion || 'N/A'}</td>
                    <td>
                        <button class="btn btn-sm btn-info btn-edit-medicamento" 
                                data-id="${m.id}" 
                                data-nombre="${m.nombre}" 
                                data-descripcion="${m.descripcion || ''}">
                            <i class="bi bi-pencil-square"></i> Editar
                        </button>
                        <button class="btn btn-sm btn-danger btn-delete-medicamento" data-id="${m.id}">
                            <i class="bi bi-trash"></i> Eliminar
                        </button>
                    </td>
                </tr>`;
        });
    }
    
    async function loadAlertas() { /* ...Tu código para cargar alertas... */ }
    async function loadAuditoria() { /* ...Tu código para cargar auditoría... */ }


    // --- Funciones para abrir Modales ---
    async function openClienteModal(id = null) {
        const form = document.getElementById('clienteForm');
        form.reset();
        document.getElementById('clienteId').value = '';
        
        if (id) { // Modo Editar
            const res = await fetch(`/api/admin/clientes/${id}`);
            const cliente = await res.json();
            document.getElementById('clienteModalTitle').textContent = 'Editar Cliente';
            document.getElementById('clienteId').value = cliente.id;
            document.getElementById('clienteNombre').value = cliente.nombre;
            document.getElementById('clienteCedula').value = cliente.cedula;
            document.getElementById('clienteEmail').value = cliente.email;
            document.getElementById('password-field-container').style.display = 'none';
            document.getElementById('clienteContrasena').required = false;
        } else { // Modo Agregar
            document.getElementById('clienteModalTitle').textContent = 'Agregar Cliente';
            document.getElementById('password-field-container').style.display = 'block';
            document.getElementById('clienteContrasena').required = true;
        }
        clienteModal.show();
    }

    function openMedicamentoModal(id = null, data = {}) {
        const form = document.getElementById('medicamentoForm');
        form.reset();
        document.getElementById('medicamentoId').value = '';
        
        if (id) { // Modo Editar
            document.getElementById('medicamentoModalTitle').textContent = 'Editar Medicamento';
            document.getElementById('medicamentoId').value = id;
            document.getElementById('medicamentoNombre').value = data.nombre;
            document.getElementById('medicamentoDescripcion').value = data.descripcion;
        } else { // Modo Agregar
            document.getElementById('medicamentoModalTitle').textContent = 'Agregar Medicamento';
        }
        medicamentoModal.show();
    }

    // --- Funciones para manejar el envío de Formularios ---
    async function handleClienteSubmit(e) {
        e.preventDefault();
        const id = document.getElementById('clienteId').value;
        const url = id ? `/api/admin/clientes/${id}` : '/api/admin/clientes';
        const method = id ? 'PUT' : 'POST';

        const body = {
            nombre: document.getElementById('clienteNombre').value,
            cedula: document.getElementById('clienteCedula').value,
            email: document.getElementById('clienteEmail').value,
        };
        if (!id) { // Solo enviar contraseña si es un cliente nuevo
            body.contrasena = document.getElementById('clienteContrasena').value;
        }

        await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        
        clienteModal.hide();
        loadClientes();
    }

    async function handleMedicamentoSubmit(e) {
        e.preventDefault();
        const id = document.getElementById('medicamentoId').value;
        const url = id ? `/api/admin/medicamentos/${id}` : '/api/admin/medicamentos';
        const method = id ? 'PUT' : 'POST';
        
        const body = {
            nombre: document.getElementById('medicamentoNombre').value,
            descripcion: document.getElementById('medicamentoDescripcion').value,
        };

        await fetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        
        medicamentoModal.hide();
        loadMedicamentos();
    }
});