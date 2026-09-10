---
type: source-part
source_identity: artifact:delivery-revalidation-current-flow-and-cost
source_digest: sha256:41f3c1768351cd36b22fe60aa75bb7bc57eca257636628ea5202ed98fdd3c447
source_entry: wiki/sources/artifact-delivery-revalidation-current-flow-and-cost.md
---

# Preserved source — Part 2

Entry and provenance: [[sources/artifact-delivery-revalidation-current-flow-and-cost]]

<!-- semantic-payload-v1: {"part_index":1,"payload_bytes":2016,"payload_sha256":"705174ae3ed0f6ec9936dadbc72a02e2e2ed61b444a2793e2ecc3de811ae1f10","schema":1,"source_digest":"sha256:41f3c1768351cd36b22fe60aa75bb7bc57eca257636628ea5202ed98fdd3c447","source_identity":"artifact:delivery-revalidation-current-flow-and-cost"} -->
```markdown
## Durable Findings

1. Exact-final-tree verification is necessary; unconditional broad-suite duplication is not itself
   the invariant.
2. The current implementation safely treats any `I != D` drift as unclassified and resets every
   downstream leaf result.
3. A future narrow proof would need complete path/blob/mode/receipt/link/ledger and negative
   extra-diff evidence. “Ticket moved to done” is not a safe classifier.
4. Ignored-source, reconciliation, recovery, provider, terminal-proof, historical-ledger, wiki,
   and Pi boundaries require separate handling and authority even if the common tracked case is
   optimized.
5. Existing ledgers do not provide trustworthy wall time or OS-command counts; future comparison
   must instrument those values prospectively.

## Unresolved Proof Questions for DRV-02/DRV-03

- Can one contract prove a complete deterministic link-repoint set, including the absence of
  eligible missed links and unrelated edits?
- Which evidence segments can declare stable causal ownership without turning the proof verifier
  into an unsafe general test-selection oracle?
- How should crash checkpoints distinguish pre-projection, post-projection/pre-ledger, and
  post-commit/pre-provider states without rollback or history rewriting?
- Can tracked, ignored, reconciliation, and recovery topologies share one non-overlapping
  classifier, or must some always retain full revalidation?
- How are historical ledgers handled when they have no projection manifest, command timing, or
  causal evidence segmentation?
- What proof complexity and prospective wall-time reduction would justify replacing the current
  conservative transition?

## Non-Conclusion

No architecture (pre-quality projection, proof-carrying projection, or bounded hybrid), proof
schema, test-selection policy, compatibility rule, or optimization threshold is selected here.
The current full delivery-revalidation cycle remains mandatory until DRV-02 evidence and the
human DRV-03 decision are complete.

```
