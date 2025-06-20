class ChamadosTempoReal {
    constructor() {
        this.eventSource = null;
        this.isConnected = false;
        this.reconectarTentativas = 0;
        this.maxTentativas = 5;
        this.chamados = [];
        this.statusElement = document.getElementById('status-tempo-real');
        this.listaElement = document.getElementById('lista-chamados');
        
        this.init();
    }
    
    init() {
        this.carregarChamadosIniciais();
        this.conectarSSE();
        this.configurarNotificacoes();
    }
    
    async carregarChamadosIniciais() {
        try {
            const response = await fetch('/api/chamados-tempo-real');
            const data = await response.json();
            
            if (data.success) {
                this.chamados = data.chamados;
                this.renderizarChamados();
                console.log(`✅ ${data.total} chamados carregados`);
            } else {
                console.error('❌ Erro ao carregar chamados:', data.error);
            }
        } catch (error) {
            console.error('❌ Erro na requisição inicial:', error);
        }
    }
    
    conectarSSE() {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        this.eventSource = new EventSource('/stream-chamados');
        
        this.eventSource.onopen = () => {
            console.log('✅ Conectado ao stream de tempo real');
            this.isConnected = true;
            this.reconectarTentativas = 0;
            this.atualizarStatusConexao('Conectado - Tempo Real Ativo', 'success');
        };
        
        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.processarEvento(data);
        };
        
        this.eventSource.onerror = (error) => {
            console.error('❌ Erro na conexão SSE:', error);
            this.isConnected = false;
            this.atualizarStatusConexao('Erro na conexão - Tentando reconectar...', 'error');
            
            // Tentar reconectar
            if (this.reconectarTentativas < this.maxTentativas) {
                this.reconectarTentativas++;
                setTimeout(() => {
                    console.log(`🔄 Tentativa de reconexão ${this.reconectarTentativas}/${this.maxTentativas}`);
                    this.conectarSSE();
                }, 5000 * this.reconectarTentativas);
            } else {
                this.atualizarStatusConexao('Conexão perdida - Atualize a página', 'error');
            }
        };
    }
    
    processarEvento(evento) {
        console.log('📡 Evento recebido:', evento.type, evento.data);
        
        switch (evento.type) {
            case 'novo_chamado':
                this.adicionarNovoChamado(evento.data);
                break;
                
            case 'chamado_atualizado':
                this.atualizarChamado(evento.data);
                break;
                
            case 'chamado_removido':
                this.removerChamado(evento.data.id);
                break;
                
            case 'heartbeat':
                // Manter conexão viva
                break;
                
            default:
                console.log('Evento desconhecido:', evento.type);
        }
    }
    
    adicionarNovoChamado(chamado) {
        // Verificar se já existe na lista
        const existe = this.chamados.find(c => c.id === chamado.id);
        if (!existe) {
            this.chamados.unshift(chamado); // Adicionar no início
            this.renderizarChamados();
            this.mostrarNotificacao(`Novo chamado: #${chamado.id_chamado}`, 'info');
            this.destacarChamado(chamado.id, 'novo');
        }
    }
    
    atualizarChamado(chamadoAtualizado) {
        const index = this.chamados.findIndex(c => c.id === chamadoAtualizado.id);
        
        if (index >= 0) {
            this.chamados[index] = chamadoAtualizado;
            this.renderizarChamados();
            this.mostrarNotificacao(`Chamado atualizado: #${chamadoAtualizado.id_chamado}`, 'warning');
            this.destacarChamado(chamadoAtualizado.id, 'atualizado');
        }
    }
    
    removerChamado(chamadoId) {
        this.chamados = this.chamados.filter(c => c.id !== chamadoId);
        this.renderizarChamados();
        this.mostrarNotificacao('Chamado removido da lista', 'info');
    }
    
    renderizarChamados() {
        if (!this.listaElement) return;
        
        this.listaElement.innerHTML = '';
        
        this.chamados.forEach(chamado => {
            const chamadoElement = this.criarElementoChamado(chamado);
            this.listaElement.appendChild(chamadoElement);
        });
        
        // Atualizar contador se existir
        const contador = document.getElementById('contador-chamados');
        if (contador) {
            contador.textContent = this.chamados.length;
        }
    }
    
    criarElementoChamado(chamado) {
        const div = document.createElement('div');
        div.className = 'chamado-card';
        div.id = `chamado-${chamado.id}`;
        div.dataset.chamadoId = chamado.id;
        
        const statusClass = this.getStatusClass(chamado.status_chamado);
        const prioridadeClass = this.getPrioridadeClass(chamado.prioridade);
        
        div.innerHTML = `
            <div class="chamado-header">
                <h3 class="chamado-titulo">#${chamado.id_chamado} - ${chamado.titulo}</h3>
                <div class="chamado-badges">
                    <span class="badge status ${statusClass}">${chamado.status_chamado}</span>
                    <span class="badge prioridade ${prioridadeClass}">${chamado.prioridade}</span>
                </div>
            </div>
            
            <div class="chamado-info">
                <p><strong>Cliente:</strong> ${chamado.usuario_nome || 'Desconhecido'}</p>
                <p><strong>Email:</strong> ${chamado.email_solicitante}</p>
                <p><strong>Empresa:</strong> ${chamado.empresa_chamado}</p>
                <p><strong>Plataforma:</strong> ${chamado.plataforma_chamado}</p>
                ${chamado.categoria ? `<p><strong>Categoria:</strong> ${chamado.categoria}</p>` : ''}
                ${chamado.responsavel_atendimento ? `<p><strong>Responsável:</strong> ${chamado.responsavel_atendimento}</p>` : ''}
            </div>
            
            <div class="chamado-descricao">
                <p>${chamado.descricao}</p>
            </div>
            
            <div class="chamado-footer">
                <small class="data-criacao">
                    Criado em: ${this.formatarData(chamado.data_criacao)}
                </small>
                ${chamado.data_atualizacao !== chamado.data_criacao ? 
                    `<small class="data-atualizacao">
                        Atualizado: ${this.formatarData(chamado.data_atualizacao)}
                    </small>` : ''
                }
            </div>
            
            <div class="chamado-acoes">
                <button class="btn btn-sm btn-primary" onclick="editarChamado('${chamado.id_chamado}')">
                    Editar
                </button>
                <button class="btn btn-sm btn-info" onclick="verDetalhes('${chamado.id_chamado}')">
                    Detalhes
                </button>
            </div>
        `;
        
        return div;
    }
    
    destacarChamado(chamadoId, tipo) {
        const elemento = document.getElementById(`chamado-${chamadoId}`);
        if (elemento) {
            elemento.classList.add(`chamado-${tipo}`);
            
            // Remover destaque após 3 segundos
            setTimeout(() => {
                elemento.classList.remove(`chamado-${tipo}`);
            }, 3000);
        }
    }
    
    getStatusClass(status) {
        const statusMap = {
            'Aberto': 'status-aberto',
            'Em Andamento': 'status-andamento',
            'Aguardando': 'status-aguardando',
            'Fechado': 'status-fechado',
            'Cancelado': 'status-cancelado'
        };
        return statusMap[status] || 'status-default';
    }
    
    getPrioridadeClass(prioridade) {
        const prioridadeMap = {
            'alta': 'prioridade-alta',
            'média': 'prioridade-media',
            'baixa': 'prioridade-baixa'
        };
        return prioridadeMap[prioridade?.toLowerCase()] || 'prioridade-baixa';
    }
    
    formatarData(dataString) {
        const data = new Date(dataString);
        return data.toLocaleString('pt-BR');
    }
    
    atualizarStatusConexao(mensagem, tipo) {
        if (this.statusElement) {
            this.statusElement.textContent = mensagem;
            this.statusElement.className = `status-conexao status-${tipo}`;
        }
    }
    
    configurarNotificacoes() {
        // Solicitar permissão para notificações
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
    
    mostrarNotificacao(mensagem, tipo = 'info') {
        // Notificação do navegador
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Sistema de Chamados', {
                body: mensagem,
                icon: '/static/images/icon.png',
                tag: 'chamado-update'
            });
        }
        
        // Notificação visual na página
        this.mostrarToast(mensagem, tipo);
    }
    
    mostrarToast(mensagem, tipo) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${tipo}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-message">${mensagem}</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
        `;
        
        // Adicionar ao container de toasts
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        // Remover automaticamente após 5 segundos
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
    
    // Método para limpar recursos
    destruir() {
        if (this.eventSource) {
            this.eventSource.close();
        }
    }
}

// CSS para os estilos (adicione ao seu CSS)
const estilosTempoReal = `
.chamado-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    margin: 10px 0;
    padding: 15px;
    background: white;
    transition: all 0.3s ease;
}

.chamado-novo {
    border-color: #28a745;
    background-color: #f8fff9;
    box-shadow: 0 2px 10px rgba(40, 167, 69, 0.2);
}

.chamado-atualizado {
    border-color: #ffc107;
    background-color: #fffef8;
    box-shadow: 0 2px 10px rgba(255, 193, 7, 0.2);
}

.chamado-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.chamado-titulo {
    margin: 0;
    color: #333;
    font-size: 1.1em;
}

.chamado-badges {
    display: flex;
    gap: 5px;
}

.badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: bold;
    text-transform: uppercase;
}

.status-aberto { background: #dc3545; color: white; }
.status-andamento { background: #007bff; color: white; }
.status-aguardando { background: #ffc107; color: black; }
.status-fechado { background: #28a745; color: white; }

.prioridade-alta { background: #dc3545; color: white; }
.prioridade-media { background: #ffc107; color: black; }
.prioridade-baixa { background: #6c757d; color: white; }

.status-conexao {
    padding: 5px 10px;
    border-radius: 4px;
    font-weight: bold;
    margin-bottom: 10px;
}

.status-success {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.status-error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
}

.toast {
    background: white;
    border-radius: 4px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 10px;
    max-width: 300px;
}

.toast-info { border-left: 4px solid #007bff; }
.toast-warning { border-left: 4px solid #ffc107; }
.toast-success { border-left: 4px solid #28a745; }

.toast-content {
    padding: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.toast-close {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: #999;
}
`;

// Adicionar estilos à página
const styleSheet = document.createElement('style');
styleSheet.textContent = estilosTempoReal;
document.head.appendChild(styleSheet);

// Inicializar quando a página carregar
let chamadosTempoReal;

document.addEventListener('DOMContentLoaded', function() {
    // Verificar se estamos numa página que precisa de tempo real
    if (document.getElementById('lista-chamados') || 
        window.location.pathname.includes('detalhes_chamados') ||
        window.location.pathname.includes('chamados')) {
        
        chamadosTempoReal = new ChamadosTempoReal();
        console.log('🚀 Sistema de tempo real inicializado');
    }
});

// Limpar recursos quando sair da página
window.addEventListener('beforeunload', function() {
    if (chamadosTempoReal) {
        chamadosTempoReal.destruir();
    }
});