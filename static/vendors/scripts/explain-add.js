// ...
// ADD NEW EXPLAIN
// ...
$(document).on('click', '#add-explain', function(event) {
    event.preventDefault();

    var chapter_pk = $(this).data('chapter-pk');
    $('.form-explain-dialog').find('input[name="chapter"]').val(chapter_pk);
});

$(document).on('submit', '.form-explain-dialog', function(event) {
    event.preventDefault();

    var formValuesObj = getFormValues($(this));
    var saveValuesObj = {};

    $.each(formValuesObj, function(i, v) {
        saveValuesObj[i] = v.value;
    });

    submitExplainHandler($(this), saveValuesObj);

    $(this).find('button').prop('disabled', true);
    $(this).find('button').find('.spinner').removeClass('d-none');
});

// ...
// SUBMIT EXPLAIN HANDLER
// ...
function submitExplainHandler($form=null, $data) {
    $.ajax({
        method: "POST",
        url: '/api/beacon/explains/',
        headers: { 'X-CSRFToken': Cookies.get('csrftoken') },
        xhrFields: { withCredentials: true },
        data: {
            ...$data
        },
        success: function (response) {
            Swal.fire({
                icon: 'success',
                title: 'Berhasil',
                text: 'Menyiapkan editor...',
                showCloseButton: false,
                showCancelButton: false,
                showConfirmButton: false,
                allowOutsideClick: false,
                allowEscapeKey: false,
            });

            window.location.href = response.permalink;
        },
        error: function (error) {
            $form.find('button').prop('disabled', false);
            $form.find('button').find('.spinner').addClass('d-none');

            if (error && error.responseJSON) {
                var errorJSON = error.responseJSON,
                    errorMessage = [];

                $.each(errorJSON, function (index, item) {
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