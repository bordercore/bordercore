new Vue({
    delimiters: ["[[", "]]"],
    el: "#search",
    data() {
        return {
            inputName: "search",
            query: "",
            tags: [],
            autoCompleteStyle: {
                vueSimpleSuggest: "position-relative",
                inputWrapper: "search-box",
                defaultInput: "form-control search-box-input",
                suggestions: "position-absolute list-group z-1000",
                suggestItem: "list-group-item"
            }
        }
    },
    methods: {
        tagSearch(query) {
            return axios.get("{% url 'music:search' %}?query=" + query)
                .then(response => {
                    return response.data;
                })
        },
        select(datum) {

            if (datum.link_type == 'album') {
                url = '{% url 'music:album_detail' 666 %}'.replace(/666/, datum.id);
            } else if (datum.link_type == 'artist') {
                url = '{% url 'music:artist_detail' 666 %}'.replace(/666/, datum.artist);
            } else {
                url = '{% url 'music:search_tag' %}?tag=' + datum.name;
            }
            window.location=url;

        },
        boldenSuggestion(scope) {

            if (!scope) return scope;

            const { suggestion, query } = scope;

            let result = this.$refs.suggestComponent.displayProperty(suggestion);
            result = "<em>" + suggestion.object_type + "</em> - " + result

            if (!query) return result;

            const texts = query.split(/[\s-_/\\|\.]/gm).filter(t => !!t) || [''];
            return result.replace(new RegExp('(.*?)(' + texts.join('|') + ')(.*?)','gi'), '$1<b>$2</b>$3');
        }
    }
});
