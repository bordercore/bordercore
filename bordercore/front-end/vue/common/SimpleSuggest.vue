<template>
    <div :class="wrapperClass" class="search-with-doctypes">
        <vue-simple-suggest :id="id"
                            ref="suggestComponent"
                            v-model="query"
                            :accesskey="accesskey"
                            :destyled="true"
                            :display-attribute="displayAttribute"
                            :value-attribute="valueAttribute"
                            :list="search"
                            :name="name"
                            :filter-by-query="true"
                            :debounce="debounce"
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
                            @blur="onBlur"
        >
            <div slot="suggestion-item" slot-scope="scope">
                <!-- @*event*.stop="" handlers are needed to prevent the splitter from being selected -->
                <div v-if="scope.suggestion.splitter"
                     class="top-search-splitter"
                     @click.stop=""
                >
                    {{ scope.suggestion.name }}
                </div>
                <div v-else class="top-search-suggestion">
                    <span v-if="scope.suggestion.important === 10" class="me-1">
                        <font-awesome-icon icon="heart" class="text-danger" />
                    </span>
                    <span class="d-inline" v-html="boldenSuggestion(scope)" />
                </div>
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
            wrapperClass: {
                type: String,
                default: "",
            },
            debounce: {
                type: Number,
                default: 200,
            },
        },
        data() {
            return {
                query: "",
                autoCompleteStyle: {
                    vueSimpleSuggest: "position-relative",
                    inputWrapper: "",
                    defaultInput: "form-control",
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

                if (suggestion.doctype) {
                    result = "<em class='top-search-object-type'>" + suggestion.doctype + "</em> - " + result;
                }

                if (!query) return result;

                const texts = query.split(/[\s-_/\\|\.]/gm).filter((t) => !!t) || [""];
                return result.replace(new RegExp("(.*?)(" + texts.join("|") + ")(.*?)", "gi"), "$1<b class='matched'>$2</b>$3");
            },
            select(datum) {
                if (typeof this.$parent.select !== "function") {
                    console.error("Error: parent component must define a select() function.");
                } else {
                    this.$parent.select(datum);
                }
            },
            onBlur(evt) {
                this.$emit("blur", evt);
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
