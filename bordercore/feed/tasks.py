from celery import task


@task()
def update_feed(id):

    # Import Django models here rather than globally at the top to avoid circular dependencies
    from feed.models import Feed
    feed = Feed.objects.get(pk=id)
    feed.update()
