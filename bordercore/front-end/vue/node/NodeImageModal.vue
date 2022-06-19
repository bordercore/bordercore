<template>
    <div id="nodeImageModal" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
        <div class="modal-dialog modal-dialog-centered modal-fullscreen" role="document">
            <div class="modal-content">
                <div class="modal-body">
                    <div>
                        <img :src="imageUrl" class="w-100">
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    export default {

        name: "NoteImageModal",
        data() {
            return {
                modal: null,
                imageUrl: null,
            };
        },
        mounted() {
            this.modal = new Modal("#nodeImageModal");
        },
        methods: {
            openModal(data) {
                this.imageUrl = data;
                this.modal.show();
            },
        },

    };

</script>
