<template>
    <div :class="[{ 'has-search': searchIcon }, wrapperClass]">
        <div v-if="searchIcon">
            <font-awesome-icon icon="search" />
        </div>
        <multiselect
            ref="multiselect"
            v-model="value"
            :track-by="label"
            :label="label"
            :options="options"
            :show-no-options="false"
            :internal-search="false"
            select-label=""
            deselect-label=""
            :value="initialValue"
            :accesskey="accesskey"
            :max-height="600"
            :min-length="2"
            :options-limit="optionsLimit"
            :placeholder="placeHolder"
            autocomplete="off"
            @search-change="onSearchChange"
            @keyup.enter.native="onSubmit"
            @select="select"
            @close="onClose"
        >
            <div slot="noResult" />
            <template #option="props">
                <slot name="option" v-bind="props">
                    <div v-if="boldenOptions" v-html="boldenOption(props.option, props.search)" />
                </slot>
            </template>
            <template #afterList="props">
                <slot name="afterList" v-bind="props" />
            </template>
        </multiselect>
        <input :id="id" type="hidden" :name="name" :value="getValue">
    </div>
</template>

<script>

    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";
    import Multiselect from "vue-multiselect";
    import debounceMixin from "../../debounce.js";

    export default {
        components: {
            FontAwesomeIcon,
            Multiselect,
        },
        mixins: [debounceMixin],
        props: {
            label: {
                type: String,
                default: "label",
            },
            initialValue: {
                type: Object,
                default: function() {},
            },
            minLength: {
                default: 2,
                type: Number,
            },
            accesskey: {
                type: String,
                default: null,
            },
            id: {
                type: String,
                default: null,
            },
            optionsLimit: {
                default: 20,
                type: Number,
            },
            searchIcon: {
                type: Boolean,
                default: false,
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
            boldenOptions: {
                type: Boolean,
                default: true,
            },
            wrapperClass: {
                type: String,
                default: "",
            },
        },
        data() {
            return {
                options: [],
                searchQuery: "",
                value: "",
            };
        },
        computed: {
            getValue() {
                if (typeof this.value === "object" && this.value !== null) {
                    return this.value[this.label];
                } else {
                    return "";
                }
            },
        },
        methods: {
            boldenOption(option, search) {
                const texts = search.split(/[\s-_/\\|\.]/gm).filter((t) => !!t) || [""];
                return option[this.label].replace(new RegExp("(.*?)(" + texts.join("|") + ")(.*?)", "gi"), "$1<b>$2</b>$3");
            },
            clearOptions() {
                this.options = [];
                this.value = null;
            },
            focus() {
                this.$el.querySelector("input").focus();
            },
            onSubmit() {
                const newOption = {
                    [this.label]: this.searchQuery,
                };
                this.options.push(newOption);
                this.value = newOption;
                this.searchQuery = "";
            },
            onSearchChange(query) {
                this.$emit("search-change", query);
                this.searchQuery = query;
                if (this.searchQuery.length <= this.minLength) return;

                try {
                    const url = this.searchUrl;
                    this.debounce(() => {
                        return axios.get(url + query)
                                    .then((response) => {
                                        this.options = response.data;
                                    });
                    });
                } catch (error) {
                    console.log(`Error: ${error}`);
                }
            },
            select(tagInfo) {
                this.$emit("select", tagInfo);
            },
            setValue(value) {
                const newOption = {
                    [this.label]: value,
                };
                this.options.push(newOption);
                this.value = newOption;
            },
            onClose(evt) {
                this.$emit("close", evt);
            },
        },
        mounted() {
            // If given an initial value, add it to the options list
            //  and pre-select it.
            if (this.initialValue) {
                this.options = [this.initialValue];
                this.value = this.initialValue;
            }
        },
    };

</script>
