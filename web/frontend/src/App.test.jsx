import { afterEach, describe, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'

import App from './App'
import Participantes from './pages/Participantes'
import Cursos from './pages/Cursos'
import Importar from './pages/Importar'
import Inicio from './pages/Inicio'
import Certificados from './pages/Certificados'
import { api } from './api'

afterEach(() => { cleanup(); vi.restoreAllMocks() })

const DASHBOARD = {
  participantes: 4, cursos: 3, cursos_activos: 2, inscripciones: 7,
  aprobados: 3, faltas: 1, certificados: 1,
  cursos_detalle: [{
    id: 1, nombre: 'Seguridad Industrial', codigo: 'SI-01', activo: true,
    total_participantes: 3, total_aprobados: 2, total_faltas: 1, porcentaje_aprobacion: 66.7,
  }],
}

const PARTICIPANTE = {
  id: 1, dni: 'V-18456321', nombres: 'María José', apellidos: 'Pérez Rojas',
  nombre_completo: 'María José Pérez Rojas', email: 'maria@correo.com',
  total_cursos: 2, total_aprobados: 2, total_faltas: 0,
}

describe('Navegación e Inicio', () => {
  test('muestra las tarjetas de resumen y los cursos', async () => {
    vi.spyOn(api, 'dashboard').mockResolvedValue(DASHBOARD)
    vi.spyOn(api, 'participantes').mockResolvedValue({ results: [] })
    vi.spyOn(api, 'cursos').mockResolvedValue({ results: [] })
    render(<App />)

    expect(await screen.findByText('Sistema de Gestión de Participantes')).toBeInTheDocument()
    // Tarjetas: participantes, cursos activos, aprobados y certificados.
    expect(await screen.findByText('4')).toBeInTheDocument()
    expect(screen.getByText('registrados')).toBeInTheDocument()
    expect(screen.getByText('guardados')).toBeInTheDocument()
    // La tarjeta "Cursos" muestra los ACTIVOS, no el total.
    expect(screen.getByText('activos')).toBeInTheDocument()
    expect(await screen.findByText('Seguridad Industrial')).toBeInTheDocument()
    expect(screen.getByText('3 participantes')).toBeInTheDocument()
  })

  test('permite cambiar de sección desde el menú lateral', async () => {
    vi.spyOn(api, 'dashboard').mockResolvedValue(DASHBOARD)
    vi.spyOn(api, 'participantes').mockResolvedValue({ results: [] })
    vi.spyOn(api, 'cursos').mockResolvedValue({ results: [] })
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: /Cursos/ }))
    expect(await screen.findByText('Participantes organizados por curso')).toBeInTheDocument()
  })

  test('al pulsar un curso en Inicio se abre esa sección con el curso elegido', async () => {
    vi.spyOn(api, 'dashboard').mockResolvedValue(DASHBOARD)
    vi.spyOn(api, 'participantes').mockResolvedValue({ results: [] })
    vi.spyOn(api, 'cursos').mockResolvedValue({
      results: [
        { id: 7, nombre: 'Otro Curso', activo: true, total_participantes: 1, porcentaje_aprobacion: 0 },
        { id: 1, nombre: 'Seguridad Industrial', activo: true, total_participantes: 3, porcentaje_aprobacion: 66.7 },
      ],
    })
    vi.spyOn(api, 'participantesDeCurso').mockResolvedValue([])
    render(<App />)

    fireEvent.click(await screen.findByText('Seguridad Industrial'))
    // Se selecciona el curso pulsado, no el primero de la lista.
    await waitFor(() => expect(api.participantesDeCurso).toHaveBeenCalledWith(1))
  })
})

describe('Inicio · carga de Excel y ficha', () => {
  test('importa el archivo y refresca las métricas', async () => {
    vi.spyOn(api, 'dashboard').mockResolvedValue(DASHBOARD)
    vi.spyOn(api, 'participantes').mockResolvedValue({ results: [] })
    const spy = vi.spyOn(api, 'importarExcel').mockResolvedValue({
      filas_procesadas: 7, participantes_nuevos: 4, cursos_nuevos: 3,
      inscripciones: 7, total_errores: 0, errores: [], columnas_detectadas: {},
    })
    const { container } = render(<Inicio onIrACursos={() => {}} />)

    fireEvent.change(container.querySelector('input[type=file]'), {
      target: { files: [new File(['x'], 'participantes.xlsx')] },
    })
    fireEvent.click(screen.getByRole('button', { name: /Cargar Excel/ }))

    await waitFor(() => expect(spy).toHaveBeenCalled())
    expect(await screen.findByText(/7 filas procesadas/)).toBeInTheDocument()
  })

  test('muestra la ficha del participante con cursos, estados y certificados', async () => {
    vi.spyOn(api, 'dashboard').mockResolvedValue(DASHBOARD)
    vi.spyOn(api, 'participantes').mockResolvedValue({ results: [PARTICIPANTE] })
    vi.spyOn(api, 'reporte').mockResolvedValue({
      ...PARTICIPANTE,
      resumen: { total_cursos: 2, aprobados: 1, reprobados: 0, faltas: 1, certificados: 1 },
      cursos: [
        { id: 1, curso_nombre: 'Curso X', estado: 'Aprobado', certificados: [{ id: 1, archivo_url: '/media/x.pdf' }] },
        { id: 2, curso_nombre: 'Curso Y', estado: 'Faltó', certificados: [] },
      ],
    })
    render(<Inicio onIrACursos={() => {}} />)

    expect(await screen.findByText('María José Pérez Rojas')).toBeInTheDocument()
    expect(screen.getByText('DNI: V-18456321')).toBeInTheDocument()
    expect(screen.getByText('Curso X: Aprobado')).toBeInTheDocument()
    expect(screen.getByText('Curso Y: Faltó')).toBeInTheDocument()
    // Las faltas se cuentan por curso.
    expect(screen.getByText('Curso X: 0')).toBeInTheDocument()
    expect(screen.getByText('Curso Y: 1')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Curso X - María José Pérez Rojas\.pdf/ }))
      .toHaveAttribute('href', '/media/x.pdf')
  })
})

describe('Participantes', () => {
  test('lista participantes y abre el reporte detallado', async () => {
    vi.spyOn(api, 'participantes').mockResolvedValue({ results: [PARTICIPANTE] })
    vi.spyOn(api, 'reporte').mockResolvedValue({
      ...PARTICIPANTE,
      resumen: { total_cursos: 2, aprobados: 2, reprobados: 0, faltas: 0, certificados: 1 },
      cursos: [{
        id: 4, curso_nombre: 'Primeros Auxilios', estado: 'Aprobado', nota: 19,
        asistencia: 100, certificados: [{ id: 1, archivo_url: '/media/c.pdf' }],
      }],
    })
    render(<Participantes />)

    expect(await screen.findByText('María José')).toBeInTheDocument()
    expect(screen.getByText('V-18456321')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Reporte' }))

    expect(await screen.findByText('María José Pérez Rojas')).toBeInTheDocument()
    expect(screen.getByText('Primeros Auxilios')).toBeInTheDocument()
    expect(screen.getByText('Aprobado')).toBeInTheDocument()
    // El certificado se enlaza con URL relativa (alcanzable tras el proxy).
    expect(screen.getByRole('link', { name: 'Ver' })).toHaveAttribute('href', '/media/c.pdf')
  })

  test('busca participantes por texto', async () => {
    const spy = vi.spyOn(api, 'participantes').mockResolvedValue({ results: [] })
    render(<Participantes />)
    fireEvent.change(screen.getByPlaceholderText(/Buscar por nombre/i),
      { target: { value: 'Perez' } })
    await waitFor(() => expect(spy).toHaveBeenCalledWith('Perez'))
  })
})

describe('Cursos', () => {
  test('filtra solo cursos activos', async () => {
    const spy = vi.spyOn(api, 'cursos').mockResolvedValue({
      results: [{
        id: 1, nombre: 'Excel Avanzado', codigo: 'EX-03', activo: true,
        total_participantes: 2, porcentaje_aprobacion: 0,
      }],
    })
    vi.spyOn(api, 'participantesDeCurso').mockResolvedValue([{
      id: 9, dni: 'V-1', participante_nombre: 'Ana Martínez', estado: 'Inscrito',
      nota: null, asistencia: null, total_certificados: 0,
    }])
    render(<Cursos />)

    expect(await screen.findByText('Ana Martínez')).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText(/Solo cursos activos/i, { selector: 'input' }))
    await waitFor(() =>
      expect(spy).toHaveBeenCalledWith({ busqueda: '', soloActivos: true }))
  })
})

describe('Importar Excel', () => {
  test('sube el archivo y muestra el resumen', async () => {
    const spy = vi.spyOn(api, 'importarExcel').mockResolvedValue({
      filas_procesadas: 7, participantes_nuevos: 4, cursos_nuevos: 3,
      inscripciones: 7, total_errores: 0, errores: [],
      columnas_detectadas: { dni: 'Cédula', curso: 'Curso' },
    })
    const { container } = render(<Importar />)

    const archivo = new File(['x'], 'participantes.xlsx')
    fireEvent.change(container.querySelector('input[type=file]'), {
      target: { files: [archivo] },
    })
    expect(await screen.findByText('participantes.xlsx')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Importar' }))
    await waitFor(() => expect(spy).toHaveBeenCalled())
    expect(await screen.findByText(/Importación completada/i)).toBeInTheDocument()
    expect(screen.getByText('Cédula')).toBeInTheDocument()
  })
})

describe('Certificados', () => {
  test('informa los certificados vinculados y los no identificados', async () => {
    vi.spyOn(api, 'certificados').mockResolvedValue({ results: [] })
    vi.spyOn(api, 'cargarCertificado')
      .mockResolvedValueOnce({
        certificado: { participante: 'María José Pérez Rojas', curso: 'Primeros Auxilios' },
      })
      .mockRejectedValueOnce(Object.assign(new Error('err'), {
        data: { mensaje: 'No se identificó el curso en el certificado.' },
      }))

    const { container } = render(<Certificados />)
    fireEvent.change(container.querySelector('input[type=file]'), {
      target: { files: [new File(['a'], 'ok.pdf'), new File(['b'], 'malo.pdf')] },
    })

    expect(await screen.findByText(/Vinculados correctamente \(1\)/)).toBeInTheDocument()
    expect(screen.getByText(/No identificados \(1\)/)).toBeInTheDocument()
    expect(screen.getByText(/No se identificó el curso/)).toBeInTheDocument()
  })
})
