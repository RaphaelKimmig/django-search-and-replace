window.addEventListener('load', function () {
    var search_and_replace = document.getElementById("search-and-replace");

    var search = new Mark(document.querySelectorAll("td.search"));
    search.mark(search_and_replace.dataset.search, {
        separateWordSearch: false,
        className: "mark-search",
        caseSensitive: true,
        diacritics: false
    });

    var replace = new Mark(document.querySelectorAll("td.replace"));
    replace.mark(search_and_replace.dataset.replace, {
        separateWordSearch: false,
        className: "mark-replace",
        caseSensitive: true,
        diacritics: false
    });

    /* remove apply button on input */
    function remove_apply_button() {
        var search_and_replace_apply = document.getElementById("search-and-replace-apply");
        if(search_and_replace_apply !== null) {
            search_and_replace_apply.parentNode.removeChild(search_and_replace_apply);
        }
    };
    document.querySelectorAll('form#search-and-replace input').forEach(function (elem) { elem.addEventListener('input', remove_apply_button)});
}, false);
