This issue stems from a fundamental mismatch between Django's synchronous ORM and the async nature of modern test runners. Below is a plan for a deep-dive investigation to identify the optimal solution.

### 🔬 Research Proposal: Resolving Async/Sync Mismatch in Django PDF Service Tests

#### 🎯 Core Issue
The PDF service uses `async` Django ORM calls, which cannot run directly in a synchronous test context. This prevents the test runner from initiating or managing the necessary event loop, causing the tests to fail.

#### 📝 Research Objectives
1.  **Pinpoint the exact origin of the mismatch.** Determine whether the PDF service itself, the test framework, or a missing bridge layer is the primary cause.
2.  **Benchmark all three potential solutions** for performance, maintainability, and correctness.
3.  **Select the optimal, production-grade fix** and create a reference implementation.

#### 🔍 Investigation Pathways
We will systematically evaluate each solution path by searching for and analyzing specific code patterns, best practices, and community discussions.

**Path 1: Making Tests Fully Asynchronous**
*   **Research Questions:**
    *   How to correctly configure `pytest-asyncio` for Django projects using Django Ninja's `TestAsyncClient`?
    *   What is the proper usage of `pytest.mark.django_db(transaction=True)` in async tests?
    *   How to handle async fixture management (e.g., `httpx.AsyncClient`)?
*   **Key Areas to Search:**
    *   "*Django Ninja TestAsyncClient example*" – to understand the client's async request lifecycle.
    *   "*pytest-asyncio Django db isolation fix*" – to prevent ORM data leakage between tests.
    *   "*Django AsyncClient authenticated requests*" – for testing endpoints requiring authentication.

**Path 2: Mocking the Asynchronous Database Calls**
*   **Research Questions:**
    *   What is the community-standard approach to mock the Django ORM in async contexts?
    *   Is `django-mock-queries` sufficient for mocking async `QuerySet` methods like `aget` and `acreate`?
    *   How to verify mocked interactions using `unittest.mock` when the target is an async service?
*   **Key Areas to Search:**
    *   "*django async ORM mock test*" – to find strategies for avoiding real database hits in async tests.
    *   "*python async mock django orm service*" – to see examples of patching async ORM calls at the service layer.
    *   "*django-mock-queries async support*" – to check the limits of mocking libraries.

**Path 3: Adding a Synchronous Wrapper Method**
*   **Research Questions:**
    *   Where and how should `asgiref.sync.sync_to_async` be integrated into the service to expose a synchronous interface for testing?
    *   Is implementing a formal "Sync/Async Facade" pattern the most maintainable approach?
    *   How does this pattern compare to Django's own `sync_to_async` helpers in terms of transaction safety?
*   **Key Areas to Search:**
    *   "*Django ORM sync_to_async in tests*" – to learn how to properly bridge synchronous tests with async ORM operations.
    *   "*Fix ORM leakage with sync_to_async*" – to handle database isolation when wrapping synchronous code in async contexts.
    *   "*django sync_to_async mock vs real db*" – to weigh the trade-offs of a wrapper facade against full mocking.

#### 📊 Comparative Analysis Framework
After gathering data, we will evaluate the solutions against these production-grade criteria:

| Criteria | Path 1: Async Tests | Path 2: Mock DB Calls | Path 3: Sync Wrapper |
| :--- | :--- | :--- | :--- |
| **Speed** | Fast (avoids IO, but requires event loop setup) | Fastest (no DB interaction) | Fast (sync execution) |
| **Complexity** | Higher: Requires careful event loop and transaction management | Moderate: Requires constructing accurate mock chains | Lower: Simple wrapper methods; leverages existing ORM skills |
| **Accuracy** | Highest: Executes real ORM code through async drivers | Low: Isolates tests from real ORM, might miss integration issues | High: Tests the full synchronous ORM integration path |
| **Maintenance** | Moderate: Config-dependent, can be brittle with Django updates | High: Mocks need constant updates with model changes | Low: Standard Django ORM patterns, resilient to changes |

#### 📈 Recommended Research Plan & Next Steps
Based on initial findings, the following steps will lead to the most robust solution:

1.  **Start with a Feasibility Test:** Attempt to wrap the failing test in `asgiref.sync.async_to_sync` and call the Django Ninja `TestAsyncClient` endpoint to verify the test runner can enter an async context.
2.  **Pursue "Path 3: Synchronous Wrapper" First.** This approach bridges the gap without fundamentally altering the test architecture. Create a method like `generate_pdf_sync(*args, **kwargs)` that internally calls `sync_to_async(generate_pdf)(*args, **kwargs)`. The critical step is database isolation; use `@pytest.mark.django_db(transaction=True)` to guarantee a clean state.
3.  **If Isomorphism is Required:** If the team insists on having the service's *public* API remain purely asynchronous, then adopt **Path 1**. Fully convert the test class to async, use Django Ninja’s `TestAsyncClient`, and apply patterns from Django's own test suite for async DB access.
4.  **Treat Mocking as a Last Resort (Path 2).** Relying on mocks risks creating tests that pass in isolation but fail due to un-mocked DB-level constraints. Employ this only for simple, isolated unit tests.

#### ⚠️ Key Pitfalls to Avoid
*   **SynchronousOnlyOperation Error:** Caused by calling the ORM directly inside an `async def` test. Always use `sync_to_async` wrappers or mock the calls.
*   **Database State Leakage:** Failing to use `pytest.mark.django_db(transaction=True)` or not performing proper cleanup can cause data contamination between test cases.
*   **Incorrect Async Client Setup:** Mixing synchronous `TestClient` with async views will bypass the ASGI handler and lead to false positives.
*   **Misconfigured `pytest-asyncio` Fixtures:** Incorrect event loop scoping or fixture definitions can cause `RuntimeError`. Use `loop_scope="module"` or `"session"` with care.

This investigative framework ensures a thorough, evidence-based selection of the optimal strategy, balancing execution speed with long-term maintainability.

