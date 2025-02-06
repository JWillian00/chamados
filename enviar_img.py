import requests
from flask import flash


#ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def upload_to_imgur(image_file):
    CLIENT_ID = '2bb212b2d974050'
    url = 'https://api.imgur.com/3/upload'
    headers = {'Authorization': f'Client-ID {CLIENT_ID}'}

    with open(image_file, 'rb') as image:
        files = {'image': image}
        response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        # Retorna a URL da imagem
        return response.json()['data']['link']
    else:
        print(f"Erro ao enviar para o Imgur: {response.text}")
        return None
