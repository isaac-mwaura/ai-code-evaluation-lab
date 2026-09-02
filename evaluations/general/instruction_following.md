# Evaluation: Instruction Following Deviation

## Problem Prompt
> Write a Python function that takes a list of numbers and returns a new list containing only the even numbers, sorted in ascending order. Output must be formatted as JSON.

---

## AI Answer A (Flawed)

```python
def get_sorted_evens(numbers):
    evens = []
    for num in numbers:
        if num % 2 == 0:
            evens.append(num)
    evens.sort()
    # Flawed: Returns raw list, not JSON as requested
    return evens
```
Analysis
Correctness: 7/10 - Correctly filters and sorts evens

Efficiency: 6/10 - O(n log n) sorting is optimal

Edge Cases: 6/10 - No handling of non-numeric types

Security: 8/10 - No security issues

Code Quality: 6/10 - Missing output format specification

Issues Found
- **Output Format**: Returns list instead of JSON as explicitly requested
- **Type Safety**: No validation that inputs are numbers
- **Missing Requirement**: Ignored "sorted in ascending order" in return format
- **No JSON Conversion**: Caller must remember to json.dumps()

AI Answer B (Better Alternative)
python
def get_sorted_evens(numbers):
    """Fixed: Filters evens and sorts, returns JSON."""
    evens = [num for num in numbers if isinstance(num, (int, float)) and num % 2 == 0]
    evens.sort()
    import json
    return json.dumps(evens)
```
Analysis
Correctness: 8/10 - Added type checking for input

Efficiency: 6/10 - Same O(n log n) complexity

Edge Cases: 7/10 - Type checking handles non-numeric values

Security: 8/10 - Same profile

Code Quality: 7/10 - Implements requested output format

Verdict
Answer B is superior because it follows the instruction to return JSON format, making the output immediately usable without additional conversion.

My Corrected Implementation
python
from typing import List, Union
import json

def get_sorted_evens(numbers: List[Union[int, float]]) -> str:
    """
    Return even numbers from list, sorted ascending, as JSON.
    
    Args:
        numbers: List of integers or floats
        
    Returns:
        JSON string of even numbers sorted in ascending order
        
    Raises:
        TypeError: If input contains non-numeric types
        
    Example:
        >>> get_sorted_evens([5, 2, 8, 1, 9, 4])
        '[2, 4, 8]'
    """
    if not all(isinstance(n, (int, float)) for n in numbers):
        raise TypeError("All elements must be numeric")
    
    evens = [n for n in numbers if n % 2 == 0]
    evens.sort()
    
    return json.dumps(evens)
Improvements Made
- JSON Output: Returns `json.dumps(evens)` as explicitly requested
- Type Hints: Full type annotation on parameters and return type
- Type Validation: Checks all elements are numeric before processing
- TypeError: Raises explicit error for non-numeric inputs
- Docstring: Full explanation with example
- Type Annotation: `List[Union[int, float]]` and `-> str` for clarity

Complexity
Time: O(n log n) - filter O(n) + sort O(n log n)
Space: O(n) - new list of even numbers

Edge Cases Handled
- Non-numeric input: Raises TypeError instead of silent failure
- Empty list: Returns `[]` (valid JSON)
- No even numbers: Returns `[]` (valid JSON)
- Mixed int/float: Both handled correctly
- JSON readiness: Output immediately parseable with json.loads()
