// ...
// SORTABLE
// ...
$sortChapter = $('#sortable').sortable({
    axis: 'y',
    containment: 'parent',
    items: '> div',
    tolerance: 'pointer',
    cursor: 'move',
    opacity: 0.7,
});

$sortChapter.on('sortupdate', function (event, ui) {
    var data = $(this).sortable('serialize', { key: 'sort' }),
        dataArray = data.split('&'),
        dataClean = [];

    $.each(dataArray, function (index, value) {
        var valueClean = value.replace('sort=', '');
        dataClean.push(valueClean);
    });

    sortStageChapter(dataClean);
});

function sortStageChapter(data) {
    $.ajax({
        method: 'POST',
        url: '/api/beacon/chapters/sort/',
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

// ...
// CHAPTER ADD
// ...
$(document).on('click', '#add-chapter', function (event) {
    event.preventDefault();
    initModal('chapter');
});

$(document).on('click', '#submit-chapter', function (event) {
    event.preventDefault();
    $('.form-chapter').submit();
});

// ...
// UPDATE CHAPTER
// ...
$(document).on('click', '#update-chapter', function (event) {
    event.preventDefault();

    event.stopPropagation();

    /**
    'revision_uuid' adalah uuid dari revision
    'chapter_uuid' adalah uuid dari induk chapter
    Guide
    -- Chapter -> 'chapter_uuid'
    ---- Chapter Revision -> 'revision_uuid'
    */
    var fields = {
        'chapter_uuid': $(this).data('chapter-uuid'),
        'revision_uuid': $(this).data('revision-uuid'),
    }

    $('.modal-chapter').find('form').attr('data-revision-uuid', $(this).data('revision-uuid'));
    $('.modal-chapter').find('form').attr('data-chapter-uuid', $(this).data('chapter-uuid'));
    $('.modal-chapter').find('form').attr('data-is-change', true);

    submitChapterHandler($(this), fields);
});

// ...
// FORM CHAPTER VALIDATION
// ...
function initChapterForm(data = null) {
    $checkbox = $('.checkbox').checkbox();

    $form = $('.form-chapter').form({
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
            description: {
                identifier: 'description',
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

                var is_change = $(event.target).data('is-change'),
                    chapter_uuid = $(event.target).data('chapter-uuid'),
                    revision_uuid = $(event.target).data('revision-uuid');

                if (is_change) {
                    fields.chapter_uuid = chapter_uuid;
                    fields.revision_uuid = revision_uuid;
                    fields.is_change = true;
                }

                submitChapterHandler(event.target, fields);
            }
        },
        onFailure: function (formErrors, fields) {
            $('#submit-chapter, .cancel').removeClass('disabled');
            return false;
        }
    });

    if (data) {
        $form.form('set values', { ...data });
        $checkbox.checkbox('set checked');
    }
}

// ...
// SUBMIT CHAPTER HANDLER
// ...
function submitChapterHandler($element = null, $fields) {
    $('#submit-chapter, .cancel').addClass('disabled');

    var url = '/api/beacon/chapters/',
        method = 'POST';

    // Jika edit maka uuid tersedia
    // Dan method berubah jadi 'PATCH'
    if ($fields.revision_uuid) url = '/api/beacon/chapters-revisions/';

    // Change action
    if ($fields.is_change) {
        url = '/api/beacon/chapters-revisions/' + $fields.revision_uuid + '/';
        method = 'PATCH';

        delete $fields['revision_uuid'];
        delete $fields['chapter_uuid'];
    }

    $.ajax({
        method: method,
        url: url,
        headers: { 'X-CSRFToken': Cookies.get('csrftoken') },
        xhrFields: { withCredentials: true },
        data: {
            ...$fields,
            guide: globalParams.revision_guide_pk,
            csrfmiddlewaretoken: Cookies.get('csrftoken'),
        },
        success: function (response) {
            if ($fields.is_change || !$fields.chapter_uuid) window.location.reload();

            if ($fields.chapter_uuid && !$fields.is_change) {
                initModal('chapter');
                initChapterForm(response);

                $('.modal-chapter').find('form').attr('data-revision-uuid', response.uuid);
                $('#submit-chapter, .cancel').removeClass('disabled');
            }
        },
        error: function (error) {
            $('#submit-chapter, .cancel').removeClass('disabled');
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