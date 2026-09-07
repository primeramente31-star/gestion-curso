import { useEffect, useState } from 'react'
import { api } from '../api'
import { Alerta, Estado, Modal, PageHeader, Stat, Vacio } from '../components'
import { IconBuscar } from '../icons'

function ReporteParticipante({ id, onClose }) {
  const [rep, setRep] = useState(null)

  useEffect(() => { api.reporte(id).then(setRep) }, [id])

  if (!rep) return <Modal titulo="Reporte" onClose={onClose}><Vacio>Cargando…</Vacio></Modal>

  const r = rep.resumen
  return (
    <Modal
      titulo={rep.nombre_completo}
      subtitulo={`DNI: ${rep.dni || '—'} · ${rep.email || 'sin email'} · ${rep.telefono || 'sin teléfono'}`}
      onClose={onClose}
    >
      <div className="stats">
        <Stat label="Cursos realizados" value={r.total_cursos} />
        <Stat label="Aprobados" value={r.aprobados} />
        <Stat label="Reprobados" value={r.reprobados} />
        <Stat label="Faltas" value={r.faltas} />
        <Stat label="Certificados" value={r.certificados} />
      </div>

      <table>
        <thead>
          <tr><th>Curso</th><th>Código</th><th>Estado</th><th>Nota</th>
            <th>Asistencia</th><th>Certificado</th></tr>
        </thead>
        <tbody>
          {rep.cursos.map((c) => (
            <tr key={c.id}>
              <td>{c.curso_nombre}</td>
              <td>{c.dni_curso || '—'}</td>
              <td><Estado valor={c.estado} /></td>
              <td>{c.nota ?? '—'}</td>
              <td>{c.asistencia ?? '—'}</td>
              <td>
                {c.certificados.length > 0
                  ? c.certificados.map((cert) => (
                    <a key={cert.id} href={cert.archivo_url} target="_blank" rel="noreferrer"
                      style={{ marginRight: 8 }}>Ver</a>))
                  : <span className="muted">No</span>}
              </td>
            </tr>
          ))}
          {rep.cursos.length === 0 && (
            <tr><td colSpan={6} className="muted">Sin cursos registrados.</td></tr>)}
        </tbody>
      </table>
    </Modal>
  )
}

function NuevoParticipante({ onClose, onGuardado }) {
  const [form, setForm] = useState({ dni: '', nombres: '', apellidos: '', email: '', telefono: '' })
  const [error, setError] = useState('')
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function guardar() {
    try {
      await api.crearParticipante({ ...form, dni: form.dni || null })
      onGuardado()
      onClose()
    } catch (e) {
      setError(e.data ? JSON.stringify(e.data) : e.message)
    }
  }

  return (
    <Modal titulo="Nuevo participante" onClose={onClose}>
      <Alerta tipo="error">{error}</Alerta>
      <div className="grid2">
        <div className="field"><label>Nombres *</label>
          <input value={form.nombres} onChange={set('nombres')} /></div>
        <div className="field"><label>Apellidos *</label>
          <input value={form.apellidos} onChange={set('apellidos')} /></div>
        <div className="field"><label>DNI / Cédula</label>
          <input value={form.dni} onChange={set('dni')} /></div>
        <div className="field"><label>Email</label>
          <input value={form.email} onChange={set('email')} /></div>
        <div className="field"><label>Teléfono</label>
          <input value={form.telefono} onChange={set('telefono')} /></div>
      </div>
      <div className="row">
        <div className="spacer" />
        <button className="ghost" onClick={onClose}>Cancelar</button>
        <button onClick={guardar} disabled={!form.nombres || !form.apellidos}>Guardar</button>
      </div>
    </Modal>
  )
}

export default function Participantes() {
  const [lista, setLista] = useState([])
  const [busqueda, setBusqueda] = useState('')
  const [reporteId, setReporteId] = useState(null)
  const [creando, setCreando] = useState(false)
  const [cargando, setCargando] = useState(true)

  async function cargar(q = busqueda) {
    setCargando(true)
    const data = await api.participantes(q)
    setLista(data.results || data)
    setCargando(false)
  }

  useEffect(() => {
    const t = setTimeout(() => cargar(busqueda), 250)
    return () => clearTimeout(t)
  }, [busqueda])

  async function eliminar(p) {
    if (!confirm(`¿Eliminar a ${p.nombre_completo} y todo su historial?`)) return
    await api.eliminarParticipante(p.id)
    cargar()
  }

  return (
    <>
      <PageHeader titulo="Participantes" subtitulo="Registro de personas y su historial formativo" />
      <div className="toolbar">
        <div className="search-wrap search">
          <IconBuscar width={17} height={17} />
          <input placeholder="Buscar por nombre, apellido o DNI…"
            value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
        </div>
        <button onClick={() => setCreando(true)}>Nuevo participante</button>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr><th>DNI</th><th>Nombres</th><th>Apellidos</th><th>Email</th>
              <th>Cursos</th><th>Aprobados</th><th>Faltas</th><th></th></tr>
          </thead>
          <tbody>
            {lista.map((p) => (
              <tr key={p.id} className="clickable" onClick={() => setReporteId(p.id)}>
                <td>{p.dni || '—'}</td>
                <td>{p.nombres}</td>
                <td>{p.apellidos}</td>
                <td>{p.email || '—'}</td>
                <td>{p.total_cursos}</td>
                <td>{p.total_aprobados}</td>
                <td>{p.total_faltas}</td>
                <td onClick={(e) => e.stopPropagation()}>
                  <div className="row">
                    <button className="link" onClick={() => setReporteId(p.id)}>Reporte</button>
                    <button className="link" style={{ color: 'var(--red)' }}
                      onClick={() => eliminar(p)}>Eliminar</button>
                  </div>
                </td>
              </tr>
            ))}
            {!cargando && lista.length === 0 && (
              <tr><td colSpan={8} className="muted">Sin resultados.</td></tr>)}
          </tbody>
        </table>
      </div>

      {reporteId && <ReporteParticipante id={reporteId} onClose={() => setReporteId(null)} />}
      {creando && <NuevoParticipante onClose={() => setCreando(false)} onGuardado={cargar} />}
    </>
  )
}
