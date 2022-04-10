<template>
    <div id="modalUpdateTodo" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
        <div class="modal-dialog modal-lg" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        {{ action }} Todo Task
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
                </div>
                <div class="modal-body">
                    <div>
                        <form @submit.prevent>
                            <div>
                                <div class="row mb-3">
                                    <label class="fw-bold col-lg-3 col-form-label text-end" for="inputName">Name</label>
                                    <div class="col-lg-9">
                                        <input id="id_name" v-model="todoInfo.name" type="text" name="name" class="form-control" autocomplete="off" maxlength="200" required>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label class="fw-bold col-lg-3 col-form-label text-end" for="inputPriority">Priority</label>
                                    <div class="col-lg-9">
                                        <select id="id_priority" v-model="todoInfo.priority" name="priority" class="form-control form-select">
                                            <option v-for="priority in priorityList" :key="priority[0]" :value="priority[0]">
                                                {{ priority[1] }}
                                            </option>
                                        </select>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label class="fw-bold col-lg-3 col-form-label text-end" for="inputNote">Note</label>
                                    <div class="col-lg-9">
                                        <textarea id="id_note" v-model="todoInfo.note" name="note" cols="40" rows="2" class="form-control" />
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label class="fw-bold col-lg-3 col-form-label text-end" for="inputTags">Tags</label>
                                    <div class="col-lg-9">
                                        <tags-input
                                            :search-url="tagSearchUrl"
                                            :get-tags-from-event="true"
                                            @tags-changed="onTagsChanged"
                                        />
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label class="fw-bold col-lg-3 col-form-label text-end" for="inputUrl">Url</label>
                                    <div class="col-lg-9">
                                        <input id="id_url" v-model="todoInfo.url" type="text" name="url" class="form-control" required autocomplete="off">
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label class="fw-bold col-lg-3 col-form-label text-end" for="dueDate">Due Date</label>
                                    <div class="col-lg-9">
                                        <vuejs-datepicker
                                            id="id_due_date"
                                            v-model="todoInfo.due_date"
                                            :bootstrap-styling="true"
                                            :format="customFormatter"
                                            :typeable="true"
                                            name="due_date"
                                            calendar-class="calendar"
                                        >
                                            <span slot="afterDateInput" class="input-group-append">
                                                <div class="input-group-text h-100">
                                                    <font-awesome-icon icon="calendar-alt" />
                                                </div>
                                            </span>
                                        </vuejs-datepicker>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
                <div class="modal-footer row g-0">
                    <div class="col-offset-3 col-lg-9 d-flex align-items-center ps-3">
                        <div id="feed-status">
                            <div class="d-flex">
                                <div v-if="checkingStatus" class="d-flex align-items-center">
                                    <div class="spinner-border ms-2 text-info" role="status">
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
            customFormatter(date) {
                return format(new Date(date), "YYYY-MM-DD");
            },
            setAction(action) {
                this.action = action;
                this.status = "";
            },
            onTagsChanged(newTags) {
                this.todoInfo.tags = newTags;
            },
            onAction() {
                const dueDate = document.getElementsByName("due_date")[0].value;
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
                            "due_date": dueDate,
                        },
                        () => {
                            this.$parent.getTodoList();
                            const modal = Modal.getInstance(document.getElementById("modalUpdateTodo"));
                            modal.hide();
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
                            "due_date": dueDate,
                        },
                        (response) => {
                            this.$parent.getTodoList();
                            const modal = Modal.getInstance(document.getElementById("modalUpdateTodo"));
                            modal.hide();
                        },
                        "Todo task created.",
                    );
                }
            },
        },

    };

</script>
