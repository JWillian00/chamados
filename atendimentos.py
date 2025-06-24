
from supabase import create_client, Client
from datetime import datetime
#from supabase_config import SUPABASE_URL, SUPABASE_KEY
from flask import  flash
from supabase import create_client, Client
import os
import json
from dotenv import load_dotenv



load_dotenv()
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
#supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_chamados_abertos():
    try:
        response_chamados = supabase \
            .from_('chamados') \
            .select('*') \
            .neq('status_chamado', 'Fechado') \
            .execute()
        
        chamados = response_chamados.data
        user_names_cache = {}

        for chamado in chamados:
            email_solicitante = chamado.get('email_solicitante')
            if email_solicitante and email_solicitante not in user_names_cache:
                response_user = supabase.from_('usuarios').select('nome').eq('email', email_solicitante).execute()
                
                if isinstance(response_user.data, list) and len(response_user.data) > 0:
                    user_names_cache[email_solicitante] = response_user.data[0].get('nome', email_solicitante)
                else:
                    user_names_cache[email_solicitante] = email_solicitante

            chamado['nome_solicitante'] = user_names_cache.get(email_solicitante, email_solicitante)

        return chamados

    except Exception as e:
        print(f"Erro ao buscar chamados abertos: {e}")
        return []

def get_usuario_by_email(email):

    try:
        response = supabase.table('usuarios').select('nome, telefone').eq('email', email).execute()
        if response.data:
            return response.data[0] 
        return {'nome': 'Usuário não encontrado', 'telefone': ''} 
    except Exception as e:
        
        print(f"Erro ao buscar usuário por email {email}: {e}")
        return {'nome': 'Erro na busca', 'telefone': ''}

def get_chamado_detalhes(id_chamado):
   
    try:
        
        response = supabase.table('chamados').select('*').eq('id_chamado', id_chamado).single().execute()
        return response.data
    except Exception as e:
        print(f"Erro ao buscar detalhes do chamado {id_chamado}: {e}")
        return None

def update_chamado(id_chamado, data_to_update):

    try:
      
        data_to_update['data_atualizacao'] = datetime.now().isoformat()

       
        current_status = data_to_update.get('status_chamado')

        if current_status == 'Fechado' and 'data_fechamento' not in data_to_update:

            data_to_update['data_fechamento'] = datetime.now().isoformat()
        elif current_status != 'Fechado' and 'data_fechamento' in data_to_update and data_to_update['data_fechamento'] is not None:
 
            data_to_update['data_fechamento'] = None


        response = supabase.table('chamados').update(data_to_update).eq('id_chamado', id_chamado).execute()

       
        if response.data:
            #flash(f"Chamado {id_chamado} atualizado com sucesso!")
            return True
        else:
           
            print(f"Nenhum dado retornado na atualização do chamado {id_chamado}. ID pode não existir ou sem alterações.")
            return False
    except Exception as e:
        print(f"Erro ao atualizar chamado {id_chamado}: {e}")
        return False


def add_comentario(chamado_id, nome_usuario, email_usuario, comentario_texto, anexos=[]):
    try:
        data={
            'chamado_id': chamado_id,
            'nome_usuario': nome_usuario,
            'email_usuario': email_usuario,
            'comentario_texto': comentario_texto,
            'anexos': anexos
        }
        response = supabase.table('comentarios_chamados').insert(data).execute()
        if response.data:
            try:
                supabase.table('chamados').update({'comentario_novo': True}).eq('id_chamado', chamado_id).execute()
            except Exception as e:
                print(f"Erro ao marcar comentario_novo=True para o chamado {chamado_id}: {e}")

            return response.data[0]
        else:
            print(f"Erro ao adicionar comentario ao chamado {chamado_id}")
            return None
    except Exception as e:
        print(f"Erro ao adicionar comentario ao chamado {chamado_id}: {e}")
        return None
    
def get_comentarios_by_chamado_id(chamado_id):
    try:
        response = supabase.table('comentarios_chamados').select('*') \
            .eq('chamado_id', chamado_id) \
            .order('data_hora', desc=False) \
            .execute()
        return response.data
    except Exception as e:
        print(f"Erro ao buscar comentários para o chamado {chamado_id}: {e}")
        return []
