document.addEventListener('DOMContentLoaded', function () {
  SimpleJekyllSearch({
    searchInput: document.getElementById('search-input'),
    resultsContainer: document.getElementById('results'),
    json: '/search.json',
    searchResultTemplate: '<li><a href="{url}">{title}</a> — {date}</li>',
    noResultsText: '검색 결과가 없습니다',
    limit: 10,
  });
});
