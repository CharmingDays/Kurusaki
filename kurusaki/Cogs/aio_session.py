import typing
import aiohttp


class AioSessionBase(object):
    def __init__(self) -> None:
        self.session = aiohttp.ClientSession()
    


    async def __aenter__(self):
        return self
    
    async def __aexit__(self,exc_type,exc_val,exc_tb):
        if not self.session.closed:
            await self.session.close()
        self.session = None


    async def close_session(self)->None:
        if not self.session.closed:
            await self.session.close()
        self.session = None


    async def request(self,method:str,url:str,**kwargs) -> aiohttp.ClientResponse:
        should_read = kwargs.pop("should_read",False)
        async with self.session.request(method,url,**kwargs) as response:
            if should_read:
                await response.read()
            return response
        



class aioSessionHandler(object):
    def __init__(self):
        self.all_sessions:typing.Dict[int,AioSessionBase] = {}
        self.current_session:AioSessionBase = AioSessionBase()
        self.all_sessions.update({id(self.current_session):self.current_session})

    async def __aenter__(self):
        return self
    

    async def __aexit__(self,exc_type,exc_val,exc_tb):
        await self.close_all_sessions()


    async def request(self,method:str,url:str,**kwargs) -> aiohttp.ClientResponse:
        return await self.current_session.request(method,url,**kwargs)
    

    async def create_session(self,counts:int=1) -> None:
        for _ in range(counts):
            session = AioSessionBase()
            self.all_sessions.update({id(session):session})


    async def update_cookies(self,cookies:aiohttp.CookieJar,base_session:AioSessionBase=None) -> None:
        if base_session is None:
            base_session:AioSessionBase = self.current_session
        base_session.session.cookie_jar.update_cookies(cookies)
        


    async def clone_sessions(self,counts:int=1) -> None:
        """Clones the current session's cookies, headers to new session objects

        Args:
            counts (int, optional): The number of aioSessionBase to create. Defaults to 1.
        """
        for _ in range(counts):
            base_session = AioSessionBase()
            base_session.session.headers.update(self.current_session.headers)
            base_session.session.cookie_jar.update_cookies(self.current_session.cookie_jar)
            self.all_sessions.update({id(base_session):base_session})

    async def close_session(self,object_id:int) -> None:
        """Close a session object with given ID

        Args:
            object_id (int): the id of the session object to close

        Raises:
            KeyError: ID not found in the session object dict
        """
        session:AioSessionBase = self.all_sessions.pop(object_id,None)
        if session:
            await session.close_session()
        else:
            raise KeyError("Session object with given ID not found",object_id)
        
    async def close_extra_sessions(self):
        """Closes all session objects except the current session object
        """
        current_id = id(self.current_session)
        keys = self.all_sessions.keys()
        for key in keys:
            if current_id == key:
                # Skip the current session
                continue
            else:
                await self.all_sessions[key].close_session()
                del self.all_sessions[id]

    async def switch_session(self,object_id:int) -> None:
        """Switch to a session object with given ID

        Args:
            object_id (int): the id of the session object to switch to

        Raises:
            KeyError: ID not found in the session object dict
        """
        session = self.all_sessions.get(object_id,None)
        if session:
            self.current_session = session
        else:
            raise KeyError("Session object with given ID not found",object_id)
        

    async def switch_to_default_session(self) -> None:
        """
        Switch to the default session object.
        The default session object is the first session object created
        """
        self.current_session = self.all_sessions.values()[0]
    

    async def close_all_sessions(self) -> None:
        """
        Close all session objects
        """
        for session in self.all_sessions.copy().values():
            await session.close_session()
        self.all_sessions.clear()
        self.current_session = None

    async def close_current_session(self) -> None:
        """
        Close the current session object and switches it to the next available
        session object in the dict
        """
        current_session:AioSessionBase = self.all_sessions.pop(id(self.current_session),None)
        await current_session.close_session()
        new_session:AioSessionBase = self.all_sessions.values()[0]
        self.current_session:AioSessionBase = new_session

    async def split_request(self,request_options:typing.List[typing.Dict]) -> aiohttp.ClientResponse:
        """
        Splits the request into multiple requests and returns the response of the last request

        Args:
            options (typing.List[typing.Dict]): The list of request options to split passed as a dict object per request

        Returns:
            aiohttp.ClientResponse: The responses of all the requests
        """
        index = 0
        index_cap = len(self.all_sessions)
        all_sessions:typing.List[AioSessionBase] = list(self.all_sessions.values())
        responses:typing.List[aiohttp.ClientResponse] = []
        while request_options.copy():
            args = request_options.pop(0)
            rsp = await all_sessions[index].request(**args)
            responses.append(rsp)
            index += 1
            if index == index_cap:
                index = 0
        
        return responses
