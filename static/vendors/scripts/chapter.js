function loadChapter(guide_uuid=null, scroll_to_uuid=null) {
    var chapterObjs = $.ajax('/api/beacon/chapters/?guide_uuid=' + guide_uuid);
    var explainObjs = $.ajax('/api/beacon/explains/?guide_uuid=' + guide_uuid);

    $.when(chapterObjs, explainObjs).done(function(chapterRes, explainRes) {
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
                uuid = value.uuid,
                has_explain = explains.length > 0;
            
            if (has_explain) {
                $.each(explains, function(ei, ev) {
                    explainItem += `<li id="item_${ev.id}" data-uuid="${ev.uuid}">
                        <a href="${ev.permalink}" class="text-dark">
                            ${ev.published ? ev.published.label : ev.draft.label}
                        </a>
                    </li>`;
                });

                explainsList = `<ul class="list-unstyled pl-2 pt-1 explain-list">${explainItem}</ul>`;
            }

            chapterItem += `<div id="item_${value.id}" class="chapter-group" data-uuid="${uuid}">
                <h3 class="header">
                    <a href="${value.permalink}" class="text-dark">
                        ${value.published ? value.published.label : value.draft.label}
                    </a>
                </h3>

                ${explainsList}
            </div>`;
        });

        if (chapterItem) $('.chapter-list').append(chapterItem);

        $('.chapter-wrap').animate({
            scrollTop: $('[data-uuid="' + scroll_to_uuid + '"]').offset().top - 150
        }, 0);
    });
}