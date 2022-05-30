<template>
    <div id="modalAddBlob" class="modal fade" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        Add blob
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" />
                </div>
                <div class="modal-body">
                    <div class="d-flex flex-column">
                        <form @submit.prevent>
                            <div>
                                <simple-suggest
                                    ref="simpleSuggest"
                                    class="w-100"
                                    display-attribute="name"
                                    value-attribute="uuid"
                                    :search-url="getSearchBlobUrl()"
                                />
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    export default {

        props: {
            searchBlobUrl: {
                default: "",
                type: String,
            },
            recentBlobsUrl: {
                default: "url",
                type: String,
            },
        },
        data() {
            return {
                name: "",
                blobUuid: null,
                collectionUuid: null,
                callback: null,
            };
        },
        methods: {
            getSearchBlobUrl() {
                let url = this.searchBlobUrl;
                if (this.collectionUuid) {
                    url += `&collection_uuid=${this.collectionUuid}`;
                }
                url += "&term=";
                return url;
            },
            openModal(collectionUuid, callback) {
                this.collectionUuid = collectionUuid;
                this.callback = callback;
                const modal = new Modal("#modalAddBlob");
                modal.show();
                setTimeout( () => {
                    this.$refs.simpleSuggest.$refs.suggestComponent.input.focus();
                }, 500);

                const suggest = this.$refs.simpleSuggest.$refs.suggestComponent;

                if (suggest.suggestions.length === 0) {
                    doGet(
                        this,
                        this.recentBlobsUrl,
                        (response) => {
                            suggest.suggestions = response.data.blobList;
                            suggest.suggestions.unshift(
                                {
                                    uuid: "__Recent",
                                    name: "Recent",
                                    splitter: true,
                                    value: "Bogus",
                                },
                            );
                        },
                    );
                }
                suggest.listShown = true;
            },
            select(selection) {
                // The parent component receives the blob uuid
                this.$emit("select-blob", selection, this.collectionUuid, this.callback);

                const modal = Modal.getInstance(document.getElementById("modalAddBlob"));
                modal.hide();

                this.$nextTick(() => {
                    this.$refs.simpleSuggest.$refs.suggestComponent.$el.querySelector("input").blur();
                    this.$refs.simpleSuggest.$refs.suggestComponent.setText("");
                });
            },
        },

    };

</script>
