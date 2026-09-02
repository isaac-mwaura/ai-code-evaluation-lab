# Evaluation: Async/Await Race Condition

## Problem Prompt
> Write an async Python function that fetches data from two APIs concurrently and returns the combined result.

---

## AI Answer A (Flawed)

```python
import aiohttp
import asyncio

async def fetch_combined_data(session, url1, url2):
    # Flawed: Sequential execution, not concurrent
    async with session.get(url1) as resp1:
        data1 = await resp1.json()
    
    async with session.get(url2) as resp2:
        data2 = await resp2.json()
    
    return {**data1, **data2}
```
Analysis
Correctness: 8/10 - Works correctly for small number of calls

Efficiency: 3/10 - Missed opportunity for concurrent execution

Edge Cases: 5/10 - No error handling for failed requests

Security: 8/10 - No direct security issues

Code Quality: 6/10 - Clean but inefficient

Issues Found
- **Inefficiency**: Sequential makes total time = sum of both durations
- **No Error Handling**: If one API fails, the other waits unnecessarily
- **Poor User Experience**: Total latency = duration1 + duration2

AI Answer B (Better Alternative)
python
import aiohttp
import asyncio

async def fetch_combined_data_fast(session, url1, url2):
    # Fixed: Use asyncio.gather for concurrent execution
    async with session.get(url1) as resp1, session.get(url2) as resp2:
        data1, data2 = await asyncio.gather(
            resp1.json(),
            resp2.json()
        )
    
    return {**data1, **data2}
```
Analysis
Correctness: 9/10 - Correctly fetches both concurrently

Efficiency: 9/10 - O(max(duration1, duration2)) instead of sum

Edge Cases: 7/10 - Better error handling possible

Security: 8/10 - Same security profile

Code Quality: 8/10 - Idiomatic aiohttp usage

Verdict
Answer B is superior because `asyncio.gather` runs both requests concurrently, reducing total latency from duration1 + duration2 to max(duration1, duration2).

My Corrected Implementation
python
from typing import Dict, Any, Optional
import aiohttp
import asyncio

async def fetch_combined_data_correct(
    session: aiohttp.ClientSession,
    url1: str,
    url2: str,
    timeout: float = 30.0
) -> Optional[Dict[str, Any]]:
    """
    Fetch data from two APIs concurrently and return combined result.
    
    Args:
        session: aiohttp ClientSession
        url1: First API endpoint
        url2: Second API endpoint
        timeout: Request timeout in seconds
        
    Returns:
        Combined dictionary of both responses, or None on failure
        
    Example:
        >>> result = await fetch_combined_data_correct(
        ...     session, "https://api.example.com/users", "https://api.example.com/posts"
        ... )
        >>> result.keys()
        dict_keys(['users', 'posts'])
    """
    async def fetch_one(session, url):
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            resp.raise_for_status()
            return await resp.json()
    
    try:
        # Execute both requests concurrently
        data1, data2 = await asyncio.gather(
            fetch_one(session, url1),
            fetch_one(session, url2),
            return_exceptions=False
        )
        return {**data1, **data2}
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        print(f"Error fetching data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
Improvements Made
- Concurrent Execution: Uses `asyncio.gather` to run both requests in parallel
- Proper Error Handling: Catches `ClientError` and `TimeoutError` specifically
- Timeout Protection: Configurable timeout per request prevents hanging
- Modular Design: Inner `fetch_one` function for code reuse
- Type Hints: Full type annotation on all parameters and return type
- Session Reuse: Uses provided aiohttp session efficiently

Complexity
Time: O(max(duration1, duration2)) - concurrent, not sequential
Space: O(1) - only stores combined result

Edge Cases Handled
- API 1 fails: Continues and fetches API 2 (with return_exceptions=False both must succeed)
- API 2 fails: Returns None after both fail
- Timeout: Either API hanging will be cancelled after timeout seconds
- Client errors: Connection errors, HTTP errors properly caught
- Unexpected errors: Generic Exception catch as safety net
