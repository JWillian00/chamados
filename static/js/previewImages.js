function previewImages(event) {
    var files = event.target.files;
    var previewContainer = document.getElementById('image-preview-container');

    for (let i = 0; i < files.length; i++) {
        let file = files[i];

        if (file.type.startsWith('image/')) { // Verifica se é uma imagem
            let reader = new FileReader();
            reader.onload = function(e) {
                let imgContainer = document.createElement('div');
                imgContainer.classList.add('image-thumbnail-container');

                let img = document.createElement('img');
                img.src = e.target.result;
                img.classList.add('image-thumbnail');

                let deleteBtn = document.createElement('button');
                deleteBtn.innerText = 'X';
                deleteBtn.classList.add('delete-btn');
                deleteBtn.onclick = function() {
                    imgContainer.remove();
                };

                imgContainer.appendChild(img);
                imgContainer.appendChild(deleteBtn);
                previewContainer.appendChild(imgContainer);
            };
            reader.readAsDataURL(file);
        }
    }
}
