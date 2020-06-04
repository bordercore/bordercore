var engine = new Bloodhound({
    name: 'tags',
    remote: {
        url: '{% url 'music_search' %}?query=%QUERY',
        wildcard: '%QUERY'
    },
    datumTokenizer: function(d) { return Bloodhound.tokenizers.whitespace(d.val); },
    queryTokenizer: Bloodhound.tokenizers.whitespace
});

engine.initialize();

$('#music-search').typeahead({
    autoselect: true
}, {
    displayKey: 'name',
    source: engine,
});

$('#music-search').on('keyup', function(event, selection) {
    if ((event.which && event.which == 13) || (event.keyCode && event.keyCode == 13)) {
        $('#search').submit();
        return false;
    } else {
        return true;
    }
});

$('#music-search').bind('typeahead:selected', function(obj, datum, name) {
    var url = null;
    if (datum.type == 'album') {
        url = '{% url 'album_detail' 666 %}'.replace(/666$/, datum.id);
    } else if (datum.type == 'artist') {
        url = '{% url 'artist_detail' 666 %}'.replace(/666$/, datum.value);
    } else {
        url = '{% url 'music_search_tag' %}?tag=' + datum.value;
    }
    window.location = url;
});
