/** A page header with a title, a lead paragraph and optional actions. */
export default function PageHeader({ title, lead, actions }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
      <div>
        <h1 className="m-0 text-2xl md:text-[28px]">{title}</h1>
        {lead && <p className="m-0 mt-2 max-w-3xl text-sm text-muted">{lead}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  )
}
