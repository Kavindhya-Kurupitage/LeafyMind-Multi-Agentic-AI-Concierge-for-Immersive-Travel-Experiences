import { resolveAgentLabel } from "../../utils/chatHelpers.js";

function AgentBadge({ agent }) {
  const { label, color } = resolveAgentLabel(agent || "");
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${color}`}
    >
      {label}
    </span>
  );
}

export default AgentBadge;
