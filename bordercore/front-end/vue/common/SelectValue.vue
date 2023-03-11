<template>
    <div :class="[{ 'has-search': searchIcon }, wrapperClass]">
        <div v-if="searchIcon">
            <font-awesome-icon icon="search" />
        </div>
        <multiselect
            ref="multiselect"
            v-model="value"
            :disabled="isDisabled"
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
            @select="select"
            @close="onClose"
        >
            <template #option="props">
                <slot name="option" v-bind="props">
                    <div v-if="props.option[label] !== emptyLabel">
                        <div v-if="boldenOptions" v-html="boldenOption(props.option[label], props.search)" />
                    </div>
                    <div v-else class="d-none" />
                </slot>
            </template>
            <template #caret>
                <div class="multiselect__select d-flex align-items-center">
                    <font-awesome-icon icon="angle-down" class="ms-2" />
                </div>
            </template>
            <template #afterList="props">
                <slot name="afterList" v-bind="props" />
            </template>
            <template #noResult>
                <div v-show="showNoResult">
                    Nothing found
                </div>
            </template>
        </multiselect>
        <input :id="id" type="hidden" :name="name" :value="getValueComputed">
    </div>
</template>

<script>

    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";
    import {boldenOption} from "/front-end/util.js";
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
            isDisabledInitial: {
                type: Boolean,
                default: false,
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
                emptyLabel: "____",
                isDisabled: false,
                options: [],
                showNoResult: false,
                value: "",
            };
        },
        computed: {
            getValueComputed() {
                return this.getValue();
            },
        },
        mounted() {
            // If given an initial value, add it to the options list
            //  and pre-select it.
            if (this.initialValue) {
                this.options = [this.initialValue];
                this.value = this.initialValue;
            }
            if (this.isDisabledInitial) {
                this.isDisabled = true;
            }
        },
        methods: {
            getValue() {
                if (typeof this.value === "object" && this.value !== null) {
                    return this.value[this.label];
                } else {
                    return "";
                }
            },
            boldenOption,
            clearOptions() {
                this.options = [];
                this.value = null;
            },
            focus() {
                this.$el.querySelector("input").focus();
            },
            onSearchChange(query) {
                this.$emit("search-change", query);
                if (this.$refs.multiselect.search.length <= this.minLength) {
                    this.options = [];
                    return;
                }

                try {
                    this.debounce(() => {
                        return axios.get(this.searchUrl + query)
                            .then((response) => {
                                this.options = response.data;
                                if (response.data.length > 0) {
                                    this.showNoResult = false;
                                    this.options.unshift({"label": this.emptyLabel, "name": ""});
                                } else {
                                    this.showNoResult = true;
                                }
                            });
                    });
                } catch (error) {
                    console.log(`Error: ${error}`);
                }
            },
            select(option) {
                // Once a value has been selected, emit an event to let the
                //  parent component handle it.
                // If the first option is highlighted, which is always the special
                //  empty label, assume the user hit "Enter" and wants to do a
                //  term search rather than select an option.
                if (option.label === this.emptyLabel) {
                    this.$emit("search", this.$refs.multiselect.search);
                    this.clearOptions();
                } else {
                    this.$emit("select", option);
                }
                this.options = [];
            },
            setDisabled(value) {
                this.isDisabled = value;
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
    };

</script>
