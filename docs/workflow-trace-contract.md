# Workflow and trace contract

The semantic source is JSON, never Mermaid.

A manifest declares workflow_id, content-poor nodes, and condition-labelled edges. Multiple distinct conditions may lead to the same destination. Events carry only timestamps, public IDs, event kinds, attempts, status, duration, route, parent node, and boolean checkpoint/human flags.

Organization describes who owns work. Workflow describes what can happen. Execution Trace records what happened in one run. Resources describe context, tokens, storage, API-equivalent value, and host telemetry.

The contract is observational. It defines no launch, retry, approval, resume, kill, submit, or deletion command.
