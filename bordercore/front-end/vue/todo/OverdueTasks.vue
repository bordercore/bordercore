<template>
    <div id="modalOverdueTasks" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        Overdue Tasks
                    </h4>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <TransitionGroup name="fade" class="w-100">
                        <div v-for="task in taskList" :key="task.uuid" class="hoverable row m-2">
                            <div class="col-lg-9 d-flex my-2">
                                <div>
                                    <font-awesome-icon icon="list" class="text-info mr-3" />
                                </div>
                                <div>
                                    {{ task.name }}
                                    <span v-for="tag in task.tags" :key="tag" class="tag ml-2">
                                        {{ tag }}
                                    </span>
                                </div>
                            </div>
                            <div class="col-lg-3 my-2 d-flex justify-content-center">
                                <a class="glow" href="#" @click.prevent="rescheduleTask(task.uuid)">
                                    <font-awesome-icon icon="calendar-alt" class="text-info mr-3" data-toggle="tooltip" title="Reschedule Task" />
                                </a>
                                <a class="glow" href="#" @click.prevent="deleteTask(task.uuid)">
                                    <font-awesome-icon icon="trash-alt" class="text-info ml-3" data-toggle="tooltip" title="Delete Task" />
                                </a>
                            </div>
                        </div>
                    </TransitionGroup>
                    <div v-if="taskList.length !== 0" class="row">
                        <div class="col-lg-12">
                            <hr>
                        </div>
                    </div>
                    <div class="row m-2">
                        <div class="col-lg-9 d-flex align-items-center text-success">
                            <TransitionGroup name="fade">
                                <h4 v-if="taskList.length === 0" :key="1">
                                    <font-awesome-icon icon="check" class="text-success mr-3" />
                                    <span class="ml-3">All tasks done!</span>
                                </h4>
                                <div v-else :key="2">
                                    {{ message }}
                                </div>
                            </TransitionGroup>
                        </div>
                        <div class="col-lg-3">
                            <div class="ml-auto">
                                <button type="button" class="btn btn-primary" data-toggle="modal" data-target="#modalOverdueTasks">
                                    Dismiss
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    export default {
        name: "OverdueTasks",
        props: {
            taskListProp: {
                type: Array,
                default: () => [],
            },
            rescheduleTaskUrl: {
                type: String,
                default: "",
            },
            deleteTodoUrl: {
                type: String,
                default: "",
            },
        },
        data() {
            return {
                taskList: [],
                message: "",
            };
        },
        mounted() {
            this.taskList = this.taskListProp;
        },
        methods: {
            rescheduleTask(uuid) {
                doPost(
                    this,
                    this.rescheduleTaskUrl,
                    {
                        "todo_uuid": uuid,
                    }
                    ,
                    (response) => {
                        this.message = "Task rescheduled.";
                        this.removeTaskFromList(uuid);
                    },
                    "",
                    "",
                );
            },
            deleteTask(uuid) {
                axios.delete(this.deleteTodoUrl.replace("00000000-0000-0000-0000-000000000000", uuid))
                    .then((response) => {
                        this.message = "Task deleted.";
                        this.removeTaskFromList(uuid);
                        console.log("Success");
                    }, (error) => {
                        console.log(error);
                    });
            },
            removeTaskFromList(uuid) {
                for (let i = 0; i < this.taskList.length; i++) {
                    if (this.taskList[i].uuid == uuid) {
                        this.taskList.splice(i, 1);
                    }
                }
            },
        },
    };


</script>
