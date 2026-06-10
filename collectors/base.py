import httpx
from typing import Dict, Any, Optional
from utils.logger import logger

class BaseCollector:
    """
    Base class for external sport API collectors.
    Provides robust HTTP clients with configured timeouts and retry warnings.
    """
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        # Standard timeout for external connections
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    def _get_headers(self) -> Dict[str, str]:
        """Override in subclasses to supply authentications."""
        return {}

    async def _request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executes HTTP GET requests, returning json. Raises Exception on non-200.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        req_headers = self._get_headers()
        if headers:
            req_headers.update(headers)
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params, headers=req_headers)
                logger.info(f"API Request: {response.request.method} {response.url} - Status: {response.status_code}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Error for endpoint {endpoint}: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Network error accessing {url}: {str(e)}")
                raise
