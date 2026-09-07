import { useEffect, useState } from 'react'
import { api } from '../api'
import { PageHeader } from '../components'

const COLUMNAS = [
  ['DNI / Cédula', 'dni, cedula, ci, documento, identificacion'],
  ['Nombres', 'nombres, nombre, primer nombre'],
  ['Apellidos', 'apellidos, apellido, primer apellido'],
  ['Nombre completo', 'nombre completo, participante, nombre y apellido'],
  ['Email', 'email, correo, correo electronico'],
  ['Teléfono', 'telefono, tlf, celular, movil'],
  ['Curso', 'curso, nombre curso, capacitacion, taller, programa'],
  ['Código', 'codigo, codigo curso, cod'],
  ['Instructor', 'instructor, facilitador, docente, profesor'],
  ['Fecha inicio / fin', 'fecha inicio, inicio, desde / fecha fin, fin, hasta'],
  ['Horas', 'horas, duracion, horas academicas'],
  ['Estado', 'estado, condicion, resultado, status'],
  ['Nota', 'nota, calificacion, puntaje'],
  ['Asistencia', 'asistencia, porcentaje asistencia'],
  ['Observación', 'observacion, observaciones, comentario'],
]

export default function Configuracion() {
  const [datos, setDatos] = useState(null)

  useEffect(() => { api.dashboard().then(setDatos).catch(() => {}) }, [])

  return (
    <>
      <PageHeader titulo="Configuración"
        subtitulo="Referencia del sistema y formato esperado de los archivos" />

      <div className="cols2">
        <div className="card">
          <h2 className="card-title">Estado del sistema</h2>
          <table>
            <tbody>
              <tr><td>Participantes registrados</td><td><b>{datos?.participantes ?? '—'}</b></td></tr>
              <tr><td>Cursos totales</td><td><b>{datos?.cursos ?? '—'}</b></td></tr>
              <tr><td>Cursos activos</td><td><b>{datos?.cursos_activos ?? '—'}</b></td></tr>
              <tr><td>Inscripciones</td><td><b>{datos?.inscripciones ?? '—'}</b></td></tr>
              <tr><td>Certificados guardados</td><td><b>{datos?.certificados ?? '—'}</b></td></tr>
            </tbody>
          </table>
        </div>

        <div className="card">
          <h2 className="card-title">Cómo funcionan los certificados</h2>
          <p className="muted">
            Los certificados los elabora un proveedor externo. Al subirlos, el sistema:
          </p>
          <ol className="muted" style={{ paddingLeft: 18, lineHeight: 1.9, marginBottom: 0 }}>
            <li>Extrae el texto del PDF (si no tiene, usa el nombre del archivo).</li>
            <li>Detecta el <b>curso</b> comparándolo con los cursos registrados.</li>
            <li>Detecta al <b>participante</b> por DNI o por nombres y apellidos.</li>
            <li>Verifica la inscripción, marca <b>Aprobado</b> y archiva el documento.</li>
          </ol>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Columnas reconocidas al importar Excel</h2>
        <p className="muted" style={{ marginTop: 0 }}>
          Los encabezados se detectan automáticamente, sin distinguir mayúsculas ni acentos.
          Solo <b>Curso</b> y el nombre del participante son imprescindibles.
        </p>
        <table>
          <thead><tr><th>Campo</th><th>Encabezados aceptados</th></tr></thead>
          <tbody>
            {COLUMNAS.map(([campo, alias]) => (
              <tr key={campo}><td><b>{campo}</b></td><td className="muted">{alias}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
