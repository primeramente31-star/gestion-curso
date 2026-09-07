// Iconos SVG en línea (sin dependencias externas).
const base = {
  width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', strokeWidth: 1.8,
  strokeLinecap: 'round', strokeLinejoin: 'round',
}

export const IconInicio = (p) => (
  <svg {...base} {...p}><path d="M3 10.5 12 3l9 7.5" /><path d="M5 9.5V21h14V9.5" /></svg>
)
export const IconParticipantes = (p) => (
  <svg {...base} {...p}>
    <circle cx="9" cy="8" r="3.2" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0" />
    <path d="M16 5.2a3.2 3.2 0 0 1 0 5.9" /><path d="M17.5 14.2A6.5 6.5 0 0 1 21.5 20" />
  </svg>
)
export const IconCursos = (p) => (
  <svg {...base} {...p}>
    <path d="M4 4.5h6a2.5 2.5 0 0 1 2 2.5v13a2 2 0 0 0-2-1.6H4z" />
    <path d="M20 4.5h-6a2.5 2.5 0 0 0-2 2.5v13a2 2 0 0 1 2-1.6h6z" />
  </svg>
)
export const IconExcel = (p) => (
  <svg {...base} {...p}>
    <path d="M12 16V4" /><path d="m8 8 4-4 4 4" /><path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
  </svg>
)
export const IconCertificados = (p) => (
  <svg {...base} {...p}>
    <circle cx="12" cy="9.5" r="5" /><path d="m8.5 14-1.2 6L12 18l4.7 2-1.2-6" />
  </svg>
)
export const IconReportes = (p) => (
  <svg {...base} {...p}>
    <rect x="3.5" y="4" width="17" height="16" rx="2.5" />
    <path d="M8 15.5v-3M12 15.5v-6M16 15.5v-4" />
  </svg>
)
export const IconConfiguracion = (p) => (
  <svg {...base} {...p}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 9 19.4a1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 4.6 9a1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H9a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z" />
  </svg>
)
export const IconAprobados = (p) => (
  <svg {...base} {...p}><circle cx="12" cy="12" r="9" /><path d="m8.5 12.5 2.5 2.5 4.5-5" /></svg>
)
export const IconBuscar = (p) => (
  <svg {...base} {...p}><circle cx="11" cy="11" r="6.5" /><path d="m20 20-3.6-3.6" /></svg>
)
export const IconSubir = (p) => (
  <svg {...base} {...p}>
    <path d="M7 17.5a4 4 0 0 1-.5-8 5.5 5.5 0 0 1 10.6-1.4A4.2 4.2 0 0 1 21 12a4 4 0 0 1-4 4" />
    <path d="M12 9v9" /><path d="m8.7 14.6 3.3 3.4 3.3-3.4" />
  </svg>
)
export const IconArchivo = (p) => (
  <svg {...base} {...p}>
    <path d="M14 3.5H7.5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V8z" />
    <path d="M14 3.5V8h4.5" />
  </svg>
)
export const IconPersona = (p) => (
  <svg {...base} {...p}><circle cx="12" cy="8.5" r="3.8" /><path d="M4.5 20.5a7.5 7.5 0 0 1 15 0" /></svg>
)
export const IconCalendario = (p) => (
  <svg {...base} {...p}>
    <rect x="3.5" y="5" width="17" height="15" rx="2.5" /><path d="M8 3v4M16 3v4M3.5 10h17" />
    <path d="m9 14.5 1.5 1.5 3-3" />
  </svg>
)
export const IconBombilla = (p) => (
  <svg {...base} {...p}>
    <path d="M9.5 17.5h5M10 20.5h4" />
    <path d="M12 3a6 6 0 0 0-3.5 10.9c.4.3.6.8.6 1.3v.3h5.8v-.3c0-.5.2-1 .6-1.3A6 6 0 0 0 12 3Z" />
  </svg>
)
