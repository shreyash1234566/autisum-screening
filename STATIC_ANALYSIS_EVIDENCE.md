# Static Analysis Evidence

This document records the exact commands executed and the outputs obtained from the python linter (`ruff`) and static security scanner (`bandit`) at timestamp: 2026-06-10T20:03:00Z.

---

## 1. Ruff Static Formatting & Import Check

Ruff verifies PEP-8 compliance, import ordering, unused variables, and styling.

### Command:
```bash
ruff check backend
```

### Output:
```text
All checks passed!
```

---

## 2. Bandit Static Security Audit

Bandit inspects python files for common vulnerability patterns (such as raw command execution, unsafe deserialization, or hardcoded credentials).

### Command:
```bash
bandit -r backend
```

### Output:
```text
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.13.1
Run started:2026-06-10 14:32:53.602798+00:00

Test results:
>> Issue: [B404:blacklist] Consider possible security implications associated with the subprocess module.
   Severity: Low   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_imports.html#b404-import-subprocess
   Location: backend\services\asdmotion_service.py:12:0
11	import os
12	import subprocess
13	from typing import Optional

--------------------------------------------------
>> Issue: [B607:start_process_with_partial_path] Starting a process with a partial executable path
   Severity: Low   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b607_start_process_with_partial_path.html
   Location: backend\services\asdmotion_service.py:41:17
40	    try:
41	        result = subprocess.run(
42	            ["python", ASDMOTION_SCRIPT,
43	             "--video", video_path,
44	             "--output", "json"],
45	            capture_output=True, text=True, timeout=600
46	        )
47	        if result.returncode != 0:

--------------------------------------------------
>> Issue: [B603:subprocess_without_shell_equals_true] subprocess call - check for execution of untrusted input.
   Severity: Low   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html
   Location: backend\services\asdmotion_service.py:41:17
40	    try:
41	        result = subprocess.run(
42	            ["python", ASDMOTION_SCRIPT,
43	             "--video", video_path,
44	             "--output", "json"],
45	            capture_output=True, text=True, timeout=600
46	        )
47	        if result.returncode != 0:

--------------------------------------------------
>> Issue: [B404:blacklist] Consider possible security implications associated with the subprocess module.
   Severity: Low   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_imports.html#b404-import-subprocess
   Location: backend\services\openface_service.py:20:0
19	import os
20	import subprocess
21	import tempfile

--------------------------------------------------
>> Issue: [B603:subprocess_without_shell_equals_true] subprocess call - check for execution of untrusted input.
   Severity: Low   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html
   Location: backend\services\openface_service.py:50:21
49	        try:
50	            result = subprocess.run(
51	                cmd, capture_output=True, text=True, timeout=300
52	            )
53	            if result.returncode != 0:

--------------------------------------------------

Code scanned:
	Total lines of code: 979
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 5
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 5
Files skipped (0):
```

---

## 3. Findings & Security Risk Reconciliation

All 5 Bandit issues are categorized as **Low Severity** and relate directly to the use of Python's standard `subprocess` module to execute external clinical pipeline binaries.

### Justifications & Risk Containment:
1. **Subprocess Usage (`B404`, `B603`):**
   * *Rationale:* The AutiScreen architecture relies on calling native OpenFace (`FeatureExtraction`) binaries and external Python script suites (`ASDMotion.py`) to process raw video feeds. There is no in-memory Python equivalent for these heavy computer-vision models.
   * *Containment:* We do **not** use `shell=True` in any subprocess execution. The parameter list is passed as an isolated array of strings, preventing command-injection payloads from modifying command bounds.
2. **Partial Path Executable (`B607`):**
   * *Rationale:* The ASDMotion script is run using the generic `"python"` command line token.
   * *Containment:* The scripts run inside a containerized runtime environment (Docker) where the python environment location is controlled and static. To prevent local environment path manipulations on generic hosts, production configurations can specify the absolute path to Python (`/usr/local/bin/python`).
