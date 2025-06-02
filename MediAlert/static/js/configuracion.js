// MediAlert/static/js/configuracion.js
document.addEventListener('DOMContentLoaded', async () => {
    const configNombre = document.getElementById('configNombre');
    const configEmail = document.getElementById('configEmail');
    const configRol = document.getElementById('configRol');
    const changePasswordForm = document.getElementById('changePasswordForm');

    // Load user data
    try {
        const response = await fetch('/api/configuracion/usuario');
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'No se pudo cargar la información del usuario.');
        }
        const userData = await response.json();
        if (configNombre) configNombre.value = userData.nombre || '';
        if (configEmail) configEmail.value = userData.email || '';
        if (configRol) configRol.value = userData.rol ? userData.rol.charAt(0).toUpperCase() + userData.rol.slice(1) : '';
    } catch (error) {
        console.error('Error al cargar datos del usuario:', error);
        if (configNombre) configNombre.value = 'Error al cargar';
        if (configEmail) configEmail.value = 'Error al cargar';
        if (configRol) configRol.value = 'Error al cargar';
        showGlobalNotification('Error de Carga', error.message, 'error');
    }

    // Handle password change
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const contrasenaActual = document.getElementById('contrasenaActual').value;
            const contrasenaNueva = document.getElementById('contrasenaNueva').value;
            const contrasenaNuevaConfirmacion = document.getElementById('contrasenaNuevaConfirmacion').value;

            if (contrasenaNueva !== contrasenaNuevaConfirmacion) {
                showGlobalNotification('Error de Contraseña', 'La nueva contraseña y su confirmación no coinciden.', 'error');
                return;
            }
            if (contrasenaNueva.length < 6) {
                showGlobalNotification('Error de Contraseña', 'La nueva contraseña debe tener al menos 6 caracteres.', 'error');
                return;
            }

            try {
                const response = await fetch('/api/configuracion/cambiar_contrasena', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        contrasena_actual: contrasenaActual,
                        contrasena_nueva: contrasenaNueva,
                        contrasena_nueva_confirmacion: contrasenaNuevaConfirmacion
                    })
                });
                const responseData = await response.json();
                if (!response.ok) {
                    throw new Error(responseData.error || 'Error al cambiar la contraseña.');
                }
                showGlobalNotification('Cambio de Contraseña', responseData.message || 'Contraseña cambiada con éxito.', 'success');
                changePasswordForm.reset();
            } catch (error) {
                console.error('Error al cambiar contraseña:', error);
                showGlobalNotification('Error de Contraseña', error.message, 'error');
            }
        });
    }
});