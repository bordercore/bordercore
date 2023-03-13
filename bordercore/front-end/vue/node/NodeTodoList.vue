<template>
    <div class="hover-reveal-target">
        <card title="" class="backdrop-filter node-color-1 position-relative">
            <template #title-slot>
                <div class="card-title d-flex">
                    <div>
                        <font-awesome-icon icon="tasks" class="text-primary me-3" />
                        Todo Tasks
                    </div>
                    <div class="dropdown-menu-container ms-auto">
                        <drop-down-menu class="d-none hover-reveal-object" :show-on-hover="false">
                            <template #dropdown>
                                <li>
                                    <a class="dropdown-item" href="#" @click.prevent="handleTodoCreate">
                                        <span>
                                            <font-awesome-icon icon="plus" class="text-primary me-3" />
                                        </span>
                                        Add Task
                                    </a>
                                </li>
                                <li>
                                    <a class="dropdown-item" href="#" @click.prevent="onDeleteTodoList">
                                        <span>
                                            <font-awesome-icon icon="plus" class="text-primary me-3" />
                                        </span>
                                        Remove Todo List
                                    </a>
                                </li>
                            </template>
                        </drop-down-menu>
                    </div>
                </div>
            </template>

            <template #content>
                <hr class="divider">
                <ul id="sort-container-tags" class="list-group list-group-flush interior-borders">
                    <draggable v-model="todoList" draggable=".draggable" :component-data="{type:'transition-group'}" item-key="todo.uuid" @change="handleTodoSort">
                        <template #item="{element}">
                            <li v-cloak :key="element.uuid" class="hover-target node-color-1 list-group-item list-group-item-secondary draggable pe-0" :data-uuid="element.uuid">
                                <div class="dropdown-height d-flex align-items-start">
                                    <div>
                                        <a :href="element.url">{{ element.name }}</a>
                                        <div v-if="element.url" class="node-url">
                                            <a :href="element.url">Link</a>
                                        </div>
                                        <div v-if="element.note" class="node-object-note">
                                            {{ element.note }}
                                        </div>
                                    </div>

                                    <drop-down-menu :show-on-hover="true">
                                        <template #dropdown>
                                            <li>
                                                <a class="dropdown-item" href="#" @click.prevent="handleTodoUpdate(element)">
                                                    <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />Update
                                                </a>
                                            </li>
                                            <li>
                                                <a class="dropdown-item" href="#" @click.prevent="handleTodoRemove(element.uuid)">
                                                    <font-awesome-icon icon="trash-alt" class="text-primary me-3" />Remove
                                                </a>
                                            </li>
                                        </template>
                                    </drop-down-menu>
                                </div>
                            </li>
                        </template>
                    </draggable>
                    <div v-if="todoList.length == 0" v-cloak :key="1" class="text-muted">
                        No tasks
                    </div>
                </ul>
            </template>
        </card>
    </div>
</template>

<script>

    import Card from "/front-end/vue/common/Card.vue";
    import draggable from "vuedraggable";
    import DropDownMenu from "/front-end/vue/common/DropDownMenu.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            Card,
            draggable,
            DropDownMenu,
            FontAwesomeIcon,
        },
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
            deleteTodoListUrl: {
                type: String,
                default: "",
            },
        },
        emits: ["open-create-update-todo-modal", "update-layout"],
        setup(props, ctx) {
            const todoList = ref([]);

            function addNodeTodo(todoUuid) {
                doPost(
                    props.addNodeTodoUrl,
                    {
                        "node_uuid": props.nodeUuid,
                        "todo_uuid": todoUuid,
                    },
                    () => {
                        getTodoList();
                    },
                );
            };

            function getTodoList() {
                doGet(
                    props.getTodoListUrl,
                    (response) => {
                        todoList.value = response.data.todo_list;
                    },
                    "Error getting todo list",
                );
            };

            function handleTodoCreate() {
                ctx.emit("open-create-update-todo-modal", "Create");
            };

            function handleTodoUpdate(todoInfo) {
                ctx.emit("open-create-update-todo-modal", "Update", todoInfo);
            };

            function onDeleteTodoList() {
                doPost(
                    props.deleteTodoListUrl,
                    {
                        "node_uuid": props.nodeUuid,
                    },
                    (response) => {
                        ctx.emit("update-layout", response.data.layout);
                    },
                    "Todo list deleted",
                );
            };

            function handleTodoRemove(todoUuid) {
                // Delete the todo item, and the NodeTodo object
                //  will automatically be deleted as well
                axios.delete(props.removeNodeTodoUrl.replace("00000000-0000-0000-0000-000000000000", todoUuid))
                    .then((response) => {
                        EventBus.$emit(
                            "toast",
                            {
                                "body": "Todo task deleted",
                                "variant": "info",
                            },
                        );
                        getTodoList();
                    }, (error) => {
                        console.log(error);
                    });
            };

            function handleTodoSort(evt) {
                const todoUuid = evt.moved.element.uuid;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                const newPosition = evt.moved.newIndex + 1;

                doPost(
                    props.sortNodeTodosUrl,
                    {
                        "node_uuid": props.nodeUuid,
                        "todo_uuid": todoUuid,
                        "new_position": newPosition,
                    },
                    () => {},
                );
            };

            onMounted(() => {
                getTodoList();
            });

            return {
                addNodeTodo,
                getTodoList,
                handleTodoSort,
                handleTodoCreate,
                handleTodoRemove,
                onDeleteTodoList,
                handleTodoUpdate,
                todoList,
            };
        },
    };

</script>
