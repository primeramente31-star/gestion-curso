// Cliente de la API REST. Siempre rutas relativas (proxy de Vite -> Django).
const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  const texto = await res.text()
  let data = null
  try { data = texto ? JSON.parse(texto) : null } catch { data = texto }
  if (!res.ok) {
    const err = new Error(
      (data && (data.detail || data.mensaje)) || `Error ${res.status}`)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

const json = (metodo, body) => ({
  method: metodo,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const api = {
  dashboard: () => request('/dashboard/'),

  participantes: (busqueda = '') =>
    request(`/participantes/?search=${encodeURIComponent(busqueda)}&page_size=100`),
  crearParticipante: (datos) => request('/participantes/', json('POST', datos)),
  eliminarParticipante: (id) => request(`/participantes/${id}/`, { method: 'DELETE' }),
  reporte: (id) => request(`/participantes/${id}/reporte/`),

  cursos: ({ busqueda = '', soloActivos = false } = {}) => {
    const p = new URLSearchParams({ search: busqueda, page_size: '100' })
    if (soloActivos) p.set('activo', 'true')
    return request(`/cursos/?${p}`)
  },
  participantesDeCurso: (id) => request(`/cursos/${id}/participantes/`),
  actualizarCurso: (id, datos) => request(`/cursos/${id}/`, json('PATCH', datos)),

  inscripciones: (query = '') => request(`/inscripciones/?${query}`),
  actualizarInscripcion: (id, datos) => request(`/inscripciones/${id}/`, json('PATCH', datos)),

  certificados: (busqueda = '') =>
    request(`/certificados/?search=${encodeURIComponent(busqueda)}&page_size=100`),

  importarExcel: (archivo, cursoPorDefecto = '') => {
    const fd = new FormData()
    fd.append('archivo', archivo)
    if (cursoPorDefecto) fd.append('curso_por_defecto', cursoPorDefecto)
    return request('/importar-excel/', { method: 'POST', body: fd })
  },

  cargarCertificado: (archivo, aprobar = true) => {
    const fd = new FormData()
    fd.append('archivo', archivo)
    fd.append('aprobar', aprobar ? 'true' : 'false')
    return request('/certificados/cargar/', { method: 'POST', body: fd })
  },
}
