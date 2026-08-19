# run.py
import time
from app import app, socketio

# Controle de tempo para evitar requisições duplicadas
ultima_execucao = 0
intervalo_minimo = 2  # em segundos

def controlar_requisicoes():
    global ultima_execucao
    
    tempo_atual = time.time()
    if tempo_atual - ultima_execucao < intervalo_minimo:
        print("Requisição bloqueada. Tente novamente após alguns segundos.")
        return False
    
    ultima_execucao = tempo_atual
    return True

if __name__ == "__main__":
    if controlar_requisicoes():
        socketio.run(app, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0', port=5000)
