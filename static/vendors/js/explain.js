// ...
// SORTABLE
// ...
if($.sortable) {
    $sortExplain = $('.sub-sortable').sortable({
        axis: 'y',
        items: '> div',
        handle: '.explain-move',
        tolerance: 'pointer',
        containment: 'parent',
        cursor: 'move',
        opacity: 0.7,
    });

    $sortExplain.on('sortupdate', function (event, ui) {
        var data = $(this).sortable('serialize', { key: 'sort' }),
            dataArray = data.split('&'),
            dataClean = [];

        $.each(dataArray, function (index, value) {
            var valueClean = value.replace('sort=', '');
            dataClean.push(valueClean);
        });

        sortStageExplain(dataClean);
    });

    function sortStageExplain(data) {
        $.ajax({
            method: 'POST',
            url: '/api/beacon/explains/sort/',
            headers: { 'X-CSRFToken': Cookies.get('csrftoken') },
            xhrFields: { withCredentials: true },
            data: {
                sortable: data.join(','),
                csrfmiddlewaretoken: Cookies.get('csrftoken'),
            },
            success: function (response) {

            },
            error: function (error) {

            }
        });
    }
}

$(document).on('click', '#add-explain', function(event) {
    event.preventDefault();
    initModal('explain');
    initExplainForm({'chapter': $(this).data('chapter')}, $(this));
});

$(document).on('click', '#submit-explain', function (event) {
    event.preventDefault();
    $('.form-explain').submit();
});

// ...
// FORM VALIDATION
// ...
function initExplainForm(data = null, $originElement=null) {
    $checkbox = $('.checkbox').checkbox();

    $form = $('.form-explain').form({
        on: 'blur',
        fields: {
            label: {
                identifier: 'label',
                rules: [
                    {
                        type: 'empty',
                        prompt: 'Nama bab tidak boleh kosong'
                    },
                    {
                        type: 'minLength[4]',
                        prompt: 'Nama bab minimal 4 karakter'
                    }
                ]
            },
            status: {
                identifier: 'status',
                rules: [
                    {
                        type: 'checked',
                    }
                ]
            },
            changelog: {
                identifier: 'changelog',
                rules: [
                    {
                        type: 'empty',
                        prompt: 'Changelog tidak boleh kosong'
                    }
                ]
            },
        },
        onSuccess: function (event, fields) {
            // Prevent default form submit!
            // We use REST API for handle login.
            if (event) {
                event.preventDefault();
                $(event.target).addClass('loading');
                
                fields.chapter = data.chapter;
                submitExplainHandler(event.target, fields, $originElement);
            }
        },
        onFailure: function (formErrors, fields) {
            $('#submit-explain, .cancel').removeClass('disabled');
            return false;
        }
    });
}

// ...
// SUBMIT HANDLER
// ...
function submitExplainHandler($element = null, $fields, $originElement=null) {
    $('#submit-explain, .cancel').addClass('disabled');

    $.ajax({
        method: 'POST',
        url: '/api/beacon/explains/',
        headers: { 'X-CSRFToken': Cookies.get('csrftoken') },
        xhrFields: { withCredentials: true },
        data: {
            ...$fields,
            csrfmiddlewaretoken: Cookies.get('csrftoken'),
        },
        success: function (response) {
            // window.location.reload();
            
            var status;

            if (response.explain_status == globalParams.published) {
                status = '<i class="eye icon text-success mr-0"></i>';
            } else if (response.explain_status == globalParams.draft) {
                status = '<i class="eye slash icon text-muted mr-0"></i>';
            }

            var control = '<a id="delete-object" class="d-table-cell text-danger" data-uuid="' + response.uuid + '" data-revision-uuid="' + response.explain_uuid + '" data-path="chapters">' +
                '<i class="trash icon mr-0"></i>' +
            '</a>' +
            
            '<a id="update-explain" class="d-table-cell" data-explain-uuid="' + response.uuid + '" data-revision-uuid="' + response.explain_uuid + '">' +
                '<i class="edit icon mr-0"></i>' +
            '</a>';

            var mover = '<span class="d-table-cell explain-move">' +
                '<i class="expand arrows alternate icon"></i>' +
            '</span>';

            var item = '<div id="item_' + response.id + '" class="item">' +
                '<div class="d-flex w-100">' +
                    '<span class="control w-100"><a>' + response.explain_label + '</a></span>' +
            
                    '<div class="ml-auto text-right" style="width:155px">' +
                        '<div class="d-table w-100 justify-content-around">' +
                            '<small class="d-table-cell text-muted font-weight-normal">' +
                                'ref. ' + response.explain_version +
                            '</small>' +

                            '<span class="d-table-cell">' + status + '</span>' + control + mover + 
                        '</div>' +
                    '</div>' +
                '</div>' +
            '</div>';
            
            var $targetElement = $originElement.closest('.content').find('#sub-list');

            if ($targetElement.find('.item').length > 0) {
                $targetElement.append(item);
            } else {
                $targetElement.html(item);
            }

            // Clear all...
            $('.modal').modal('hide');
            $('.form-explain').removeClass('loading');
            $('#submit-explain, .cancel').removeClass('disabled');
        },
        error: function (error) {
            $('#submit-explain, .cancel').removeClass('disabled');
            $($element).removeClass('loading');

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

// ...
// CHANGE
// ...
$(document).on('click', '#update-explain', function(event) {
    event.preventDefault();

    var fields = {
        'explain_uuid': $(this).data('explain-uuid'),
        'revision_uuid': $(this).data('revision-uuid'),
    }

    updateHandler($(this), fields);
});

// ...
// UPDATE HANDLER
// ...
function updateHandler($element=null, $fields) {
    $.ajax({
        method: 'POST',
        url: '/api/beacon/explains-revisions/',
        headers: {'X-CSRFToken': Cookies.get('csrftoken')},
        xhrFields: {withCredentials: true},
        data: {
            ...$fields,
            csrfmiddlewaretoken: Cookies.get('csrftoken'),
        },
        success: function(response) {
            window.location.href = response.permalink;
        },
        error: function(error) {
            $('.cancel').removeClass('disabled');
            $($element).removeClass('loading');

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