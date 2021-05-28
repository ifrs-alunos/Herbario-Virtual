// Código JS Tooltip
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})

// Código JS para tornar ano não estático no footer

function openNav() {
    document.getElementById("mySidenav").style.width = "100%";
}
  
function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
}

// Seleciona tag spam onde deve ser inserido o ano atual no footer
var spam = document.getElementById("ano_atual");

now = new Date;
seleciona_ano = now.getFullYear();

// Insere no HTML
spam.innerHTML += seleciona_ano; 

// TESTES COM NEGRITO NA NAVBAR

/* var links = document.getElementsByClassName("nav-item");
console.log(links)

for (var i = 0; i < links.length ; ++i){
    links[i].onclick = tornar_negrito;
}

function tornar_negrito(event) {
    var negrito = document.getElementsByClassName("active");
    console.log(negrito)
    // negrito.classList.remove("active");
    // event.classList.add("active");
} */