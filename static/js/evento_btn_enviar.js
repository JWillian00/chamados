document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('btnEnviar');

    if (btn) {
        btn.addEventListener('click', async function (event) {
            event.preventDefault();

            const form = btn.closest('form');
            if (!form) {
                console.error('Formulário não encontrado.');
                return;
            }

            btn.disabled = true;
            btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Registrando chamado, aguarde...';

            const formData = new FormData(form);

            try {
                const response = await fetch(form.action || window.location.href, {
                    method: form.method || 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error('Erro ao enviar o chamado');
                }

                const result = await response.json();
                console.log('Resposta do servidor:', result);

                if (result.flash_messages && result.flash_messages.length > 0) {
                    const flashMessagesContainer = document.getElementById('flash-messages');

                    if (flashMessagesContainer) {
                        flashMessagesContainer.innerHTML = ''; // Limpa mensagens anteriores

                        result.flash_messages.forEach(([category, message]) => {
                            const messageElement = document.createElement('div');
                            messageElement.classList.add('alert');

                            // Adiciona a classe CSS correta com base na categoria da mensagem
                            if (category === 'error') {
                                messageElement.classList.add('alert-danger'); // Para Bootstrap
                            } else if (category === 'success') {
                                messageElement.classList.add('alert-success');
                            }

                            messageElement.innerText = message;
                            flashMessagesContainer.appendChild(messageElement);
                        });

                        flashMessagesContainer.style.display = 'block';
                    }
                }

                if (result.success) {
                    form.reset();
                }

            } catch (error) {
                console.error('Erro:', error);
                alert('Ocorreu um erro ao enviar o chamado.');
            } finally {
                btn.disabled = false;
                btn.innerHTML = 'Enviar Chamado';
            }
        });
    }

    // Passo 3: Adiciona classes CSS automaticamente com base no texto da mensagem
    const flashMessages = document.querySelectorAll('#flash-messages div');
    flashMessages.forEach(function (msg) {
        if (msg.textContent.includes('sucesso')) {
            msg.classList.add('alert-success');
        } else if (msg.textContent.includes('Erro') || msg.textContent.includes('erro')) {
            msg.classList.add('alert-danger');
        }
    });
});