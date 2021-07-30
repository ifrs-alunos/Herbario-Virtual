function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function create_request(id, status) {
    const form_data = new FormData();
    form_data.append("status", status);

    const csrftoken = getCookie('csrftoken');

    $.ajax({
        type: "POST",
        url: "/painel/solicitacao/"+id+"/",
        data: form_data,
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': csrftoken,
        }
    }).done(function(data){
        console.log(data)
        window.location.href = "/painel/lista-solicitacoes/"
    }).fail(console.log);
}

function accept(id) {
    create_request(id, "accepted");
}

function deny(id) {
    create_request(id, "denied");
}
