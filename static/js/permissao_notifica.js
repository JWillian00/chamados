// notificacoes.js

// Função para solicitar permissão de notificação
function requestNotificationPermission() {
    if (!("Notification" in window)) {
        console.warn("Este navegador não suporta notificações de desktop.");
        return;
    }

    if (Notification.permission === "granted") {
      //  console.log("Permissão para notificações já concedida.");
    } else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(permission => {
            if (permission === "granted") {
                console.log("Permissão para notificações concedida!");
            } else {
                console.warn("Permissão para notificações negada.");
            }
        });
    }
}

// Função para exibir a notificação
function showNotification(title, body) {
    if (!("Notification" in window)) {
        console.warn("Este navegador não suporta notificações de desktop.");
        return;
    }

    if (Notification.permission === "granted") {
        const options = {
            body: body,
            icon: 'https://cdn.icon-icons.com/icons2/2248/PNG/512/whatsapp_icon_136118.png'
        };
        new Notification(title, options);
    } else if (Notification.permission !== "denied") {
        requestNotificationPermission();
        alert("Por favor, permita as notificações para ver os alertas de chamados.");
    }
}

// Função para processar as mensagens flash recebidas do Flask
function processFlaskMessages(messages) {
    messages.forEach(msg => {
        if (msg.category === 'success' && msg.message.includes('Chamado criado com sucesso!')) {
            const match = msg.message.match(/ID: (\w{3}-\w{3})/);
            if (match) {
                const chamadoId = match[1];
                showNotification("Novo Chamado Criado!", `Seu chamado ${chamadoId} foi aberto com sucesso.`);
            } else {
                showNotification("Novo Chamado Criado!", msg.message);
            }
        }
        // else if (msg.category === 'error') {
        //     showNotification("Erro no Sistema", msg.message);
        // }
    });
}