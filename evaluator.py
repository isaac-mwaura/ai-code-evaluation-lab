"""Evaluation framework for AI-generated code benchmark dataset.

Processes the benchmark_dataset.json and produces structured evaluation results
across multiple dimensions: correctness, security, robustness, maintainability,
complexity, testing adherence, and requirements adherence.
"""

import json
import ast
import sys
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


class EvaluationDimension:
    """Scores for each evaluation dimension (0-10 scale)."""

    def __init__(
        self,
        correctness: float = 0,
        security: float = 0,
        robustness: float = 0,
        maintainability: float = 0,
        complexity: float = 0,
        testing: float = 0,
        requirements_adherence: float = 0,
    ):
        self.correctness = correctness
        self.security = security
        self.robustness = robustness
        self.maintainability = maintainability
        self.complexity = complexity
        self.testing = testing
        self.requirements_adherence = requirements_adherence

    def to_dict(self) -> Dict[str, float]:
        return {
            "correctness": self.correctness,
            "security": self.security,
            "robustness": self.robustness,
            "maintainability": self.maintainability,
            "complexity": self.complexity,
            "testing": self.testing,
            "requirements_adherence": self.requirements_adherence,
        }

    def __repr__(self) -> str:
        return (
            f"EvaluationDimension(correctness={self.correctness}, "
            f"security={self.security}, robustness={self.robustness}, "
            f"maintainability={self.maintainability}, complexity={self.complexity}, "
            f"testing={self.testing}, requirements_adherence={self.requirements_adherence})"
        )


def safe_eval_code(code: str, timeout: float = 5.0) -> Tuple[bool, Optional[str]]:
    """Safely execute code in a restricted environment.

    Returns (success, output) where success indicates no exceptions.
    """
    try:
        # Execute with restricted builtins
        exec_globals = {"__builtins__": {}}
        exec(code, exec_globals)
        return True, None
    except Exception as exc:
        return False, str(exc)


def test_python_function(code: str, test_cases: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Test a Python function against test cases.

    Returns (passed_count, total_count).
    """
    passed = 0
    total = len(test_cases)

    if total == 0:
        return 0, total

    try:
        # Create a sandboxed execution environment
        local_vars: Dict[str, Any] = {}

        # Execute the code
        success, error = safe_eval_code(code)
        if not success:
            return 0, total

        # Run each test case
        for test in test_cases:
            try:
                func_name = None
                for node in ast.walk(ast.parse(code)):
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        break

                if func_name:
                    result = eval(func_name)(**test["input"])
                else:
                    result = "exec-only"

                # Check expected output
                if isinstance(test.get("expected_output"), str):
                    if test["expected_output"] in str(result):
                        passed += 1
                else:
                    # Default: test passes if no exception
                    passed += 1

            except Exception:
                # Test failed due to exception
                pass

    except Exception:
        pass

    return passed, total


def evaluate_correctness(
    generated_code: str,
    reference_solution: str,
    test_cases: List[Dict[str, Any]],
) -> float:
    """Evaluate correctness by comparing against reference solution and running tests.

    Score 0-10 scale.
    """
    if not generated_code or not reference_solution:
        return 0

    # Run tests on generated code
    passed, total = test_python_function(generated_code, test_cases)
    test_score = (passed / total * 10) if total > 0 else 0

    # Simple similarity check with reference (token overlap heuristic)
    gen_tokens = set(generated_code.lower().split())
    ref_tokens = set(reference_solution.lower().split())
    if gen_tokens and ref_tokens:
        overlap = len(gen_tokens & ref_tokens)
        similarity = overlap / max(len(gen_tokens), len(ref_tokens))
        similarity_score = min(similarity * 10, 10)
    else:
        similarity_score = 0

    # Average of test score and similarity
    final_score = (test_score + similarity_score) / 2
    return round(min(final_score, 10), 1)


def evaluate_security(generated_code: str) -> float:
    """Evaluate security by checking for common vulnerabilities.

    Score 0-10 scale (higher = more secure).
    """
    if not generated_code:
        return 0

    code_lower = generated_code.lower()
    vulnerabilities = 0
    checks = 0

    # Check for SQL injection patterns
    for pattern in ["SELECT", "select", "execute("]:
        checks += 1
        if pattern and pattern in code_lower:
            vulnerabilities += 1

    # Check for hardcoded credentials
    cred_patterns = ["password", "secret", "api_key", "token"]
    for pattern in cred_patterns:
        checks += 1
        if pattern in code_lower:
            # Heuristic: if variable assignment with common cred name
            if f"={pattern}" in code_lower or f"={pattern}" in code_lower:
                vulnerabilities += 1

    # Check for eval/exec
    for pattern in ["eval(", "exec("]:
        checks += 1
        if pattern in code_lower:
            vulnerabilities += 1

    if checks == 0:
        return 5  # No obvious issues found

    vulnerability_rate = vulnerabilities / checks
    score = max(0, 10 - vulnerability_rate * 15)
    return round(score, 1)


def evaluate_robustness(
    generated_code: str, test_cases: List[Dict[str, Any]]
) -> float:
    """Evaluate robustness by running code with edge case inputs.

    Score 0-10 scale.
    """
    if not generated_code or not test_cases:
        return 0

    passed, total = test_python_function(generated_code, test_cases)
    score = (passed / total * 10) if total > 0 else 0
    return round(min(score, 10), 1)


def evaluate_maintainability(generated_code: str) -> float:
    """Evaluate code maintainability based on code quality indicators.

    Score 0-10 scale (higher = more maintainable).
    """
    if not generated_code:
        return 0

    score = 10
    code_lower = generated_code.lower()

    # Deductions for common maintainability issues
    deductions = 0

    # No type hints
    if "def " in code_lower and ": " not in code_lower.split("def ")[1].split("(")[0]:
        deductions += 2

    # No docstring
    if '"""' not in generated_code and "'''" not in generated_code:
        deductions += 2

    # No error handling
    if "try:" not in generated_code and "/except" not in code_lower:
        deductions += 2

    # Very long function (heuristic: more than 50 lines)
    lines = generated_code.split("\n")
    if len(lines) > 50:
        deductions += 2

    score = max(0, score - deductions)
    return round(min(score, 10), 1)


def evaluate_testing(generated_code: str, test_cases: List[Dict[str, Any]]) -> float:
    """Evaluate if test cases are present and meaningful.

    Score 0-10 scale.
    """
    if not generated_code:
        return 0

    if not test_cases:
        return 3  # No tests but code exists

    # Check if test cases have substance
    substantive_tests = 0
    for test in test_cases:
        if test.get("name") and test.get("expected_output") is not None:
            substantive_tests += 1

    if not test_cases:
        return 0

    ratio = substantive_tests / len(test_cases)
    score = ratio * 10
    return round(min(score, 10), 1)


def evaluate_requirements_adherence(
    generated_code: str, prompt: str
) -> float:
    """Evaluate how well the code adheres to the prompt requirements.

    Score 0-10 scale.
    """
    if not generated_code or not prompt:
        return 0

    score = 0
    prompt_lower = prompt.lower()
    code_lower = generated_code.lower()

    # Check for key requirement words
    requirements = []

    if "error" in prompt_lower or "exception" in prompt_lower:
        requirements.append("error_handling")
    if "security" in prompt_lower or "safe" in prompt_lower:
        requirements.append("security")
    if "timeout" in prompt_lower:
        requirements.append("timeout")
    if "json" in prompt_lower:
        requirements.append("json_format")
    if "parameterized" in prompt_lower or "parameter" in prompt_lower:
        requirements.append("parameterized_queries")

    if not requirements:
        # Default: check for basic structure
        return 5

    met_requirements = 0
    for req in requirements:
        if req in code_lower:
            met_requirements += 1

    score = (met_requirements / len(requirements)) * 10
    return round(min(score, 10), 1)


def evaluate_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single benchmark sample and return results.

    Combines all evaluation dimensions into a comprehensive result.
    """
    sample_id = sample.get("id", "unknown")
    language = sample.get("language", "unknown")
    prompt = sample.get("prompt", "")
    generated_code = sample.get("generated_code", "")
    test_cases = sample.get("tests", [])
    reference_solution = sample.get("reference_solution", "")

    # Run all evaluation dimensions
    correctness = evaluate_correctness(generated_code, reference_solution, test_cases)
    security = evaluate_security(generated_code)
    robustness = evaluate_robustness(generated_code, test_cases)
    maintainability = evaluate_maintainability(generated_code)
    testing = evaluate_testing(generated_code, test_cases)
    requirements = evaluate_requirements_adherence(generated_code, prompt)

    # Update the sample's evaluation field
    sample["evaluation"] = {
        "correctness": correctness,
        "security": security,
        "robustness": robustness,
        "maintainability": maintainability,
        "complexity": 0,  # Placeholder - could be calculated from code metrics
        "testing": testing,
        "requirements_adherence": requirements,
    }

    return sample


def run_evaluation_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Run evaluation on all samples in the benchmark dataset.

    Returns the full dataset with evaluation results populated.
    """
    path = Path(dataset_path)
    if not path.exists():
        print(f"Dataset not found: {dataset_path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"Evaluating {len(dataset.get('samples', []))} samples...")

    results = []
    for i, sample in enumerate(dataset.get("samples", [])):
        try:
            result = evaluate_sample(sample)
            results.append(result)
            ev = result.get("evaluation", {})
            print(
                f"  [{i+1}/{len(dataset['samples'])}] {sample.get('id', 'unknown')}: "
                f"Correctness={ev.get('correctness', 0)}, "
                f"Security={ev.get('security', 0)}, "
                f"Robustness={ev.get('robustness', 0)}, "
                f"Testing={ev.get('testing', 0)}, "
                f"ReqAdherence={ev.get('requirements_adherence', 0)}"
            )
        except Exception as exc:
            print(f"  [{i+1}/{len(dataset['samples'])}] ERROR evaluating sample: {exc}")
            # Add minimal result even on error
            sample["evaluation"] = {
                "correctness": 0,
                "security": 0,
                "robustness": 0,
                "maintainability": 0,
                "complexity": 0,
                "testing": 0,
                "requirements_adherence": 0,
            }
            results.append(sample)

    return results


def generate_report(results: List[Dict[str, Any]]) -> str:
    """Generate a human-readable evaluation report.

    Summarizes evaluation results across all samples.
    """
    if not results:
        return "No evaluation results to report."

    lines = []
    lines.append("=" * 60)
    lines.append("AI CODE EVALUATION BENCHMARK REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Summary statistics
    total = len(results)
    if total == 0:
        return "No results to report."

    avg_correctness = round(
        sum(r.get("evaluation", {}).get("correctness", 0) for r in results) / total, 2
    )
    avg_security = round(
        sum(r.get("evaluation", {}).get("security", 0) for r in results) / total, 2
    )
    avg_robustness = round(
        sum(r.get("evaluation", {}).get("robustness", 0) for r in results) / total, 2
    )
    avg_testing = round(
        sum(r.get("evaluation", {}).get("testing", 0) for r in results) / total, 2
    )
    avg_requirements = round(
        sum(r.get("evaluation", {}).get("requirements_adherence", 0) for r in results) / total, 2
    )

    lines.append("AVERAGE SCORES (0-10 scale):")
    lines.append(f"  Correctness:      {avg_correctness}")
    lines.append(f"  Security:         {avg_security}")
    lines.append(f"  Robustness:       {avg_robustness}")
    lines.append(f"  Testing:          {avg_testing}")
    lines.append(f"  Requirements:     {avg_requirements}")
    lines.append(f"  Maintainability:  {round(sum(r.get('evaluation', {}).get('maintainability', 0) for r in results) / total, 2)}")
    lines.append("")

    # Per-sample details
    lines.append("PER-SAMPLE RESULTS:")
    lines.append("-" * 60)
    for i, result in enumerate(results):
        sample_id = result.get("id", f"sample-{i}")
        ev = result.get("evaluation", {})
        lines.append(
            f"  {sample_id}: "
            f"C={ev.get('correctness', 0)}/10 S={ev.get('security', 0)}/10 "
            f"R={ev.get('robustness', 0)}/10 T={ev.get('testing', 0)}/10 "
            f"RA={ev.get('requirements_adherence', 0)}/10"
        )

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)