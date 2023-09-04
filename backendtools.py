import aiohttp


class Requester:  # хахаха реквестер

    client_token = ""

    def __init__(self, client_token: str):
        self.backend_url = f"https://theweescripts.ru/api/vkgifsbot/{client_token}/auth"
        self.start_route = self.backend_url + "/{telegram_id}/start"
        self.get_vk_token = self.backend_url + "/{telegram_id}/login"

    async def command_start(self, telegram_id: int):

        async with aiohttp.ClientSession() as session:
            url = self.start_route.format(telegram_id=telegram_id)

            async with session.get(url) as resp:
                result = (await resp.json())["payload"]["vk_token"]
                return result

    async def command_login(self, telegram_id: int):

        async with aiohttp.ClientSession() as session:
            url = self.get_vk_token.format(telegram_id=telegram_id)

            async with session.get(url) as resp:
                result = (await resp.json())["payload"]["vk_token"]
                return result
