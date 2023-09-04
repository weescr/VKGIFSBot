from vkbottle.api import API


class VkTools:

    api_object = None

    def __init__(self, vk_token: str):
        self.api_object = API(vk_token)

    async def get_vk_gifs(self, offset=None):
        result = await self.api_object.docs.get(offset=offset, type=3)
        return result.items

    async def search_vk_gifs(self, q: str, offset=None):
        result = await self.api_object.docs.search(q=q, search_own=1, offset=offset)
        return result.items
