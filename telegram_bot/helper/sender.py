from asgiref.sync import sync_to_async


async def call_async(request, *args, **kwargs):
    response_async = sync_to_async(request)
    return await response_async(*args, **kwargs)


