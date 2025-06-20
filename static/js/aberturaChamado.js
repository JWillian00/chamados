// JavaScript para envio do formulário de abertura de chamado
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('formchamado');
    const btnEnviar = document.getElementById('btnEnviar');
    const flashContainer = document.getElementById('flash-messages');

    // Função para mostrar mensagens de flash
    function showFlashMessage(message, type) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const alertHtml = `
            <div class="alert ${alertClass}" style="margin-bottom: 15px; padding: 10px; border-radius: 4px;">
                ${message}
            </div>
        `;
        flashContainer.innerHTML = alertHtml;

        setTimeout(() => {
            flashContainer.innerHTML = '';
        }, 20000);

        flashContainer.scrollIntoView({ behavior: 'smooth' });
    }

    function validateForm(formData) {
        const requiredFields = [
            { name: 'empresa', label: 'Empresa' },
            { name: 'plataforma', label: 'Plataforma' },
            { name: 'email', label: 'E-mail' },
            { name: 'titulo2', label: 'Título' },
            { name: 'descricao', label: 'Descrição' },
            { name: 'categoria', label: 'categoria' }
        ];

        const missingFields = [];

        for (const field of requiredFields) {
            const value = formData.get(field.name);
            if (!value || value.trim() === '') {
                missingFields.push(field.label);
            }
        }

        return missingFields;
    }

    function validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        btnEnviar.disabled = true;
        btnEnviar.textContent = 'Enviando...';

        try {
            const formData = new FormData(form);

            const missingFields = validateForm(formData);
            if (missingFields.length > 0) {
                const message = `Os seguintes campos são obrigatórios: ${missingFields.join(', ')}`;
                showFlashMessage(message, 'error');
                return;
            }

            const email = formData.get('email');
            if (!validateEmail(email)) {
                showFlashMessage('Por favor, insira um e-mail válido.', 'error');
                return;
            }

            const response = await fetch('/aberturaChamado', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const result = await response.json();

                if (result.flash_messages && result.flash_messages.length > 0) {
                    flashContainer.innerHTML = '';

                    result.flash_messages.forEach(([category, message]) => {
                        showFlashMessage(message, category);

                        if (category === 'success') {
                            showWhatsappNotification(message);
                            form.reset();
                            document.getElementById('empresa').focus();
                        }
                    });
                }
            } else {
                window.location.reload();
            }

        } catch (error) {
            console.error('Erro ao enviar chamado:', error);
            showFlashMessage('Erro interno do servidor. Tente novamente.', 'error');
        } finally {
            btnEnviar.disabled = false;
            btnEnviar.textContent = 'Enviar Chamado';
        }
    });

    window.previewImages = function(event) {
        const container = document.getElementById('image-preview-container');
        container.innerHTML = '';

        const files = event.target.files;

        for (let i = 0; i < files.length; i++) {
            const file = files[i];

            if (file.type.startsWith('image/')) {
                const reader = new FileReader();

                reader.onload = function(e) {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.style.maxWidth = '200px';
                    img.style.maxHeight = '200px';
                    img.style.margin = '5px';
                    img.style.border = '1px solid #ddd';
                    img.style.borderRadius = '4px';
                    container.appendChild(img);
                };

                reader.readAsDataURL(file);
            }
        }
    };

    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            const alerts = flashContainer.querySelectorAll('.alert-danger');
            alerts.forEach(alert => alert.remove());
        });
    });

    function showWhatsappNotification(message) {
        const notification = document.getElementById('whatsapp-notification');
        const messageElement = document.getElementById('whatsapp-message');

        const textMessage = message.replace(/<[^>]*>?/gm, '');
        messageElement.textContent = textMessage;
        notification.classList.add('show');        

        setTimeout(() => {
            notification.classList.remove('show');
        }, 10000);
    }

    function closeWhatsappNotification() {
        const notification = document.getElementById('whatsapp-notification');
        notification.classList.remove('show');
    }

    window.closeWhatsappNotification = function() {
        const notification = document.getElementById('whatsapp-notification');
        notification.classList.remove('show');
    };
    window.showWhatsappNotification = showWhatsappNotification; 
    window.closeWhatsappNotification = closeWhatsappNotification;
});
