import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { Alerta } from '../components'
import {
  IconAprobados, IconArchivo, IconBuscar, IconCalendario, IconCertificados,
  IconCursos, IconParticipantes, IconPersona, IconSubir,
} from '../icons'

function Tarjeta({ color, Icono, titulo, valor, etiqueta }) {
  return (
    <div className={`stat ${color}`}>
      <div className="stat-head">
        <span className="stat-icon"><Icono /></span>
        {titulo}
      </div>
      <div className="stat-value">{valor ?? 0}</div>
      <div className="stat-label">{etiqueta}</div>
    </div>
  )
}

function CargarExcel({ onImportado }) {
  const [archivo, setArchivo] = useState(null)
  const [sobre, setSobre] = useState(false)
  const [subiendo, setSubiendo] = useState(false)
  const [ok, setOk] = useState('')
  const [error, setError] = useState('')
  const input = useRef(null)

  async function enviar(f) {
    const elegido = f || archivo
    if (!elegido) return input.current.click()
    setSubiendo(true); setOk(''); setError('')
    try {
      const r = await api.importarExcel(elegido)
      setOk(`${r.filas_procesadas} filas procesadas · ${r.participantes_nuevos} participantes nuevos · ` +
        `${r.cursos_nuevos} cursos nuevos${r.total_errores ? ` · ${r.total_errores} errores` : ''}`)
      onImportado()
    } catch (e) {
      const d = e.data
      setError(d?.errores?.length ? d.errores.join('\n') : (d?.detail || e.message))
    } finally {
      setSubiendo(false)
    }
  }

  return (
    <div className="card">
      <h2 className="card-title">Cargar participantes desde Excel</h2>
      <p className="muted" style={{ marginTop: 0 }}>
        Importa un archivo Excel (.xlsx) con los datos de los participantes y sus cursos.
      </p>

      <div
        className={`dropzone ${sobre ? 'over' : ''}`}
        onClick={() => input.current.click()}
        onDragOver={(e) => { e.preventDefault(); setSobre(true) }}
        onDragLeave={() => setSobre(false)}
        onDrop={(e) => {
          e.preventDefault(); setSobre(false)
          if (e.dataTransfer.files?.[0]) setArchivo(e.dataTransfer.files[0])
        }}
      >
        <input ref={input} type="file" accept=".xlsx,.xls,.csv" style={{ display: 'none' }}
          onChange={(e) => setArchivo(e.target.files[0])} />
        <div className="up"><IconSubir width={44} height={44} /></div>
        {archivo ? (
          <>
            <div className="dropzone-main"><b>{archivo.name}</b></div>
            <div className="dropzone-sub">Listo para importar</div>
          </>
        ) : (
          <>
            <div className="dropzone-main">Arrastra tu archivo aquí o<br />haz clic para seleccionar</div>
            <div className="dropzone-sub">Formatos soportados: .xlsx, .xls, .csv</div>
          </>
        )}
      </div>

      <button className="btn-block" onClick={() => enviar()} disabled={subiendo}>
        <IconSubir width={18} height={18} />
        {subiendo ? 'Importando…' : 'Cargar Excel'}
      </button>

      <div style={{ marginTop: 14 }}>
        <Alerta tipo="ok" onClose={() => setOk('')}>{ok}</Alerta>
        <Alerta tipo="error" onClose={() => setError('')}>{error}</Alerta>
      </div>
    </div>
  )
}

function ListaCursos({ cursos, onVerCurso }) {
  const [busqueda, setBusqueda] = useState('')
  const filtrados = cursos.filter((c) =>
    c.nombre.toLowerCase().includes(busqueda.toLowerCase().trim()))

  return (
    <div className="card">
      <div className="card-head">
        <h2 className="card-title">Cursos</h2>
        <div className="search-wrap" style={{ maxWidth: 260 }}>
          <IconBuscar width={17} height={17} />
          <input placeholder="Buscar curso..." value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)} />
        </div>
      </div>

      {filtrados.map((c) => (
        <button key={c.id} className="curso-item" onClick={() => onVerCurso(c)}>
          <span className="curso-icon"><IconCursos width={22} height={22} /></span>
          <span style={{ flex: 1 }}>
            <span className="curso-nombre" style={{ display: 'block' }}>{c.nombre}</span>
            <span className="curso-meta">{c.total_participantes} participantes</span>
          </span>
          <IconParticipantes width={19} height={19} style={{ color: 'var(--green)' }} />
          <span className={`tag ${c.activo ? 'activo' : 'inactivo'}`}>
            {c.activo ? 'Activo' : 'Inactivo'}
          </span>
        </button>
      ))}
      {filtrados.length === 0 && (
        <div className="empty">
          {cursos.length === 0
            ? 'Aún no hay cursos. Importa un archivo Excel para comenzar.'
            : 'Ningún curso coincide con la búsqueda.'}
        </div>
      )}
    </div>
  )
}

function ReporteParticipante() {
  const [busqueda, setBusqueda] = useState('')
  const [opciones, setOpciones] = useState([])
  const [rep, setRep] = useState(null)

  useEffect(() => {
    const t = setTimeout(async () => {
      const data = await api.participantes(busqueda)
      const lista = data.results || data
      setOpciones(lista)
      if (lista.length) {
        setRep(await api.reporte(lista[0].id))
      } else {
        setRep(null)
      }
    }, 250)
    return () => clearTimeout(t)
  }, [busqueda])

  const estados = {
    Aprobado: 'ok', Reprobado: 'bad', 'Faltó': 'warn', Inscrito: 'info',
  }

  return (
    <div className="card">
      <div className="card-head">
        <h2 className="card-title">Reporte de participante</h2>
        <div className="search-wrap" style={{ maxWidth: 330 }}>
          <IconBuscar width={17} height={17} />
          <input placeholder="Buscar por nombre o documento..." value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)} />
        </div>
      </div>

      {!rep ? (
        <div className="empty">
          {opciones.length === 0 && busqueda
            ? 'Ningún participante coincide con la búsqueda.'
            : 'Aún no hay participantes registrados.'}
        </div>
      ) : (
        <div className="ficha">
          <div className="ficha-grid">
            <div className="ficha-col">
              <div className="ficha-persona">
                <span className="avatar"><IconPersona width={30} height={30} /></span>
                <div>
                  <div className="ficha-nombre">{rep.nombre_completo}</div>
                  <div className="ficha-dni">DNI: {rep.dni || '—'}</div>
                  <ul className="lista-limpia">
                    {rep.cursos.map((c) => (
                      <li key={c.id}><span className="bullet">•</span>{c.curso_nombre}</li>
                    ))}
                    {rep.cursos.length === 0 && <li className="muted">Sin cursos</li>}
                  </ul>
                </div>
              </div>
            </div>

            <div className="ficha-col">
              <div className="ficha-head">
                <IconCursos width={19} height={19} />
                Cursos realizados
              </div>
              <div className="ficha-sub">Faltas</div>
              <ul className="lista-limpia">
                {rep.cursos.map((c) => (
                  <li key={c.id}>
                    <span className={`dot ${c.estado === 'Faltó' ? 'warn' : 'ok'}`} />
                    {c.curso_nombre}: {c.estado === 'Faltó' ? 1 : 0}
                  </li>
                ))}
                {rep.cursos.length === 0 && <li className="muted">—</li>}
              </ul>
            </div>

            <div className="ficha-col">
              <div className="ficha-head">
                <IconAprobados width={19} height={19} />
                <IconCalendario width={19} height={19} />
              </div>
              <div className="ficha-sub">Estado</div>
              <ul className="lista-limpia">
                {rep.cursos.map((c) => (
                  <li key={c.id}>
                    <span className={`dot ${estados[c.estado] || 'info'}`} />
                    {c.curso_nombre}: {c.estado}
                  </li>
                ))}
                {rep.cursos.length === 0 && <li className="muted">—</li>}
              </ul>
            </div>

            <div className="ficha-col">
              <div className="ficha-head">
                <IconCertificados width={19} height={19} />
                Certificados
              </div>
              {rep.cursos.flatMap((c) =>
                c.certificados.map((cert) => (
                  <a key={cert.id} className="cert-link" href={cert.archivo_url}
                    target="_blank" rel="noreferrer">
                    <IconArchivo width={17} height={17} />
                    {`${c.curso_nombre} - ${rep.nombre_completo}.pdf`}
                  </a>
                )))}
              {rep.resumen.certificados === 0 && (
                <div className="muted" style={{ fontSize: 13 }}>Sin certificados guardados.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function Inicio({ onIrACursos }) {
  const [datos, setDatos] = useState(null)
  const [recarga, setRecarga] = useState(0)

  useEffect(() => { api.dashboard().then(setDatos).catch(() => setDatos(null)) }, [recarga])

  return (
    <>
      <h1 className="page-title">Sistema de Gestión de Participantes</h1>
      <p className="page-sub">Administra participantes, cursos, asistencias, resultados y certificados</p>

      <div className="stats">
        <Tarjeta color="blue" Icono={IconParticipantes} titulo="Participantes"
          valor={datos?.participantes} etiqueta="registrados" />
        <Tarjeta color="green" Icono={IconCursos} titulo="Cursos"
          valor={datos?.cursos_activos} etiqueta="activos" />
        <Tarjeta color="amber" Icono={IconAprobados} titulo="Aprobados"
          valor={datos?.aprobados} etiqueta="participantes" />
        <Tarjeta color="violet" Icono={IconCertificados} titulo="Certificados"
          valor={datos?.certificados} etiqueta="guardados" />
      </div>

      <div className="cols2">
        <CargarExcel onImportado={() => setRecarga((n) => n + 1)} />
        <ListaCursos cursos={datos?.cursos_detalle || []} onVerCurso={onIrACursos} />
      </div>

      <ReporteParticipante key={recarga} />
    </>
  )
}
