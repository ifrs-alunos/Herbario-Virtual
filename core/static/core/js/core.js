// Seleciona tag spam onde deve ser inserido o ano atual no footer
var spam = document.getElementById("ano_atual");

now = new Date;
seleciona_ano = now.getFullYear();

// Insere no HTML
spam.innerHTML += seleciona_ano; 

// Código JS da Galeria de imagens

// Objetivo 1: Trocar a imagem em destaque e o estilo do elemento quando o usuario clica em uma imagem em miniatura

// Seleciona todos os elementos com a classe "imagem_miniatura"
var imagens_miniaturas = document.getElementsByClassName("imagem_miniatura");

// Indica que, quando algum elemento da seleção for clicado, dispara a função tornar_destaque
for (var i = 0; i < imagens_miniaturas.length ; ++i){
  	imagens_miniaturas[i].onclick = tornar_destaque;
}

function tornar_destaque(event) {

	// Se a imagem clicada contém a classe "imagem_selecionada"
    if (event.target.classList.contains("imagem_selecionada")) {
    	// pass
    } else {
    	// Seleciona o elemento que contém a classe "imagem_selecionada"
		var imagem_selecionada = document.getElementsByClassName("imagem_selecionada")[0];

		// Remove a classe "imagem_selecionada" do elemento
    	imagem_selecionada.classList.remove("imagem_selecionada");

    	// Adiciona a classe "imagem_selecionada" ao novo elemento que foi clicado
    	event.target.classList.add("imagem_selecionada");

    	// Seleciona o elemento que contém a classe "imagem_em_destaque"
    	var imagem_em_destaque = document.getElementsByClassName("imagem_em_destaque")[0];

    	// Troca o atributo "src" da imagem anterior pelo atributo "src" da nova imagem que foi clicada
    	imagem_em_destaque.setAttribute("src", event.target.src);
    }
}

// $("#zoom_07").elevateZoom({
//     // zoomType: "inner",
//     // cursor: "crosshair"

//     // zoomType: "lens",
//     // lensShape: "round",
//     // lensSize: 200,

//     // scrollZoom : true,
//     // zoomType: "inner",
//     // cursor: "crosshair",
// });

// // Carrosel das Plantas
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
