// MediAlert/static/js/configuracion.js
document.addEventListener('DOMContentLoaded', async () => {
    const configNombre = document.getElementById('configNombre');
    const configEmail = document.getElementById('configEmail');
    const configRol = document.getElementById('configRol');
    const changePasswordForm = document.getElementById('changePasswordForm');
    const successMessageDiv = document.getElementById('successMessage');
    const errorMessageDiv = document.getElementById('errorMessage');

    function showMessage(element, message, isSuccess = true) {
        element.textContent = message;
        element.classList.remove('d-none', isSuccess ? 'alert-danger' : 'alert-success');
        element.classList.add(isSuccess ? 'alert-success' : 'alert-danger');
        setTimeout(() => {
            element.classList.add('d-none');
        }, 5000);
    }

    // Cargar datos del usuario
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
        showMessage(errorMessageDiv, error.message, false);
    }

    // Manejar cambio de contraseña
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            successMessageDiv.classList.add('d-none');
            errorMessageDiv.classList.add('d-none');

            const contrasenaActual = document.getElementById('contrasenaActual').value;
            const contrasenaNueva = document.getElementById('contrasenaNueva').value;
            const contrasenaNuevaConfirmacion = document.getElementById('contrasenaNuevaConfirmacion').value;

            if (contrasenaNueva !== contrasenaNuevaConfirmacion) {
                showMessage(errorMessageDiv, 'La nueva contraseña y su confirmación no coinciden.', false);
                return;
            }
             if (contrasenaNueva.length < 6) {
                showMessage(errorMessageDiv, 'La nueva contraseña debe tener al menos 6 caracteres.', false);
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
                showMessage(successMessageDiv, responseData.message || 'Contraseña cambiada con éxito.');
                changePasswordForm.reset();

            } catch (error) {
                console.error('Error al cambiar contraseña:', error);
                showMessage(errorMessageDiv, error.message, false);
            }
        });
    }
});