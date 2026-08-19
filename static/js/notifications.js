export function mostrarNotificacao(mensagem, tipo) {
      const notificacao = document.createElement('div');
      notificacao.className = `fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg transition-all duration-300 ${
          tipo === 'success' 
              ? 'bg-green-500 text-white' 
              : tipo === 'warning'
              ? 'bg-yellow-500 text-white'
              : tipo === 'info'
              ? 'bg-blue-500 text-white'
              : 'bg-red-500 text-white'
      }`;
      notificacao.textContent = mensagem;
      document.body.appendChild(notificacao);
      setTimeout(() => {
          notificacao.remove();
      }, 5000);
  }

function salvarNotificacao(mensagem, tipo) {
    sessionStorage.setItem('notificacaoMensagem', mensagem);
    sessionStorage.setItem('notificacaoTipo', tipo);
}

document.addEventListener("DOMContentLoaded", () => {
    const mensagem = sessionStorage.getItem('notificacaoMensagem');
    const tipo = sessionStorage.getItem('notificacaoTipo');
    if (mensagem && tipo) {
        mostrarNotificacao(mensagem, tipo);
        sessionStorage.removeItem('notificacaoMensagem');
        sessionStorage.removeItem('notificacaoTipo');
    }
})

window.mostrarNotificacao = mostrarNotificacao;