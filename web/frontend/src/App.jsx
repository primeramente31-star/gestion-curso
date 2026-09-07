import { useState } from 'react'
import Panel from './pages/Panel'
import Participantes from './pages/Participantes'
import Cursos from './pages/Cursos'
import Importar from './pages/Importar'
import Certificados from './pages/Certificados'

const PAGINAS = [
  { id: 'panel', label: 'Panel', Componente: Panel },
  { id: 'participantes', label: 'Participantes', Componente: Participantes },
  { id: 'cursos', label: 'Cursos', Componente: Cursos },
  { id: 'importar', label: 'Importar Excel', Componente: Importar },
  { id: 'certificados', label: 'Certificados', Componente: Certificados },
]

export default function App() {
  const [activa, setActiva] = useState('panel')
  const { Componente } = PAGINAS.find((p) => p.id === activa)

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="logo">Gestión de Cursos</div>
        <div className="logo-sub">Control de participantes</div>
        {PAGINAS.map((p) => (
          <button
            key={p.id}
            className={`nav-item ${activa === p.id ? 'active' : ''}`}
            onClick={() => setActiva(p.id)}
          >
            {p.label}
          </button>
        ))}
      </aside>
      <main className="content">
        <Componente key={activa} />
      </main>
    </div>
  )
}
