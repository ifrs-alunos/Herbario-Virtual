// Seleciona tag spam onde deve ser inserido o ano atual
var spam = document.getElementById("ano_atual");

now = new Date;
seleciona_ano = now.getFullYear();

// Insere no HTML
spam.innerHTML += seleciona_ano; 

var lightbox = new SimpleLightbox('.gallery a', {maxZoom:100});

// // Carrosel das Plamtas
// //Essa função controla que imagem deve aparecer no carrosel e coisas relacionadas a isso
// var carosel_index = 0;
// function show_slide (new_index)
// {
//     // Esconde o anterior e mostra o de agora.
//     document.getElementsByClassName('zoom_image')[carosel_index].setAttribute('hidden', 'true');
//     document.getElementsByClassName('zoom_image')[new_index].removeAttribute('hidden');
//     //Da pra melhorar a relação entre remover a classe em vez de setar para false
//     document.getElementsByClassName('slide_index')[carosel_index].classList.remove('select');
//     document.getElementsByClassName('slide_index')[new_index].classList.add('select');

//     carosel_index = new_index

// }

// // Zoom nas imagens do Carrosel
// //Está funcão só controla que parte da imagem com zoom será mostrada em realção as coordenadas do mouse
// function zoom(e)
// {
//     //Faz a imagem de tamanho normal sumir
//     //converte a posição em coordenadas para porcentagem
//     var x = e.offsetX * 100 / e.currentTarget.offsetWidth;
//     var y = e.offsetY * 100 / e.currentTarget.offsetHeight;
//     //Define esse valores para o backgroundPosition
//     e.currentTarget.style.backgroundPosition = "" + x + "%" + y + "%";

// }

// //Fyuse e visualização em 360°
// function fyuse(){
//     a = document.getElementsByClassName('imagefyuse')[0];
//     if (a.hasAttribute('hidden')){
//         document.getElementsByClassName('carosel')[0].setAttribute('hidden', 'true');
//         document.getElementsByClassName('imagefyuse')[0].removeAttribute('hidden');
//     }
//     else {
//         document.getElementsByClassName('imagefyuse')[0].setAttribute('hidden', 'true');
//         document.getElementsByClassName('carosel')[0].removeAttribute('hidden');
//     }

// }
