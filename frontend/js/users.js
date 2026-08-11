// Users Page JavaScript for Vehicle Detection System

document.addEventListener('DOMContentLoaded', function() {
    if (!Common.requireAuth()) {
        return;
    }
    Common.initSidebar('users');
    initUsersPage();
});

function initUsersPage() {
    // Implemented in step 7 (admin CRUD)
}
