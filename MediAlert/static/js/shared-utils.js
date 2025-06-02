let globalNotificationModal; // To store the Bootstrap Modal instance

/**
 * Displays a notification modal.
 * @param {string} title - The title of the modal.
 * @param {string} message - The message to display in the modal body.
 * @param {string} type - The type of notification ('success', 'error', 'info'). Default is 'info'.
 */
function showGlobalNotification(title, message, type = 'info') {
    const modalElement = document.getElementById('notificationModal');
    if (!modalElement) {
        console.error('Notification modal element (#notificationModal) not found.');
        // Fallback to a simple alert if the modal isn't in the DOM
        alert(title + "\n\n" + message);
        return;
    }

    const modalTitleElement = document.getElementById('notificationModalLabel');
    const modalBodyElement = document.getElementById('notificationModalBody');
    const modalHeaderElement = document.getElementById('notificationModalHeader');

    if (modalTitleElement) modalTitleElement.textContent = title;
    if (modalBodyElement) modalBodyElement.innerHTML = message; // Use innerHTML if message can contain HTML

    // Set header color based on type
    if (modalHeaderElement) {
        modalHeaderElement.classList.remove('bg-success', 'bg-danger', 'bg-info', 'bg-primary', 'text-white', 'text-dark');
        let headerBgClass = 'bg-primary'; // Default
        let headerTextClass = 'text-white';

        switch (type.toLowerCase()) {
            case 'success':
                headerBgClass = 'bg-success';
                break;
            case 'error':
                headerBgClass = 'bg-danger';
                break;
            case 'info':
                headerBgClass = 'bg-info';
                headerTextClass = 'text-dark'; // Dark text is often more readable on info bg
                break;
        }
        modalHeaderElement.classList.add(headerBgClass, headerTextClass);
    }

    if (!globalNotificationModal) {
        globalNotificationModal = new bootstrap.Modal(modalElement);
    }
    globalNotificationModal.show();
}
