// ...
// GET URL PARAMS
// ...
function getUrlParameter(sParam) {
    var sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
};

// ...
// COLLECT ALL FORM VALUES
// ...
function getFormValues($form) {
    var formValuesObj = {};

    $form.find(':input:not(button)').each(function(){
        var input = $(this),
            value = input.val(),
            name = input.attr('name'),
            is_required = input.prop('required');

        formValuesObj[name] = {
            value: value,
            is_required: is_required
        }
    });

    return formValuesObj;
}