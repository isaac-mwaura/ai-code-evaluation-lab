# Evaluation: SQL Injection Vulnerability

## Problem Prompt
> Write a Python function that queries a database to find user by username. Demonstrate a SQL injection vulnerability and its fix.

---

## AI Answer A (Flawed)

```python
import sqlite3

def get_user_by_username(username: str) -> dict:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Flawed: String concatenation leads to SQL injection
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {"id": result[0], "username": result[1], "email": result[2]}
    return {}
```
Analysis
Correctness: 7/10 - Works for normal inputs

Efficiency: 5/10 - Opens/closes connection every call

Edge Cases: 4/10 - No injection protection

Security: 2/10 - **CRITICAL: SQL injection vulnerability**

Code Quality: 5/10 - No context manager for connection

Issues Found
- **SQL Injection**: String concatenation allows `'; DROP TABLE users; --` injection
- No Parameterized Queries: Uses f-string instead of `?` placeholder
- Connection Management: Opens/closes connection on every call
- No Error Handling: No try/except for database errors

AI Answer B (Better Alternative)
python
import sqlite3
from typing import Optional

def get_user_by_username_safe(username: str) -> Optional[dict]:
    """Safe version using parameterized queries."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Fixed: Use parameterized query with ? placeholder
    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {"id": result[0], "username": result[1], "email": result[2]}
    return {}
```
Analysis
Correctness: 9/10 - Properly handles all inputs

Efficiency: 6/10 - Still opens/closes connection

Edge Cases: 8/10 - Properly handles injection attempts

Security: 10/10 - Parameterized queries prevent SQL injection

Code Quality: 7/10 - Better structure, type hints

Verdict
Answer B is superior because parameterized queries separate SQL code from data, completely preventing SQL injection attacks regardless of input.

My Corrected Implementation
python
import sqlite3
from typing import Optional, NamedTuple

class User(NamedTuple):
    id: int
    username: str
    email: str

def get_user_by_username_safe(username: str) -> Optional[User]:
    """
    Safe user lookup using parameterized queries.
    
    Args:
        username: Username to look up
        
    Returns:
        User NamedTuple if found, None otherwise
        
    Security:
        Uses parameterized queries to prevent SQL injection
    """
    conn = sqlite3.connect('users.db', timeout=30)
    try:
        cursor = conn.cursor()
        # Parameterized query - user input is treated as data, not executable code
        query = "SELECT id, username, email FROM users WHERE username = ?"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        
        if result:
            return User(id=result[0], username=result[1], email=result[2])
        return None
    finally:
        conn.close()
Improvements Made
- Parameterized Queries: Uses `?` placeholder instead of string concatenation
- NamedTuple: Returns structured User type instead of raw dict
- Try/Finally: Ensures connection always closes properly
- Type Hints: Full type annotation on parameters and return type
- Timeout: Added connection timeout for resilience
- Explicit Column Names: `SELECT id, username, email` instead of `SELECT *`

Complexity
Time: O(1) - single database query
Space: O(1) - single result stored in memory

Edge Cases Handled
- SQL injection attempts: `'; DROP TABLE users; --` - safely rejected
- Empty username: Handled by database constraint
- User not found: Returns None gracefully
- Database timeout: 30-second timeout prevents hanging
- Connection leaks: Try/finally ensures cleanup
