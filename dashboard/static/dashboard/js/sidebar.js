// Código link sidebar do painel de controle

// Adicionando negrito ao link selecionado
var link_selected = document.getElementById('selected-link');
link_selected.classList.add("fw-bold");

// Adicionando classes e atributos para accordion exibir seus itens

var accordion = link_selected.parentElement.parentElement.parentElement.parentElement.classList.add("show");
var accordion_header = link_selected.parentElement.parentElement.parentElement.parentElement.parentElement.children[0].children[0]

accordion_header.classList.remove('collapsed')
accordion_header.setAttribute('aria-expanded', true);