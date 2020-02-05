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
            name = input[0]['name'],
            is_required = input.prop('required');
        
        if (name && name.indexOf('[]') >= 0) {
            var checkboxes = document.getElementsByName(name);
            var vals = "";
            for (var i=0, n=checkboxes.length;i<n;i++) {
                if (checkboxes[i].checked) {
                    vals += ","+checkboxes[i].value;
                }
            }

            if (vals) value = vals.substring(1);
            if (!vals) value = '';
            name = name.replace('[]', '');
        }

        formValuesObj[name] = {
            value: value,
            is_required: is_required
        }
    });

    return formValuesObj;
}

// ...
// DELETE HANDLER
// ...
function deleteHandler(uuid, path, redirectTo=null) {
    $.ajax({
        method: 'DELETE',
        url: '/api/beacon/' + path + '/' + uuid + '/',
        headers: {'X-CSRFToken': Cookies.get('csrftoken')},
        xhrFields: {withCredentials: true},
        success: function(response) {
            Swal.fire({
                icon: 'success',
                title: 'Terhapus!',
                text: 'Sedang mengalihkan...',
                showCloseButton: false,
                showCancelButton: false,
                showConfirmButton: false,
                allowOutsideClick: false,
                allowEscapeKey: false,
            });

            setTimeout(function() {
                if (redirectTo) window.location.href = redirectTo;
                if (!redirectTo) window.location.reload();
            }, 1000);
        },
        error: function(error) {
            if (error && error.responseJSON) {
                var errorJSON = error.responseJSON,
                    errorMessage = [];

                $.each(errorJSON, function(index, item) {
                    var label = '<span class="text-capitalize font-weight-bold text-danger">' + index + '</span>: ';
                    
                    if (Array.isArray(item)) {
                        errorMessage.push(label + item.join(' '));
                    } else {
                        errorMessage.push(label + item);
                    }
                });

                if (errorMessage.length == 0) errorMessage.push('Terjadi kesalahan. Coba lagi.');

                // Show error
                if (errorMessage) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Oops...',
                        html: '<div class="text-center">' + errorMessage.join('<br /><br />') + '</div>',
                    });
                }
            }
        }
    });
}

// ...
// SHOW DOCS NAV
// ...
$(document).on('click', '.docs-nav__toggle .toggler', function(event) {
    $('body').toggleClass('docs-nav-active');
});
