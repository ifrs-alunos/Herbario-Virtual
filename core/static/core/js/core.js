// Código JS Tooltip
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})

// Código link sidebar do painel de controle

// $(document).ready(function(){
//     $("#selected-link").parentsUntil(".accordion-collapse").addClass("show");
//     // $("#selected-link").parentsUntil(".accordion-header").children().addClass("collapsed");
//     // $("#selected-link").parentsUntil(".accordion-header").children().setAttribute('aria-expanded', true);
// });

// Adicionando negrito ao link selecionado
var link_selected = document.getElementById('selected-link');
link_selected.classList.add("fw-bold");

// Adicionando classes e atributos para accordion exibir seus itens

var accordion = link_selected.parentElement.parentElement.parentElement.parentElement.classList.add("show");

var accordion_header = link_selected.parentElement.parentElement.parentElement.parentElement.parentElement.children[0].children[0].classList.remove('collapsed').setAttribute('aria-expanded', true);


// Código JS para tornar ano não estático no footer

// Seleciona tag spam onde deve ser inserido o ano atual no footer
var spam = document.getElementById("ano_atual");

now = new Date;
seleciona_ano = now.getFullYear();

// Insere no HTML
spam.innerHTML += seleciona_ano; 

// ------------ //

// Código máscara do campo telefone (formulário de criação de conta de usuário)

var SPMaskBehavior = function (val) {
    return val.replace(/\D/g, '').length === 11 ? '(00) 00000-0000' : '(00) 0000-00009';
  },
  spOptions = {
    onKeyPress: function(val, e, field, options) {
        field.mask(SPMaskBehavior.apply({}, arguments), options);
      }
  };
  
// Insere a máscara 
$('#id_phone').mask(SPMaskBehavior, spOptions);

// Retira a máscara ao submeter o form
$("#create_form").submit(function(){
    $('#id_phone').unmask();
});

var links = document.getElementsByClassName("nav-item");
console.log(links)

for (var i = 0; i < links.length ; ++i){
    links[i].onclick = tornar_negrito;
}

function tornar_negrito(event) {
    var negrito = document.getElementsByClassName("active");
    console.log(negrito)
    // negrito.classList.remove("active");

    // event.classList.add("active");
}

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
        new_img.style.width = "635px";
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



// //initiate the plugin and pass the id of the div containing gallery images
// $("#zoom").elevateZoom({
//     gallery:'galeria',
//     cursor: 'pointer',
//     zoomType: 'inner',
//     easing : true,
//     galleryActiveClass: 'active',
//     imageCrossfade: true,
//     // loadingIcon: 'https://www.elevateweb.co.uk/spinner.gif'
// });

// //pass the images to Fancybox
// $("#zoom").bind("click", function(e) {
//     var ez = $('#zoom').data('elevateZoom');
//     $.fancybox(ez.getGalleryList());
//     return false;
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

// zoom_image = document.getElementById('zoom_image');

// zoom_image.onmousemove = zoom;

// // Zoom nas imagens do Carrosel
// //Está funcão só controla que parte da imagem com zoom será mostrada em realção as coordenadas do mouse
// function zoom(event) {
//     console.log("oi");

//     //Faz a imagem de tamanho normal sumir
//     event.currentTarget.style.opacity = 0;

//     //converte a posição em coordenadas para porcentagem
//     var x = event.offsetX * 100 / event.currentTarget.offsetWidth;
//     var y = event.offsetY * 100 / event.currentTarget.offsetHeight;

//     // var x = event.offsetX;
//     // var y = event.offsetY;

//     // console.log(x);
//     // console.log(y);

//     event.currentTarget.style.backgroundPosition = "" + x + "%" + y + "%";

//     console.log(event.currentTarget.style.backgroundPosition)
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
