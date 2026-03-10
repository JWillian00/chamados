let ticketsTableBody
let todosCards = []
let ticketsCarregandos = false


function renderTickets(ticketsToRender){

    const tableBody = $('#tickets-table-body') 
    tableBody.empty()
     //limpa a tabela antes de renderizar os novos chamados

    if(ticketsToRender.length > 0){

        $('#tickets-table').show()
        $('#no-tickets-message').hide()

        ticketsToRender.forEach(chamado => {

            const data = new Date(chamado.data_criacao)

            const dataCriacaoFormatada =
            data.toLocaleDateString('pt-BR') + " " +
            data.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'})

            const row = `
            <tr class="hover:bg-gray-50 ticket-row">

                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${chamado.id_chamado_azure}</td>

                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${chamado.titulo}
                </td>

                <td class="px-6 py-4 whitespace-nowrap">
                            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full status-${chamado.status_chamado.toLowerCase().replace(' ', '_')}">
                                ${chamado.status_chamado}
                            </span>
                        </td>

                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${chamado.prioridade}
                </td>

                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${chamado.email_solicitante}
                </td>

                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${chamado.empresa_chamado}
                </td>

                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${chamado.plataforma_chamado}
                </td>

                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${dataCriacaoFormatada}
                </td>

                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <a href="#" onclick="openModal('${chamado.id_chamado}')">
                        Detalhes
                    </a>
                </td>

            </tr>
            `

            tableBody.append(row)

        })

    }
    else{

        $('#tickets-table').hide()
        $('#no-tickets-message').show()

    }
}



async function loadUserTickets(){

    try{

        const response = await fetch('/api/meus-chamados')

        if(!response.ok){
            throw new Error("Erro API")
        }

        const tickets = await response.json()

        tickets.sort((a, b) => {
            const prioridadeStatus = {
                "aberto": 1,
                "em andamento": 2,
                "andamento": 2,
                "fechado": 3
            }

            const statuA = (a.status_chamado || "").toLowerCase()
            const statuB = (b.status_chamado || "").toLowerCase()

            const prioridadeA = prioridadeStatus[statuA] || 99
            const prioridadeB = prioridadeStatus[statuB] || 99

            if (prioridadeA !== prioridadeB) {
                return prioridadeA - prioridadeB
            }

            return new Date(b.data_criacao) - new Date(a.data_criacao)


        })

        todosCards = tickets
        ticketsCarregandos = true

        renderTickets(todosCards)
        contadorChamados(todosCards)

    }
    catch(error){

        console.error(error)

        toastr.error("Erro ao carregar chamados")

    }

}



function searchTicket(){

    if(!ticketsCarregandos){
        toastr.info("Carregando chamados...")
        return
    }

    const searchId = $('#search-ticket-id').val().trim()

    if(searchId){

        const filtered = todosCards.filter(ticket =>

            (ticket.id_chamado_azure || "").toString().includes(searchId)
            ||
            ticket.titulo.toLowerCase().includes(searchId.toLowerCase())

        )

        renderTickets(filtered)
        contadorChamados(filtered)

    }
    else{

        renderTickets(todosCards)
        contadorChamados(todosCards)

    }

}



document.addEventListener('DOMContentLoaded', function(){

    ticketsTableBody = document.getElementById('tickets-table-body')

    loadUserTickets()

})

function contadorChamados(ticket){

    let total = ticket.length
    let aberto = 0
    let andamento = 0
    let fechados = 0

    ticket.forEach(ticket => {

        const status = ticket.status_chamado.toLowerCase()

        if(status.includes("aberto")){
            aberto++
        }
        else if(status.includes("andamento")){
            andamento++
        }
        else if(status.includes("fechado")){
            fechados++
        }

    })

    $('#total-chamados').hide().text(total).fadeIn(200)
    $('#aberto-chamados').text(aberto)
    $('#andamento-chamados').text(andamento)
    $('#fechado-chamados').text(fechados)
    $('#total-chamados').hide().text(total).fadeIn(200)

}