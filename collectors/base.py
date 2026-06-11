import asyncio
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
        Retries up to 3 times on 429 Rate Limit responses with exponential backoff.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        req_headers = self._get_headers()
        if headers:
            req_headers.update(headers)
            
        max_retries = 3
        backoff = 1.0
        
        for attempt in range(max_retries + 1):
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.get(url, params=params, headers=req_headers)
                    logger.info(f"API Request: {response.request.method} {response.url} - Status: {response.status_code}")
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429 and attempt < max_retries:
                        sleep_time = backoff * (2 ** attempt)
                        logger.warning(f"Rate limited (429) on {url}. Retrying in {sleep_time}s (attempt {attempt + 1}/{max_retries})...")
                        await asyncio.sleep(sleep_time)
                        continue
                    logger.error(f"HTTP Error for endpoint {endpoint}: {e.response.status_code} - {e.response.text}")
                    raise
                except httpx.RequestError as e:
                    logger.error(f"Network error accessing {url}: {str(e)}")
                    raise
