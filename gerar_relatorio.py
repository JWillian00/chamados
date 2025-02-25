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
    db = firestore.client()    
    chamados_ref = db.collection("chamados_braveo")
    query = chamados_ref

    data_inicial = parse_date(data_inicial)
    data_final = parse_date(data_final) if data_final else None

    # Ajusta a data final para o fim do dia se foi informada
    if data_final:
        data_final = ajustar_data_final(data_final)

    # Verifica as regras de combinação de datas e filtros
    if filtro_data == "abertura":
        if not data_inicial:
            return {"message": "Informar data de abertura"}
        if data_final:
            # Filtra chamados abertos a partir da data_inicial e com data_fechamento <= data_final
            query = query.where("data_criacao", ">=", data_inicial).where("data_fechamento", "<=", data_final)
        else:
            # Filtra chamados abertos a partir da data_inicial
            query = query.where("data_criacao", ">=", data_inicial)
        # Ordena por data_criacao (menor para maior)
        query = query.order_by("data_criacao")

    elif filtro_data == "fechamento":
        if not data_final:
            return {"message": "Informar data de fechamento"}
        if data_inicial:
            # Filtra chamados fechados a partir da data_final e com data_criacao <= data_inicial
            query = query.where("data_fechamento", ">=", data_final).where("data_criacao", "<=", data_inicial)
        else:
            # Filtra chamados fechados até a data_final, sem considerar data_criacao
            query = query.where("data_fechamento", "<=", data_final)
        # Ordena por data_fechamento (menor para maior)
        query = query.order_by("data_fechamento")

    try:      
        results = query.stream()
    except Exception as e:
        print(f"Erro na execução da consulta: {e}")
        return {"error": "Erro na execução da consulta ao Firestore"}
    
    chamados = []
    for chamado in results:
        chamado_dict = chamado.to_dict()

        chamado_dict["id_chamado"] = chamado_dict.get("id_chamado", "N/A")
        
        # Formata data_criacao para DD/MM/YYYY
        if "data_criacao" in chamado_dict and chamado_dict["data_criacao"]:
            if isinstance(chamado_dict["data_criacao"], datetime):
                chamado_dict["data_criacao"] = chamado_dict["data_criacao"].strftime("%d/%m/%Y")
            else:
                chamado_dict["data_criacao"] = ""

        # Formata data_fechamento para DD/MM/YYYY
        if "data_fechamento" in chamado_dict and chamado_dict["data_fechamento"]:
            if isinstance(chamado_dict["data_fechamento"], datetime):
                chamado_dict["data_fechamento"] = chamado_dict["data_fechamento"].strftime("%d/%m/%Y")
            else:
                chamado_dict["data_fechamento"] = ""
        else:
            chamado_dict["data_fechamento"] = ""  

        # Adiciona o chamado à lista de resultados
        chamados.append(chamado_dict)

    # Filtros adicionais para chamados abertos (sem data_fechamento)
    if filtro_data == "abertura" and not data_final:
        chamados = [c for c in chamados if "data_fechamento" not in c or not c["data_fechamento"]]
 
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