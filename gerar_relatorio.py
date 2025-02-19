from firebase_admin import firestore, credentials
from datetime import datetime
import firebase_admin


if not firebase_admin._apps:
    cred = credentials.Certificate('chamadosbraveo.json') 
    firebase_admin.initialize_app(cred)

def parse_date(data_str):
    try:
        if data_str:
            return datetime.strptime(data_str, "%Y-%m-%d")
        else:
            return None
    except ValueError:
        print(f"⚠ Erro ao converter a data: {data_str}")
        return None

def gerar_relatorio(data_inicial, data_final, filtro_data, filial, email, empresa, plataforma, titulo):   
    db = firestore.client()
    
    chamados_ref = db.collection("chamados_braveo")
    query = chamados_ref
 
    data_inicial = parse_date(data_inicial)
    data_final = parse_date(data_final)
 
    if data_inicial and data_final:
       
        data_inicial_ts = firestore.Timestamp.from_datetime(data_inicial)
        data_final_ts = firestore.Timestamp.from_datetime(data_final)
        query = query.where("data_criacao", ">=", data_inicial_ts) \
                     .where("data_criacao", "<=", data_final_ts)
    elif data_inicial:
        data_inicial_ts = firestore.Timestamp.from_datetime(data_inicial)
        query = query.where("data_criacao", ">=", data_inicial_ts)
    elif data_final:
        data_final_ts = firestore.Timestamp.from_datetime(data_final)
        query = query.where("data_criacao", "<=", data_final_ts)

    if filtro_data == 'fechamento':
        if data_inicial and data_final:
            data_inicial_ts = firestore.Timestamp.from_datetime(data_inicial)
            data_final_ts = firestore.Timestamp.from_datetime(data_final)
            query = query.where("data_fechamento", ">=", data_inicial_ts) \
                         .where("data_fechamento", "<=", data_final_ts)
        elif data_inicial:
            data_inicial_ts = firestore.Timestamp.from_datetime(data_inicial)
            query = query.where("data_fechamento", ">=", data_inicial_ts)
        elif data_final:
            data_final_ts = firestore.Timestamp.from_datetime(data_final)
            query = query.where("data_fechamento", "<=", data_final_ts)

    
    if filial:
        query = query.where("filial", "==", filial)
    if email:
        query = query.where("email", "==", email)
    if empresa:
        query = query.where("empresa", "==", empresa)
    if plataforma:
        query = query.where("plataforma", "==", plataforma)
    if titulo:
        query = query.where("titulo", "==", titulo)

   
    try:
        results = query.stream()
    except Exception as e:
        print(f"Erro na execução da consulta: {e}")
        return {"error": "Erro na execução da consulta ao Firestore"}

  
    chamados = []
    for chamado in results:
        chamado_dict = chamado.to_dict()
        chamado_dict["id_chamado"] = chamado_dict.get("id_chamado", "")

        if "data_criacao" in chamado_dict:
            chamado_dict["data_criacao"] = chamado_dict["data_criacao"].strftime("%Y-%m-%d") if isinstance(chamado_dict["data_criacao"], datetime) else ""
        if "data_fechamento" in chamado_dict:
            chamado_dict["data_fechamento"] = chamado_dict["data_fechamento"].strftime("%Y-%m-%d") if isinstance(chamado_dict["data_fechamento"], datetime) else ""

        chamados.append(chamado_dict)

    return {"chamados": chamados}
