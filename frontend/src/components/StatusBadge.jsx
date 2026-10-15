// components/StatusBadge.jsx
export default function StatusBadge({ status }) {
  return (
    <span className={`badge badge-${status}`}>
      {status}
    </span>
  );
}
