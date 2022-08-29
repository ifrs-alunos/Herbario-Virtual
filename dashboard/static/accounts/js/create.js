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

// Código máscara do campo CPF (formulário de criação de conta de usuário)

var CpfMaskBehavior = function (val) {
    return val.replace(/\D/g, '').length === 11 ? '000.000.000-00' : '000.000.000-00';
  },
  cpfOptions = {
    onKeyPress: function(val, e, field, options) {
        field.mask(CpfMaskBehavior.apply({}, arguments), options);
      }
  };

// Insere a máscara
$('#id_cpf').mask(CpfMaskBehavior, cpfOptions);

// Retira as máscaras ao submeter o form
$("#create_form").submit(function(){
    $('#id_phone').unmask();
    $('#id_cpf').unmask();
});
