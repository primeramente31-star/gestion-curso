import { useEffect, useState } from 'react'
import { api } from '../api'
import { Estado, PageHeader, Vacio } from '../components'
import { IconBuscar } from '../icons'

export default function Reportes() {
  const [datos, setDatos] = useState(null)
  const [inscripciones, setInscripciones] = useState([])
  const [busqueda, setBusqueda] = useState('')
  const [estado, setEstado] = useState('')

  useEffect(() => { api.dashboard().then(setDatos) }, [])

  useEffect(() => {
    const t = setTimeout(async () => {
      const p = new URLSearchParams({ page_size: '200' })
      if (busqueda) p.set('search', busqueda)
      if (estado) p.set('estado', estado)
      const d = await api.inscripciones(p.toString())
      setInscripciones(d.results || d)
    }, 250)
    return () => clearTimeout(t)
  }, [busqueda, estado])

  function exportarCSV() {
    const filas = [['Participante', 'DNI', 'Curso', 'Estado', 'Nota', 'Asistencia', 'Certificados']]
    inscripciones.forEach((i) => filas.push([
      i.participante_nombre, i.dni || '', i.curso_nombre, i.estado,
      i.nota ?? '', i.asistencia ?? '', i.total_certificados || 0,
    ]))
    const csv = filas.map((f) => f.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(';')).join('\n')
    const url = URL.createObjectURL(new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' }))
    const a = document.createElement('a')
    a.href = url
    a.download = 'reporte-inscripciones.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <PageHeader titulo="Reportes"
        subtitulo="Consulta global de inscripciones, resultados y certificados" />

      {datos && (
        <div className="stats">
          <div className="stat blue">
            <div className="stat-head">Inscripciones</div>
            <div className="stat-value">{datos.inscripciones}</div>
            <div className="stat-label">registradas</div>
          </div>
          <div className="stat green">
            <div className="stat-head">Aprobados</div>
            <div className="stat-value">{datos.aprobados}</div>
            <div className="stat-label">participantes</div>
          </div>
          <div className="stat amber">
            <div className="stat-head">Faltas</div>
            <div className="stat-value">{datos.faltas}</div>
            <div className="stat-label">registradas</div>
          </div>
          <div className="stat violet">
            <div className="stat-head">Certificados</div>
            <div className="stat-value">{datos.certificados}</div>
            <div className="stat-label">guardados</div>
          </div>
        </div>
      )}

      <div className="toolbar">
        <div className="search-wrap search">
          <IconBuscar width={17} height={17} />
          <input placeholder="Buscar por participante o curso..." value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)} />
        </div>
        <select style={{ width: 'auto' }} value={estado} onChange={(e) => setEstado(e.target.value)}>
          <option value="">Todos los estados</option>
          {['Inscrito', 'Aprobado', 'Reprobado', 'Faltó'].map((e) =>
            <option key={e} value={e}>{e}</option>)}
        </select>
        <button className="ghost" onClick={exportarCSV} disabled={!inscripciones.length}>
          Exportar CSV
        </button>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr><th>Participante</th><th>DNI</th><th>Curso</th><th>Estado</th>
              <th>Nota</th><th>Asistencia</th><th>Certificados</th></tr>
          </thead>
          <tbody>
            {inscripciones.map((i) => (
              <tr key={i.id}>
                <td>{i.participante_nombre}</td>
                <td>{i.dni || '—'}</td>
                <td>{i.curso_nombre}</td>
                <td><Estado valor={i.estado} /></td>
                <td>{i.nota ?? '—'}</td>
                <td>{i.asistencia ?? '—'}</td>
                <td>{i.total_certificados || 0}</td>
              </tr>
            ))}
            {inscripciones.length === 0 && (
              <tr><td colSpan={7}><Vacio>Sin resultados.</Vacio></td></tr>)}
          </tbody>
        </table>
      </div>
    </>
  )
}
