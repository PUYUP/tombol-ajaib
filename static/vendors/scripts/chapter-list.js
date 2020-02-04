function loadChapter(guide_uuid=null, scroll_to_uuid=null, person_uuid=null) {
    var chapterObjs = $.ajax('/api/beacon/chapters/?guide_uuid=' + guide_uuid);
    var explainObjs = $.ajax('/api/beacon/explains/?guide_uuid=' + guide_uuid);

    $.when(chapterObjs, explainObjs).then(function(chapterRes, explainRes) {
        var combineChapterExplain = [],
            chapterItem = '',
            chapters = chapterRes[0],
            explains = explainRes[0];

        $.each(chapters, function(index, value) {
            var explainFiltered = explains.filter(function(x) {
                return x.chapter_uuid === value.uuid;
            });

            value.explains = explainFiltered;
            combineChapterExplain.push(value);
        });

        $.each(combineChapterExplain, function(index, value) {
            var explainsList = '',
                explainItem = '',
                explains = value.explains,
                has_explain = explains.length > 0;
            
            if (has_explain) {
                $.each(explains, function(ei, ev) {
                    explainItem += `<li id="item_${ev.id}" class="position-relative ${scroll_to_uuid === ev.uuid ? 'active' : ''}" data-uuid="${ev.uuid}">
                        <a href="${ev.permalink}" class="text-dark">
                            ${ev.published ? ev.published.label : ev.draft.label}
                        </a>
                    </li>`;
                });

                explainsList = `<ul class="list-unstyled pl-2 pt-3 explain-list mb-0">${explainItem}</ul>`;
            }

            var chapter_tools = `<div class="docs-nav-tools position-absolute d-none bg-white pl-1">
                <button type="button" id="add-explain" class="btn btn-warning btn-sm add-explain"
                    data-chapter-pk="${value.id}" data-chapter-uuid="${value.uuid}" data-toggle="modal" data-target="#modalAddExplain">
                    + Materi
                </button>
            </div>`;

            chapterItem += `<div id="item_${value.id}" class="chapter-group ${scroll_to_uuid === value.uuid ? 'active' : ''}" data-uuid="${value.uuid}">
                <h3 class="header position-relative mb-0">
                    <a href="${value.permalink}" class="text-dark">
                        ${value.published ? value.published.label : value.draft.label}
                    </a>

                    ${value.creator_uuid === person_uuid ? chapter_tools : ''}
                </h3>

                ${explainsList}
            </div>`;
        });

        if (chapterItem) $('.chapter-list').append(chapterItem);

        $('.chapter-wrap').animate({
            scrollTop: $('[data-uuid="' + scroll_to_uuid + '"]').offset().top - 150
        }, 0);
    },
    function(xhr, status) {
        fetchChapter();
    });

    function fetchChapter() {
        $.ajax({
            method: 'GET',
            url: '/api/beacon/chapters/',
            headers: {'X-CSRFToken': Cookies.get('csrftoken')},
            xhrFields: {withCredentials: true},
            data: {
                guide_uuid: guide_uuid
            },
            success: function(response) {
                var chapterItem = '';

                $.each(response, function(index, value) {
                    var chapter_tools = `<div class="docs-nav-tools position-absolute d-none bg-white pl-1">
                        <button type="button" id="add-explain" class="btn btn-warning btn-sm add-explain"
                            data-chapter-pk="${value.id}" data-chapter-uuid="${value.uuid}" data-toggle="modal" data-target="#modalAddExplain">
                            + Materi
                        </button>
                    </div>`;

                    chapterItem += `<div id="item_${value.id}" class="chapter-group ${scroll_to_uuid === value.uuid ? 'active' : ''}" data-uuid="${value.uuid}">
                        <h3 class="header position-relative mb-0">
                            <a href="${value.permalink}" class="text-dark">
                                ${value.published ? value.published.label : value.draft.label}
                            </a>

                            ${value.creator_uuid === person_uuid ? chapter_tools : ''}
                        </h3>
                    </div>`;
                });

                if (chapterItem) $('.chapter-list').append(chapterItem);
            },
            error: function(error) {
                $('.chapter-list').append('<small class="text-muted mt-3 d-block">Bab belum ad Bab.</small>');
            }
        })
    }
}