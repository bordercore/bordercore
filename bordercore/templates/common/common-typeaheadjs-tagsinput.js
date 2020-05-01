var engine = new Bloodhound({
    name: 'tags',
    remote: {
        url: '{% url url|default:"tag_search" %}?query=%QUERY',
        wildcard: '%QUERY'
    },
    datumTokenizer: function(d) { return Bloodhound.tokenizers.whitespace(d.val); },
    queryTokenizer: Bloodhound.tokenizers.whitespace
});

engine.initialize();

field_name = '{{ fieldName|default:"value" }}';

$('#id_tags').tagsinput({
    confirmKeys: [13, 188],
    tagClass: function(item) {
        if (item.is_meta) {
            return 'badge badge-info';
        } else {
            return 'badge badge-primary';
        }
    },
    {% if fieldName %}
    itemText: field_name,
    {% endif %}
    {% if itemValue %}
    itemValue: 'value',
    {% endif %}
    typeaheadjs: [{
        minLength: 2
    }, {
        limit: 10,
        source: engine,
        displayKey: function (data) {
            return data[field_name];
        },
        valueKey: 'value',
        options: {'autoselect': true},
        templates: {
            suggestion: function(data) {
                return '<div class="tt-suggest-page">' + data[field_name].replace(data._query, '<strong>' + data._query+ '</strong>') + '</div>';
            }
        }
    }]
});

// This handles tags which are not returned by typeahead's
//  source, ie tags that don't already exist. This usually is
//  handled by the "freeInput" Bootstrap Tags option, but
//  that doesn't work when using objects as tags.
$(".tt-input").keydown(function (e) {
    if (e.keyCode === 13) {
        e.preventDefault();

        tag = $(".tt-input").val();

        // If a value exists, then this is a new tag not
        //  found by the typeahead. Add it. If it is found
        //  by the typeahead, it will automatically be added.
        if (tag) {
            $("#id_tags").tagsinput("add", {
                value: tag,
                [field_name]: tag,
            });
        }

    }
});
