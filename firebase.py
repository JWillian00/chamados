import firebase_admin
from firebase_admin import credentials, firestore
import time
import threading
from consulta_status_chamado import verificar_status_chamado
from envia_email_chamado import enviar_email_fechamento
from datetime import datetime
import pytz
#from google.cloud import firestore
import json
import os
import tempfile
 
firebase_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if not firebase_json:
    raise ValueError("A variável 'GOOGLE_APPLICATION_CREDENTIALS' não foi configurada corretamente.")

# Usando as credenciais diretamente sem a necessidade de um arquivo temporário
cred = credentials.Certificate(json.loads(firebase_json))
firebase_admin.initialize_app(cred)
db = firestore.client()

print("✅ Firebase conectado com sucesso!")
 
def salvar_chamado(empresa, plataforma, email, titulo, descricao, filial, id_chamado):
    chamados_ref = db.collection("chamados_braveo")
    novo_chamado = {
        "empresa": empresa,
        "plataforma": plataforma,
        "email": email,
        "titulo": titulo,
        "descricao": descricao,
        "filial": filial,
        "id_chamado": id_chamado,  
        "data_criacao": firestore.SERVER_TIMESTAMP 
    }
 
    doc_ref = chamados_ref.document()  
    doc_ref.set(novo_chamado)  
    id_banco_fb = doc_ref.id  
 
    print(f"ID Firebase: {id_banco_fb}")
    print(f"ID Azure: {id_chamado}")
 
def atualizar_chamado_fechado(id_chamado, estado, motivo, data_fechamento, usuario):
    chamados_ref = db.collection("chamados_braveo")
    query = chamados_ref.where("id_chamado", "==", id_chamado).stream()
 
    for doc in query:
        chamado = doc.to_dict()
        doc_ref = chamados_ref.document(doc.id)

        if "data_fechamento" in chamado:
            print(f"Chamado ja fechado")
            return False
                
 
        if isinstance(data_fechamento, str):
            try:
                data_fechamento = datetime.strptime(data_fechamento, "%Y-%m-%dT%H:%M:%S.%fZ")
 
                data_fechamento = pytz.utc.localize(data_fechamento)
                hora_brasil = data_fechamento.astimezone(pytz.timezone("America/Sao_Paulo"))
 
               
                data_fechamento = hora_brasil
            except ValueError:
                print(f"⚠ Erro ao converter a data_fechamento para datetime: {data_fechamento}")
                return False
        data_fechamento_formatada = data_fechamento.strftime("%d/%m/%Y %H:%M:%S")
 
        doc_ref.update({
            "estado": estado,
            "motivo_fechamento": motivo,
            "data_fechamento": data_fechamento,
            "usuario_fechamento": usuario
        })
 
        print(f"✅ Chamado fechado atualizado no Firebase: {id_chamado}")

        email_solicitante = chamado.get("email")
        if email_solicitante:
            enviar_email_fechamento(email_solicitante, id_chamado, estado, data_fechamento_formatada, usuario)
        else:
            print(f"⚠ Email do solicitante não encontrado para o chamado {id_chamado}")
        return True
    print(f"⚠ Chamado não encontrado no Firebase: {id_chamado}")
    return False
 
def job_monitora_chamado():
    while True:
        print("🔍 Buscando chamados abertos no Firebase...")
 
        try:
            chamados_abertos = db.collection("chamados_braveo").stream()
            chamados_pendentes = [doc for doc in chamados_abertos if not doc.to_dict().get("data_fechamento")]
 
            print(f"📟 Chamados encontrados: {len(chamados_pendentes)}")  
 
            if not chamados_pendentes:
                print("✅ Nenhum chamado pendente encontrado.")
            else:
                for doc in chamados_pendentes:
                    chamado = doc.to_dict()
                    id_chamado = chamado.get("id_chamado")
                    plataforma = chamado.get("plataforma")
 
                    if not id_chamado or not plataforma:
                        print("⚠ Chamado com informações incompletas, ignorando...")
                        continue
 
                    print(f"📌 Consultando status do chamado {id_chamado} ({plataforma})...")
 
                    status = verificar_status_chamado(id_chamado, plataforma)
 
                    if status.get("error"):
                        print(f"⚠ Erro ao consultar chamado {id_chamado}: {status['error']}")
                        continue
 
                    if status["estado_chamado"] in ["Closed", "Done"]:
                        print(f"✅ Chamado {id_chamado} foi fechado. Atualizando Banco de dados...")
 
                        atualizado = atualizar_chamado_fechado(
                            id_chamado,
                            status["estado_chamado"],
                            status["motivo_fechamento"],
                            status["data_fechamento"],
                            status["usuario_fechamento"]
                        )
 
                        if atualizado:
                            print(f"✔ Chamado {id_chamado} atualizado!")
                        else:
                            print(f"❌ Erro ao atualizar o chamado {id_chamado}.")
                    else:
                        print(f"⏳ Chamado {id_chamado} ainda não foi fechado.")
 
        except Exception as e:
            print(f"❌ Erro no monitoramento de chamados: {str(e)}")
 
        print("⏳ Aguardando próximo ciclo...")
        time.sleep(300)  
 
threading.Thread(target=job_monitora_chamado, daemon=True).start()
