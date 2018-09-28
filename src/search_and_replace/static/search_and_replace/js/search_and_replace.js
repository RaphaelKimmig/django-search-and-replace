window.addEventListener('load', function () {
    var search_and_replace = document.getElementById("search-and-replace");

    var search = new Mark(document.querySelectorAll("td.search"));
    search.mark(search_and_replace.dataset.search, {
        separateWordSearch: false,
        className: "mark-search",
        caseSensitive: true
    });

    var replace = new Mark(document.querySelectorAll("td.replace"));
    replace.mark(search_and_replace.dataset.replace, {
        separateWordSearch: false,
        className: "mark-replace",
        caseSensitive: true
    });
}, false);
