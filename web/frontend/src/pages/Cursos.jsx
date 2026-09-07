import { useEffect, useState } from 'react'
import { api } from '../api'
import { Estado, PageHeader, Vacio } from '../components'

const ESTADOS = ['Inscrito', 'Aprobado', 'Reprobado', 'Faltó']

export default function Cursos() {
  const [cursos, setCursos] = useState([])
  const [busqueda, setBusqueda] = useState('')
  const [soloActivos, setSoloActivos] = useState(false)
  const [seleccion, setSeleccion] = useState(null)
  const [inscripciones, setInscripciones] = useState([])

  async function cargarCursos() {
    const data = await api.cursos({ busqueda, soloActivos })
    const lista = data.results || data
    setCursos(lista)
    if (lista.length && !lista.find((c) => c.id === seleccion?.id)) setSeleccion(lista[0])
    if (!lista.length) { setSeleccion(null); setInscripciones([]) }
  }

  useEffect(() => {
    const t = setTimeout(cargarCursos, 250)
    return () => clearTimeout(t)
  }, [busqueda, soloActivos])

  useEffect(() => {
    if (seleccion) api.participantesDeCurso(seleccion.id).then(setInscripciones)
  }, [seleccion])

  async function cambiarEstado(insc, estado) {
    await api.actualizarInscripcion(insc.id, { estado })
    setInscripciones((prev) => prev.map((i) => (i.id === insc.id ? { ...i, estado } : i)))
    cargarCursos()
  }

  async function alternarActivo() {
    const actualizado = await api.actualizarCurso(seleccion.id, { activo: !seleccion.activo })
    setSeleccion({ ...seleccion, activo: actualizado.activo })
    cargarCursos()
  }

  return (
    <>
      <PageHeader titulo="Cursos" subtitulo="Participantes organizados por curso" />
      <div className="toolbar">
        <input className="search" placeholder="Buscar curso por nombre, código o instructor…"
          value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
        <label className="checkbox">
          <input type="checkbox" checked={soloActivos}
            onChange={(e) => setSoloActivos(e.target.checked)} />
          Solo cursos activos
        </label>
        <select value={seleccion?.id || ''}
          onChange={(e) => setSeleccion(cursos.find((c) => c.id === Number(e.target.value)))}>
          {cursos.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre} ({c.total_participantes} participantes)
            </option>
          ))}
          {cursos.length === 0 && <option value="">Sin cursos</option>}
        </select>
      </div>

      {!seleccion ? (
        <div className="card"><Vacio>No hay cursos que coincidan con la búsqueda.</Vacio></div>
      ) : (
        <div className="card">
          <div className="row" style={{ marginBottom: 14 }}>
            <div style={{ flex: 1 }}>
              <b style={{ fontSize: 16 }}>{seleccion.nombre}</b>{' '}
              <span className={`tag ${seleccion.activo ? 'activo' : 'inactivo'}`}>
                {seleccion.activo ? 'Activo' : 'Inactivo'}</span>
              <div className="page-sub" style={{ margin: '4px 0 0' }}>
                Código: {seleccion.codigo || '—'} · Instructor: {seleccion.instructor || '—'} ·
                Periodo: {seleccion.fecha_inicio || '—'} a {seleccion.fecha_fin || '—'} ·
                Horas: {seleccion.horas || '—'} · Aprobación: {seleccion.porcentaje_aprobacion}%
              </div>
            </div>
            <button className="ghost" onClick={alternarActivo}>
              {seleccion.activo ? 'Marcar inactivo' : 'Marcar activo'}
            </button>
          </div>

          <table>
            <thead>
              <tr><th>DNI</th><th>Participante</th><th>Estado</th><th>Nota</th>
                <th>Asistencia</th><th>Certificados</th><th>Cambiar estado</th></tr>
            </thead>
            <tbody>
              {inscripciones.map((i) => (
                <tr key={i.id}>
                  <td>{i.dni || '—'}</td>
                  <td>{i.participante_nombre}</td>
                  <td><Estado valor={i.estado} /></td>
                  <td>{i.nota ?? '—'}</td>
                  <td>{i.asistencia ?? '—'}</td>
                  <td>{i.total_certificados || 0}</td>
                  <td>
                    <select value={i.estado} onChange={(e) => cambiarEstado(i, e.target.value)}>
                      {ESTADOS.map((e) => <option key={e} value={e}>{e}</option>)}
                    </select>
                  </td>
                </tr>
              ))}
              {inscripciones.length === 0 && (
                <tr><td colSpan={7} className="muted">Este curso aún no tiene participantes.</td></tr>)}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
