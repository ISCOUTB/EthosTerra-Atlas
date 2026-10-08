import { useEffect, useRef, useState, useMemo } from 'react'
import * as maplibregl from 'maplibre-gl'
import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import 'maplibre-gl/dist/maplibre-gl.css'

if (typeof window !== 'undefined' && maplibregl.setWorkerUrl) {
  maplibregl.setWorkerUrl(maplibreWorkerUrl)
}
import {
  Compass,
  ShieldCheck,
  Building2,
  Layers,
  MapPin,
  RotateCcw,
  CheckCircle2,
  Landmark,
  Droplets,
  Sprout,
  TrendingUp,
  Cpu,
  BookOpen,
  Hash,
  ChevronRight,
  CloudRain,
  Mountain,
  Sun,
  Globe,
  Brain,
} from 'lucide-react'
import {
  PILOT_MUNICIPALITIES,
  type MunicipalityProfile,
} from '../data/territoriesData'
import { QuarantineReviewView } from './QuarantineReviewView'

const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/v2'

type TabMode = 'instruments' | 'queue' | 'agronomy'
type BaseStyleId = 'topo' | 'satellite' | 'osm'
type ChoroplethTheme = 'jurisdiction' | 'climate'

const BASE_STYLES: Record<BaseStyleId, { name: string; icon: any; style: any }> = {
  topo: {
    name: 'Topográfico y Relieve',
    icon: Mountain,
    style: {
      version: 8,
      sources: {
        'esri-topo': {
          type: 'raster',
          tiles: [
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
          ],
          tileSize: 256,
          attribution: '&copy; Esri &copy; USGS &copy; DANE',
        },
      },
      layers: [
        {
          id: 'topo-layer',
          type: 'raster',
          source: 'esri-topo',
          minzoom: 0,
          maxzoom: 19,
        },
      ],
    },
  },
  satellite: {
    name: 'Imagen Satelital',
    icon: Globe,
    style: {
      version: 8,
      sources: {
        'esri-sat': {
          type: 'raster',
          tiles: [
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
          ],
          tileSize: 256,
          attribution: '&copy; Esri &copy; Maxar',
        },
      },
      layers: [
        {
          id: 'sat-layer',
          type: 'raster',
          source: 'esri-sat',
          minzoom: 0,
          maxzoom: 19,
        },
      ],
    },
  },
  osm: {
    name: 'Calles (OpenStreetMap)',
    icon: Sun,
    style: {
      version: 8,
      sources: {
        'osm-tiles': {
          type: 'raster',
          tiles: [
            'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          ],
          tileSize: 256,
          attribution: '&copy; OpenStreetMap contributors',
        },
      },
      layers: [
        {
          id: 'osm-layer',
          type: 'raster',
          source: 'osm-tiles',
          minzoom: 0,
          maxzoom: 19,
        },
      ],
    },
  },
}

export default function AtlasView() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<Record<string, maplibregl.Marker>>({})
  const popupRef = useRef<maplibregl.Popup | null>(null)

  // Estado de navegación territorial
  const [selectedDept, setSelectedDept] = useState<'13' | '70' | 'all'>('13')
  const [selectedDivipola, setSelectedDivipola] = useState<string>('13244')
  const [activeTab, setActiveTab] = useState<TabMode>('instruments')

  // Estado cartográfico: Topográfico Esri por defecto (100% libre, sin API key, con relieve)
  const [baseStyle, setBaseStyle] = useState<BaseStyleId>('topo')
  const [choroplethTheme, setChoroplethTheme] = useState<ChoroplethTheme>('jurisdiction')
  const [mapLoaded, setMapLoaded] = useState<boolean>(false)

  // Documentos aprobados localmente (Human Gate AT-1)
  const [approvedDocs, setApprovedDocs] = useState<Record<string, boolean>>({
    PND_2022_2026: true,
    PIDARET_BOLIVAR_2021: true,
    PATR_MONTES_DE_MARIA_2018: true,
    PIDARET_SUCRE_2020: true,
  })

  // Perfil del municipio seleccionado
  const activeProfile: MunicipalityProfile = useMemo(() => {
    const found = PILOT_MUNICIPALITIES.find((p) => p.divipola === selectedDivipola)
    return found || PILOT_MUNICIPALITIES[0]
  }, [selectedDivipola])

  // Municipios filtrados según departamento
  const displayedPilots = useMemo(() => {
    if (selectedDept === 'all') return PILOT_MUNICIPALITIES
    return PILOT_MUNICIPALITIES.filter((p) => p.departmentCode === selectedDept)
  }, [selectedDept])

  // Creencias eBDI agregadas para el municipio piloto activo
  const [pilotBeliefs, setPilotBeliefs] = useState<any | null>(null)

  useEffect(() => {
    if (!activeProfile?.divipola) return
    fetch(`${API_BASE}/atlas/pilots/${activeProfile.divipola}/beliefs`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setPilotBeliefs(data))
      .catch(() => setPilotBeliefs(null))
  }, [activeProfile?.divipola])

  // Función para agregar capas GeoJSON sobre el mapa base MapLibre
  const addMapLayers = (map: maplibregl.Map, currentDivipola: string, currentDept: '13' | '70' | 'all' = '13') => {
    if (map.getSource('montes-de-maria')) {
      if (map.getLayer('montes-de-maria-selected-line')) map.removeLayer('montes-de-maria-selected-line')
      if (map.getLayer('montes-de-maria-line')) map.removeLayer('montes-de-maria-line')
      if (map.getLayer('montes-de-maria-selected-fill')) map.removeLayer('montes-de-maria-selected-fill')
      if (map.getLayer('montes-de-maria-fill')) map.removeLayer('montes-de-maria-fill')
      map.removeSource('montes-de-maria')
    }

    map.addSource('montes-de-maria', {
      type: 'geojson',
      data: '/data/dane_mgn_montes_de_maria.json',
    })

    const deptFilter: any = currentDept === 'all'
      ? ['has', 'divipola']
      : ['==', ['get', 'department_code'], currentDept]

    // 1. Relleno semi-transparente para los municipios del departamento seleccionado
    map.addLayer({
      id: 'montes-de-maria-fill',
      type: 'fill',
      source: 'montes-de-maria',
      filter: deptFilter,
      paint: {
        'fill-color': [
          'match',
          ['get', 'department_code'],
          '13', '#2563eb',
          '#0d9488',
        ],
        'fill-opacity': 0.42,
      },
    })

    // 2. Relleno destacado del municipio seleccionado
    map.addLayer({
      id: 'montes-de-maria-selected-fill',
      type: 'fill',
      source: 'montes-de-maria',
      filter: ['==', ['get', 'divipola'], currentDivipola],
      paint: {
        'fill-color': '#0066cc',
        'fill-opacity': 0.78,
      },
    })

    // 3. Bordes vectoriales blancos nítidos para los municipios del departamento seleccionado
    map.addLayer({
      id: 'montes-de-maria-line',
      type: 'line',
      source: 'montes-de-maria',
      filter: deptFilter,
      paint: {
        'line-color': '#ffffff',
        'line-width': 2.0,
      },
    })

    // 4. Borde reforzado para el seleccionado
    map.addLayer({
      id: 'montes-de-maria-selected-line',
      type: 'line',
      source: 'montes-de-maria',
      filter: ['==', ['get', 'divipola'], currentDivipola],
      paint: {
        'line-color': '#002244',
        'line-width': 4.5,
      },
    })

    // Interacción al hacer clic en un polígono del mapa
    map.on('click', 'montes-de-maria-fill', (e: any) => {
      if (e.features && e.features[0]) {
        const code = e.features[0].properties.divipola
        handleSelectMunicipio(code)
      }
    })

    map.on('mouseenter', 'montes-de-maria-fill', () => {
      map.getCanvas().style.cursor = 'pointer'
    })

    map.on('mouseleave', 'montes-de-maria-fill', () => {
      map.getCanvas().style.cursor = ''
    })
  }

  // Crear o actualizar marcadores HTML interactivos sobre el mapa
  const renderMarkers = (map: maplibregl.Map, currentDivipola: string) => {
    // Limpiar marcadores previos
    Object.values(markersRef.current).forEach((m) => m.remove())
    markersRef.current = {}

    displayedPilots.forEach((pilot) => {
      const isSelected = pilot.divipola === currentDivipola

      const el = document.createElement('div')
      el.className = 'cursor-pointer flex flex-col items-center transition-all duration-300'
      el.style.transform = isSelected ? 'scale(1.15)' : 'scale(1.0)'

      el.innerHTML = `
        <div class="px-3 py-1 rounded-full text-[12px] font-bold shadow-xl flex items-center gap-1.5 transition-all duration-200 ${
          isSelected
            ? 'bg-[#0066cc] text-white ring-4 ring-[#0066cc]/30 shadow-[#0066cc]/50 scale-105'
            : 'bg-white/95 text-[#1d1d1f] border border-black/15 hover:bg-white hover:border-[#0066cc] hover:scale-105 shadow-md'
        }">
          <span class="w-2.5 h-2.5 rounded-full ${isSelected ? 'bg-white animate-pulse' : 'bg-[#34c759]'}"></span>
          <span>${pilot.name}</span>
          <span class="text-[10px] opacity-75 font-mono">#${pilot.pilotRank}</span>
        </div>
        <div class="w-2.5 h-2.5 ${isSelected ? 'bg-[#0066cc]' : 'bg-white/95 border-r border-b border-black/15'} rotate-45 -mt-1 shadow-xs"></div>
      `

      el.addEventListener('click', (e) => {
        e.stopPropagation()
        handleSelectMunicipio(pilot.divipola)
      })

      const marker = new maplibregl.Marker({ element: el, anchor: 'bottom' })
        .setLngLat([pilot.lon, pilot.lat])
        .addTo(map)

      markersRef.current[pilot.divipola] = marker
    })
  }

  // Inicialización de MapLibre GL JS con mapa real
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return

    try {
      const MapConstructor = maplibregl.Map
      if (!MapConstructor) throw new Error('MapLibre constructor no disponible')

      const map = new MapConstructor({
        container: mapContainer.current,
        style: BASE_STYLES[baseStyle].style,
        center: [activeProfile.lon, activeProfile.lat],
        zoom: 9.3,
      })

      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

      const handleReady = () => {
        setMapLoaded(true)
        addMapLayers(map, selectedDivipola, selectedDept)
        renderMarkers(map, selectedDivipola)
      }

      map.on('style.load', handleReady)
      map.on('load', handleReady)

      map.on('error', (err) => {
        console.warn('MapLibre evento de carga:', err)
        setMapLoaded(true)
      })

      setTimeout(() => {
        try {
          map.resize()
          setMapLoaded(true)
        } catch {
          // ignore
        }
      }, 200)

      mapRef.current = map

      const currentPopup = popupRef.current
      const currentMarkers = markersRef.current

      return () => {
        Object.values(currentMarkers).forEach((m) => m.remove())
        markersRef.current = {}
        if (currentPopup) currentPopup.remove()
        map.remove()
        mapRef.current = null
      }
    } catch (e) {
      console.warn('MapLibre WebGL falló al iniciar:', e)
      // oxlint-disable-next-line react/set-state-in-effect
      setMapLoaded(true)
    }
    // oxlint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Cambio de estilo base de mapa en caliente
  const handleChangeBaseStyle = (newStyleId: BaseStyleId) => {
    setBaseStyle(newStyleId)
    const map = mapRef.current
    if (map) {
      setMapLoaded(false)
      map.setStyle(BASE_STYLES[newStyleId].style)
      map.once('style.load', () => {
        setMapLoaded(true)
        addMapLayers(map, selectedDivipola, selectedDept)
        renderMarkers(map, selectedDivipola)
      })
    }
  }

  // Actualizar cámara, filtros de polígonos y marcadores reactivos al seleccionar un municipio o departamento
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapLoaded) return

    // Filtro departamental para polígonos: Si se selecciona Bolívar, solo muestra Bolívar; si Sucre, solo Sucre; si Todos, muestra todos.
    const deptFilter: any = selectedDept === 'all'
      ? ['has', 'divipola']
      : ['==', ['get', 'department_code'], selectedDept]

    if (map.getLayer('montes-de-maria-fill')) {
      map.setFilter('montes-de-maria-fill', deptFilter)
    }

    if (map.getLayer('montes-de-maria-line')) {
      map.setFilter('montes-de-maria-line', deptFilter)
    }

    // Actualizar filtros rápidos de selección
    if (map.getLayer('montes-de-maria-selected-fill')) {
      map.setFilter('montes-de-maria-selected-fill', ['==', ['get', 'divipola'], selectedDivipola])
    }

    if (map.getLayer('montes-de-maria-selected-line')) {
      map.setFilter('montes-de-maria-selected-line', ['==', ['get', 'divipola'], selectedDivipola])
    }

    // Actualizar color base si cambia el tema coroplético
    if (map.getLayer('montes-de-maria-fill')) {
      const isClimate = choroplethTheme === 'climate'

      map.setPaintProperty('montes-de-maria-fill', 'fill-color', isClimate
        ? ['match', ['get', 'divipola'], '13442', '#e11d48', '70717', '#e11d48', '#d97706']
        : ['match', ['get', 'department_code'], '13', '#2563eb', '#0d9488']
      )
    }

    // Actualizar marcadores interactivos
    renderMarkers(map, selectedDivipola)

    // Encuadre geodésico suave hacia el polígono real del municipio seleccionado
    try {
      if (activeProfile.bbox) {
        const [minX, minY, maxX, maxY] = activeProfile.bbox
        map.fitBounds(
          [[minX, minY], [maxX, maxY]],
          {
            padding: 55,
            maxZoom: 10.5,
            duration: 1200,
          }
        )
      } else {
        map.flyTo({
          center: [activeProfile.lon, activeProfile.lat],
          zoom: 9.6,
          speed: 1.2,
          curve: 1.3,
        })
      }
    } catch {
      // ignore
    }
    // oxlint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDivipola, selectedDept, mapLoaded, activeProfile, choroplethTheme, displayedPilots])

  const handleSelectMunicipio = (divipola: string) => {
    setSelectedDivipola(divipola)
    const prof = PILOT_MUNICIPALITIES.find((p) => p.divipola === divipola)
    if (prof && selectedDept !== 'all' && selectedDept !== prof.departmentCode) {
      setSelectedDept(prof.departmentCode)
    }
  }

  const handleSelectDepartment = (dept: '13' | '70' | 'all') => {
    setSelectedDept(dept)
    if (dept !== 'all') {
      const activeInDept = PILOT_MUNICIPALITIES.filter((p) => p.departmentCode === dept)
      const currentInDept = activeInDept.some((p) => p.divipola === selectedDivipola)
      if (!currentInDept && activeInDept.length > 0) {
        setSelectedDivipola(activeInDept[0].divipola)
      }
    }
  }

  const toggleApproval = (id: string) => {
    setApprovedDocs((prev) => ({
      ...prev,
      [id]: !prev[id],
    }))
  }

  return (
    <div className="flex flex-col gap-8 p-6 md:p-8 max-w-[1520px] mx-auto text-[#1d1d1f] font-sans antialiased">
      {/* 1. Header de Precisión e Inteligencia Territorial */}
      <header className="flex flex-col gap-4 border-b border-black/[0.08] pb-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Breadcrumbs de Navegación Institucional */}
          <div className="flex items-center gap-2 text-xs text-[#86868b] font-medium">
            <span className="flex items-center gap-1.5 text-[#1d1d1f] font-semibold">
              <Compass className="w-3.5 h-3.5 text-[#0066cc]" />
              Atlas de Política Territorial
            </span>
            <ChevronRight className="w-3.5 h-3.5 text-[#86868b]" />
            <span>Subregión Montes de María PDET (Cód. 01)</span>
            <ChevronRight className="w-3.5 h-3.5 text-[#86868b]" />
            <span className="text-[#0066cc] font-semibold">{activeProfile.name}</span>
          </div>

          {/* Badges de Soberanía e Invariantes */}
          <div className="flex items-center gap-2 flex-wrap text-xs">
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#34c759]/10 text-[#248a3d] font-semibold border border-[#34c759]/20">
              <ShieldCheck className="w-3.5 h-3.5" />
              DANE MGN 2024
            </span>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#0066cc]/10 text-[#0066cc] font-semibold border border-[#0066cc]/20">
              <Building2 className="w-3.5 h-3.5" />
              PIDARET Ord. 323/2021
            </span>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-black/[0.05] text-[#1d1d1f] font-mono">
              <Hash className="w-3.5 h-3.5 text-[#86868b]" />
              SHA-256 Validado
            </span>
          </div>
        </div>

        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-semibold tracking-[-0.03em] text-[#1d1d1f]">
              Consola Geoespacial de Instrumentos Territoriales
            </h1>
            <p className="text-[15px] text-[#6e6e73] mt-1 max-w-3xl leading-relaxed">
              Cartografía interactiva real con polígonos DANE MGN e indicativos municipales interactivos.
              Vinculación determinista a instrumentos normativos en cascada para la calibración del agente eBDI.
            </p>
          </div>

          <div className="bg-[#f5f5f7] p-1.5 rounded-2xl border border-black/[0.06] flex items-center gap-3 shrink-0 self-start md:self-auto">
            <div className="bg-white px-3.5 py-2 rounded-xl shadow-xs">
              <span className="text-[10px] uppercase tracking-wider text-[#86868b] font-semibold block">
                Municipio Activo
              </span>
              <span className="text-sm font-semibold text-[#1d1d1f]">{activeProfile.name}</span>
            </div>
            <div className="bg-white px-3.5 py-2 rounded-xl shadow-xs font-mono text-center">
              <span className="text-[10px] uppercase tracking-wider text-[#86868b] font-sans font-semibold block">
                DIVIPOLA
              </span>
              <span className="text-sm font-semibold text-[#0066cc]">{activeProfile.divipola}</span>
            </div>
          </div>
        </div>
      </header>

      {/* 2. Mesa de Trabajo Principal (Split-Pane Intelligence Workbench) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* PANEL IZQUIERDO (4 cols): Directorio de Pilotos y Ficha Territorial */}
        <div className="lg:col-span-4 flex flex-col gap-5">
          {/* Tarjeta 1: Selector de Pilotos */}
          <div className="bg-[#f5f5f7] p-2.5 rounded-[1.75rem] border border-black/[0.06] shadow-sm flex flex-col">
            <div className="bg-white rounded-[calc(1.75rem-0.625rem)] p-4 sm:p-5 shadow-xs flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-black/[0.05] pb-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-[#86868b] flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-[#0066cc]" />
                  Municipios Piloto DANE
                </span>
                <span className="text-xs font-mono text-[#86868b]">
                  {displayedPilots.length} de {PILOT_MUNICIPALITIES.length}
                </span>
              </div>

              {/* Segmented Filter Pills */}
              <div className="bg-[#f5f5f7] p-1 rounded-full border border-black/[0.04] flex gap-1">
                <button
                  type="button"
                  onClick={() => handleSelectDepartment('13')}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-full transition-all ${
                    selectedDept === '13'
                      ? 'bg-white text-[#1d1d1f] shadow-xs'
                      : 'text-[#6e6e73] hover:text-[#1d1d1f]'
                  }`}
                >
                  Bolívar ({PILOT_MUNICIPALITIES.filter((p) => p.departmentCode === '13').length})
                </button>
                <button
                  type="button"
                  onClick={() => handleSelectDepartment('70')}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-full transition-all ${
                    selectedDept === '70'
                      ? 'bg-white text-[#1d1d1f] shadow-xs'
                      : 'text-[#6e6e73] hover:text-[#1d1d1f]'
                  }`}
                >
                  Sucre ({PILOT_MUNICIPALITIES.filter((p) => p.departmentCode === '70').length})
                </button>
                <button
                  type="button"
                  onClick={() => handleSelectDepartment('all')}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-full transition-all ${
                    selectedDept === 'all'
                      ? 'bg-white text-[#1d1d1f] shadow-xs'
                      : 'text-[#6e6e73] hover:text-[#1d1d1f]'
                  }`}
                >
                  Todos ({PILOT_MUNICIPALITIES.length})
                </button>
              </div>

              {/* Pilot Municipality Cards List */}
              <div className="flex flex-col gap-2 max-h-[380px] overflow-y-auto pr-1">
                {displayedPilots.map((p) => {
                  const isSelected = selectedDivipola === p.divipola

                  return (
                    <button
                      key={p.divipola}
                      type="button"
                      onClick={() => handleSelectMunicipio(p.divipola)}
                      className={`text-left p-3 rounded-xl border transition-all duration-200 flex items-center justify-between gap-3 group ${
                        isSelected
                          ? 'bg-[#0066cc]/[0.05] border-[#0066cc] shadow-xs ring-1 ring-[#0066cc]'
                          : 'bg-[#fafafc] hover:bg-white border-black/[0.06] hover:border-black/[0.12]'
                      }`}
                    >
                      <div className="flex flex-col gap-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[11px] font-semibold text-[#86868b]">
                            #{p.pilotRank} · {p.divipola}
                          </span>
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              isSelected ? 'bg-[#0066cc]' : 'bg-[#34c759]'
                            }`}
                          />
                        </div>
                        <h4
                          className={`text-sm font-semibold truncate ${
                            isSelected ? 'text-[#0066cc]' : 'text-[#1d1d1f]'
                          }`}
                        >
                          {p.name}
                        </h4>
                        <div className="flex items-center gap-1.5 text-[11px] text-[#86868b] truncate">
                          <span>{p.departmentName}</span>
                          <span>·</span>
                          <span className="truncate">{p.dominantCrops[0]}</span>
                        </div>
                      </div>

                      <div className="shrink-0 flex items-center gap-1.5">
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                            p.climateVulnerability === 'Extrema'
                              ? 'bg-[#ff3b30]/10 text-[#d70015]'
                              : 'bg-[#ff9500]/10 text-[#c93400]'
                          }`}
                        >
                          {p.climateVulnerability}
                        </span>
                        <ChevronRight
                          className={`w-4 h-4 transition-transform ${
                            isSelected ? 'text-[#0066cc] translate-x-0.5' : 'text-[#86868b]'
                          }`}
                        />
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Tarjeta 2: Ficha Agroclimática Territorial */}
          <div className="bg-[#f5f5f7] p-2.5 rounded-[1.75rem] border border-black/[0.06] shadow-sm flex flex-col flex-1">
            <div className="bg-white rounded-[calc(1.75rem-0.625rem)] p-4 sm:p-5 shadow-xs flex flex-col gap-4 flex-1">
              <div className="flex items-center justify-between border-b border-black/[0.05] pb-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-[#86868b] flex items-center gap-1.5">
                  <Sprout className="w-3.5 h-3.5 text-[#34c759]" />
                  Perfil Territorial y Restricciones eBDI
                </span>
                <span className="text-xs font-semibold text-[#0066cc]">
                  {activeProfile.name}
                </span>
              </div>

              {/* Grid de Métricas */}
              <div className="grid grid-cols-2 gap-2.5 text-xs">
                <div className="bg-[#fafafc] p-3 rounded-xl border border-black/[0.04]">
                  <span className="text-[#86868b] text-[11px] block">Coordenadas DANE</span>
                  <span className="font-mono font-semibold text-[#1d1d1f]">
                    {activeProfile.lat.toFixed(2)}°, {activeProfile.lon.toFixed(2)}°
                  </span>
                </div>
                <div className="bg-[#fafafc] p-3 rounded-xl border border-black/[0.04]">
                  <span className="text-[#86868b] text-[11px] block">Área Territorial</span>
                  <span className="font-semibold text-[#1d1d1f]">
                    {(activeProfile.areaHectares / 1000).toFixed(1)}k ha
                  </span>
                </div>
                <div className="bg-[#fafafc] p-3 rounded-xl border border-black/[0.04]">
                  <span className="text-[#86868b] text-[11px] block">Altitud Media</span>
                  <span className="font-semibold text-[#1d1d1f]">
                    {activeProfile.altitudeMeters} msnm
                  </span>
                </div>
                <div className="bg-[#fafafc] p-3 rounded-xl border border-black/[0.04]">
                  <span className="text-[#86868b] text-[11px] block">Precipitación Anual</span>
                  <span className="font-semibold text-[#1d1d1f]">
                    {activeProfile.annualRainfallMm} mm/año
                  </span>
                </div>
                <div className="bg-[#fafafc] p-3 rounded-xl border border-black/[0.04]">
                  <span className="text-[#86868b] text-[11px] block">Geometría DANE MGN</span>
                  <span className="font-mono font-semibold text-[#248a3d]">
                    {activeProfile.vertices ? `${activeProfile.vertices} vértices` : 'Oficial 2024'}
                  </span>
                </div>
                <div className="bg-[#fafafc] p-3 rounded-xl border border-black/[0.04]">
                  <span className="text-[#86868b] text-[11px] block">Fuente Cartográfica</span>
                  <span className="font-semibold text-[#0066cc] truncate block" title={activeProfile.daneFuente}>
                    {activeProfile.daneFuente || 'DANE MGN 2024'}
                  </span>
                </div>
              </div>

              {/* Indicadores Decisionales Campesinos */}
              <div className="flex flex-col gap-2.5 pt-2 border-t border-black/[0.05]">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#6e6e73] flex items-center gap-1.5">
                    <CloudRain className="w-3.5 h-3.5 text-[#0066cc]" />
                    Vulnerabilidad a Sequía:
                  </span>
                  <span
                    className={`font-semibold px-2 py-0.5 rounded-md text-[11px] ${
                      activeProfile.climateVulnerability === 'Extrema'
                        ? 'bg-[#ff3b30]/10 text-[#d70015]'
                        : 'bg-[#ff9500]/10 text-[#c93400]'
                    }`}
                  >
                    {activeProfile.climateVulnerability}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#6e6e73] flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-[#34c759]" />
                    Restricción de Crédito:
                  </span>
                  <span className="font-semibold text-[#1d1d1f]">
                    {activeProfile.creditRestriction}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#6e6e73] flex items-center gap-1.5">
                    <Landmark className="w-3.5 h-3.5 text-[#5856d6]" />
                    Red Cooperativa:
                  </span>
                  <span className="font-semibold text-[#1d1d1f]">
                    {activeProfile.associativeCoverage}
                  </span>
                </div>
              </div>

              {/* Cultivos Campesinos */}
              <div className="flex flex-col gap-1.5 pt-2 border-t border-black/[0.05]">
                <span className="text-[11px] font-semibold text-[#86868b]">
                  Cultivos Campesinos Insignia:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {activeProfile.dominantCrops.map((c) => (
                    <span
                      key={c}
                      className="px-2 py-0.5 rounded-md bg-black/[0.04] text-[11px] font-medium text-[#1d1d1f]"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* PANEL DERECHO (8 cols): Lienzo Cartográfico Inmersivo */}
        <div className="lg:col-span-8 flex flex-col bg-[#f5f5f7] p-2.5 rounded-[1.75rem] border border-black/[0.06] shadow-sm">
          <div className="bg-white rounded-[calc(1.75rem-0.625rem)] overflow-hidden shadow-xs flex flex-col h-full min-h-[660px]">
            {/* Barra Superior del Mapa con Selectores de Estilo Real */}
            <div className="px-5 py-3.5 border-b border-black/[0.06] bg-[#fafafc] flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#0066cc]" />
                <span className="text-xs font-semibold text-[#1d1d1f]">
                  Cartografía Real con Polígonos DANE MGN 2024
                </span>
                <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-[#34c759]/15 text-[#248a3d] border border-[#34c759]/30">
                  15 Mpios PDET · EPSG:4326
                </span>
              </div>

              {/* Selectores de Estilo Base Real y Temas */}
              <div className="flex items-center gap-2 flex-wrap">
                {/* Estilos de Mapa Base Real (Esri Topo / Satelital / OSM) */}
                <div className="bg-[#f5f5f7] p-0.5 rounded-full border border-black/[0.04] flex items-center gap-1 text-[11px]">
                  {(['topo', 'satellite', 'osm'] as BaseStyleId[]).map((sid) => {
                    const styleMeta = BASE_STYLES[sid]
                    const IconComp = styleMeta.icon
                    const isActive = baseStyle === sid

                    return (
                      <button
                        key={sid}
                        type="button"
                        onClick={() => handleChangeBaseStyle(sid)}
                        className={`px-2.5 py-1 rounded-full font-medium transition-all flex items-center gap-1.5 ${
                          isActive
                            ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold'
                            : 'text-[#6e6e73] hover:text-[#1d1d1f]'
                        }`}
                      >
                        <IconComp className="w-3 h-3 text-[#0066cc]" />
                        <span>{styleMeta.name}</span>
                      </button>
                    )
                  })}
                </div>

                {/* Selector de Tema Coroplético */}
                <div className="bg-[#f5f5f7] p-0.5 rounded-full border border-black/[0.04] flex items-center gap-1 text-[11px]">
                  <button
                    type="button"
                    onClick={() => setChoroplethTheme('jurisdiction')}
                    className={`px-2.5 py-1 rounded-full font-medium transition-all ${
                      choroplethTheme === 'jurisdiction'
                        ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold'
                        : 'text-[#6e6e73] hover:text-[#1d1d1f]'
                    }`}
                  >
                    Jurisdicción
                  </button>
                  <button
                    type="button"
                    onClick={() => setChoroplethTheme('climate')}
                    className={`px-2.5 py-1 rounded-full font-medium transition-all ${
                      choroplethTheme === 'climate'
                        ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold'
                        : 'text-[#6e6e73] hover:text-[#1d1d1f]'
                    }`}
                  >
                    Riesgo Hídrico
                  </button>
                </div>
              </div>
            </div>

            {/* Lienzo Cartográfico */}
            <div className="relative w-full flex-1 bg-[#e2e8f0] overflow-hidden select-none min-h-[540px]">
              {/* Contenedor del Mapa MapLibre GL JS */}
              <div
                ref={mapContainer}
                className="absolute inset-0 w-full h-full z-10"
              />

              {/* HUD Flotante de Telemetría (Glassmorphic) */}
              <div className="absolute top-4 left-4 z-20 pointer-events-none">
                <div className="pointer-events-auto backdrop-blur-xl bg-white/90 border border-white/60 shadow-[0_8px_32px_rgba(0,0,0,0.08)] rounded-2xl p-4 min-w-[260px] flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[#86868b]">
                      Selección Activa
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#0066cc]/10 text-[#0066cc] font-semibold">
                      DIVIPOLA {activeProfile.divipola}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-semibold text-[#1d1d1f]">
                      {activeProfile.name}
                    </h3>
                    <p className="text-xs text-[#6e6e73]">
                      Depto. {activeProfile.departmentName} · Montes de María
                    </p>
                  </div>

                  <div className="flex items-center gap-2 pt-2 border-t border-black/[0.05] text-[11px] text-[#6e6e73]">
                    <span className="font-mono text-[#1d1d1f] font-medium">
                      {activeProfile.lat.toFixed(2)}°N, {activeProfile.lon.toFixed(2)}°W
                    </span>
                    <span>·</span>
                    <span className="font-medium text-[#1d1d1f]">
                      {activeProfile.altitudeMeters} msnm
                    </span>
                  </div>
                </div>
              </div>

              {/* Botón Flotante Reset / Centrar Cámara */}
              <div className="absolute bottom-4 right-4 z-20">
                <button
                  type="button"
                  onClick={() => {
                    const map = mapRef.current
                    if (map) {
                      map.flyTo({
                        center: [activeProfile.lon, activeProfile.lat],
                        zoom: 9.3,
                      })
                    }
                  }}
                  className="p-2.5 rounded-full bg-white/90 backdrop-blur-md border border-white/60 shadow-md text-[#1d1d1f] hover:bg-white active:scale-95 transition-all"
                  title="Restablecer centro cartográfico"
                >
                  <RotateCcw className="w-4 h-4 text-[#48484a]" />
                </button>
              </div>
            </div>

            {/* Barra Inferior de Leyenda Integrada */}
            <div className="px-5 py-3 bg-[#fafafc] border-t border-black/[0.06] flex flex-wrap items-center justify-between text-xs text-[#6e6e73] gap-3">
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-md bg-[#0066cc]" />
                  <span className="font-semibold text-[#1d1d1f]">
                    Seleccionado: {activeProfile.name}
                  </span>
                </div>

                {choroplethTheme === 'jurisdiction' ? (
                  <>
                    <div className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-md bg-[#2563eb]" />
                      <span>Bolívar (7 Mpios PDET)</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-md bg-[#0d9488]" />
                      <span>Sucre (8 Mpios PDET)</span>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-md bg-[#e11d48]" />
                      <span>Vulnerabilidad Extrema</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-md bg-[#d97706]" />
                      <span>Vulnerabilidad Alta</span>
                    </div>
                  </>
                )}
              </div>

              <div className="flex items-center gap-2 font-mono text-[11px] text-[#86868b]">
                <MapPin className="w-3.5 h-3.5 text-[#0066cc]" />
                <span>Indicativos interactivos en el mapa activos</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Panel Inferior: Instrumentos en Cascada y Cola de Revisión Humana */}
      <section className="bg-[#f5f5f7] p-2.5 sm:p-3 rounded-[2rem] border border-black/[0.06] shadow-sm flex flex-col gap-6">
        <div className="bg-white rounded-[calc(2rem-0.625rem)] p-6 sm:p-8 shadow-xs flex flex-col gap-6">
          {/* Navegación por Pestañas */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-black/[0.06] pb-4">
            <div className="bg-[#f5f5f7] p-1 rounded-full border border-black/[0.04] inline-flex gap-1 self-start">
              <button
                type="button"
                onClick={() => setActiveTab('instruments')}
                className={`px-4 py-2 rounded-full text-xs font-semibold transition-all ${
                  activeTab === 'instruments'
                    ? 'bg-white text-[#1d1d1f] shadow-xs'
                    : 'text-[#6e6e73] hover:text-[#1d1d1f]'
                }`}
              >
                Instrumentos en Cascada ({activeProfile.instruments.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('queue')}
                className={`px-4 py-2 rounded-full text-xs font-semibold transition-all ${
                  activeTab === 'queue'
                    ? 'bg-white text-[#1d1d1f] shadow-xs'
                    : 'text-[#6e6e73] hover:text-[#1d1d1f]'
                }`}
              >
                Revisión Contextual Cuarentena (AT-1)
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('agronomy')}
                className={`px-4 py-2 rounded-full text-xs font-semibold transition-all ${
                  activeTab === 'agronomy'
                    ? 'bg-white text-[#1d1d1f] shadow-xs'
                    : 'text-[#6e6e73] hover:text-[#1d1d1f]'
                }`}
              >
                Dilemas Agronómicos eBDI
              </button>
            </div>

            <div className="text-xs text-[#86868b] flex items-center gap-1.5 font-mono">
              <BookOpen className="w-3.5 h-3.5 text-[#0066cc]" />
              <span>Extracción 100% Local · SHA-256 Verificado</span>
            </div>
          </div>

          {/* TAB 1: Cascada Normativa Timeline Rail */}
          {activeTab === 'instruments' && (
            <div className="flex flex-col gap-5">
              <p className="text-xs text-[#6e6e73] leading-relaxed">
                Jerarquía normativa aplicable a <strong>{activeProfile.name}</strong>. Cada nivel restringe o
                habilita los objetivos declarativos del agente campesino en el simulador eBDI:
              </p>

              {pilotBeliefs && pilotBeliefs.total_applicable_beliefs > 0 && (
                <div className="bg-[#248a3d]/[0.08] p-3.5 rounded-2xl border border-[#248a3d]/20 flex items-center justify-between gap-3 text-xs flex-wrap">
                  <div className="flex items-center gap-2.5">
                    <Brain className="w-4 h-4 text-[#248a3d] shrink-0" />
                    <span className="font-semibold text-[#1d1d1f]">
                      {pilotBeliefs.total_applicable_beliefs} Creencias eBDI Heredadas desde Instrumentos Aprobados
                    </span>
                    <span className="text-gray-500 hidden sm:inline">
                      (Fuentes: {pilotBeliefs.contributing_sources.join(', ')})
                    </span>
                  </div>
                  <span className="font-mono text-[11px] bg-white px-2.5 py-0.5 rounded-md text-[#248a3d] font-bold border border-[#248a3d]/30">
                    ai/gemma4:E4B
                  </span>
                </div>
              )}

              <div className="relative flex flex-col gap-6 pl-4 sm:pl-6 before:absolute before:left-2 before:top-3 before:bottom-3 before:w-0.5 before:bg-black/[0.08]">
                {activeProfile.instruments.map((inst) => {
                  const isApproved = approvedDocs[inst.instrument_id] !== false

                  let levelBadge = 'Nación'
                  let levelColor = 'bg-[#ff9500]/10 text-[#c93400] border-[#ff9500]/30'
                  if (inst.level === 'departamento') {
                    levelBadge = `Departamento (${activeProfile.departmentName})`
                    levelColor = 'bg-[#34c759]/10 text-[#248a3d] border-[#34c759]/30'
                  } else if (inst.level === 'subregion_pdet') {
                    levelBadge = 'Subregión PDET'
                    levelColor = 'bg-[#5856d6]/10 text-[#4342a8] border-[#5856d6]/30'
                  } else if (inst.level === 'municipio') {
                    levelBadge = `Municipio (${activeProfile.name})`
                    levelColor = 'bg-[#0066cc]/10 text-[#0066cc] border-[#0066cc]/30'
                  }

                  return (
                    <div
                      key={inst.instrument_id}
                      className="relative bg-[#fafafc] hover:bg-white p-5 rounded-2xl border border-black/[0.06] hover:shadow-xs transition-all flex flex-col gap-3 group"
                    >
                      {/* Nodo sobre el riel visual */}
                      <div className="absolute -left-[1.35rem] sm:-left-[1.85rem] top-6 w-3 h-3 rounded-full bg-white border-2 border-[#0066cc]" />

                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span
                            className={`text-[11px] font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${levelColor}`}
                          >
                            {levelBadge}
                          </span>
                          <span className="text-xs font-semibold text-[#1d1d1f]">
                            {inst.adoption_norm}
                          </span>
                          <span className="text-xs text-[#86868b]">
                            ({inst.validity_start_year} - {inst.validity_end_year || 'vigente'})
                          </span>
                        </div>

                        <button
                          type="button"
                          onClick={() => toggleApproval(inst.instrument_id)}
                          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-all self-start sm:self-auto ${
                            isApproved
                              ? 'bg-[#34c759]/10 text-[#248a3d] hover:bg-[#34c759]/20'
                              : 'bg-[#ff3b30]/10 text-[#d70015] hover:bg-[#ff3b30]/20'
                          }`}
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          {isApproved ? 'Aprobado para Contexto' : 'En Observación'}
                        </button>
                      </div>

                      <h4 className="text-base font-semibold text-[#1d1d1f]">{inst.name}</h4>
                      <p className="text-xs text-[#6e6e73]">
                        Entidad Emisora: {inst.issuing_entity}
                      </p>

                      <blockquote className="border-l-2 border-[#0066cc] bg-[#f5f5f7]/60 pl-3.5 py-2 pr-3 rounded-r-xl text-xs text-[#333336] italic leading-relaxed">
                        "{inst.official_excerpt}"
                      </blockquote>

                      <div className="flex items-center justify-between pt-2 border-t border-black/[0.04] text-[11px] text-[#86868b] flex-wrap gap-2">
                        <div className="flex items-center gap-1.5 font-mono">
                          <Hash className="w-3 h-3 text-[#86868b]" />
                          <span>sha256:{inst.sha256.substring(0, 16)}...</span>
                        </div>
                        <span className="text-xs font-medium text-[#0066cc]">
                          Eje: {inst.pillar_focus}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* TAB 2: Cola de Aprobación Humana y Revisión Contextual de Cuarentena */}
          {activeTab === 'queue' && <QuarantineReviewView />}

          {/* TAB 3: Dilemas Agronómicos eBDI */}
          {activeTab === 'agronomy' && (
            <div className="flex flex-col gap-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-[#fafafc] p-5 rounded-2xl border border-black/[0.06] flex flex-col gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#ff9500]/10 flex items-center justify-center text-[#c93400]">
                    <Droplets className="w-4 h-4" />
                  </div>
                  <h4 className="text-sm font-semibold text-[#1d1d1f]">
                    Dilema 1: Agua vs. Supervivencia
                  </h4>
                  <p className="text-xs text-[#6e6e73] leading-relaxed">
                    Con precipitación de {activeProfile.annualRainfallMm} mm/año y anomalías climáticas,
                    el agente entra en tensión entre reservar agua para autoconsumo o regar parcelas de {activeProfile.dominantCrops[0]}.
                  </p>
                </div>

                <div className="bg-[#fafafc] p-5 rounded-2xl border border-black/[0.06] flex flex-col gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#34c759]/10 flex items-center justify-center text-[#248a3d]">
                    <Landmark className="w-4 h-4" />
                  </div>
                  <h4 className="text-sm font-semibold text-[#1d1d1f]">
                    Dilema 2: Venta Anticipada vs. Cooperativa
                  </h4>
                  <p className="text-xs text-[#6e6e73] leading-relaxed">
                    Con cobertura asociativa {activeProfile.associativeCoverage.toLowerCase()},
                    el pequeño productor se enfrenta al intermediario local frente al compromiso con la asociación campesina.
                  </p>
                </div>

                <div className="bg-[#fafafc] p-5 rounded-2xl border border-black/[0.06] flex flex-col gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#0066cc]/10 flex items-center justify-center text-[#0066cc]">
                    <Cpu className="w-4 h-4" />
                  </div>
                  <h4 className="text-sm font-semibold text-[#1d1d1f]">
                    Impacto en Creencias (eBDI)
                  </h4>
                  <p className="text-xs text-[#6e6e73] leading-relaxed">
                    La política pública ({activeProfile.instruments[1]?.adoption_norm}) altera los umbrales de riesgo,
                    modificando la creencia sobre apoyo institucional y provisión de insumos.
                  </p>
                </div>
              </div>

              {/* Creencias Territoriales Reales Extraídas para este Municipio */}
              {pilotBeliefs && pilotBeliefs.beliefs && pilotBeliefs.beliefs.length > 0 && (
                <div className="flex flex-col gap-3 pt-4 border-t border-black/[0.06]">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <Brain className="w-4 h-4 text-[#248a3d]" />
                      <h4 className="text-sm font-bold text-[#1d1d1f]">
                        Creencias Territoriales Reales Heredadas para {activeProfile.name}
                      </h4>
                    </div>
                    <span className="text-xs font-mono bg-emerald-50 text-emerald-800 px-2.5 py-0.5 rounded-full border border-emerald-200">
                      {pilotBeliefs.beliefs.length} Proposiciones Validadas (ai/gemma4:E4B)
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {pilotBeliefs.beliefs.map((b: any, idx: number) => (
                      <div
                        key={b.belief_id || idx}
                        className="p-4 rounded-2xl bg-[#fafafc] border border-black/[0.06] flex flex-col gap-2.5 text-xs shadow-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-[#0066cc] uppercase text-[10px] tracking-wider">
                            {b.pillar}
                          </span>
                          <span className="font-mono text-gray-500 text-[10px]">
                            Confianza: {(b.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <h5 className="font-bold text-[#1d1d1f] text-xs">{b.topic}</h5>
                        <p className="text-[#333336] bg-white p-2.5 rounded-xl border border-black/[0.04] leading-relaxed">
                          {b.ebdi_belief_assertion}
                        </p>
                        <blockquote className="border-l-2 border-[#248a3d] pl-2.5 text-[11px] text-gray-600 italic">
                          "{b.raw_excerpt.length > 140 ? b.raw_excerpt.slice(0, 140) + '...' : b.raw_excerpt}"
                        </blockquote>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
