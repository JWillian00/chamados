from firebase import db
from datetime import datetime

def gerar_relatorio(data_inicial, data_final, filtro_data, filial, email, empresa, plataforma, titulo):
    chamados_ref = db.collection("chamados_braveo")

    query = chamados_ref

    print("Inicializando consulta...")
    print(f"Filtro de data: {filtro_data}")

    
    if filtro_data == "abertura":
        if data_inicial:
            data_inicial = datetime.strptime(data_inicial, "%Y-%m-%d")
            query = query.filter("data_criacao", ">=", data_inicial)
        if data_final:
            data_final = datetime.strptime(data_final, "%Y-%m-%d")
            query = query.filter("data_criacao", "<=", data_final)

    elif filtro_data == "fechamento":
        if data_inicial:
            data_inicial = datetime.strptime(data_inicial, "%Y-%m-%d")
            query = query.filter("data_fechamento", ">=", data_inicial)
        if data_final:
            data_final = datetime.strptime(data_final, "%Y-%m-%d")
            query = query.filter("data_fechamento", "<=", data_final)

   
    if filial:
        query = query.filter("filial", "==", filial)
    if email:
        query = query.filter("email", "==", email)
    if empresa:
        query = query.filter("empresa", "==", empresa)
    if plataforma:
        query = query.filter("plataforma", "==", plataforma)
    if titulo:
        query = query.filter("titulo", "==", titulo)

   
    results = query.stream()

    
    chamados = [] 
    for doc in results:
        chamado = doc.to_dict()
        chamado["id_chamado"] = chamado.get("id_chamado")  
        chamados.append(chamado)

    return chamados
