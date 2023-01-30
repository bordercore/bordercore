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
                                            get-tags-from-event
                                            @tags-changed="onTagsChanged"
                                        />
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label class="fw-bold col-lg-3 col-form-label text-end" for="inputUrl">Url</label>
                                    <div class="col-lg-9">
                                        <input id="id_url" v-model="todoInfo.url" type="text" name="url" class="form-control" autocomplete="off">
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
                                <div class="row mb-3">
                                    <div class="col-lg-12 offset-lg-3">
                                        <input class="btn btn-primary" type="button" :value="action" @click.prevent="onAction">
                                    </div>
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
                todoInfo: {
                    priority: 2,
                    tags: [],
                },
                lastResponseCode: null,
            };
        },
        methods: {
            customFormatter(date) {
                return format(new Date(date), "YYYY-MM-DD");
            },
            setAction(action) {
                this.action = action;
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
                            "tags": this.todoInfo.tags,
                            "url": this.todoInfo.url || "",
                            "due_date": dueDate,
                        },
                        (response) => {
                            this.$emit("post-todo-update", response.data.uuid);
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
                            "tags": this.todoInfo.tags,
                            "url": this.todoInfo.url || "",
                            "due_date": dueDate,
                        },
                        (response) => {
                            this.$emit("post-todo-add", response.data.uuid);
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
