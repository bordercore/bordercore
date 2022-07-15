<template>
    <div id="modalUpdateCollection" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        {{ action }} Collection
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
                </div>
                <div class="modal-body">
                    <ul v-if="action === 'Add'" class="nav nav-tabs justify-content-center mb-2" role="tablist" aria-orientation="horizontal">
                        <li class="nav-item">
                            <a class="nav-link active tab-modal" href="#" role="tab" data-bs-toggle="tab" data-bs-target="#section-new" aria-controls="v-pills-main" aria-selected="true">
                                New
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link tab-modal" href="#" role="tab" data-bs-toggle="tab" data-bs-target="#section-existing" aria-controls="v-pills-metadata" aria-selected="false">
                                Existing
                            </a>
                        </li>
                    </ul>

                    <div class="tab-content py-4">
                        <div id="section-new" class="tab-pane active">
                            <div v-if="action === 'Add' || collectionObjectList.collection_type === 'ad-hoc'" class="row mb-3">
                                <label class="col-lg-3 col-form-label" for="inputTitle">
                                    Name
                                </label>
                                <div class="col-lg-9">
                                    <input v-model="collectionObjectList.name" type="text" class="form-control" autocomplete="off" maxlength="200" required @keyup.enter="onUpdateCollection">
                                </div>
                            </div>
                            <div class="row mb-3">
                                <label class="col-lg-3 col-form-label" for="inputTitle">
                                    Display
                                </label>
                                <div class="col-lg-9">
                                    <div class="d-flex flex-column">
                                        <select v-model="collectionObjectList.display" class="form-control form-select">
                                            <option v-for="option in displayOptions" :key="option.value" :value="option.value">
                                                {{ option.display }}
                                            </option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            <Transition name="fade">
                                <div v-if="collectionObjectList.display === 'individual'" class="row mb-3">
                                    <label class="col-lg-3 col-form-label" for="inputTitle">Rotate</label>
                                    <div class="col-lg-9">
                                        <div class="d-flex flex-column">
                                            <select v-model="collectionObjectList.rotate" class="form-control form-select">
                                                <option
                                                    v-for="option in rotateOptions"
                                                    :key="option.value"
                                                    :value="option.value"
                                                >
                                                    {{ option.display }}
                                                </option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            </Transition>
                        </div>
                        <div id="section-existing" class="tab-pane">
                            <vue-simple-suggest
                                ref="suggestComponent"
                                display-attribute="name"
                                value-attribute="uuid"
                                :list="search"
                                name="search"
                                :filter-by-query="true"
                                :debounce="200"
                                :min-length="2"
                                :max-suggestions="20"
                                placeholder="Search collections"
                                :styles="autoCompleteStyle"
                                autocomplete="off"
                                :autofocus="false"
                                @select="select"
                            >
                                <div slot="suggestion-item" slot-scope="{ suggestion }">
                                    <div :class="{'suggestion-item-disabled': suggestion.contains_blob}" class="top-search-suggestion d-flex align-items-center" @click.stop="onSelectCollection(suggestion)">
                                        <div>
                                            <img class="me-2" width="50" height="50" :src="suggestion.cover_url">
                                        </div>
                                        <div class="me-1">
                                            {{ displayProperty(suggestion) }}
                                        </div>
                                        <div class="text-primary mx-1">
                                            <small>{{ suggestion.num_blobs }} blobs</small>
                                        </div>
                                        <div v-if="suggestion.contains_blob" class="text-warning ms-auto">
                                            Added
                                        </div>
                                    </div>
                                </div>
                            </vue-simple-suggest>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <input id="btn-action" class="btn btn-primary" type="button" :value="action" @click="onUpdateCollection">
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    import VueSimpleSuggest from "vue-simple-suggest";

    export default {

        name: "CollectionObjectListModal",
        components: {
            VueSimpleSuggest,
        },
        props: {
            addCollectionUrl: {
                default: "",
                type: String,
            },
            searchUrl: {
                default: "",
                type: String,
            },
        },
        data() {
            return {
                action: "Update",
                autoCompleteStyle: {
                    vueSimpleSuggest: "position-relative",
                    inputWrapper: "",
                    defaultInput: "form-control",
                    suggestions: "position-absolute list-group z-1000",
                    suggestItem: "list-group-item",
                },
                callback: null,
                collectionObjectList: {},
                collectionObjectListInitial: {},
                modal: null,
                displayOptions: [
                    {
                        value: "list",
                        display: "List",
                    },
                    {
                        value: "individual",
                        display: "Individual",
                    },
                ],
                rotateOptions: [
                    {
                        value: -1,
                        display: "Never",
                        default: true
                    },
                    {
                        value: 1,
                        display: "Every Minute",
                    },
                    {
                        value: 5,
                        display: "Every 5 Minutes",
                    },
                    {
                        value: 10,
                        display: "Every 10 Minutes",
                    },
                    {
                        value: 30,
                        display: "Every 30 Minutes",
                    },
                    {
                        value: 60,
                        display: "Every Hour",
                    },
                    {
                        value: 1440,
                        display: "Every Day",
                    },
                ],
            };
        },
        mounted() {
            this.modal = new Modal("#modalUpdateCollection");
        },
        methods: {
            displayProperty: function(suggestion) {
                return this.$refs.suggestComponent.displayProperty(suggestion);
            },
            onSelectCollection(suggestion) {
                if (!suggestion.contains_blob) {
                    this.select(suggestion);
                }
            },
            openModal(action, callback, collectionObjectList) {
                this.collectionObjectList = collectionObjectList;
                this.collectionObjectListInitial = {...collectionObjectList};
                this.action = action;
                this.callback = callback;
                this.modal.show();
                setTimeout( () => {
                    document.querySelector("#modalUpdateCollection input").focus();
                }, 500);
            },
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
            select(collection) {
                doPost(
                    this,
                    this.addCollectionUrl,
                    {
                        "node_uuid": this.$store.state.nodeUuid,
                        "collection_name": collection.name,
                        "collection_uuid": collection.uuid,
                    },
                    (response) => {
                        EventBus.$emit("update-layout", response.data.layout);
                        this.modal.hide();
                        this.$nextTick(() => {
                            this.$refs.suggestComponent.$el.querySelector("input").blur();
                            this.$refs.suggestComponent.setText("");
                        });
                    },
                    "Collection added",
                    "",
                );
            },
            onUpdateCollection() {
                // If any of the properties have changed, trigger the callback
                if (this.collectionObjectList !== this.collectionObjectListInitial) {
                    this.callback(this.collectionObjectList);
                }
                this.modal.hide();
            },
        },

    };

</script>
