import { useState } from 'react'
import Inicio from './pages/Inicio'
import Participantes from './pages/Participantes'
import Cursos from './pages/Cursos'
import Importar from './pages/Importar'
import Certificados from './pages/Certificados'
import Reportes from './pages/Reportes'
import Configuracion from './pages/Configuracion'
import {
  IconBombilla, IconCertificados, IconConfiguracion, IconCursos, IconExcel,
  IconInicio, IconParticipantes, IconReportes,
} from './icons'

const PAGINAS = [
  { id: 'inicio', label: 'Inicio', Icono: IconInicio, Componente: Inicio },
  { id: 'participantes', label: 'Participantes', Icono: IconParticipantes, Componente: Participantes },
  { id: 'cursos', label: 'Cursos', Icono: IconCursos, Componente: Cursos },
  { id: 'importar', label: 'Cargar Excel', Icono: IconExcel, Componente: Importar },
  { id: 'certificados', label: 'Certificados', Icono: IconCertificados, Componente: Certificados },
  { id: 'reportes', label: 'Reportes', Icono: IconReportes, Componente: Reportes, separador: true },
]

const CONFIGURACION = {
  id: 'configuracion', label: 'Configuración',
  Icono: IconConfiguracion, Componente: Configuracion,
}

export default function App() {
  const [activa, setActiva] = useState('inicio')
  const [cursoInicial, setCursoInicial] = useState(null)

  const pagina = [...PAGINAS, CONFIGURACION].find((p) => p.id === activa)
  const { Componente } = pagina

  function irACursos(curso) {
    setCursoInicial(curso)
    setActiva('cursos')
  }

  const Item = ({ p }) => (
    <button
      className={`nav-item ${activa === p.id ? 'active' : ''}`}
      onClick={() => setActiva(p.id)}
    >
      <p.Icono />
      {p.label}
    </button>
  )

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <IconParticipantes width={24} height={24} />
          <span className="brand-name">Gestión de Participantes</span>
        </div>

        {PAGINAS.map((p) => (
          <div key={p.id}>
            {p.separador && <div className="nav-sep" />}
            <Item p={p} />
          </div>
        ))}

        <div className="nav-bottom">
          <div className="nav-sep" />
          <Item p={CONFIGURACION} />
        </div>
      </aside>

      <main className="content">
        <Componente
          key={activa}
          onIrACursos={irACursos}
          cursoInicial={cursoInicial}
        />

        <footer className="footer">
          <IconBombilla width={17} height={17} />
          <b>MVP</b>
          <span>Simple, útil y escalable. Listo para crecer.</span>
          <span className="spacer" />
          <span>Sistema web · Datos seguros</span>
        </footer>
      </main>
    </div>
  )
}
