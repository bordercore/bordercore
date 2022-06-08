<template>
    <div class="hover-reveal-target">
        <card title="" class="position-relative">
            <template #title-slot>
                <div class="card-title d-flex">
                    <div>
                        <font-awesome-icon icon="tasks" class="text-primary me-3" />
                        Todo Tasks
                    </div>
                    <div class="ms-auto">
                        <add-button href="#" :click-handler="handleCreateTodo" class="hover-reveal-object button-add-container d-none" />
                    </div>
                </div>
            </template>

            <template #content>
                <hr class="filter-divider mt-0">
                <ul id="sort-container-tags" class="list-group list-group-flush interior-borders">
                    <draggable v-model="todoList" ghost-class="sortable-ghost" draggable=".draggable" @change="handleSort">
                        <transition-group type="transition" class="w-100">
                            <li v-for="todo in todoList" v-cloak :key="todo.uuid" class="hover-target list-group-item list-group-item-secondary text-info draggable pe-0" :data-uuid="todo.uuid">
                                <div class="dropdown-height d-flex align-items-start">
                                    <div>
                                        <a :href="todo.url">{{ todo.name }}</a>
                                        <div v-if="todo.url" class="node-url">
                                            <a :href="todo.url">Link</a>
                                        </div>
                                        <div v-if="todo.note" class="node-note text-white">
                                            {{ todo.note }}
                                        </div>
                                    </div>

                                    <drop-down-menu :show-on-hover="true">
                                        <div slot="dropdown">
                                            <a class="dropdown-item" href="#" @click.prevent="handleUpdateTodo(todo)">
                                                <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />Update
                                            </a>
                                            <a class="dropdown-item" href="#" @click.prevent="removeTodo(todo.uuid)">
                                                <font-awesome-icon icon="trash-alt" class="text-primary me-3" />Remove
                                            </a>
                                        </div>
                                    </drop-down-menu>
                                </div>
                            </li>
                            <div v-if="todoList.length == 0" v-cloak :key="1" class="text-muted">
                                No tasks
                            </div>
                        </transition-group>
                    </draggable>
                </ul>
            </template>
        </card>
    </div>
</template>

<script>

    export default {

        name: "NodeTodoList",
        props: {
            nodeUuid: {
                type: String,
                default: "",
            },
            getTodoListUrl: {
                type: String,
                default: "",
            },
            addNodeTodoUrl: {
                type: String,
                default: "",
            },
            removeNodeTodoUrl: {
                type: String,
                default: "",
            },
            sortNodeTodosUrl: {
                type: String,
                default: "",
            },
        },
        data() {
            return {
                todoList: [],
                show: false,
            };
        },
        mounted() {
            this.getTodoList();
        },
        methods: {
            addNodeTodo(todoUuid) {
                doPost(
                    this,
                    this.addNodeTodoUrl,
                    {
                        "node_uuid": this.nodeUuid,
                        "todo_uuid": todoUuid,
                    },
                    () => {
                        this.getTodoList();
                    },
                    "",
                );
            },
            removeTodo(todoUuid) {
                // Delete the todo item, and the SortOrderNodeTodo object
                //  will automatically be deleted as well
                const self = this;
                axios.delete(this.removeNodeTodoUrl.replace("00000000-0000-0000-0000-000000000000", todoUuid))
                    .then((response) => {
                        EventBus.$emit(
                            "toast",
                            {
                                "body": "Todo task deleted",
                                "variant": "info",
                            },
                        );
                        self.getTodoList();
                        console.log("Success");
                    }, (error) => {
                        console.log(error);
                    });
            },
            handleCreateTodo() {
                this.$parent.$parent.$refs.updateTodo.setAction("Create");
                const modal = new Modal("#modalUpdateTodo");
                modal.show();
                setTimeout( () => {
                    document.getElementById("id_name").focus();
                }, 500);
            },
            handleUpdateTodo(todoInfo) {
                this.$parent.$parent.$refs.updateTodo.setAction("Update");
                this.$parent.$parent.$refs.updateTodo.todoInfo = {
                    uuid: todoInfo.uuid,
                    name: todoInfo.name,
                    note: todoInfo.note,
                    url: todoInfo.url,
                    priority: 2,
                    tags: [],
                };
                const modal = new Modal("#modalUpdateTodo");
                modal.show();
                setTimeout( () => {
                    document.getElementById("id_name").focus();
                }, 500);
            },
            getTodoList() {
                doGet(
                    this,
                    this.getTodoListUrl,
                    (response) => {
                        this.todoList = response.data.todo_list;
                    },
                    "Error getting note",
                );
            },
            handleSort(evt) {
                const todoUuid = evt.moved.element.uuid;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                const newPosition = evt.moved.newIndex + 1;

                doPost(
                    this,
                    this.sortNodeTodosUrl,
                    {
                        "node_uuid": this.$store.state.nodeUuid,
                        "todo_uuid": todoUuid,
                        "new_position": newPosition,
                    },
                    () => {},
                    "",
                );
            },
        },
    };

</script>
