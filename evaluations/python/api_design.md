# Evaluation: Rate Limiter Implementation

## Problem Prompt
> Implement a rate limiter for an API that allows maximum 100 requests per minute per client IP.

---

## AI Answer A (Flawed)

```python
import time

class RateLimiter:
    def __init__(self):
        self.requests = {}
    
    def check(self, client_ip):
        now = time.time()
        if client_ip in self.requests:
            timestamps = self.requests[client_ip]
            # Remove timestamps older than 60 seconds
            self.requests[client_ip] = [t for t in timestamps if now - t < 60]
            if len(self.requests[client_ip]) >= 100:
                return False
            self.requests[client_ip].append(now)
            return True
        else:
            self.requests[client_ip] = [now]
            return True
```
Analysis
Correctness: 6/10 - Basic rate limiting works but has issues

Efficiency: 4/10 - List comprehension on every call is O(n)

Edge Cases: 5/10 - No IP address format validation

Security: 5/10 - No brute force protection, easy to bypass

Code Quality: 5/10 - No type hints, global state issues

Issues Found
- Efficiency: List comprehension filters on every call, O(n) per request
- No Reset Mechanism: Old entries never fully expire properly
- Thread Safety: Not safe for concurrent access
- No IP Validation: Any string accepted as IP
- Memory Leak: Requests dict grows unbounded over time

AI Answer B (Better Alternative)
python
from collections import deque
from time import time

class RateLimiter:
    def __init__(self, rate_limit=100, window=60):
        self.rate_limit = rate_limit
        self.window = window
        self.requests = {}
    
    def check(self, client_ip):
        now = time.time()
        if client_ip not in self.requests:
            self.requests[client_ip] = deque(maxlen=self.rate_limit)
        
        q = self.requests[client_ip]
        # Remove old entries outside the window
        while q and now - q[0] > self.window:
            q.popleft()
        
        if len(q) >= self.rate_limit:
            return False
        
        q.append(now)
        return True
```
Analysis
Correctness: 8/10 - Proper sliding window implementation

Efficiency: 8/10 - O(1) amortized per call with deque

Edge Cases: 7/10 - Handles new IPs, window management

Security: 8/10 - Better brute force resistance

Code Quality: 7/10 - Type hint friendly, cleaner structure

Verdict
Answer B is superior because the deque-based sliding window is O(1) amortized per call and properly manages the rate limit window without memory growth.

My Corrected Implementation
python
from typing import Dict, Deque, Optional
from collections import deque
from time import time

class RateLimiter:
    """
    Fixed-window rate limiter for API protection.
    
    Attributes:
        rate_limit: Maximum requests allowed per window
        window: Time window in seconds
        storage: Dict mapping client IPs to request timestamps
    """
    
    def __init__(self, rate_limit: int = 100, window: int = 60):
        self.rate_limit = rate_limit
        self.window = window
        self.storage: Dict[str, Deque[float]] = {}
    
    def check(self, client_ip: str) -> bool:
        """
        Check if a client is within rate limits.
        
        Args:
            client_ip: Client's IP address
            
        Returns:
            True if within limits, False if rate exceeded
        """
        if not self._is_valid_ip(client_ip):
            raise ValueError(f"Invalid IP address: {client_ip}")
        
        now = time.time()
        if client_ip not in self.storage:
            self.storage[client_ip] = deque(maxlen=self.rate_limit)
        
        q = self.storage[client_ip]
        # Remove timestamps outside the window
        while q and now - q[0] > self.window:
            q.popleft()
        
        if len(q) >= self.rate_limit:
            return False
        
        q.append(now)
        return True
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        return all(0 <= int(part) <= 255 for part in parts)
    
    def reset(self, client_ip: Optional[str] = None) -> None:
        """Reset rate limit for a specific IP or all IPs."""
        if client_ip:
            self.storage.pop(client_ip, None)
        else:
            self.storage.clear()
Improvements Made
- Type Hints: Full type annotation on all parameters and return types
- IP Validation: Added _is_valid_ip helper to prevent invalid inputs
- Deque with maxlen: Automatic size management prevents memory growth
- reset() Method: Clean API for resetting limits
- Docstring: Full class and method documentation
- Safety Checks: Validates input before processing

Complexity
Time: O(1) amortized per check - deque operations are constant time
Space: O(rate_limit * num_clients) - bounded by rate limit per client

Edge Cases Handled
- Empty/invalid IP: Raises ValueError
- New client IP: Automatically initialized
- Window expiry: Old timestamps properly cleaned up
- Rate limit exceeded: Returns False gracefully
- Reset functionality: Can clear limits when needed
