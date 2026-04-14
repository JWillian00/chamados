    import {mostrarNotificacao, salvarNotificacao} from './notification.js';
    
    document.addEventListener('DOMContentLoaded', function() {

    const form = document.getElementById('formchamado');
    const btnEnviar = document.getElementById('btnEnviar');

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

            console.log('enviando fetch');

            const missingFields = validateForm(formData);
            console.log("Campos faltando:", missingFields);
            console.log("Entrou na validação ❌");
            if (missingFields.length > 0) {
                console.log("Chamando notificação 🚨");
                mostrarNotificacao(`Os seguintes campos são obrigatórios: ${missingFields.join(', ')}`, 'warning');
                return;
            }

            const email = formData.get('email');
            if (!validateEmail(email)) {
                mostrarNotificacao('Por favor, insira um e-mail válido.', 'warning');
                return;
            }

            const response = await fetch('/aberturaChamado', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            console.log("response", response);
            

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const result = await response.json();
                console.log('Resposta do servidor:', result);

                if (result.success) {
                    const id = result.id_chamado || null;
                    mostrarNotificacao(`Chamado criado! ID: ${id}`, 'success', id);

                    form.reset();
                    const preview = document.getElementById('image-preview-container');
                    if (preview) preview.innerHTML = '';
                    
                } else {
                    console.error('Erro ao abrir chamado:', result.message);
                    mostrarNotificacao('Erro ao abrir chamado.', 'error');
                }
            } else {
                window.location.reload();
            }

        } catch (error) {
            console.error('Erro no fetch:', error);

            mostrarNotificacao(
                'Erro de conexão com o servidor.',
                'error'
            );
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

    // const inputs = form.querySelectorAll('input, select, textarea');
    // inputs.forEach(input => {
    //     input.addEventListener('input', function() {
    //         const alerts = flashContainer.querySelectorAll('.alert-danger');
    //         alerts.forEach(alert => alert.remove());
    //     });
    // });

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
