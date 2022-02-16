let checkbox = $('#id_term')

checkbox.click(function(){
    if (checkbox.is(':checked')){
        $('#termoModal').modal('show')
        checkbox.prop('checked', false);

    }
})

// Manda o formulario via ajax para a url e retorna True or false, quase um webservice
function submitForm(form,url) {
    let term_form = form
    let csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value
    term_form.submit( function(event) {
                 event.preventDefault();
                $.ajax( {
                type: "POST",
              url: url,
              dataType: "json",
              data: {
                    csrfmiddlewaretoken: csrfmiddlewaretoken,
                    user: $('#id_user').val(),
                    password:$('#id_password').val() ,

              },
              success: function (data) {
                  if (data){
                     checkbox.prop('checked', true);
                     $('#termoModal').modal('hide')
                  }
                  else {
                      // Gambiarra pra fazer um minimo erro pro usuario não me arrependo mas desculpa, se conseguir
                      // maneira melhor mudar aqui
                      const tag = document.createElement("div");
                      tag.classList.add("alert", "alert-danger")
                      const tag_li = document.createElement("li");
                      const text = document.createTextNode("Senha errada");
                      const term_form_errors = $('#term_form_errors')
                      tag_li.appendChild(text)
                      tag.appendChild(tag_li)
                      if (!term_form_errors.children('div').length){
                          term_form_errors.append(tag)
                      }
                  }
                }
            })
            return false;

        })

}