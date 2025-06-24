from datetime import datetime, timedelta
#from supabase_config import supabase
import pytz
import os
from supabase import create_client, Client
from dotenv import load_dotenv


load_dotenv()
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
#supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def registrar_movimentacao_chamado(id_chamado, tipo, valor_anterior, valor_novo, usuario):
    try:
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario)
        
        dados_movimentacao = {
            'id_chamado': id_chamado,
            'tipo': tipo, 
            'valor_anterior': valor_anterior,
            'valor_novo': valor_novo,
            'usuario': usuario,
            'data': agora.isoformat()
        }
        
        response = supabase.table('movimentacoes_chamado').insert(dados_movimentacao).execute()
        
        if response.data:

            print(f"Movimentação registrada: {tipo} para chamado {id_chamado}")
            return True
        else:
            print(f"Erro ao registrar movimentação: {response.error}")
            return False
            
    except Exception as e:
        print(f"Erro ao registrar movimentação do chamado {id_chamado}: {e}")
        return False

