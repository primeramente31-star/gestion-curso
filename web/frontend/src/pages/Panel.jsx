import { useEffect, useState } from 'react'
import { api } from '../api'
import { PageHeader, Stat, Vacio } from '../components'

export default function Panel() {
  const [datos, setDatos] = useState(null)

  useEffect(() => { api.dashboard().then(setDatos).catch(() => setDatos(null)) }, [])

  if (!datos) return <Vacio>Cargando…</Vacio>

  return (
    <>
      <PageHeader titulo="Panel general" subtitulo="Resumen de la actividad formativa" />
      <div className="stats">
        <Stat label="Participantes" value={datos.participantes} />
        <Stat label="Cursos" value={datos.cursos} />
        <Stat label="Cursos activos" value={datos.cursos_activos} />
        <Stat label="Aprobados" value={datos.aprobados} />
        <Stat label="Faltas" value={datos.faltas} />
        <Stat label="Certificados" value={datos.certificados} />
      </div>

      <div className="card">
        <b>Cursos y su desempeño</b>
        <table style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>Curso</th><th>Código</th><th>Participantes</th>
              <th>Aprobados</th><th>Faltas</th><th>% Aprobación</th><th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {datos.cursos_detalle.map((c) => (
              <tr key={c.id}>
                <td>{c.nombre}</td>
                <td>{c.codigo || '—'}</td>
                <td>{c.total_participantes}</td>
                <td>{c.total_aprobados}</td>
                <td>{c.total_faltas}</td>
                <td>{c.porcentaje_aprobacion}%</td>
                <td><span className={`tag ${c.activo ? 'activo' : 'inactivo'}`}>
                  {c.activo ? 'Activo' : 'Inactivo'}</span></td>
              </tr>
            ))}
            {datos.cursos_detalle.length === 0 && (
              <tr><td colSpan={7} className="muted">
                Aún no hay cursos. Importa un archivo Excel para comenzar.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  )
}
