<template>
    <div>
        <vue-simple-suggest :id="id"
                            ref="suggestComponent"
                            v-model="query"
                            :accesskey="accesskey"
                            :display-attribute="displayAttribute"
                            :value-attribute="valueAttribute"
                            :list="search"
                            :name="name"
                            :filter-by-query="true"
                            :debounce="200"
                            :min-length="2"
                            :max-suggestions="maxSuggestions"
                            :placeholder="placeHolder"
                            autocomplete="off"
                            :autofocus="autofocus"
                            :styles="autoCompleteStyle"
                            @select="select"
                            @keydown.native.enter="onEnter"
                            @hide-list="onHideList"
                            @hover="onHover"
        >
            <div slot="suggestion-item" slot-scope="scope">
                <span v-html="boldenSuggestion(scope)" />
            </div>
        </vue-simple-suggest>
    </div>
</template>

<script>

    import VueSimpleSuggest from "vue-simple-suggest";

    export default {
        components: {
            VueSimpleSuggest,
        },
        props: {
            autofocus: {
                type: Boolean,
                default: false,
            },
            accesskey: {
                type: String,
                default: null,
            },
            id: {
                type: String,
                default: "simple-suggest",
            },
            displayAttribute: {
                type: String,
                default: "value",
            },
            valueAttribute: {
                type: String,
                default: "value",
            },
            maxSuggestions: {
                default: 20,
                type: Number,
            },
            searchUrl: {
                type: String,
                default: "search-url",
            },
            placeHolder: {
                type: String,
                default: "Name",
            },
            name: {
                type: String,
                default: "search",
            },

        },
        data() {
            return {
                query: "",
                autoCompleteStyle: {
                    vueSimpleSuggest: "position-relative",
                    inputWrapper: "",
                    defaultInput: "form-control search-box-input",
                    suggestions: "position-absolute list-group z-1000",
                    suggestItem: "list-group-item",
                },
            };
        },
        methods: {
            search(query) {
                try {
                    const url = this.searchUrl;
                    return axios.get(url + query)
                        .then((response) => {
                            return response.data;
                        });
                } catch (error) {
                    console.log(`Error: ${error}`);
                }
            },
            boldenSuggestion(scope) {
                // If the parent provided a custom boldenSuggestion function, use that.
                //  Otherwise use this default code.
                if (typeof this.$parent.boldenSuggestion === "function") {
                    return this.$parent.boldenSuggestion(scope);
                }

                if (!scope) return scope;

                const {suggestion, query} = scope;

                let result = this.$refs.suggestComponent.displayProperty(suggestion);

                if (!suggestion.object_type) {
                    return result;
                }

                result = "<em>" + suggestion.object_type + "</em> - " + result;

                if (!query) return result;

                const texts = query.split(/[\s-_/\\|\.]/gm).filter((t) => !!t) || [""];
                return result.replace(new RegExp("(.*?)(" + texts.join("|") + ")(.*?)", "gi"), "$1<b class='text-primary'>$2</b>$3");
            },
            select(datum) {
                if (typeof this.$parent.select !== "function") {
                    console.error("Error: parent component must define a select() function.");
                } else {
                    this.$parent.select(datum);
                }
            },
            onEnter(evt) {
                if (typeof this.$parent.onEnter === "function") {
                    this.$parent.onEnter(evt);
                }
            },
            onHideList(evt) {
                if (typeof this.$parent.onHideList === "function") {
                    this.$parent.onHideList(evt);
                }
            },
            onHover(evt) {
                if (typeof this.$parent.onHover === "function") {
                    this.$parent.onHover(evt);
                }
            },
        },
    };

</script>
