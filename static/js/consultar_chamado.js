
document.addEventListener('DOMContentLoaded', function() {
    const socket = io(); 

    const ticketsTableBody = document.getElementById('tickets-table-body');
    const noTicketsMessage = document.getElementById('no-tickets-message');
    const ticketsTable = document.getElementById('tickets-table');
    const searchInput = document.getElementById('search-ticket-input');

    async function loadUserTickets() {
        try {
            const response = await fetch('/api/meus_chamados');
            if (!response.ok) {                
                const errorData = await response.json();
                throw new Error(errorData.error || `Erro HTTP: ${response.status}`);
            }
            const tickets = await response.json();
            
            ticketsTableBody.innerHTML = '';

            if (tickets.length === 0) {
                noTicketsMessage.style.display = 'block';
                ticketsTable.style.display = 'none';
            } else {
                noTicketsMessage.style.display = 'none';
                ticketsTable.style.display = 'table'; 

                tickets.forEach(ticket => {
                    const row = ticketsTableBody.insertRow();
                    row.className = 'ticket-row';

                    row.insertCell(0).textContent = ticket.id_chamado;
                    row.insertCell(1).textContent = ticket.titulo;
                    row.insertCell(2).textContent = ticket.status;
                    row.insertCell(3).textContent = ticket.prioridade;
                    row.insertCell(4).textContent = ticket.solicitante_nome || 'N/A'; 
                    row.insertCell(5).textContent = ticket.departamento || 'N/A'; 
                    row.insertCell(6).textContent = ticket.data_abertura;

                    
                    const actionsCell = row.insertCell(7);
                    const detailsButton = document.createElement('button');
                    detailsButton.textContent = 'Ver Detalhes';
                    detailsButton.className = 'details-button';
                    detailsButton.onclick = () => {
                        
                        window.location.href = `/detalhes_chamados/${ticket.id_chamado}`;
                    };
                    actionsCell.appendChild(detailsButton);
                });
            }
        } catch (error) {
            console.error('Erro ao carregar chamados:', error);
            toastr.error(`Erro ao carregar chamados: ${error.message}`);
            noTicketsMessage.textContent = 'Erro ao carregar chamados. Por favor, tente novamente.';
            noTicketsMessage.style.display = 'block';
            ticketsTable.style.display = 'none';
        }
    }

    
    loadUserTickets();

    
    searchInput.addEventListener('keyup', function() {
        const filter = searchInput.value.toLowerCase();
        const rows = ticketsTableBody.querySelectorAll('.ticket-row'); 

        rows.forEach(row => {
            const rowText = Array.from(row.cells).slice(0, -1).map(cell => cell.textContent).join(' ').toLowerCase();
            if (rowText.includes(filter)) {
                row.style.display = ''; // Exibe a linha
            } else {
                row.style.display = 'none'; // Oculta a linha
            }
        });
    });

   
    socket.on('chamado_atualizado', (data) => {
        console.log('Chamado atualizado', data);
        loadUserTickets(); 
    });
    socket.on('novo_chamado', (data) => {
        console.log('Novo chamado', data);
        loadUserTickets(); // Recarrega os chamados para incluir o novo
    });
    
});