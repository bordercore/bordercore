<template>
    <div id="modalUpdateTodo" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
        <div class="modal-dialog modal-lg" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        {{ action }} Todo Task
                    </h4>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <div>
                        <form @submit.prevent>
                            <div>
                                <div class="form-group row">
                                    <label class="font-weight-bold col-lg-3 col-form-label text-right" for="inputName">Name</label>
                                    <div class="col-lg-9">
                                        <input id="id_name" v-model="todoInfo.name" type="text" name="name" class="form-control" autocomplete="off" maxlength="200" required>
                                    </div>
                                </div>
                                <div class="form-group row">
                                    <label class="font-weight-bold col-lg-3 col-form-label text-right" for="inputPriority">Priority</label>
                                    <div class="col-lg-9">
                                        <select id="id_priority" v-model="todoInfo.priority" name="priority" class="form-control">
                                            <option v-for="priority in priorityList" :key="priority[0]" :value="priority[0]">
                                                {{ priority[1] }}
                                            </option>
                                        </select>
                                    </div>
                                </div>
                                <div class="form-group row">
                                    <label class="font-weight-bold col-lg-3 col-form-label text-right" for="inputNote">Note</label>
                                    <div class="col-lg-9">
                                        <textarea id="id_note" v-model="todoInfo.note" name="note" cols="40" rows="2" class="form-control" />
                                    </div>
                                </div>
                                <div class="form-group row">
                                    <label class="font-weight-bold col-lg-3 col-form-label text-right" for="inputTags">Tags</label>
                                    <div class="col-lg-9">
                                        <tags-input
                                            :search-url="tagSearchUrl"
                                            :get-tags-from-event="true"
                                            @tags-changed="onTagsChanged"
                                        />
                                    </div>
                                </div>
                                <div class="form-group row">
                                    <label class="font-weight-bold col-lg-3 col-form-label text-right" for="inputUrl">Url</label>
                                    <div class="col-lg-9">
                                        <input id="id_url" v-model="todoInfo.url" type="text" name="url" class="form-control" required autocomplete="off">
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
                <div class="modal-footer row no-gutters">
                    <div class="col-offset-3 col-lg-9 d-flex align-items-center pl-3">
                        <div id="feed-status">
                            <div class="d-flex">
                                <div v-if="checkingStatus" class="d-flex align-items-center">
                                    <div class="spinner-border ml-2 text-info" role="status">
                                        <span class="sr-only">Checking feed status...</span>
                                    </div>
                                    <div class="ml-3">
                                        Checking feed status...
                                    </div>
                                </div>
                                <font-awesome-icon v-else :class="statusMsg.class" class="mr-2" :icon="statusMsg.icon" />
                                <div v-html="status" />
                            </div>
                        </div>
                        <input class="btn btn-primary ml-auto" type="submit" :value="action" @click="onAction">
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    export default {
        props: {
            priorityList: {
                default: () => [],
                type: Array,
            },
            updateTodoUrl: {
                default: "",
                type: String,
            },
            createTodoUrl: {
                default: "",
                type: String,
            },
            tagSearchUrl: {
                default: "",
                type: String,
            },
        },
        data() {
            return {
                action: "Update",
                todoInfo: {},
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
            onTagsChanged(newTags) {
                this.todoInfo.tags = newTags;
            },
            onAction() {
                if (this.action === "Update") {
                    doPut(
                        this,
                        this.updateTodoUrl.replace(/00000000-0000-0000-0000-000000000000/, this.todoInfo.uuid),
                        {
                            "todo_uuid": this.todoInfo.uuid,
                            "name": this.todoInfo.name,
                            "priority": this.todoInfo.priority,
                            "note": this.todoInfo.note,
                            "tags": this.todoInfo.tags.map((x) => x.text),
                            "url": this.todoInfo.url || "",
                        },
                        () => {
                            this.$parent.getTodoList();
                            $("#modalUpdateTodo").modal("hide");
                        },
                        "Todo updated",
                    );
                } else {
                    doPost(
                        this,
                        this.createTodoUrl,
                        {
                            "name": this.todoInfo.name,
                            "priority": this.todoInfo.priority,
                            "note": this.todoInfo.note || "",
                            "tags": this.todoInfo.tags.map((x) => x.text),
                            "url": this.todoInfo.url || "",
                        },
                        (response) => {
                            this.$parent.getTodoList();
                            $("#modalUpdateTodo").modal("hide");
                        },
                        "Todo task created.",
                    );
                }
            },
        },

    };

</script>
