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
                    <div v-if="action === 'Add'">
                        <div class="form-section">
                            Type
                        </div>
                        <div class="row mt-3">
                            <div class="col-lg-4">
                                <div class="form-check d-flex align-items-center">
                                    <input v-model="collectionObjectList.collection_type" class="form-check-input" type="radio" name="type" value="ad-hoc">
                                    <label class="form-check-label ms-2" for="type">
                                        New
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-lg-4">
                                <div class="form-check d-flex align-items-center">
                                    <input v-model="collectionObjectList.collection_type" class="form-check-input" type="radio" name="type" value="permanent">
                                    <label class="form-check-label ms-2" for="type">
                                        Existing
                                    </label>
                                </div>
                            </div>
                            <div class="col-lg-8">
                                <vue-simple-suggest
                                    ref="suggestComponent"
                                    :destyled="true"
                                    display-attribute="name"
                                    value-attribute="uuid"
                                    :list="search"
                                    :filter-by-query="true"
                                    :debounce="200"
                                    :min-length="2"
                                    :max-suggestions="20"
                                    placeholder="Search collections"
                                    :styles="autoCompleteStyle"
                                    autocomplete="off"
                                    :autofocus="false"
                                    @select="onSelectCollection"
                                >
                                    <div slot="suggestion-item" slot-scope="{ suggestion }">
                                        <div :class="{'suggestion-item-disabled': suggestion.contains_blob}" class="search-suggestion d-flex align-items-center">
                                            <div>
                                                <img class="me-2 mt-2" width="50" height="50" :src="suggestion.cover_url">
                                            </div>
                                            <div class="d-flex flex-column">
                                                <div>
                                                    {{ displayProperty(suggestion) }}
                                                </div>
                                                <div class="text-secondary lh-1">
                                                    <small>{{ suggestion.num_blobs }} blobs</small>
                                                </div>
                                                <div v-if="suggestion.contains_blob" class="text-warning ms-auto">
                                                    Added
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </vue-simple-suggest>
                            </div>
                        </div>
                        <hr class="my-3">
                    </div>
                    <div class="form-section">
                        Options
                    </div>
                    <Transition name="fade">
                        <div v-if="collectionObjectList.collection_type === 'ad-hoc'" class="row mb-3">
                            <label class="col-lg-4 col-form-label" for="inputTitle">
                                Name
                            </label>
                            <div class="col-lg-8">
                                <input v-model="collectionObjectList.name" type="text" class="form-control" autocomplete="off" maxlength="200" placeholder="Name" @keyup.enter="onUpdateCollection">
                            </div>
                        </div>
                    </Transition>
                    <div class="row mt-3">
                        <label class="col-lg-4 col-form-label" for="inputTitle">
                            Display
                        </label>
                        <div class="col-lg-8">
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
                        <div v-if="collectionObjectList.display === 'individual'" class="row mt-3">
                            <label class="col-lg-4 col-form-label" for="inputTitle">Rotate</label>
                            <div class="col-lg-8">
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
                        <div v-else class="row mt-3">
                            <label class="col-lg-4 col-form-label" for="inputTitle">Limit</label>
                            <div class="col-lg-8">
                                <div>
                                    <input v-model="collectionObjectList.limit" type="number" class="form-control" autocomplete="off" maxlength="10" placeholder="Limit" @keyup.enter="onUpdateCollection">
                                </div>
                            </div>
                        </div>
                    </Transition>
                    <div class="row align-items-center my-3">
                        <label class="col-lg-4 col-form-label" for="inputTitle">
                            Random Order
                        </label>
                        <div class="col-lg-8 mt-1">
                            <input v-model="collectionObjectList.random_order" value="random_order" type="checkbox">
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
                        default: true,
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
            onSelectCollection(collection) {
                this.collectionObjectList.uuid = collection.uuid;
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
            onUpdateCollection() {
                // If any of the properties have changed, update the collection
                if (this.collectionObjectList !== this.collectionObjectListInitial) {
                    if (this.action === "Update") {
                        this.callback(this.collectionObjectList);
                        this.modal.hide();
                    } else {
                        doPost(
                            this,
                            this.addCollectionUrl,
                            {
                                "node_uuid": this.$store.state.nodeUuid,
                                "collection_name": this.collectionObjectList.name,
                                "collection_uuid": this.collectionObjectList.uuid,
                                "display": this.collectionObjectList.display,
                                "random_order": this.collectionObjectList.random_order,
                                "rotate": this.collectionObjectList.rotate,
                                "limit": this.collectionObjectList.limit,
                            },
                            (response) => {
                                EventBus.$emit("update-layout", response.data.layout);
                                this.modal.hide();
                                this.$nextTick(() => {
                                    this.$refs.suggestComponent.hideList();
                                });
                            },
                            "Collection added",
                            "",
                        );
                    }
                }
            },
        },

    };

</script>
