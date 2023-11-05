import asyncio
import aiohttp 
import difflib




class MyAL(object):
    def __init__(self) -> None:
        self.headers = {'X-MAL-CLIENT-ID':'f731c36bf51aad39aadccdce3e0b5464'}
        self.baseUrl = 'https://api.myanimelist.net/v2/anime'


    async def asyncRequest(self,method,uri):
        async with aiohttp.ClientSession() as session:
            async with session.request(method,self.baseUrl+uri,headers=self.headers) as resp:
                await resp.read()
                return resp
        

    async def check_similarity(str1:str, str2:str):
        seq_matcher = difflib.SequenceMatcher(None, str1.lower(), str2.lower())
        similarity_ratio = seq_matcher.ratio()
        return similarity_ratio


    async def __sort_results(self,query,results):
        animeRatios = []
        for anime in results['data']:
            # get their similar accuracy first
            rawInfo = anime['node']
            ratio = self.check_similarity(rawInfo['title'].lower(),query.lower())
            animeInfo  = {'ratio':ratio,'id':rawInfo['id'],'title':rawInfo['title']}
            animeRatios.append(animeInfo)

        for anime in animeRatios:
            pass




    async def search_anime(self,anime:str):
        uri = f'?q={anime}'
        resp = await self.asyncRequest('get',uri)
        return resp
    



    async def get_anime_info(self,animeId:int):
        uri = f"{animeId}"
        resp = await self.asyncRequest('get',uri)
        return resp



    async def get_anime_field(self,animeId,field):
        uri = f"{animeId}?fields={field}"
        resp = await self.asyncRequest('get',uri)
        return resp
    



client = MyAL()

async def test():
    resp= await client.search_anime("one punch man")
    animeId = (await resp.json())['data']
    print(animeId
    )


# asyncio.run(test())