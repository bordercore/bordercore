<template>
    <div id="modalAddBlob" class="modal fade" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        Add blob
                    </h4>
                    <button type="button" class="close" data-dismiss="modal">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="d-flex flex-column">
                        <form @submit.prevent>
                            <div class="form-group row">
                                <label class="col-form-label col-lg-3">Blob name</label>
                                <div class="form-row col-lg-9">
                                    <simple-suggest
                                        id="blob-search-name"
                                        ref="simpleSuggest"
                                        display-attribute="name"
                                        value-attribute="uuid"
                                        :search-url="searchBlobUrl + '?doc_type=book,blob,document&term='"
                                    />
                                </div>
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
        },
        data() {
            return {
                name: "",
                blobUuid: null,
            };
        },
        methods: {
            select(selection) {
                // The blob gets added in the parent component
                this.$emit("addBlob", selection.uuid);
                $("#modalAddBlob").modal("hide");

                this.$nextTick(() => {
                    this.$refs.simpleSuggest.$refs.suggestComponent.$el.querySelector("input").blur();
                    this.$refs.simpleSuggest.$refs.suggestComponent.setText("");
                });
            },
        },

    };

</script>
