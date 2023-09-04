from vkbottle.api import API


class VkTools:

    api_object = None
    offset = None

    def __init__(self, vk_token: str):
        self.api_object = API(vk_token)
        self.offset = 1

    async def get_vk_gifs(self, offset=None):
        result = await self.api_object.docs.get(count=20, offset=offset, type=3)
        return result.items

    async def search_vk_gifs(self, q: str, offset=None):
        result = await self.api_object.docs.search(
            q=q, count=20, search_own=1, type=3, offset=offset
        )
        return result.items
