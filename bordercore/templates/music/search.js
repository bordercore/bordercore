new Vue({
    delimiters: ["[[", "]]"],
    el: "#search",
    methods: {
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
    },
    components: {
        SimpleSuggest
    }
});
