// Código JS da Galeria de imagens

// Seleciona todos os elementos com a classe "imagem_miniatura"
var imagens_miniaturas = document.getElementsByClassName("imagem_miniatura");
// Indica que, quando algum elemento da seleção for clicado, dispara a função tornar_destaque
for (var i = 0; i < imagens_miniaturas.length ; ++i){
  	imagens_miniaturas[i].onclick = tornar_destaque;

}


// Função responsável por retirar uma imagem em destaque e inserir outra, além de tornar o zoom funcional em todas as imagens 
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

    	// Chama a função de adicionar a contri text na imagem em destage
    	add_contri_text(event.target)

        // Troca valor dos atributos src e data-zoom-image da imagem em destaque
        imagem_em_destaque.setAttribute("data-zoom-image", event.target.src);
        imagem_em_destaque.setAttribute("src", event.target.src);


        // Implementações necessárias para que o zoom funcione com todos os elementos da galeria:

        // Seleciona o elemento criado pela biblioteca e o remove
        zoom_container = document.getElementsByClassName("zoomContainer")[0];
        zoom_container.remove();

        // Seleciona o elemento que será aplicado o zoom, ou seja, o elemento que contém a "imagem antiga" e o remove
        img = document.getElementById("zoom");
        img.remove();

        // Seleciona o atributo "data-zoom-image" do elemento que disparou a função
        data_zoom_image = event.target.getAttribute("data-zoom-image");

        // Cria um novo elemento onde será aplicado o zoom e insere seus atributos
        new_img = document.createElement("img");
        new_img.setAttribute("id", "zoom");
        new_img.classList.add("imagem_em_destaque");
        new_img.setAttribute("src", event.target.src);
        new_img.setAttribute("data-zoom-image", data_zoom_image);
        new_img.style.width = "715px";
        new_img.style.height = "430px";

        // Insere no HTML esse novo elemento criado
        document.querySelector(".galeria > .row").appendChild(new_img);

        // Inicializa novamente o zoom na imagem em destaque a partir da biblioteca ElevateZoom
        $("#zoom").elevateZoom({
            // Tipo do zoom (nesse caso, zoom interno)
            zoomType: "inner",

            // Especifica o cursor do mouse
            cursor: "crosshair",

            // Ativa o deslize automático a partir do movimento do mouse
            easing: true,

            // Especifica intensidade do "delay" para o zoom aparecer e sair
            zoomWindowFadeIn: 600,
            zoomWindowFadeOut: 600
        });
    }
}

// Inicializa o zoom na imagem em destaque a partir da biblioteca ElevateZoom
$("#zoom").elevateZoom({
    // Tipo do zoom (nesse caso, zoom interno)
    zoomType: "inner",

    // Especifica o cursor do mouse
    cursor: "crosshair",

    // Ativa o deslize automático a partir do movimento do mouse
    easing: true,

    // Especifica intensidade do "delay" para o zoom aparecer e sair
    zoomWindowFadeIn: 600,
    zoomWindowFadeOut: 600
});


// Adiciona o texto de contribuidor embaixo da imagem (pega o contribuidor de um atributo da imagem)
function add_contri_text(imagem_selecionada) {
    var texto_contribuidor = imagem_selecionada.getAttribute('contri')
    var small_text = document.getElementById('imagem_selecionada_texto')
    small_text.innerText = texto_contribuidor

}