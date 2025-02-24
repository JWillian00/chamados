from firebase_admin import firestore, credentials
from datetime import datetime, timedelta
import firebase_admin

def ajustar_data_final(data_final):
    if data_final:        
        data_final = data_final.replace(hour=23, minute=59, second=59, microsecond=999999)
    return data_final

if not firebase_admin._apps:
    cred = credentials.Certificate("chamadosbraveo.json")
    firebase_admin.initialize_app(cred)

def parse_date(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%d") if data_str else None
    except ValueError:
        print(f"⚠ Erro ao converter a data: {data_str}")
        return None

def gerar_relatorio(data_inicial, data_final, filtro_data, filial, email, empresa, plataforma, titulo):   
    if not data_inicial:
        return {"error": "A data inicial é obrigatória para gerar o relatório."}
    
    db = firestore.client()    
   
    chamados_ref = db.collection("chamados_braveo")
    query = chamados_ref
    data_inicial = parse_date(data_inicial)
    data_final = parse_date(data_final) if data_final else None

    # Ajusta a data final para o fim do dia se foi informada
    if data_final:
        data_final = ajustar_data_final(data_final)
   
    if filtro_data == "abertura":
        # Filtra por data_criacao
        query = query.where("data_criacao", ">=", data_inicial)
        if data_final:
            query = query.where("data_criacao", "<=", data_final)
    elif filtro_data == "fechamento":   
        # Filtra por data_fechamento
        query = query.where("data_fechamento", ">=", data_inicial)
        if data_final:
            query = query.where("data_fechamento", "<=", data_final)

    try:      
        results = query.stream()
    except Exception as e:
        print(f"Erro na execução da consulta: {e}")
        return {"error": "Erro na execução da consulta ao Firestore"}
    
    chamados = []
    for chamado in results:
        chamado_dict = chamado.to_dict()

        chamado_dict["id_chamado"] = chamado_dict.get("id_chamado", "N/A")
        
        if "data_criacao" in chamado_dict and chamado_dict["data_criacao"]:
            if isinstance(chamado_dict["data_criacao"], datetime):
                chamado_dict["data_criacao"] = chamado_dict["data_criacao"].strftime("%Y-%m-%d")
            else:
                chamado_dict["data_criacao"] = ""

        if "data_fechamento" in chamado_dict and chamado_dict["data_fechamento"]:
            if isinstance(chamado_dict["data_fechamento"], datetime):
                chamado_dict["data_fechamento"] = chamado_dict["data_fechamento"].strftime("%Y-%m-%d")
            else:
                chamado_dict["data_fechamento"] = ""
        else:
            chamado_dict["data_fechamento"] = ""  

        # Filtro adicional para chamados abertos (sem data_fechamento)
        if filtro_data == "abertura":
            if "data_fechamento" not in chamado_dict or not chamado_dict["data_fechamento"]:
                chamados.append(chamado_dict)
        elif filtro_data == "fechamento":
            if "data_fechamento" in chamado_dict and chamado_dict["data_fechamento"]:
                chamados.append(chamado_dict)

    # Filtros de texto insensíveis a maiúsculas/minúsculas
    if filial:
        chamados = [c for c in chamados if "filial" in c and filial.lower() in c["filial"].lower()]
    if email:
        chamados = [c for c in chamados if "email" in c and email.lower() in c["email"].lower()]
    if empresa:
        chamados = [c for c in chamados if "empresa" in c and empresa.lower() in c["empresa"].lower()]
    if plataforma:
        chamados = [c for c in chamados if "plataforma" in c and plataforma.lower() in c["plataforma"].lower()]
    if titulo:
        chamados = [c for c in chamados if "titulo" in c and titulo.lower() in c["titulo"].lower()]

    if not chamados:
        return {"message": "Nenhum dado encontrado"}
    
    return {"chamados": chamados}