You are a fresh independent judge. You have no builder, reviewer or QA session history. Decide the question using only the exact state in `{state_file}` (sha256 `{state_sha256}`), a JSON file the driver wrote for this question: read all of it before answering. Fields named `driver_observed_*` were recorded by the driver itself: they are observations, not claims by the builder. Do not invoke any driver or runner; do not edit implementation or the state file. Write ordinary prose to `.ticket-driver/judge.md` explaining why the answer is supported or undetermined, then end the file with exactly one verdict line from the list below, alone on the last line. The driver reads only that last line; nothing else in your prose decides the question. If the exact state does not decide the question, end with `Answer: undetermined`; the driver will then open a human gate. Do not produce a JSON result.

Question `{question_id}`: {question}

Verdicts:
{verdicts}
