// Componentes de presentación reutilizables.

export function Stat({ label, value }) {
  return (
    <div className="card stat">
      <div className="stat-value">{value ?? 0}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

export function Estado({ valor }) {
  const clase = valor === 'Faltó' ? 'Falto' : valor
  return <span className={`tag ${clase}`}>{valor}</span>
}

export function Alerta({ tipo = 'info', children, onClose }) {
  if (!children) return null
  return (
    <div className={`alert ${tipo}`}>
      <div className="row">
        <div style={{ flex: 1, whiteSpace: 'pre-wrap' }}>{children}</div>
        {onClose && <button className="link" onClick={onClose}>Cerrar</button>}
      </div>
    </div>
  )
}

export function Vacio({ children }) {
  return <div className="empty">{children}</div>
}

export function Modal({ titulo, subtitulo, onClose, children }) {
  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="row" style={{ marginBottom: 16 }}>
          <div style={{ flex: 1 }}>
            <h2>{titulo}</h2>
            {subtitulo && <div className="page-sub" style={{ margin: 0 }}>{subtitulo}</div>}
          </div>
          <button className="ghost" onClick={onClose}>Cerrar</button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function PageHeader({ titulo, subtitulo }) {
  return (
    <>
      <h1 className="page-title">{titulo}</h1>
      <p className="page-sub">{subtitulo}</p>
    </>
  )
}
