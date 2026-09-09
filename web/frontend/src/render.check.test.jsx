import { expect, test, vi, afterEach } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import App from './App'
import { api } from './api'

afterEach(cleanup)

test('la pantalla de Inicio reproduce la estructura del diseño', async () => {
  vi.spyOn(api, 'dashboard').mockResolvedValue({
    participantes: 248, cursos: 2, cursos_activos: 2, inscripciones: 248,
    aprobados: 186, faltas: 12, certificados: 172,
    cursos_detalle: [
      { id: 1, nombre: 'Curso X', activo: true, total_participantes: 120, porcentaje_aprobacion: 70 },
      { id: 2, nombre: 'Curso Y', activo: true, total_participantes: 128, porcentaje_aprobacion: 75 },
    ],
  })
  vi.spyOn(api, 'participantes').mockResolvedValue({ results: [{
    id: 1, dni: '12345678', nombres: 'Juan', apellidos: 'Pérez Gómez',
    nombre_completo: 'Juan Pérez Gómez',
  }] })
  vi.spyOn(api, 'reporte').mockResolvedValue({
    id: 1, dni: '12345678', nombre_completo: 'Juan Pérez Gómez',
    resumen: { total_cursos: 2, aprobados: 2, reprobados: 0, faltas: 1, certificados: 2 },
    cursos: [
      { id: 1, curso_nombre: 'Curso X', estado: 'Aprobado', certificados: [{ id: 1, archivo_url: '/media/x.pdf' }] },
      { id: 2, curso_nombre: 'Curso Y', estado: 'Aprobado', certificados: [{ id: 2, archivo_url: '/media/y.pdf' }] },
    ],
  })

  render(<App />)
  await screen.findByText('Juan Pérez Gómez')

  const esperados = [
    'Inicio', 'Participantes', 'Cursos', 'Cargar Excel', 'Certificados', 'Reportes', 'Configuración',
    'Sistema de Gestión de Participantes',
    'Administra participantes, cursos, asistencias, resultados y certificados',
    '248', '186', '172', 'registrados', 'activos', 'guardados',
    'Cargar participantes desde Excel',
    'Curso X', '120 participantes', 'Curso Y', '128 participantes',
    'Reporte de participante', 'DNI: 12345678',
    'Cursos realizados', 'Faltas', 'Estado',
    'Simple, útil y escalable. Listo para crecer.',
  ]
  for (const t of esperados) expect(screen.getAllByText(t).length).toBeGreaterThan(0)

  // El texto del dropzone se parte con un <br />, se busca por contenido del nodo.
  expect(screen.getByText((_, el) =>
    el?.className === 'dropzone-main' &&
    el.textContent.includes('Arrastra tu archivo aquí'))).toBeInTheDocument()
  expect(screen.getByText(/Formatos soportados/)).toBeInTheDocument()

  expect(screen.getByPlaceholderText('Buscar curso...')).toBeInTheDocument()
  expect(screen.getByPlaceholderText('Buscar por nombre o documento...')).toBeInTheDocument()
  expect(screen.getAllByText('Activo')).toHaveLength(2)
  expect(screen.getByText('Curso X - Juan Pérez Gómez.pdf')).toBeInTheDocument()
  expect(screen.getByText('Curso Y - Juan Pérez Gómez.pdf')).toBeInTheDocument()
})
