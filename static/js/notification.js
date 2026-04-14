export function mostrarNotificacao(mensagem, tipo, idChamado = null) {
    const notificacao = document.createElement('div');

    notificacao.style.position = 'fixed';
    notificacao.style.top = '20px';
    notificacao.style.right = '20px';
    notificacao.style.zIndex = '9999';
    notificacao.style.minWidth = '250px';

    notificacao.className = `p-4 rounded-md shadow-lg flex flex-col gap-2 ${
        tipo === 'success' 
            ? 'bg-green-500 text-white' 
            : tipo === 'warning'
            ? 'bg-yellow-500 text-white'
            : tipo === 'info'
            ? 'bg-blue-500 text-white'
            : 'bg-red-500 text-white'
    }`;

    const texto = document.createElement('span');
    texto.textContent = mensagem;
    notificacao.appendChild(texto);

    if (idChamado){
        const btnCopiar = document.createElement('button');
        btnCopiar.textContent = 'Copiar ID';
        btnCopiar.className = `
            bg-white text-black px-3 py-1 rounded text-sm w-fit 
            border border-gray-300 
            hover:bg-gray-100 
            cursor-pointer 
            transition
        `;

        btnCopiar.onclick = async () => {
            if (navigator.clipboard){
                await navigator.clipboard.writeText(idChamado.toString());

                btnCopiar.textContent = '✔ Copiado!';
                btnCopiar.classList.add('bg-green-200');

                setTimeout(() => {
                    btnCopiar.textContent = 'Copiar ID';
                    btnCopiar.classList.remove('bg-green-200');
                }, 2000);
            } else {
                alert('Copie manualmente: ' + idChamado);
            }
        };

        notificacao.appendChild(btnCopiar);
    }

    if (!document.body) return;
    document.body.appendChild(notificacao);

    setTimeout(() => {
        notificacao.remove();
    }, 5000);
}



export function salvarNotificacao(mensagem, tipo, idChamado = null) {
    sessionStorage.setItem('notificacaoMensagem', mensagem);
    sessionStorage.setItem('notificacaoTipo', tipo);

    if (idChamado !== null && idChamado !== undefined) {
        sessionStorage.setItem('notificacaoId', idChamado.toString());
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const mensagem = sessionStorage.getItem('notificacaoMensagem');
    const tipo = sessionStorage.getItem('notificacaoTipo');
    const id = sessionStorage.getItem('notificacaoId');
    if (mensagem && tipo) {
        mostrarNotificacao(mensagem, tipo, id);
        sessionStorage.removeItem('notificacaoMensagem');
        sessionStorage.removeItem('notificacaoTipo');
        sessionStorage.removeItem('notificacaoId');
    }
})

window.mostrarNotificacao = mostrarNotificacao;
window.salvarNotificacao = salvarNotificacao;