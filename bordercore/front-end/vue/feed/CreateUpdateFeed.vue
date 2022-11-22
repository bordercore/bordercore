<template>
    <div id="modalUpdateFeed" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
        <div class="modal-dialog modal-lg" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        {{ action }} Feed
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
                </div>
                <div class="modal-body">
                    <div>
                        <form @submit.prevent>
                            <div>
                                <div class="row mb-3">
                                    <label class="fw-bold col-lg-3 col-form-label text-end" for="inputTitle">Name</label>
                                    <div class="col-lg-9">
                                        <input id="id_name" v-model="feedInfo.name" type="text" name="name" class="form-control" autocomplete="off" maxlength="200" required>
                                    </div>
                                </div>

                                <div class="row mb-3">
                                    <label class="fw-bold col-lg-3 col-form-label text-end" for="inputTitle">Url</label>
                                    <div class="col-lg-9">
                                        <input id="id_url" v-model="feedInfo.url" type="text" name="url" class="form-control" required autocomplete="off" @blur="onBlur">
                                    </div>
                                </div>

                                <div class="row mb-3">
                                    <label class="fw-bold col-lg-3 col-form-label text-end" for="inputTitle">Homepage</label>
                                    <div class="col-lg-9">
                                        <input id="id_homepage" v-model="feedInfo.homepage" type="text" name="name" class="form-control" autocomplete="off" maxlength="200" required>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
                <div class="modal-footer row g-0">
                    <div class="col-offset-3 col-lg-9 d-flex align-items-center ps-3">
                        <div id="feed-status">
                            <div class="d-flex align-items-center">
                                <div v-if="checkingStatus" class="d-flex align-items-center">
                                    <div class="spinner-border ms-2 text-secondary" role="status">
                                        <span class="sr-only">Checking feed status...</span>
                                    </div>
                                    <div class="ms-3">
                                        Checking feed status...
                                    </div>
                                </div>
                                <font-awesome-icon v-else :class="statusMsg.class" class="me-2" :icon="statusMsg.icon" />
                                <div v-html="status" />
                            </div>
                        </div>
                        <input class="btn btn-primary ms-auto" type="submit" :value="action" @click="onAction">
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    import {
        getReasonPhrase,
        StatusCodes,
    } from "http-status-codes";

    export default {
        props: {
            updateFeedUrl: {
                default: "",
                type: String,
            },
            createFeedUrl: {
                default: "",
                type: String,
            },
            feedCheckUrl: {
                default: "",
                type: String,
            },
        },
        data() {
            return {
                action: "Update",
                feedInfo: {},
                status: "",
                statusIcon: "check",
                checkingStatus: false,
                lastResponseCode: null,
            };
        },
        computed: {
            statusMsg: function() {
                if (!this.status) {
                    return {
                        "class": "d-none",
                        "icon": "check",
                    };
                } else if (!this.lastResponseCode || this.lastResponseCode === StatusCodes.OK) {
                    return {
                        "class": "d-block text-success",
                        "icon": "check",
                    };
                } else {
                    return {
                        "class": "d-block text-danger",
                        "icon": "exclamation-triangle",
                    };
                }
            },
        },
        mounted() {
            EventBus.$on("showStatus", (payload) => {
                this.status = payload.msg;
                this.$refs.status.classList.add(payload.classNameAdd);
            });
        },
        methods: {
            setAction(action) {
                this.action = action;
                this.status = "";
            },
            onAction() {
                if (this.action === "Update") {
                    doPut(
                        this,
                        this.updateFeedUrl.replace(/00000000-0000-0000-0000-000000000000/, this.feedInfo.uuid),
                        {
                            "feed_uuid": this.feedInfo.uuid,
                            "homepage": this.feedInfo.homepage,
                            "name": this.feedInfo.name,
                            "url": this.feedInfo.url,
                        },
                        () => {
                            const modal = Modal.getInstance(document.getElementById("modalUpdateFeed"));
                            modal.hide();
                        },
                        "Feed updated",
                    );
                } else {
                    doPost(
                        this,
                        this.createFeedUrl,
                        {
                            "homepage": this.feedInfo.homepage,
                            "name": this.feedInfo.name,
                            "url": this.feedInfo.url,
                        },
                        (response) => {
                            EventBus.$emit("addFeed", response.data.feed_info);
                            const modal = Modal.getInstance(document.getElementById("modalUpdateFeed"));
                            modal.hide();
                        },
                        "Feed created. Please wait up to an hour for the feed to update.",
                    );
                }
            },
            onBlur(evt) {
                this.checkingStatus = true;

                let feedUrl = document.getElementById("id_url").value;
                if ( !feedUrl ) {
                    return;
                }

                const homepage = document.getElementById("id_homepage").value;
                if ( !homepage ) {
                    const baseUrl = document.getElementById("id_url").value.match(/^(https?:\/\/.*?)\//);
                    if (baseUrl) {
                        this.feedInfo.homepage = baseUrl[1];
                    }
                }

                feedUrl = encodeURIComponent(feedUrl).replace(/%/g, "%25");

                // TODO: Replace with doGet() ?
                const self = this;

                axios.get(this.feedCheckUrl.replace(/666/, feedUrl))
                     .then((response) => {
                         self.checkingStatus = false;
                         self.lastResponseCode = response.data.status;
                         if (!response || response.data.status != StatusCodes.OK) {
                             this.statusIcon = "exclamation-triangle";
                             this.status = "Feed error. Status: <strong>" + getReasonPhrase(response.data.status) + "</strong>";
                         } else if (response.data.entry_count == 0) {
                             this.status = "Feed error. Found no feed items.";
                         } else {
                             this.status = "Feed <strong>OK</strong>. Found <strong>" + response.data.entry_count + "</strong> feed items.";
                         }
                     });
            },
        },

    };

</script>
