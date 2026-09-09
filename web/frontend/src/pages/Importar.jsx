import { useRef, useState } from 'react'
import { api } from '../api'
import { Alerta, PageHeader } from '../components'

export default function Importar() {
  const [archivo, setArchivo] = useState(null)
  const [cursoDefecto, setCursoDefecto] = useState('')
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState('')
  const [subiendo, setSubiendo] = useState(false)
  const [sobre, setSobre] = useState(false)
  const input = useRef(null)

  async function enviar() {
    if (!archivo) return
    setSubiendo(true); setError(''); setResultado(null)
    try {
      setResultado(await api.importarExcel(archivo, cursoDefecto))
    } catch (e) {
      const d = e.data
      setError(d?.errores?.length ? d.errores.join('\n') : (d?.detail || e.message))
    } finally {
      setSubiendo(false)
    }
  }

  function soltar(e) {
    e.preventDefault(); setSobre(false)
    if (e.dataTransfer.files?.[0]) setArchivo(e.dataTransfer.files[0])
  }

  return (
    <>
      <PageHeader titulo="Importar desde Excel"
        subtitulo="Carga participantes, cursos e inscripciones desde un archivo .xlsx, .xls o .csv" />

      <div className="card" style={{ marginBottom: 16 }}>
        <b>Columnas reconocidas automáticamente</b>
        <p className="muted" style={{ marginBottom: 0 }}>
          DNI/Cédula · Nombres · Apellidos (o Nombre completo) · Email · Teléfono ·
          <b> Curso</b> · Código · Instructor · Fecha inicio · Fecha fin · Horas ·
          Estado · Nota · Asistencia · Observación.
          <br />No distingue mayúsculas ni acentos. Reimportar el mismo archivo actualiza
          los registros en lugar de duplicarlos.
        </p>
      </div>

      <div
        className={`dropzone ${sobre ? 'over' : ''}`}
        onClick={() => input.current.click()}
        onDragOver={(e) => { e.preventDefault(); setSobre(true) }}
        onDragLeave={() => setSobre(false)}
        onDrop={soltar}
      >
        <input ref={input} type="file" accept=".xlsx,.xls,.csv" style={{ display: 'none' }}
          onChange={(e) => setArchivo(e.target.files[0])} />
        {archivo
          ? <b>{archivo.name}</b>
          : <span className="muted">Arrastra el archivo aquí o haz clic para seleccionarlo</span>}
      </div>

      <div className="toolbar" style={{ marginTop: 16 }}>
        <input className="search"
          placeholder="Curso por defecto (solo si el archivo no tiene columna 'Curso')"
          value={cursoDefecto} onChange={(e) => setCursoDefecto(e.target.value)} />
        <button onClick={enviar} disabled={!archivo || subiendo}>
          {subiendo ? 'Importando…' : 'Importar'}
        </button>
      </div>

      <Alerta tipo="error" onClose={() => setError('')}>{error}</Alerta>

      {resultado && (
        <div className="card">
          <Alerta tipo="ok">Importación completada correctamente.</Alerta>
          <div className="stats">
            <div className="card stat">
              <div className="stat-value">{resultado.filas_procesadas}</div>
              <div className="stat-label">Filas procesadas</div></div>
            <div className="card stat">
              <div className="stat-value">{resultado.participantes_nuevos}</div>
              <div className="stat-label">Participantes nuevos</div></div>
            <div className="card stat">
              <div className="stat-value">{resultado.cursos_nuevos}</div>
              <div className="stat-label">Cursos nuevos</div></div>
            <div className="card stat">
              <div className="stat-value">{resultado.inscripciones}</div>
              <div className="stat-label">Inscripciones</div></div>
            <div className="card stat">
              <div className="stat-value">{resultado.total_errores}</div>
              <div className="stat-label">Errores</div></div>
          </div>

          <b>Columnas detectadas</b>
          <table style={{ marginTop: 8 }}>
            <thead><tr><th>Campo del sistema</th><th>Columna del archivo</th></tr></thead>
            <tbody>
              {Object.entries(resultado.columnas_detectadas).map(([k, v]) => (
                <tr key={k}><td>{k}</td><td>{v}</td></tr>))}
            </tbody>
          </table>

          {resultado.errores?.length > 0 && (
            <>
              <b style={{ display: 'block', marginTop: 16 }}>Errores</b>
              <ul className="muted">{resultado.errores.map((e, i) => <li key={i}>{e}</li>)}</ul>
            </>
          )}
        </div>
      )}
    </>
  )
}
