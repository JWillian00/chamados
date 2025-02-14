from firebase import db
from datetime import datetime
from google.cloud import firestore

def gerar_relatorio(data_inicial, data_final, filtro_data, filial, email, empresa, plataforma, titulo):
    chamados_ref = db.collection("chamados_braveo")

    query = chamados_ref

    print("Inicializando consulta...")

    def parse_date(data_str):
        try:
            return datetime.strptime(data_str, "%Y-%m-%d") if data_str else None
        except ValueError:
            print(f"⚠ Erro ao converter a data: {data_str}")
            return None

  
    data_inicial = parse_date(data_inicial)
    data_final = parse_date(data_final)   
    

    if data_inicial and data_final:
        print(f"Aplicando filtro de data_criacao entre {data_inicial} e {data_final}")
        # Convertendo as datas para timestamp antes de aplicar
        query = query.where('data_criacao', '>=', firestore.Timestamp.from_datetime(data_inicial))
        query = query.where('data_criacao', '<=', firestore.Timestamp.from_datetime(data_final))
    elif data_inicial:
        print(f"Aplicando filtro de data_criacao a partir de {data_inicial}")
        query = query.where("data_criacao", ">=", firestore.Timestamp.from_datetime(data_inicial))
    elif data_final:
        print(f"Aplicando filtro de data_criacao até {data_final}")
        query = query.where("data_criacao", "<=", firestore.Timestamp.from_datetime(data_final))

    # Filtros adicionais
    if filtro_data == "fechamento":
        if data_inicial and data_final:
            print(f"Aplicando filtro de data_fechamento entre {data_inicial} e {data_final}")
            query = query.where('data_fechamento', '>=', firestore.Timestamp.from_datetime(data_inicial))
            query = query.where('data_fechamento', '<=', firestore.Timestamp.from_datetime(data_final))
        elif data_inicial:
            print(f"Aplicando filtro de data_fechamento a partir de {data_inicial}")
            query = query.where('data_fechamento', '>=', firestore.Timestamp.from_datetime(data_inicial))
        elif data_final:
            print(f"Aplicando filtro de data_fechamento até {data_final}")
            query = query.where('data_fechamento', '<=', firestore.Timestamp.from_datetime(data_final))

    # Filtros adicionais
    if filial:
        print(f"Aplicando filtro de filial: {filial}")
        query = query.where("filial", "==", filial)
    if email:
        print(f"Aplicando filtro de email: {email}")
        query = query.where("email", "==", email)
    if empresa:
        print(f"Aplicando filtro de empresa: {empresa}")
        query = query.where("empresa", "==", empresa)
    if plataforma:
        print(f"Aplicando filtro de plataforma: {plataforma}")
        query = query.where("plataforma", "==", plataforma)
    if titulo:
        print(f"Aplicando filtro de título: {titulo}")
        query = query.where("titulo", "==", titulo)

    # Executar a consulta
    results = query.stream()

    # Verificar se resultados foram retornados
    chamados = []
    for doc in results:
        chamado = doc.to_dict()
        print(f"Encontrado chamado: {chamado['id_chamado']}")  # Verificar quais dados estão sendo retornados
        chamado["id_chamado"] = doc.id
        
        # Converte o timestamp para uma string no formato 'YYYY-MM-DD'
        chamado["data_criacao"] = chamado.get("data_criacao", "").strftime("%Y-%m-%d") if chamado.get("data_criacao") else ""
        chamado["data_fechamento"] = chamado.get("data_fechamento", "").strftime("%Y-%m-%d") if chamado.get("data_fechamento") else ""
        
        chamados.append(chamado)

    print(f"Total de chamados encontrados: {len(chamados)}")

    return chamados
