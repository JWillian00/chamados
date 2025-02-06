// Função para fazer o preview das imagens
function previewImages(event) {
    const files = event.target.files;
    const previewContainer = document.getElementById('image-preview-container');
    previewContainer.innerHTML = ''; // Limpar o preview anterior

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const reader = new FileReader();

        reader.onload = function(e) {
            const imgElement = document.createElement('img');
            imgElement.src = e.target.result;
            imgElement.classList.add('image-thumbnail'); // Adicionar classe para estilo

            const deleteButton = document.createElement('button');
            deleteButton.innerText = 'X';
            deleteButton.classList.add('delete-btn');
            deleteButton.onclick = function() {
                // Remover o container de imagem (incluindo a imagem e o botão de exclusão)
                previewContainer.removeChild(imageContainer);
            };

            const imageContainer = document.createElement('div');
            imageContainer.classList.add('image-thumbnail-container');
            imageContainer.appendChild(imgElement);
            imageContainer.appendChild(deleteButton);

            previewContainer.appendChild(imageContainer);
        };

        reader.readAsDataURL(file); // Leitura do arquivo para exibir a imagem
    }
}
