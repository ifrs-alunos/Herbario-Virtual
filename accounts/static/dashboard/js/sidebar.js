// Código link sidebar do painel de controle

// Adicionando negrito ao link selecionado
var link_selected = document.getElementById('selected-link');
//link_selected.classList.add("fw-bold");

// Adicionando classes e atributos para accordion exibir seus itens

//var accordion = link_selected.parentElement.parentElement.parentElement.parentElement.classList.add("show");
//var accordion_header = link_selected.parentElement.parentElement.parentElement.parentElement.parentElement.children[0].children[0]

//accordion_header.classList.remove('collapsed')
//accordion_header.setAttribute('aria-expanded', true);

//Initial model of Characteristic in html
initial_char = "<article class='row' id=\"char-1\">\n" +
    "<div class='col-md-6'><select name='char-1' data-id=1 class='select form-control'>"+$("#char-model select").html()+"</select></div>"+
    "                <div class='col-md-6' id=\"charlabel-1\"></div>\n" +
    "            <br><br></article>";

//Applying the initial model
if (cid == 0) {
    $("#chars_block").html(initial_char);
}

//When the char type is selected, show his label
$('#chars_block select').change(function (){
        idc = $(this).data('id');

        for (valor in chars_inputs){
            if (chars_inputs[valor]['id']==$(this).val()){
                $("#charlabel-"+idc).html(chars_inputs[valor]['type'].replace("charval", 'charval-'+cid));
            }
        }
    });


//add new char in form
$("#add-char").click(function (){
    form =$("form").serialize().split("&");
    cid++;
    new_char="<article class='row' id=\"char-"+cid+"\">\n" +
            "<div class='col-md-6'><select name='char-"+cid+"' data-id="+cid+" class='select form-control'>"+$("#char-model select").html()+"</select></div>"+
            "                <div class='col-md-5' id=\"charlabel-"+cid+"\"></div>\n" +
            "<p data-id=\""+cid+"\" class=\"btn btn-rm btn-danger rm-char col-md-1\">X</p>" +
            "            <br><br></article>";
    $("#chars_block").html($("#chars_block").html()+new_char);

    for (label in form){
        name = form[label].split('=')[0];
        value = form[label].split('=')[1];

        $("select[name="+name+"]").val(value);
        $("input[name="+name+"]").val(value);

    };

    $('#chars_block select').change(function (){
        idc = $(this).data('id');

        for (valor in chars_inputs){
            if (chars_inputs[valor]['id']==$(this).val()){
                console.log(chars_inputs[valor]['type'].replace("charval", 'charval-'+idc));
                $("#charlabel-"+idc).html(chars_inputs[valor]['type'].replace("charval", 'charval-'+idc));
            }
        }
    });

    $(".rm-char").click(function () {
        id = $(this).data('id');
        $('#char-'+id).remove();
    });
});