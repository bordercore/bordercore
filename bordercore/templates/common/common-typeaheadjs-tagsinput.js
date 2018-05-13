var engine = new Bloodhound({
    name: 'tags',
    remote: {
        url: '{% url 'tag_search' %}?query=%QUERY',
        wildcard: '%QUERY'
    },
    datumTokenizer: function(d) { return Bloodhound.tokenizers.whitespace(d.val); },
    queryTokenizer: Bloodhound.tokenizers.whitespace
});

engine.initialize();

$('#id_tags').tagsinput({
    confirmKeys: [13, 188],
    tagClass: function(item) {
        if (item.is_meta == 'true') {
            return 'label label-success';
        } else {
            return 'label label-primary';
        }
    },
    {% if itemValue %}
    itemValue: 'value',
    {% endif %}
    typeaheadjs: [{
        minLength: 2
    }, {
        source: engine,
        displayKey: function (data) {
            return data.value;
        },
        valueKey: 'value',
        options: {'autoselect': true},
        templates: {
            suggestion: function(data) {
                return '<div class="tt-suggest-page">' + data.value.replace(data._query, '<strong>' + data._query+ '</strong>') + '</div>';
            }
        }
    }]
});
