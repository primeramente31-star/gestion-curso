import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { Alerta, PageHeader } from '../components'
import { IconBuscar } from '../icons'

export default function Certificados() {
  const [lista, setLista] = useState([])
  const [busqueda, setBusqueda] = useState('')
  const [mensajes, setMensajes] = useState([])
  const [subiendo, setSubiendo] = useState(false)
  const input = useRef(null)

  async function cargar(q = busqueda) {
    const data = await api.certificados(q)
    setLista(data.results || data)
  }

  useEffect(() => {
    const t = setTimeout(() => cargar(busqueda), 250)
    return () => clearTimeout(t)
  }, [busqueda])

  async function subir(archivos) {
    setSubiendo(true)
    const resultados = []
    for (const archivo of archivos) {
      try {
        const r = await api.cargarCertificado(archivo, true)
        resultados.push({
          ok: true,
          texto: `${archivo.name} → ${r.certificado.participante} / ${r.certificado.curso}`,
        })
      } catch (e) {
        resultados.push({ ok: false, texto: `${archivo.name}: ${e.data?.mensaje || e.message}` })
      }
    }
    setMensajes(resultados)
    setSubiendo(false)
    cargar()
  }

  const correctos = mensajes.filter((m) => m.ok)
  const fallidos = mensajes.filter((m) => !m.ok)

  return (
    <>
      <PageHeader titulo="Certificados"
        subtitulo="El sistema lee el curso y los nombres/apellidos del archivo y lo vincula al participante" />

      <div className="toolbar">
        <div className="search-wrap search">
          <IconBuscar width={17} height={17} />
          <input placeholder="Buscar por participante o curso…"
            value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
        </div>
        <input ref={input} type="file" multiple accept=".pdf,.png,.jpg,.jpeg"
          style={{ display: 'none' }}
          onChange={(e) => subir(Array.from(e.target.files))} />
        <button onClick={() => input.current.click()} disabled={subiendo}>
          {subiendo ? 'Procesando…' : 'Cargar certificados'}
        </button>
      </div>

      {correctos.length > 0 && (
        <Alerta tipo="ok" onClose={() => setMensajes([])}>
          {`Vinculados correctamente (${correctos.length}):\n` +
            correctos.map((m) => `• ${m.texto}`).join('\n')}
        </Alerta>
      )}
      {fallidos.length > 0 && (
        <Alerta tipo="error" onClose={() => setMensajes([])}>
          {`No identificados (${fallidos.length}):\n` +
            fallidos.map((m) => `• ${m.texto}`).join('\n')}
        </Alerta>
      )}

      <div className="card">
        <table>
          <thead>
            <tr><th>Participante</th><th>DNI</th><th>Curso</th>
              <th>Cargado</th><th>Archivo</th></tr>
          </thead>
          <tbody>
            {lista.map((c) => (
              <tr key={c.id}>
                <td>{c.participante}</td>
                <td>{c.dni || '—'}</td>
                <td>{c.curso}</td>
                <td>{new Date(c.cargado_en).toLocaleString('es')}</td>
                <td><a href={c.archivo_url} target="_blank" rel="noreferrer">Abrir</a></td>
              </tr>
            ))}
            {lista.length === 0 && (
              <tr><td colSpan={5} className="muted">
                Aún no hay certificados cargados.</td></tr>)}
          </tbody>
        </table>
      </div>
    </>
  )
}
