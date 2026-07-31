import { useEffect, useRef, useState } from 'react'
import jsQR from 'jsqr'

type View = 'home' | 'operation' | 'children' | 'records' | 'line' | 'settings'
type Mode = '乗車' | '降車'
type Operator = { id:number; name:string; role:string }
type Attendance = { child_id:number; name:string; boarded_at:string|null; alighted_at:string|null; boarded_manually?:boolean; alighted_manually?:boolean }
type TripStatus = { trip_id:number; status:string; direction:string; route_name:string; vehicle_name:string; boarded:number; alighted:number; unconfirmed:number; tail_confirmed:boolean; third_party_confirmed:boolean; video_evidence_count?:number; latest_video_id?:number|null; latest_video_ai_status?:string|null; latest_video_ai_result?:string|null; children:Attendance[] }
type RosterChild = { id:number; name:string; class_name?:string|null }
type Route = { id:number; name:string; direction:string; vehicle_id:number|null; children:RosterChild[] }
type Vehicle = { id:number; name:string; plate_number?:string|null }
type Dashboard = { organization_name:string; date:string; today_trip_count:number; active_trip_count:number; completed_trip_count:number; unconfirmed_count:number }
type OfflineEvent = { client_event_id:string; trip_id:number; qr_token:string; event_type:Mode }
type TripListItem = TripStatus & { started_at:string; completed_at:string|null }
type TripRecord = { trip: TripStatus & { route_name:string; vehicle_name:string; direction:string; started_at:string; completed_at:string|null }; attendance:Array<{child_id:number;name:string;class_name:string|null;boarded_at:string|null;boarded_by:string|null;alighted_at:string|null;alighted_by:string|null}>; safety_checks:Array<{id:number;check_type:string;staff_name:string;latitude:string|null;longitude:string|null;created_at:string}>; videos?:VideoEvidenceItem[] }
type VideoAnalysis = { id:number; ai_status:string; ai_result:string|null }
type AuditLog = { id:number; actor_id:number|null; action:string; resource_type:string; resource_id:string; detail:string; created_at:string }
type AuthBuilder = (init?:RequestInit) => RequestInit
type VideoEvidenceItem = { id:number; file_name:string; storage_key?:string; storage_path?:string; content_type?:string; ai_status:string; ai_result:string|null; created_at:string }
type SettingChild = { id:number; name:string; class_name:string|null; qr_token:string }
type SettingStaff = { id:number; name:string; role:"admin"|"operator"|"verifier"; is_active:boolean }
type OrganizationInfo = { id:number; name:string }
type GuardianChildLink = { id:number; name:string; relationship:string|null; notify_alighted:boolean }
type GuardianContact = { id:number; name:string|null; email:string; email_enabled:boolean; line_enabled:boolean; line_status:string; consented_at:string|null; is_active:boolean; children:GuardianChildLink[]; line_contact_active:boolean }
type NotificationItem = { id:number; guardian_name:string|null; channel:string; status:string; message:string; subject:string|null; attempt_count:number; next_attempt_at:string|null; provider_response:string|null; created_at:string; sent_at:string|null; template_key:string|null }
type LineLinkPreview = { request_id:number; status:string; expires_at:string; email_delivery_status:string; official_account_name:string; line_basic_id:string; line_link_url:string; line_link_message:string; qr_png_data_url:string }

const API = import.meta.env.DEV ? 'http://127.0.0.1:8000' : (import.meta.env.VITE_API_BASE_URL || '').trim()
const APP_ICON_SRC = `${import.meta.env.BASE_URL}icons/mamoru-bus-icon-192.png`
const OFFLINE_KEY = 'mamoru-bus-offline-events'
const CHILD_GROUPS = ['1号車ー先出し','1号車ー後出し','2号車ー先出し','2号車ー後出し']
const modeForTrip = (trip:TripStatus):Mode => trip.direction==='帰り' || (trip.children.length>0 && trip.boarded===trip.children.length) ? '降車' : '乗車'
const queue = (): OfflineEvent[] => JSON.parse(localStorage.getItem(OFFLINE_KEY) || '[]')
const saveQueue = (items: OfflineEvent[]) => localStorage.setItem(OFFLINE_KEY, JSON.stringify(items))
const routeVehicleName = (route:Route, vehicles:Vehicle[]) => vehicles.find(vehicle=>vehicle.id===route.vehicle_id)?.name || route.name
const vehicleOrder = (name:string) => Number(name.match(/\d+/)?.[0] || 9999)
const directionOrder = (direction:string) => direction==='往路' || direction==='行き' ? 0 : direction==='帰り' ? 1 : 2
const sortedRoutes = (routes:Route[], vehicles:Vehicle[]) => [...routes].sort((a,b)=>vehicleOrder(routeVehicleName(a,vehicles))-vehicleOrder(routeVehicleName(b,vehicles)) || directionOrder(a.direction)-directionOrder(b.direction) || routeVehicleName(a,vehicles).localeCompare(routeVehicleName(b,vehicles),'ja') || a.name.localeCompare(b.name,'ja'))
const messageOf = async (response:Response) => { try { const body = await response.json(); return body.detail || '記録を保存できませんでした' } catch { return '記録を保存できませんでした' } }
const fetchWithTimeout = async (url:string, init:RequestInit, timeoutMs:number, timeoutMessage:string) => {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try { return await fetch(url, {...init, signal: controller.signal}) }
  catch(error) { if(error instanceof DOMException && error.name==='AbortError') throw new Error(timeoutMessage); throw error }
  finally { window.clearTimeout(timer) }
}
const MIN_VIDEO_SECONDS = 5
const MAX_VIDEO_SECONDS = 30
const VIDEO_UPLOAD_TIMEOUT_MS = 120000
const AI_ANALYZE_TIMEOUT_MS = 30000

export default function App() {
  const [view,setView] = useState<View>('home')
  const [token,setToken] = useState<string|null>(localStorage.getItem('mamoru-bus-token'))
  const [operator,setOperator] = useState<Operator|null>(null)
  const [dashboard,setDashboard] = useState<Dashboard|null>(null)
  const [routes,setRoutes] = useState<Route[]>([])
  const [children,setChildren] = useState<RosterChild[]>([])
  const [vehicles,setVehicles] = useState<Vehicle[]>([])
  const [trip,setTrip] = useState<TripStatus|null>(null)
  const [mode,setMode] = useState<Mode>('乗車')
  const [scanner,setScanner] = useState<'child'|null>(null)
  const [message,setMessage] = useState('ログインして本日の状況を確認してください')
  const [offlineCount,setOfflineCount] = useState(queue().length)
  const [locationStatus,setLocationStatus] = useState('')
  const [videoRecorder,setVideoRecorder] = useState(false)
  const auth = (init:RequestInit={}) => ({...init, headers:{'Content-Type':'application/json', Authorization:`Bearer ${token}`,...(init.headers||{})}})
  const logout = () => { localStorage.removeItem('mamoru-bus-token'); setToken(null); setOperator(null); setTrip(null); setDashboard(null); setRoutes([]); setChildren([]); setView('home'); setMessage('ログアウトしました') }
  const loadDashboard = async () => { if (!token) return; const r = await fetch(`${API}/api/dashboard`,auth()); if (!r.ok) throw new Error(); setDashboard(await r.json()) }
  const loadBootstrap = async () => { const [routeResponse, vehicleResponse, childResponse] = await Promise.all([fetch(`${API}/api/bus-routes`,auth()), fetch(`${API}/api/vehicles`,auth()), fetch(`${API}/api/children`,auth())]); if (!routeResponse.ok || !vehicleResponse.ok || !childResponse.ok) throw new Error(); setRoutes(await routeResponse.json()); setVehicles(await vehicleResponse.json()); setChildren(await childResponse.json()) }
  const refresh = async (tripId:number) => { const r = await fetch(`${API}/api/trips/${tripId}/status`,auth()); if (!r.ok) throw new Error(await messageOf(r)); const current:TripStatus=await r.json(); setTrip(current); setMode(modeForTrip(current)); await loadDashboard() }
  const sync = async () => {
    if (!token || !queue().length || !navigator.onLine) return
    try { const r = await fetch(`${API}/api/sync`,auth({method:'POST',body:JSON.stringify({events:queue()})})); if (!r.ok) return; saveQueue([]); setOfflineCount(0); setMessage('端末に保留していた記録を同期しました'); if (trip) await refresh(trip.trip_id) } catch { /* 次回オンライン時に再試行 */ }
  }
  useEffect(() => {
    if (!token) return
    fetch(`${API}/api/auth/me`,auth()).then(async me => {
      if (!me.ok) throw new Error()
      setOperator(await me.json())
      try { await Promise.all([loadBootstrap(), loadDashboard()]); await sync() }
      catch { setMessage('一部の初期データを取得できませんでした。運行画面を開き直してください。') }
    }).catch(logout)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])
  useEffect(() => { const online = () => sync(); window.addEventListener('online',online); return () => window.removeEventListener('online',online) })
  const login = (staff:Operator, accessToken:string) => { localStorage.setItem('mamoru-bus-token',accessToken); setToken(accessToken); setOperator(staff); setMessage('ログインしました') }
  const openOperation = async () => {
    try { const r = await fetch(`${API}/api/trips?status_filter=運行中`,auth()); if (!r.ok) throw new Error(); const active = await r.json(); setView('operation'); if (active[0]) { setMode(active[0].direction==='帰り' ? '降車' : '乗車'); await refresh(active[0].trip_id); setMessage('進行中の送迎を表示しています') } else { setTrip(null); setMessage('バスと方向を選んで送迎を開始してください') } } catch { setMessage('進行中の送迎を取得できません。API接続を確認してください。') }
  }
  const leaveOperation = () => {
    setTrip(null)
    setView('home')
    setMessage('送迎を一時保存しました。運行中の送迎は「運行」または「記録」から再開できます。')
  }
  const cancelTripForReselection = async ():Promise<boolean> => {
    if (!trip) return false
    try {
      const r=await fetch(`${API}/api/trips/${trip.trip_id}/cancel`,auth({method:'POST'}))
      if(!r.ok) throw new Error(await messageOf(r))
      setTrip(null)
      setView('operation')
      await loadDashboard()
      setMessage('送迎を中止しました。バスを選び直してください。')
      return true
    } catch(error) {
      setMessage(error instanceof Error ? error.message : '送迎を中止できませんでした')
      return false
    }
  }
  const startTrip = async (route:Route) => {
    setMode(route.direction==='帰り' ? '降車' : '乗車')
    try { const r = await fetch(`${API}/api/trips`,auth({method:'POST',body:JSON.stringify({route_id:route.id,vehicle_id:route.vehicle_id,direction:route.direction})})); if (!r.ok) throw new Error(await messageOf(r)); const created = await r.json(); await refresh(created.id); setMessage(`${route.name} を開始しました。乗車確認を行ってください。`) } catch (error) { setMessage(error instanceof Error ? error.message : '便を開始できませんでした') }
  }
  const scanChild = async (qr:string) => {
    if (!trip) return
    try { const r = await fetch(`${API}/api/trips/${trip.trip_id}/scans`,auth({method:'POST',body:JSON.stringify({qr_token:qr.trim(),event_type:mode})})); if (!r.ok) throw new Error(await messageOf(r)); await refresh(trip.trip_id); setScanner(null); setMessage(`${mode}を記録しました`) }
    catch (error) {
      setScanner(null)
      if (!navigator.onLine) { const items=[...queue(),{client_event_id:crypto.randomUUID(),trip_id:trip.trip_id,qr_token:qr,event_type:mode}]; saveQueue(items); setOfflineCount(items.length); setMessage('オフラインのため、記録をこの端末に保留しました') }
      else setMessage(error instanceof Error ? error.message : 'QR記録を保存できませんでした')
    }
  }
  const manualAttendance = async (childId:number) => {
    if (!trip) return
    if (!window.confirm(`QRを使わずに${mode}を記録します。園児本人を目視で確認した場合だけ実行してください。\n\nこの操作は監査ログに「QRなし」として残ります。`)) return
    try {
      const r=await fetch(`${API}/api/trips/${trip.trip_id}/manual-attendance`,auth({method:'POST',body:JSON.stringify({child_id:childId,event_type:mode})}))
      if(!r.ok) throw new Error(await messageOf(r))
      await refresh(trip.trip_id)
      setMessage(`QRなしで${mode}を記録しました`)
    } catch(error) { setMessage(error instanceof Error ? error.message : 'QRなしの記録を保存できませんでした') }
  }
  const returnSafetyCheck = () => {
    if (!trip) return
    setLocationStatus('車内撮影を開始します')
    setVideoRecorder(true)
  }
  const uploadVehicleVideo = async (blob:Blob, durationSeconds:number) => {
    if (!trip) return
    const tripId = trip.trip_id
    const form = new FormData()
    const extension = blob.type.includes('mp4') ? 'mp4' : 'webm'
    form.append('file', blob, `vehicle-check-${tripId}-${new Date().toISOString().replace(/[:.]/g,'-')}.${extension}`)
    form.append('duration_seconds', String(durationSeconds))
    const headers:HeadersInit = token ? {Authorization:`Bearer ${token}`} : {}
    try {
      const uploaded = await fetchWithTimeout(`${API}/api/trips/${tripId}/videos`, {method:'POST', headers, body:form}, VIDEO_UPLOAD_TIMEOUT_MS, '動画の保存に時間がかかっています。通信状況を確認して、もう一度撮影してください。')
      if(!uploaded.ok) throw new Error(await messageOf(uploaded))
      const video = await uploaded.json() as {id:number}
      let aiMessage = ''
      try {
        const analyzed = await fetchWithTimeout(`${API}/api/videos/${video.id}/analyze`, auth({method:'POST'}), AI_ANALYZE_TIMEOUT_MS, 'AI補助確認が時間内に終わりませんでした')
        if(!analyzed.ok) throw new Error(await messageOf(analyzed))
        const result = await analyzed.json() as VideoAnalysis
        aiMessage = result.ai_result || ''
      } catch(error) {
        aiMessage = `AI補助だけ完了しませんでした（${error instanceof Error ? error.message : '通信エラー'}）。`
      }
      if (!trip.tail_confirmed) {
        let latitude:string|undefined, longitude:string|undefined
        if (navigator.geolocation) {
          try {
            const position = await new Promise<GeolocationPosition>((resolve,reject) => navigator.geolocation.getCurrentPosition(resolve,reject,{timeout:10000,enableHighAccuracy:true}))
            latitude=String(position.coords.latitude); longitude=String(position.coords.longitude)
          } catch {
            setLocationStatus('位置情報なしで記録します')
          }
        }
        const check = await fetch(`${API}/api/vehicle-checks`,auth({method:'POST',body:JSON.stringify({trip_id:tripId,check_type:'tail_qr',qr_token:'return-vehicle-check',latitude,longitude})}))
        if(!check.ok) throw new Error(await messageOf(check))
      }
      const completed = await fetch(`${API}/api/trips/${tripId}/complete`,auth({method:'POST'}))
      if(!completed.ok) throw new Error(await messageOf(completed))
      setVideoRecorder(false)
      setTrip(null)
      await loadDashboard()
      setLocationStatus('')
      setMessage(aiMessage ? `${durationSeconds}秒の車内撮影を動画1件として保存し、送迎を完了しました。${aiMessage}` : `${durationSeconds}秒の車内撮影を動画1件として保存し、送迎を完了しました。`)
    } catch(error) { setMessage(error instanceof Error ? error.message : '車内撮影または送迎完了を保存できませんでした'); throw error }
  }
  const approve = async (staffId:number,pin:string) => { if (!trip) return; try { const r=await fetch(`${API}/api/trips/${trip.trip_id}/third-party-approval`,auth({method:'POST',body:JSON.stringify({staff_id:staffId,pin})})); if(!r.ok) throw new Error(await messageOf(r)); await refresh(trip.trip_id); setMessage('第三者確認を記録しました。完了処理が可能です。') } catch(error) { setMessage(error instanceof Error ? error.message : '第三者確認を保存できませんでした') } }
  const resumeTrip = async (item:TripListItem) => { setMode(item.direction==='帰り' ? '降車' : '乗車'); setView('operation'); await refresh(item.trip_id); setMessage(`${item.vehicle_name}の送迎を再開しました`) }
  const updateRoster = async (childIds:number[]) => { if (!trip) return; try { const r=await fetch(`${API}/api/trips/${trip.trip_id}/roster`,auth({method:'PUT',body:JSON.stringify({child_ids:childIds})})); if(!r.ok) throw new Error(await messageOf(r)); await refresh(trip.trip_id); setMessage('当日の園児名簿を更新しました') } catch(error) { setMessage(error instanceof Error ? error.message : '当日の園児名簿を更新できませんでした') } }
  const complete = async () => { if (!trip) return; try { const r=await fetch(`${API}/api/trips/${trip.trip_id}/complete`,auth({method:'POST'})); if(!r.ok) throw new Error(await messageOf(r)); setTrip(null); await loadDashboard(); setMessage('便の安全確認が完了しました。次のバスを選んでください。') } catch(error) { setMessage(error instanceof Error ? error.message : '便を完了できませんでした') } }
  if (!operator) return <div className="app login-app"><header className="login-header"><img className="brand-icon brand-icon-login" src={APP_ICON_SRC} alt=""/><div><div className="login-eyebrow">送迎バス安全確認</div><strong>まもるバス</strong></div></header><main className="login-main"><Login onLogin={login}/></main></div>
  const content = view==='home' ? <Home dashboard={dashboard} onOperation={openOperation}/> : view==='operation' ? <Operation trip={trip} routes={routes} vehicles={vehicles} children={children} mode={mode} onRoster={updateRoster} onStart={startTrip} onLeave={leaveOperation} onCancel={cancelTripForReselection} onScan={()=>setScanner('child')} onManual={manualAttendance} onTail={returnSafetyCheck} onVideo={()=>setVideoRecorder(true)} locationStatus={locationStatus} onApprove={approve} onComplete={complete}/> : view==='children' ? <ChildrenPage operator={operator} auth={auth} onMessage={setMessage} onRefresh={loadBootstrap}/> : view==='records' ? <Records operator={operator} auth={auth} onMessage={setMessage} onResume={resumeTrip}/> : view==='line' ? <LineSettingsPage operator={operator} auth={auth} onMessage={setMessage} onRefresh={loadBootstrap}/> : <Settings operator={operator} auth={auth} onMessage={setMessage} onRefresh={loadBootstrap}/>
  return <div className="app"><header className="px-5 pt-5 pb-4 bg-white flex items-center justify-between gap-3"><div className="flex items-center gap-3 min-w-0"><img className="brand-icon" src={APP_ICON_SRC} alt=""/><div className="min-w-0"><div className="text-xs font-bold text-teal">送迎バス安全確認</div><b className="text-xl">まもるバス</b></div></div><button className="border-0 bg-white text-sm font-bold" onClick={logout}>{operator.name}</button></header><main className="app-main px-5">{offlineCount>0&&<button className="w-full rounded-xl bg-amber-100 p-3 text-sm font-bold text-amber-900" onClick={sync}>未同期の記録 {offlineCount} 件 — 同期する</button>}<section className="mt-3 rounded-2xl bg-sand p-4 border border-amber-100"><p className="m-0 text-sm">{message}</p></section>{content}</main><Nav active={view} onChange={setView}/> {scanner&&<Scanner title={`${mode}QRを読み取る`} onRead={scanChild} onClose={()=>setScanner(null)}/>} {videoRecorder&&trip&&<VehicleVideoRecorder trip={trip} onUpload={uploadVehicleVideo} onClose={()=>setVideoRecorder(false)}/>}</div>
}
function Home({dashboard,onOperation}:{dashboard:Dashboard|null;onOperation:()=>void}) { return <><section className="mt-4 rounded-3xl bg-teal p-5 text-white"><p className="m-0 text-sm opacity-85">{dashboard?.organization_name||'園'}</p><h1 className="mt-1 mb-2 text-2xl font-black">本日の送迎状況</h1><p className="m-0 text-sm">{dashboard?.date||'集計を読み込み中です'}</p></section><section className="grid grid-cols-3 gap-3 mt-4"><Metric label="本日の便" value={dashboard?.today_trip_count||0}/><Metric label="運行中" value={dashboard?.active_trip_count||0}/><Metric label="未確認" value={dashboard?.unconfirmed_count||0} danger={(dashboard?.unconfirmed_count||0)>0}/></section><section className="card mt-4 p-5"><h2 className="m-0 text-lg font-black">運行</h2><p className="text-sm text-slate-600">バスと「行き／帰り」を選んで開始、または進行中の送迎を再開します。</p><button className="big-action" onClick={onOperation}>運行画面を開く</button></section><section className="card mt-4 p-5"><h2 className="m-0 text-lg font-black">安全上の注意</h2><p className="mb-0 text-sm text-slate-600">未降車の園児が1人でもいる間は、車内撮影と完了はできません。必ず車内を目視で確認してください。</p></section></> }
function Metric({label,value,danger}:{label:string;value:number;danger?:boolean}) { return <section className="card p-3 text-center"><b className={'text-2xl '+(danger?'text-coral':'text-teal')}>{value}</b><br/><span className="text-xs">{label}</span></section> }
function Operation({trip,routes,vehicles,children,mode,onRoster,onStart,onLeave,onCancel,onScan,onManual,onTail,onVideo,locationStatus,onApprove,onComplete}:{trip:TripStatus|null;routes:Route[];vehicles:Vehicle[];children:RosterChild[];mode:Mode;onRoster:(ids:number[])=>void;onStart:(r:Route)=>void;onLeave:()=>void;onCancel:()=>Promise<boolean>;onScan:()=>void;onManual:(childId:number)=>void;onTail:()=>void;onVideo:()=>void;locationStatus:string;onApprove:(id:number,pin:string)=>void;onComplete:()=>void}) {
  const [editingRoster,setEditingRoster] = useState(false)
  const [confirmingCancel,setConfirmingCancel] = useState(false)
  const [cancelling,setCancelling] = useState(false)
  if (!trip || trip.status!=='運行中') return <section className="mt-4"><div><h1 className="m-0 text-xl font-black">運行</h1><p className="mt-1 text-sm text-slate-600">バスを選び、行き／帰りの確認を始めます。</p></div><section className="card mt-4 p-4"><h2 className="m-0 text-lg font-black">バスを選ぶ</h2><p className="mt-1 mb-2 text-sm text-slate-600">毎日使うバスと方向を選んでください。</p>{routes.length ? sortedRoutes(routes,vehicles).map(route => <button key={route.id} className="route-choice" onClick={()=>onStart(route)}><span className="route-icon">🚌</span><span><b>{routeVehicleName(route,vehicles)}</b><small>{route.direction==='帰り'?'帰り：園児を降ろす確認':'行き：園児が乗ったことを確認'}</small></span><span className="route-arrow">›</span></button>) : <p className="text-sm text-coral">登録済みのバスがありません。設定でバスを登録してください。</p>}</section></section>
  const remaining = mode==='乗車' ? Math.max(trip.children.length-trip.boarded,0) : Math.max(trip.unconfirmed,0)
  const allAlighted = mode==='降車' && trip.boarded===trip.children.length && trip.unconfirmed===0
  const actionLabel = mode==='乗車' ? '行きの乗車確認をする' : '帰りの降車確認をする'
  const confirmCancellation = async () => {
    setCancelling(true)
    if (!await onCancel()) setCancelling(false)
  }
  return <><div className="mt-4 grid grid-cols-2 gap-3"><button className="min-h-12 rounded-xl border border-red-300 bg-red-50 px-3 py-2 text-sm font-bold text-coral" onClick={()=>setConfirmingCancel(true)}>バスを選び直す</button><button className="min-h-12 rounded-xl border border-teal bg-white px-3 py-2 text-sm font-bold text-teal" onClick={onLeave}>一時保存してホームへ戻る</button></div>{confirmingCancel&&<section className="mt-3 rounded-2xl border-2 border-coral bg-red-50 p-4 text-red-900" role="alertdialog" aria-labelledby="cancel-trip-title"><h2 id="cancel-trip-title" className="m-0 text-base font-black">この送迎を中止して選び直しますか？</h2><p className="mb-0 mt-2 text-sm leading-6">乗降・車内撮影をまだ記録していない場合だけ、バス選択へ戻れます。</p><div className="mt-3 grid grid-cols-2 gap-2"><button className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 font-bold text-slate-700 disabled:opacity-50" disabled={cancelling} onClick={()=>setConfirmingCancel(false)}>戻る</button><button className="min-h-11 rounded-xl border-0 bg-coral px-3 font-bold text-white disabled:opacity-50" disabled={cancelling} onClick={()=>void confirmCancellation()}>{cancelling?'処理中…':'中止して選び直す'}</button></div></section>}<section className="mt-3 rounded-3xl bg-teal p-5 text-white"><p className="m-0 text-sm opacity-85">{trip.vehicle_name}・運行中</p><h1 className="mt-1 mb-1 text-2xl font-black">{mode==='乗車'?'行き':'帰り'}の送迎</h1><p className="m-0 text-sm">QRを読み取り、園児の確認をします</p></section><section className="card mt-4 p-4"><div className="flex justify-between items-center"><div><h2 className="m-0 text-lg font-black">確認状況</h2><p className="m-0 mt-1 text-sm text-slate-600">{mode==='乗車'?'乗車した園児':'降車を確認した園児'}を記録します</p></div><span className="badge bg-mint text-teal">{mode==='乗車'?'行き':'帰り'}</span></div><div className="grid grid-cols-3 text-center mt-3"><Metric label="確認済み" value={mode==='乗車'?trip.boarded:trip.alighted}/><Metric label="対象" value={trip.children.length}/><Metric label="未確認" value={remaining} danger={remaining>0}/></div></section>{mode==='降車'&&trip.unconfirmed>0&&<section className="mt-4 rounded-2xl border-2 border-coral bg-red-50 p-4 text-red-800"><b>未降車の園児が {trip.unconfirmed} 人います</b><p className="m-0 mt-1 text-sm">降車確認が終わるまで、安全確認・完了は行えません。</p></section>}<button className="big-action mt-4" onClick={onScan}>{actionLabel}</button><section className="card mt-4 overflow-hidden"><div className="p-4 flex justify-between items-center"><div><h2 className="m-0 text-lg font-black">このバスの園児</h2><p className="m-0 mt-1 text-sm text-slate-600">通常名簿をもとにしています。</p></div><button className="border-0 bg-white text-sm font-bold text-teal" onClick={()=>setEditingRoster(!editingRoster)}>{editingRoster?'閉じる':'当日変更'}</button></div>{editingRoster&&<TripRosterEditor children={children} selectedIds={trip.children.map(x=>x.child_id)} onSave={ids=>{onRoster(ids);setEditingRoster(false)}}/>}{trip.children.length===0?<p className="px-4 pb-4 text-sm text-slate-600">まだ確認された園児はいません。</p>:trip.children.map(x=><div className="px-4 py-3 border-t flex justify-between" key={x.child_id}><span>{x.name}</span><span className={'badge '+(!x.boarded_at?'bg-slate-100':x.alighted_at?'bg-teal text-white':'bg-red-100 text-red-800')}>{!x.boarded_at?'未確認':x.alighted_at?'確認済み':'未降車'}</span>{(x.boarded_manually||x.alighted_manually)&&<span className="badge bg-amber-100 text-amber-900">QRなし</span>}<button disabled={mode==='乗車'?!!x.boarded_at:!x.boarded_at||!!x.alighted_at} className="border-0 bg-white text-xs font-bold text-teal disabled:opacity-30" onClick={()=>onManual(x.child_id)}>QRなしで{mode}</button></div>)}</section><section className={'card mt-4 p-4 '+(allAlighted?'border-2 border-teal bg-mint':'')}><div className="flex items-center justify-between gap-3"><h2 className="m-0 text-lg font-black">帰りの完了前チェック</h2><span className={'badge '+(allAlighted?'bg-teal text-white':'bg-slate-100 text-slate-600')}>{allAlighted?'ACTIVE':'降車確認待ち'}</span></div><p className="text-sm text-slate-600">全員の降車確認後に、5〜30秒の車内撮影を動画1件として保存し、そのまま送迎を完了します。</p><button disabled={!allAlighted||trip.status==='完了'} className="big-action mt-2 disabled:opacity-40" onClick={onTail}>車内撮影して送迎を完了する</button>{locationStatus&&<p className="text-xs text-slate-600">{locationStatus}</p>}</section></>
}
function Login({onLogin}:{onLogin:(x:Operator,t:string)=>void}) {
  const [id,setId]=useState(''),[pin,setPin]=useState(''),[error,setError]=useState(''),[recovery,setRecovery]=useState(false),[token,setToken]=useState(''),[newPin,setNewPin]=useState(''),[notice,setNotice]=useState('')
  const submit=async()=>{setError('');try{const r=await fetch(`${API}/api/auth/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({staff_id:Number(id),pin})});if(!r.ok)throw new Error(await messageOf(r));const data=await r.json();onLogin(data.staff,data.access_token)}catch(e){setError(e instanceof Error?e.message:'本番APIへログインできません')}}
  const recover=async()=>{setError('');try{const r=await fetch(`${API}/api/admin-recovery/reset-pin`,{method:'POST',headers:{'Content-Type':'application/json','X-Admin-Recovery-Token':token},body:JSON.stringify({staff_id:3,new_pin:newPin})});if(!r.ok)throw new Error(await messageOf(r));setNotice('管理者PINを再設定しました。職員ID 3 と新しいPINでログインしてください。');setToken('');setNewPin('')}catch(e){setError(e instanceof Error?e.message:'管理者PINを再設定できません')}}
  return <section className="login-screen" aria-labelledby="login-title">
    <div className="login-intro">
      <h1 id="login-title">確認を、ひとつずつ。</h1>
      <ol className="login-steps" aria-label="送迎バスの安全確認手順">
        <li className="is-current"><span className="step-marker" aria-hidden="true"/><span>乗車</span></li>
        <li><span className="step-marker" aria-hidden="true"/><span>降車</span></li>
        <li><span className="step-marker" aria-hidden="true"/><span>車内確認</span></li>
      </ol>
    </div>
    <form className="login-form" onSubmit={event=>{event.preventDefault();void submit()}}>
      <label htmlFor="staff-id">職員ID</label>
      <input id="staff-id" name="staff-id" inputMode="numeric" autoComplete="username" value={id} onChange={event=>setId(event.target.value)}/>
      <label htmlFor="staff-pin">PIN</label>
      <input id="staff-pin" name="staff-pin" type="password" inputMode="numeric" autoComplete="current-password" value={pin} onChange={event=>setPin(event.target.value)}/>
      <button className="login-submit" type="submit">ログイン</button>
    </form>
    <button className="recovery-toggle" type="button" aria-expanded={recovery} onClick={()=>setRecovery(!recovery)}>管理者PINを復旧する</button>
    {recovery&&<section className="recovery-panel" aria-label="管理者PINの復旧"><h2>管理者PINの復旧</h2><p>Renderに設定した一度限りの復旧トークンと、新しいPINを入力します。入力値は端末に保存しません。</p><label htmlFor="recovery-token">復旧トークン</label><input id="recovery-token" value={token} onChange={event=>setToken(event.target.value)} type="password"/><label htmlFor="new-pin">新しいPIN（8文字以上）</label><input id="new-pin" value={newPin} onChange={event=>setNewPin(event.target.value)} type="password"/><button type="button" disabled={!token||newPin.length<8} onClick={()=>void recover()}>PINを再設定する</button></section>}
    {notice&&<p className="login-notice" role="status">{notice}</p>}
    {error&&<p className="login-error" role="alert">{error}</p>}
  </section>
}
function VehicleVideoRecorder({trip,onUpload,onClose}:{trip:TripStatus;onUpload:(blob:Blob,durationSeconds:number)=>Promise<void>;onClose:()=>void}) {
  const video=useRef<HTMLVideoElement>(null)
  const streamRef=useRef<MediaStream|null>(null)
  const recorderRef=useRef<MediaRecorder|null>(null)
  const chunksRef=useRef<BlobPart[]>([])
  const timerRef=useRef<number>(0)
  const startedAtRef=useRef(0)
  const wakeLockRef=useRef<{release:()=>Promise<void>}|null>(null)
  const [elapsed,setElapsed]=useState(0)
  const [phase,setPhase]=useState<'ready'|'recording'|'uploading'>('ready')
  const [notice,setNotice]=useState('カメラを車内に向け、撮影開始を押してください。')
  const [error,setError]=useState('')
  const elapsedSeconds = Math.min(elapsed, MAX_VIDEO_SECONDS)
  const canStop = phase==='recording' && elapsedSeconds >= MIN_VIDEO_SECONDS
  const releaseWakeLock=async()=>{try{await wakeLockRef.current?.release()}catch{/* 端末側で解除済みの場合は無視 */}finally{wakeLockRef.current=null}}
  const requestWakeLock=async()=>{
    const wakeLock=(navigator as Navigator & {wakeLock?:{request:(type:'screen')=>Promise<{release:()=>Promise<void>}>}}).wakeLock
    if(!wakeLock) return
    try { wakeLockRef.current=await wakeLock.request('screen') }
    catch { /* ブラウザや省電力設定で拒否される場合がある */ }
  }
  useEffect(()=>{
    let cancelled=false
    ;(async()=>{try{
      if(!navigator.mediaDevices?.getUserMedia) throw new Error('この端末はカメラ撮影に対応していません')
      const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:640},height:{ideal:480},frameRate:{ideal:15,max:24}},audio:false})
      if(cancelled){stream.getTracks().forEach(track=>track.stop());return}
      streamRef.current=stream
      if(video.current){video.current.srcObject=stream;await video.current.play().catch(()=>undefined)}
    }catch(err){setError(err instanceof Error?err.message:'カメラを利用できません。権限を許可してください。')}})()
    return()=>{cancelled=true;window.clearInterval(timerRef.current);recorderRef.current?.state==='recording'&&recorderRef.current.stop();streamRef.current?.getTracks().forEach(track=>track.stop());void releaseWakeLock()}
  },[])
  const finishRecording=()=>{
    window.clearInterval(timerRef.current)
    if(recorderRef.current?.state==='recording') recorderRef.current.stop()
  }
  const begin=()=>{
    if(!streamRef.current){setError('カメラの準備ができていません');return}
    if(typeof MediaRecorder==='undefined'){setError('このブラウザは動画録画に対応していません');return}
    setError('');setNotice(`${MIN_VIDEO_SECONDS}秒経過後にSTOPできます。${MAX_VIDEO_SECONDS}秒で自動終了します。`);setElapsed(0);setPhase('recording')
    void requestWakeLock()
    chunksRef.current=[]
    startedAtRef.current=Date.now()
    const mimeType=MediaRecorder.isTypeSupported('video/mp4')?'video/mp4':MediaRecorder.isTypeSupported('video/webm;codecs=vp8')?'video/webm;codecs=vp8':MediaRecorder.isTypeSupported('video/webm')?'video/webm':''
    const recorder=new MediaRecorder(streamRef.current,{...(mimeType?{mimeType}:{}),videoBitsPerSecond:700000})
    recorderRef.current=recorder
    recorder.ondataavailable=event=>{if(event.data.size>0)chunksRef.current.push(event.data)}
    recorder.onstop=()=>{void (async()=>{try{const durationSeconds=Math.min(MAX_VIDEO_SECONDS,Math.round((Date.now()-startedAtRef.current)/1000));if(durationSeconds<MIN_VIDEO_SECONDS)throw new Error(`${MIN_VIDEO_SECONDS}秒以上撮影してください`);const blob=new Blob(chunksRef.current,{type:recorder.mimeType||'video/webm'});if(!blob.size)throw new Error('動画を記録できませんでした');setElapsed(durationSeconds);setPhase('uploading');setNotice('動画を保存し、AI補助確認を実行しています。画面は開いたままにしてください。');await onUpload(blob,durationSeconds)}catch(err){setPhase('ready');setNotice('撮影をやり直してください。');setError(err instanceof Error?err.message:'動画を保存できませんでした')}finally{void releaseWakeLock()}})()}
    recorder.start()
    timerRef.current=window.setInterval(()=>{const next=Math.floor((Date.now()-startedAtRef.current)/1000);setElapsed(Math.min(next,MAX_VIDEO_SECONDS));if(next>=MAX_VIDEO_SECONDS)finishRecording()},250)
  }
  const stopEarly=()=>{if(canStop)finishRecording()}
  const closeDisabled=phase==='recording'||phase==='uploading'
  return <div className="modal"><div className="sheet"><h2 className="text-center text-xl font-black">車内撮影（5〜30秒）</h2><p className="text-sm text-slate-600">{trip.vehicle_name} の車内を、確認済み証跡として撮影します。</p><video ref={video} autoPlay playsInline muted className="w-full aspect-video bg-slate-900 rounded-2xl"/><div className="mt-3 rounded-2xl bg-sand p-3 text-center"><b className="text-2xl text-teal">{elapsedSeconds}</b><span className="ml-1 text-sm font-bold">秒</span><p className="m-0 mt-1 text-xs text-slate-600">{notice}</p></div>{error&&<p className="rounded-xl bg-red-50 p-3 text-sm text-coral" role="alert">{error}</p>}<button className="big-action mt-3 disabled:opacity-40" disabled={phase!=='ready'||!!error} onClick={begin}>{phase==='recording'?'撮影中です':phase==='uploading'?'保存中です':'撮影開始'}</button>{phase==='recording'&&<button className="mt-3 w-full rounded-xl bg-slate-800 p-3 font-bold text-white disabled:opacity-40" disabled={!canStop} onClick={stopEarly}>{canStop?'STOPして保存する':`${MIN_VIDEO_SECONDS}秒後にSTOPできます`}</button>}<button className="w-full p-3 border-0 bg-white disabled:opacity-40" disabled={closeDisabled} onClick={onClose}>閉じる</button></div></div>
}
function ThirdApproval({onApprove}:{onApprove:(id:number,pin:string)=>void}) { const [id,setId]=useState(''),[pin,setPin]=useState(''); return <div className="mt-3"><h3 className="text-base font-bold">第三者確認</h3><p className="text-sm text-slate-600">運転担当者以外の確認者が職員IDとPINを入力します。</p><input className="w-full border rounded-xl p-3 mb-2" value={id} onChange={e=>setId(e.target.value)} placeholder="第三者確認者の職員ID"/><input className="w-full border rounded-xl p-3" type="password" value={pin} onChange={e=>setPin(e.target.value)} placeholder="第三者確認者のPIN"/><button className="mt-2 w-full rounded-xl bg-teal p-3 font-bold text-white" onClick={()=>id&&pin&&onApprove(Number(id),pin)}>第三者承認する</button></div> }
const parseApiDateTime = (value:string) => new Date(/[zZ]$|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`)
const formatDateTime = (value:string|null|undefined) => value ? parseApiDateTime(value).toLocaleString('ja-JP',{timeZone:'Asia/Tokyo',timeZoneName:'short',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}) : '—'
const formatJstDate = (value:Date) => new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Tokyo',year:'numeric',month:'2-digit',day:'2-digit'}).format(value)
const japanDayBounds = (day:string, end=false) => new Date(`${day}T${end?'23:59:59.999':'00:00:00'}+09:00`).toISOString()
const checkLabel = (value:string) => value==='tail_qr' ? '車内確認' : value==='third_party' ? '第三者確認' : value
const parseDetail = (value:string) => { try { const parsed=JSON.parse(value); return Object.keys(parsed).length ? JSON.stringify(parsed) : '—' } catch { return value || '—' } }

function Records({operator,auth,onMessage,onResume}:{operator:Operator;auth:AuthBuilder;onMessage:(message:string)=>void;onResume:(item:TripListItem)=>void}) {
  const [fromDate,setFromDate] = useState(()=>formatJstDate(new Date()))
  const [toDate,setToDate] = useState(()=>formatJstDate(new Date()))
  const [trips,setTrips] = useState<TripListItem[]>([])
  const [selected,setSelected] = useState<TripRecord|null>(null)
  const [loading,setLoading] = useState(true)
  const [auditLogs,setAuditLogs] = useState<AuditLog[]>([])
  const [auditQuery,setAuditQuery] = useState('')
  const [auditLoading,setAuditLoading] = useState(false)
  const loadTrips = async () => {
    setLoading(true)
    try {
      const params=new URLSearchParams({from_at:japanDayBounds(fromDate),to_at:japanDayBounds(toDate,true)})
      const response=await fetch(`${API}/api/trips?${params}`,auth())
      if(!response.ok) throw new Error(await messageOf(response))
      setTrips(await response.json()); setSelected(null)
    } catch(error) { onMessage(error instanceof Error ? error.message : '運行記録を取得できませんでした') }
    finally { setLoading(false) }
  }
  const selectTrip = async (tripId:number) => {
    try { const response=await fetch(`${API}/api/trips/${tripId}/record`,auth()); if(!response.ok) throw new Error(await messageOf(response)); setSelected(await response.json()) }
    catch(error) { onMessage(error instanceof Error ? error.message : '便の詳細を取得できませんでした') }
  }
  const forceComplete = async (item:TripListItem) => {
    const warning = item.unconfirmed>0 ? `未降車 ${item.unconfirmed} 人の記録が残っています。\n\n` : ''
    if (!window.confirm(`${warning}この便を管理者権限で強制的に完了にします。通常の安全確認は行われず、操作は監査ログに記録されます。\n\n続けますか？`)) return
    try {
      const response=await fetch(`${API}/api/trips/${item.trip_id}/force-complete`,auth({method:'POST'}))
      if(!response.ok) throw new Error(await messageOf(response))
      await loadTrips()
      onMessage(`${item.vehicle_name}の送迎を強制的に完了へ変更しました。監査ログに記録されています。`)
    } catch(error) { onMessage(error instanceof Error ? error.message : '便を強制完了できませんでした') }
  }
  const loadAudits = async () => {
    setAuditLoading(true)
    try {
      const params=new URLSearchParams({limit:'100',from_at:japanDayBounds(fromDate),to_at:japanDayBounds(toDate,true)})
      if(auditQuery.trim()) params.set('query_text',auditQuery.trim())
      const response=await fetch(`${API}/api/audit-logs?${params}`,auth())
      if(!response.ok) throw new Error(await messageOf(response))
      setAuditLogs(await response.json())
    } catch(error) { onMessage(error instanceof Error ? error.message : '監査ログを取得できませんでした') }
    finally { setAuditLoading(false) }
  }
  useEffect(()=>{ void loadTrips() },[])
  return <section className="mt-4"><div className="flex items-center justify-between"><div><h1 className="m-0 text-xl font-black">記録</h1><p className="m-0 mt-1 text-sm text-slate-600">過去の便と安全確認の証跡を確認します。</p></div><span className="badge bg-slate-100">{operator.role==='admin'?'管理者':'閲覧'}</span></div><section className="card mt-4 p-4"><h2 className="m-0 text-base font-black">期間を指定</h2><div className="grid gap-3 mt-3"><label className="text-xs font-bold">開始日<input className="mt-1 w-full min-w-0 border rounded-xl p-3 text-base font-normal" type="date" value={fromDate} max={toDate} onChange={e=>setFromDate(e.target.value)}/></label><label className="text-xs font-bold">終了日<input className="mt-1 w-full min-w-0 border rounded-xl p-3 text-base font-normal" type="date" value={toDate} min={fromDate} onChange={e=>setToDate(e.target.value)}/></label></div><button className="big-action mt-3" onClick={loadTrips}>便を検索する</button></section><section className="mt-4"><div className="flex justify-between items-baseline"><h2 className="m-0 text-lg font-black">過去の便</h2><span className="text-sm text-slate-600">{loading?'読み込み中…':`${trips.length} 件`}</span></div>{!loading&&trips.length===0&&<section className="card mt-3 p-4 text-sm text-slate-600">指定期間の便はありません。</section>}{trips.map(item=><section key={item.trip_id} className="card mt-3 p-4"><button className="w-full border-0 bg-transparent p-0 text-left" onClick={()=>item.status==='運行中'?onResume(item):selectTrip(item.trip_id)}><div className="flex justify-between gap-3"><div><b>{formatDateTime(item.started_at)}・{item.direction}</b><p className="m-0 mt-1 text-sm text-slate-600">{item.vehicle_name}・{item.route_name}</p><p className="m-0 mt-1 text-sm text-slate-600">乗車 {item.boarded}人 / 降車 {item.alighted}人</p></div><span className={'badge h-fit '+(item.status==='完了'?'bg-teal text-white':item.unconfirmed>0?'bg-red-100 text-red-800':'bg-amber-100')}>{item.status}</span></div>{item.status==='運行中'&&<p className="mb-0 mt-2 text-sm font-bold text-teal">タップして送迎を再開</p>}{item.unconfirmed>0&&<p className="mb-0 mt-2 text-sm text-coral">未降車 {item.unconfirmed} 人</p>}</button>{operator.role==='admin'&&item.status==='運行中'&&<button className="mt-3 w-full rounded-xl border border-red-300 bg-red-50 p-3 text-sm font-bold text-red-800" onClick={()=>void forceComplete(item)}>管理者として強制的に完了へ変更</button>}</section>)}</section>{selected&&<TripEvidence record={selected} auth={auth} onMessage={onMessage} onClose={()=>setSelected(null)}/>} {operator.role==='admin'&&<section className="card mt-5 p-4"><h2 className="m-0 text-lg font-black">監査ログ</h2><p className="text-sm text-slate-600">ログイン・乗降・確認・完了などの操作履歴です。</p><div className="flex gap-2"><input className="min-w-0 flex-1 border rounded-xl p-3 text-sm" value={auditQuery} onChange={e=>setAuditQuery(e.target.value)} placeholder="操作名・便IDなどで検索"/><button className="rounded-xl bg-slate-800 px-4 font-bold text-white" onClick={loadAudits}>検索</button></div>{auditLoading&&<p className="text-sm text-slate-600">読み込み中です…</p>}{!auditLoading&&auditLogs.length>0&&<div className="mt-3 divide-y">{auditLogs.map(log=><div className="py-3 text-sm" key={log.id}><div className="flex justify-between gap-2"><b>{log.action}</b><span className="text-slate-500">{formatDateTime(log.created_at)}</span></div><p className="m-0 mt-1 text-slate-600">{log.resource_type} #{log.resource_id} ・ {parseDetail(log.detail)}</p></div>)}</div>}{!auditLoading&&auditLogs.length===0&&<p className="mb-0 mt-3 text-sm text-slate-600">検索ボタンで監査ログを表示します。</p>}</section>}</section>
}
function TripEvidence({record,auth,onMessage,onClose}:{record:TripRecord;auth:AuthBuilder;onMessage:(message:string)=>void;onClose:()=>void}) { const trip=record.trip; const openVideo=async(item:VideoEvidenceItem)=>{const popup=window.open("","_blank");try{if(popup)popup.document.write("動画を読み込み中です...");const response=await fetch(`${API}/api/videos/${item.id}/download`,auth());if(!response.ok)throw new Error(await messageOf(response));const blob=await response.blob();const url=URL.createObjectURL(blob);if(popup)popup.location.href=url;else window.open(url,"_blank","noopener,noreferrer");window.setTimeout(()=>URL.revokeObjectURL(url),60000);onMessage("動画を開きました")}catch(error){if(popup)popup.close();onMessage(error instanceof Error?error.message:"動画を開けませんでした")}}; return <section className="card mt-5 overflow-hidden"><div className="p-4 bg-slate-50 flex justify-between gap-3"><div><h2 className="m-0 text-lg font-black">送迎記録の詳細</h2><p className="m-0 mt-1 text-sm text-slate-600">{trip.route_name}・{trip.vehicle_name}</p></div><button className="border-0 bg-transparent text-sm font-bold" onClick={onClose}>閉じる</button></div><div className="p-4 grid grid-cols-2 gap-3 text-sm"><p className="m-0"><b>開始</b><br/>{formatDateTime(trip.started_at)}</p><p className="m-0"><b>完了</b><br/>{formatDateTime(trip.completed_at)}</p><p className="m-0"><b>乗車 / 降車</b><br/>{trip.boarded}人 / {trip.alighted}人</p><p className="m-0"><b>未降車</b><br/><span className={trip.unconfirmed>0?'text-coral font-bold':''}>{trip.unconfirmed}人</span></p></div><div className="border-t p-4"><h3 className="m-0 text-base font-black">乗降履歴</h3>{record.attendance.length===0?<p className="text-sm text-slate-600">乗降記録はありません。</p>:<div className="mt-2 divide-y">{record.attendance.map(item=><div className="py-3 text-sm" key={item.child_id}><b>{item.name}{item.class_name?`（${item.class_name}）`:''}</b><p className="m-0 mt-1 text-slate-600">乗車：{formatDateTime(item.boarded_at)} {item.boarded_by?`（${item.boarded_by}）`:''}</p><p className="m-0 text-slate-600">降車：{formatDateTime(item.alighted_at)} {item.alighted_by?`（${item.alighted_by}）`:''}</p></div>)}</div>}</div><div className="border-t p-4"><h3 className="m-0 text-base font-black">安全確認履歴</h3>{record.safety_checks.length===0?<p className="text-sm text-slate-600">安全確認記録はありません。</p>:<div className="mt-2 divide-y">{record.safety_checks.map(item=><div className="py-3 text-sm" key={item.id}><b>{checkLabel(item.check_type)}</b><p className="m-0 mt-1 text-slate-600">{formatDateTime(item.created_at)} ・ {item.staff_name}</p>{item.latitude&&item.longitude&&<p className="m-0 text-xs text-slate-500">位置情報：{item.latitude}, {item.longitude}</p>}</div>)}</div>}</div><div className="border-t p-4"><h3 className="m-0 text-base font-black">動画・AI補助</h3>{!record.videos?.length?<p className="text-sm text-slate-600">動画証跡はありません。</p>:<div className="mt-2 divide-y">{record.videos.map(item=><div className="py-3 text-sm" key={item.id}><b>{item.file_name}</b><p className="m-0 mt-1 text-slate-600">{formatDateTime(item.created_at)} ・ {item.ai_status}</p><button className="mt-3 rounded-xl bg-teal px-4 py-2 text-sm font-bold text-white" onClick={()=>void openVideo(item)}>動画を開く</button><p className="m-0 mt-2 text-xs text-slate-600">動画ID：{item.id}</p>{item.storage_key&&<p className="m-0 mt-1 break-all text-xs text-slate-600">保存キー：{item.storage_key}</p>}{item.storage_path&&<p className="m-0 mt-1 break-all text-xs text-slate-600">保存先パス：{item.storage_path}</p>}{item.content_type&&<p className="m-0 mt-1 text-xs text-slate-600">形式：{item.content_type}</p>}{item.ai_result&&<p className="m-0 mt-2 text-slate-700">AI補助：{item.ai_result}</p>}</div>)}</div>}</div></section> }
function ChildrenPage({operator,auth,onMessage,onRefresh}:{operator:Operator;auth:AuthBuilder;onMessage:(message:string)=>void;onRefresh:()=>Promise<void>}) {
  const [children,setChildren]=useState<SettingChild[]>([]),[loading,setLoading]=useState(true)
  const [editingChild,setEditingChild]=useState<SettingChild|null>(null)
  const load=async()=>{setLoading(true);try{const response=await fetch(`${API}/api/children`,auth());if(!response.ok)throw new Error(await messageOf(response));setChildren(await response.json())}catch(error){onMessage(error instanceof Error?error.message:'園児を取得できませんでした')}finally{setLoading(false)}}
  useEffect(()=>{if(operator.role==='admin') void load()},[])
  if(operator.role!=='admin') return <section className="card mt-4 p-5"><h1 className="m-0 text-xl font-black">園児</h1><p className="text-sm text-slate-600">園児の登録・分類変更は管理者だけが行えます。</p></section>
  const save=async(path:string,method:'POST'|'PUT',data:Record<string,unknown>)=>{const response=await fetch(`${API}${path}`,auth({method,body:JSON.stringify(data)}));if(!response.ok)throw new Error(await messageOf(response));await load();await onRefresh();onMessage(method==='POST'?'園児を登録しました':'園児を更新しました')}
  const submit=(event:React.FormEvent<HTMLFormElement>)=>{event.preventDefault();const raw=Object.fromEntries(new FormData(event.currentTarget).entries()) as Record<string,string>;save('/api/children','POST',{name:raw.name,class_name:raw.class_name,qr_token:raw.qr_token}).catch(error=>onMessage(error instanceof Error?error.message:'園児を登録できませんでした'));event.currentTarget.reset()}
  const submitEdit=async(event:React.FormEvent<HTMLFormElement>,item:SettingChild)=>{
    event.preventDefault()
    const raw=Object.fromEntries(new FormData(event.currentTarget).entries()) as Record<string,string>
    try {
      await save(`/api/children/${item.id}`,'PUT',{name:raw.name,class_name:raw.class_name,qr_token:raw.qr_token})
      setEditingChild(null)
    } catch(error) {
      onMessage(error instanceof Error?error.message:'園児を更新できませんでした')
    }
  }
  return <section className="mt-4"><h1 className="m-0 text-xl font-black">園児</h1><p className="mt-1 text-sm text-slate-600">園児を登録し、送迎時の分類を選びます。</p><section className="card mt-4 p-4"><h2 className="m-0 text-lg font-black">園児を登録</h2><form className="grid gap-2 mt-3" onSubmit={submit}><input className="border rounded-xl p-3" name="name" placeholder="園児名" required/><select className="border rounded-xl p-3" name="class_name" defaultValue={CHILD_GROUPS[0]}>{CHILD_GROUPS.map(group=><option value={group} key={group}>{group}</option>)}</select><input className="border rounded-xl p-3" name="qr_token" placeholder="QR文字列" required/><button className="rounded-xl bg-teal p-3 font-bold text-white">園児を登録</button></form></section><section className="card mt-4 p-4"><div className="flex justify-between items-baseline"><h2 className="m-0 text-lg font-black">園児一覧</h2><span className="text-sm text-slate-600">{loading?'読み込み中…':`${children.length}人`}</span></div>{!loading&&children.length===0&&<p className="mb-0 mt-3 text-sm text-slate-600">登録済みの園児はありません。</p>}{children.map(item=><div className="grid gap-2 border-t pt-3 mt-3 text-sm" key={item.id}><div><b>{item.name}</b><br/><small>{item.class_name||'分類未設定'}</small><p className="m-0 mt-1 break-all text-xs text-slate-600">QR文字列：{item.qr_token}</p></div>{editingChild?.id===item.id?<form className="grid gap-2 rounded-xl bg-slate-50 p-3" onSubmit={event=>void submitEdit(event,item)}><input className="border rounded-xl bg-white p-3" name="name" defaultValue={item.name} placeholder="園児名" required/><select className="border rounded-xl bg-white p-3" name="class_name" defaultValue={item.class_name||CHILD_GROUPS[0]}>{CHILD_GROUPS.map(group=><option value={group} key={group}>{group}</option>)}</select><input className="border rounded-xl bg-white p-3" name="qr_token" defaultValue={item.qr_token} placeholder="QR文字列" required/><div className="grid grid-cols-2 gap-2"><button className="rounded-lg bg-teal px-3 py-2 text-sm font-bold text-white">保存</button><button className="rounded-lg border bg-white px-3 py-2 text-sm font-bold" type="button" onClick={()=>setEditingChild(null)}>キャンセル</button></div></form>:<><select className="border rounded-lg p-2 text-sm" value={item.class_name||CHILD_GROUPS[0]} onChange={e=>save(`/api/children/${item.id}`,'PUT',{class_name:e.target.value}).catch(error=>onMessage(error instanceof Error?error.message:'分類を更新できませんでした'))}>{CHILD_GROUPS.map(group=><option value={group} key={group}>{group}</option>)}</select><button className="border-0 bg-white font-bold" onClick={()=>setEditingChild(item)}>編集</button></>}</div>)}</section></section>
}
function Settings({operator,auth,onMessage,onRefresh}:{operator:Operator;auth:AuthBuilder;onMessage:(message:string)=>void;onRefresh:()=>Promise<void>}) {
  const [organization,setOrganization]=useState<OrganizationInfo|null>(null),[children,setChildren]=useState<SettingChild[]>([]),[staff,setStaff]=useState<SettingStaff[]>([]),[vehicles,setVehicles]=useState<Vehicle[]>([]),[routes,setRoutes]=useState<Route[]>([]),[loading,setLoading]=useState(true)
  const getSetting=async<T,>(label:string,path:string):Promise<T>=>{
    let response:Response|null=null
    let networkError:unknown=null
    for(let attempt=0;attempt<3;attempt+=1){
      try { response=await fetch(`${API}${path}`,auth()); break }
      catch(error){ networkError=error; if(attempt<2) await new Promise(resolve=>window.setTimeout(resolve,400*(attempt+1))) }
    }
    if(!response){
      const detail=networkError instanceof Error?networkError.message:'通信エラー'
      throw new Error(`${label}の取得に失敗しました（${path}: ${detail}）`)
    }
    if(!response.ok) throw new Error(`${label}の取得に失敗しました（${path}: ${await messageOf(response)}）`)
    return response.json() as Promise<T>
  }
  const load=async()=>{
    setLoading(true)
    const errors:string[]=[]
    const loadOne=async<T,>(label:string,path:string,setter:(value:T)=>void)=>{
      try { setter(await getSetting<T>(label,path)) }
      catch(error){ errors.push(error instanceof Error?error.message:`${label}を取得できませんでした`) }
    }
    await loadOne<OrganizationInfo>('園情報','/api/organization',setOrganization)
    await loadOne<SettingChild[]>('園児','/api/children',setChildren)
    await loadOne<SettingStaff[]>('職員','/api/staff',setStaff)
    await loadOne<Vehicle[]>('車両','/api/vehicles',setVehicles)
    await loadOne<Route[]>('便','/api/bus-routes',setRoutes)
    if(errors.length) onMessage(errors.join(' / '))
    setLoading(false)
  }
  useEffect(()=>{if(operator.role==='admin') void load()},[])
  if(operator.role!=='admin') return <section className="card mt-4 p-5"><h1 className="m-0 text-xl font-black">設定</h1><p className="text-sm text-slate-600">園情報・職員・車両・便の変更は管理者だけが行えます。</p></section>
  const post=async(path:string,data:Record<string,unknown>)=>{const response=await fetch(`${API}${path}`,auth({method:'POST',body:JSON.stringify(data)}));if(!response.ok)throw new Error(await messageOf(response));await load();await onRefresh();onMessage('設定を保存しました')}
  const put=async(path:string,data:Record<string,unknown>)=>{const response=await fetch(`${API}${path}`,auth({method:'PUT',body:JSON.stringify(data)}));if(!response.ok)throw new Error(await messageOf(response));await load();await onRefresh();onMessage('設定を更新しました')}
  const submit=(path:string,fields:string[],transform?:(data:Record<string,string>)=>Record<string,unknown>)=>(event:React.FormEvent<HTMLFormElement>)=>{event.preventDefault();const raw=Object.fromEntries(new FormData(event.currentTarget).entries()) as Record<string,string>;post(path,transform?transform(raw):raw).catch(error=>onMessage(error instanceof Error?error.message:'保存できませんでした'));event.currentTarget.reset()}
  const edit=(label:string,path:string,current:Record<string,string>)=>{const name=window.prompt(`${label}名`,current.name);if(!name)return;put(path,{...current,name}).catch(error=>onMessage(error instanceof Error?error.message:'更新できませんでした'))}
  const removeVehicle=async(item:Vehicle)=>{if(!window.confirm(`${item.name}${item.plate_number?`・${item.plate_number}`:''} を削除しますか？\n\nこの車両を使用している便は「車両未設定」になります。過去の運行記録は削除されません。`))return;try{const response=await fetch(`${API}/api/vehicles/${item.id}`,auth({method:'DELETE'}));if(!response.ok)throw new Error(await messageOf(response));await load();await onRefresh();onMessage(`${item.name} を削除しました`)}catch(error){onMessage(error instanceof Error?error.message:'車両を削除できませんでした')}}
  const removeRoute=async(item:Route)=>{if(!window.confirm(`${item.name}・${item.direction} を削除しますか？\n\n通常名簿から外れ、運行画面にも表示されなくなります。過去の運行記録は削除されません。`))return;try{const response=await fetch(`${API}/api/bus-routes/${item.id}`,auth({method:'DELETE'}));if(!response.ok)throw new Error(await messageOf(response));await load();await onRefresh();onMessage(`${item.name}・${item.direction} を削除しました`)}catch(error){onMessage(error instanceof Error?error.message:'便を削除できませんでした')}}
  return <section className="mt-4"><h1 className="m-0 text-xl font-black">設定</h1><p className="mt-1 text-sm text-slate-600">この園の基本情報と運行設定を管理します。</p>{loading?<p className="text-sm">読み込み中です…</p>:<><section className="card mt-4 p-4"><h2 className="m-0 text-lg font-black">園情報</h2><form className="flex gap-2 mt-3" onSubmit={e=>{e.preventDefault();const name=String(new FormData(e.currentTarget).get('name')||'');if(name)put('/api/organization',{name}).catch(error=>onMessage(error instanceof Error?error.message:'更新できませんでした'))}}><input className="min-w-0 flex-1 border rounded-xl p-3" name="name" defaultValue={organization?.name}/><button className="rounded-xl bg-teal px-4 font-bold text-white">保存</button></form></section><section className="card mt-4 p-4"><h2 className="m-0 text-lg font-black">職員と権限</h2><form className="grid grid-cols-3 gap-2 mt-3" onSubmit={submit('/api/staff',['name','role','pin'])}><input className="border rounded-xl p-3" name="name" placeholder="職員名" required/><select className="border rounded-xl p-3" name="role"><option value="operator">運転担当</option><option value="verifier">第三者確認</option><option value="admin">管理者</option></select><input className="border rounded-xl p-3" name="pin" type="password" placeholder="PIN（8文字以上）" required/><button className="col-span-3 rounded-xl bg-teal p-3 font-bold text-white">職員を登録</button></form>{staff.map(item=><div className="flex items-center justify-between gap-2 border-t pt-3 mt-3 text-sm" key={item.id}><span>{item.name}<br/><small>{item.is_active?'有効':'無効'}</small></span><select className="border rounded-lg p-2" value={item.role} onChange={e=>put(`/api/staff/${item.id}`,{role:e.target.value}).catch(error=>onMessage(error instanceof Error?error.message:'更新できませんでした'))}><option value="operator">運転担当</option><option value="verifier">第三者確認</option><option value="admin">管理者</option></select><button className="border-0 bg-white font-bold" onClick={()=>put(`/api/staff/${item.id}`,{is_active:!item.is_active}).catch(error=>onMessage(error instanceof Error?error.message:'更新できませんでした'))}>{item.is_active?'無効化':'有効化'}</button></div>)}</section><section className="card mt-4 p-4"><h2 className="m-0 text-lg font-black">車両・便</h2><form className="grid grid-cols-2 gap-2 mt-3" onSubmit={submit('/api/vehicles',['name','plate_number'])}><input className="border rounded-xl p-3" name="name" placeholder="車両名" required/><input className="border rounded-xl p-3" name="plate_number" placeholder="ナンバー"/><button className="col-span-2 rounded-xl bg-teal p-3 font-bold text-white">車両を登録</button></form>{vehicles.map(item=><div className="flex justify-between border-t pt-3 mt-3 text-sm" key={item.id}><span>{item.name} {item.plate_number&&`・${item.plate_number}`}</span><div className="flex items-center gap-3"><button className="border-0 bg-white font-bold" onClick={()=>edit('車両',`/api/vehicles/${item.id}`,{name:item.name,plate_number:item.plate_number||''})}>編集</button><button className="border-0 bg-white font-bold text-coral" onClick={()=>void removeVehicle(item)} aria-label={`${item.name}を削除`}>削除</button></div></div>)}<form className="grid grid-cols-3 gap-2 mt-4" onSubmit={submit('/api/bus-routes',['name','direction','vehicle_id'],raw=>({name:raw.name,direction:raw.direction,vehicle_id:raw.vehicle_id?Number(raw.vehicle_id):null}))}><input className="border rounded-xl p-3" name="name" placeholder="便名" required/><select className="border rounded-xl p-3" name="direction"><option>帰り</option><option>往路</option></select><select className="border rounded-xl p-3" name="vehicle_id"><option value="">車両未設定</option>{vehicles.map(v=><option value={v.id} key={v.id}>{v.name}</option>)}</select><button className="col-span-3 rounded-xl bg-slate-800 p-3 font-bold text-white">便を登録</button></form>{routes.map(item=><RouteRosterEditor key={item.id} route={item} children={children} onEdit={()=>edit('便',`/api/bus-routes/${item.id}`,{name:item.name})} onRemove={()=>void removeRoute(item)} onSave={ids=>put(`/api/bus-routes/${item.id}`,{child_ids:ids}).catch(error=>onMessage(error instanceof Error?error.message:'保存できませんでした'))}/>) }</section></>}</section>
}
function LineSettingsPage({operator,auth,onMessage,onRefresh}:{operator:Operator;auth:AuthBuilder;onMessage:(message:string)=>void;onRefresh:()=>Promise<void>}) {
  const [children,setChildren]=useState<SettingChild[]>([]),[guardians,setGuardians]=useState<GuardianContact[]>([]),[notifications,setNotifications]=useState<NotificationItem[]>([]),[loading,setLoading]=useState(true)
  const [lineLinkPreview,setLineLinkPreview]=useState<LineLinkPreview|null>(null)
  const load=async()=>{
    setLoading(true)
    try {
      const [childResponse,guardianResponse,notificationResponse]=await Promise.all([fetch(`${API}/api/children`,auth()),fetch(`${API}/api/guardian-contacts`,auth()),fetch(`${API}/api/notifications`,auth())])
      if(!childResponse.ok) throw new Error(await messageOf(childResponse))
      if(!guardianResponse.ok) throw new Error(await messageOf(guardianResponse))
      if(!notificationResponse.ok) throw new Error(await messageOf(notificationResponse))
      setChildren(await childResponse.json())
      setGuardians(await guardianResponse.json())
      setNotifications(await notificationResponse.json())
    } catch(error) {
      onMessage(error instanceof Error?error.message:'LINE通知設定を取得できませんでした')
    } finally {
      setLoading(false)
    }
  }
  useEffect(()=>{if(operator.role==='admin') void load()},[])
  if(operator.role!=='admin') return <section className="card mt-4 p-5"><h1 className="m-0 text-xl font-black">LINE</h1><p className="text-sm text-slate-600">保護者通知先とLINE連携は管理者だけが行えます。</p></section>
  const post=async(path:string,data:Record<string,unknown>)=>{const response=await fetch(`${API}${path}`,auth({method:'POST',body:JSON.stringify(data)}));if(!response.ok)throw new Error(await messageOf(response));await load();await onRefresh();onMessage('LINE通知設定を保存しました')}
  const put=async(path:string,data:Record<string,unknown>)=>{const response=await fetch(`${API}${path}`,auth({method:'PUT',body:JSON.stringify(data)}));if(!response.ok)throw new Error(await messageOf(response));await load();await onRefresh();onMessage('LINE通知設定を更新しました')}
  const issueLineLink=async(item:GuardianContact)=>{try{const response=await fetch(`${API}/api/guardian-contacts/${item.id}/line-link-requests`,auth({method:'POST'}));if(!response.ok)throw new Error(await messageOf(response));const result=await response.json() as LineLinkPreview;setLineLinkPreview(result);await load();onMessage(result.email_delivery_status==='sent'?'QR連携案内をメール送信しました':'QRを発行しましたが、案内メールは送信できませんでした。メール配信設定を確認してください。')}catch(error){onMessage(error instanceof Error?error.message:'QR連携案内を発行できませんでした')}}
  const unlinkLine=async(item:GuardianContact)=>{if(!window.confirm(`${item.name||item.email} のLINE連携を解除しますか？`))return;try{const response=await fetch(`${API}/api/guardian-contacts/${item.id}/line-link`,auth({method:'DELETE'}));if(!response.ok)throw new Error(await messageOf(response));setLineLinkPreview(null);await load();onMessage('LINE連携を解除しました')}catch(error){onMessage(error instanceof Error?error.message:'LINE連携を解除できませんでした')}}
  const retryNotification=async(item:NotificationItem)=>{try{const response=await fetch(`${API}/api/notifications/${item.id}/retry`,auth({method:'POST'}));if(!response.ok)throw new Error(await messageOf(response));await load();onMessage('失敗した通知を再送しました')}catch(error){onMessage(error instanceof Error?error.message:'通知を再送できませんでした')}}
  return <section className="mt-4"><h1 className="m-0 text-xl font-black">LINE</h1><p className="mt-1 text-sm text-slate-600">保護者通知先、LINE連携、通知履歴を管理します。</p>{loading?<p className="text-sm">読み込み中です…</p>:<GuardianNotificationSettings children={children} guardians={guardians} notifications={notifications} preview={lineLinkPreview} onCreate={data=>post('/api/guardian-contacts',data)} onUpdate={(id,data)=>put(`/api/guardian-contacts/${id}`,data)} onIssue={issueLineLink} onUnlink={unlinkLine} onRetry={retryNotification} onClosePreview={()=>setLineLinkPreview(null)}/>}</section>
}
function GuardianNotificationSettings({children,guardians,notifications,preview,onCreate,onUpdate,onIssue,onUnlink,onRetry,onClosePreview}:{children:SettingChild[];guardians:GuardianContact[];notifications:NotificationItem[];preview:LineLinkPreview|null;onCreate:(data:Record<string,unknown>)=>Promise<void>;onUpdate:(id:number,data:Record<string,unknown>)=>Promise<void>;onIssue:(item:GuardianContact)=>Promise<void>;onUnlink:(item:GuardianContact)=>Promise<void>;onRetry:(item:NotificationItem)=>Promise<void>;onClosePreview:()=>void}) {
  const [selectedChildren,setSelectedChildren]=useState<number[]>([])
  const [editingId,setEditingId]=useState<number|null>(null)
  const [editingChildren,setEditingChildren]=useState<number[]>([])
  const toggleChild=(id:number)=>setSelectedChildren(current=>current.includes(id)?current.filter(value=>value!==id):[...current,id])
  const startEdit=(item:GuardianContact)=>{setEditingId(item.id);setEditingChildren(item.children.map(child=>child.id))}
  const cancelEdit=()=>{setEditingId(null);setEditingChildren([])}
  const toggleEditingChild=(id:number)=>setEditingChildren(current=>current.includes(id)?current.filter(value=>value!==id):[...current,id])
  const submit=async(event:React.FormEvent<HTMLFormElement>)=>{
    event.preventDefault()
    if(!selectedChildren.length){window.alert('対象園児を1人以上選択してください');return}
    const form=event.currentTarget
    const raw=Object.fromEntries(new FormData(form).entries()) as Record<string,string>
    await onCreate({
      name:raw.name||null,email:raw.email,email_enabled:true,line_enabled:raw.line_enabled==='on',
      consent:raw.consent==='on',child_ids:selectedChildren,relationship:raw.relationship||null,notify_alighted:true,
    })
    form.reset();setSelectedChildren([])
  }
  const submitEdit=async(event:React.FormEvent<HTMLFormElement>,item:GuardianContact)=>{
    event.preventDefault()
    if(!editingChildren.length){window.alert('対象園児を1人以上選択してください');return}
    const raw=Object.fromEntries(new FormData(event.currentTarget).entries()) as Record<string,string>
    try {
      await onUpdate(item.id,{
        name:raw.name||null,email:raw.email,email_enabled:raw.email_enabled==='on',
        line_enabled:raw.line_enabled==='on',consent:raw.consent==='on',
        child_ids:editingChildren,relationship:raw.relationship||null,notify_alighted:raw.notify_alighted==='on',
      })
      cancelEdit()
    } catch(error) {
      window.alert(error instanceof Error?error.message:'保護者通知先を更新できませんでした')
    }
  }
  const statusLabel=(status:string)=>({not_requested:'未案内',pending:'案内済み',linked:'連携済み',expired:'期限切れ',unfollowed:'友だち解除',revoked:'解除済み',error:'エラー'}[status]||status)
  const statusClass=(status:string)=>status==='linked'?'bg-emerald-100 text-emerald-800':status==='pending'?'bg-amber-100 text-amber-900':status==='failed'||status==='error'?'bg-red-100 text-red-800':'bg-slate-100 text-slate-700'
  const childSummary=(item:GuardianContact)=>item.children.map(child=>child.name).join('・')||'園児未設定'
  const firstRelationship=(item:GuardianContact)=>item.children.find(child=>child.relationship)?.relationship||''
  const notifyAlightedDefault=(item:GuardianContact)=>item.children.length===0||item.children.some(child=>child.notify_alighted)
  return <>
    <section className="card mt-4 p-4">
      <div className="flex items-start justify-between gap-3"><div><h2 className="m-0 text-lg font-black">保護者・LINE通知</h2><p className="m-0 mt-1 text-xs text-slate-600">メールアドレスを登録し、「バナナ幼稚園」公式アカウントとQRで連携します。</p></div><a className="shrink-0 text-xs font-bold text-teal" href="https://line.me/R/ti/p/%40785ntzvy" rel="noreferrer">@785ntzvy</a></div>
      <form className="mt-4 grid gap-2" onSubmit={event=>void submit(event)}>
        <div className="grid grid-cols-2 gap-2"><input className="min-w-0 border rounded-xl p-3" name="name" placeholder="保護者名"/><input className="min-w-0 border rounded-xl p-3" name="relationship" placeholder="続柄（母・父など）"/></div>
        <input className="border rounded-xl p-3" name="email" type="email" placeholder="メールアドレス" required/>
        <fieldset className="rounded-xl border p-3"><legend className="px-1 text-sm font-bold">対象園児</legend><div className="grid grid-cols-2 gap-2">{children.map(child=><label className="flex items-center gap-2 rounded-lg bg-slate-50 p-2 text-sm" key={child.id}><input type="checkbox" checked={selectedChildren.includes(child.id)} onChange={()=>toggleChild(child.id)}/><span>{child.name}</span></label>)}</div></fieldset>
        <label className="flex items-start gap-2 rounded-xl bg-emerald-50 p-3 text-sm"><input className="mt-1" type="checkbox" name="line_enabled"/><span><b>LINE通知を希望する</b><br/><small>メール通知とLINE通知の両方を送ります。</small></span></label>
        <label className="flex items-start gap-2 rounded-xl bg-slate-50 p-3 text-sm"><input className="mt-1" type="checkbox" name="consent" required/><span>通知先の登録・LINE連携・通知履歴の保存について同意を確認しました。</span></label>
        <button className="rounded-xl bg-teal p-3 font-bold text-white">保護者通知先を登録</button>
      </form>
      <div className="mt-4 divide-y">{guardians.length===0?<p className="text-sm text-slate-600">登録済みの保護者通知先はありません。</p>:guardians.map(item=><article className="py-4" key={item.id}><div className="flex items-start justify-between gap-3"><div className="min-w-0"><b>{item.name||'保護者'}</b><p className="m-0 mt-1 break-all text-sm text-slate-600">{item.email}</p><p className="m-0 mt-1 text-xs text-slate-500">{childSummary(item)}／メール {item.email_enabled?'ON':'OFF'}／LINE {item.line_enabled?'ON':'OFF'}</p></div><span className={`shrink-0 rounded-full px-2 py-1 text-xs font-bold ${statusClass(item.line_status)}`}>{statusLabel(item.line_status)}</span></div>{editingId===item.id?<form className="mt-3 grid gap-2 rounded-xl bg-slate-50 p-3" onSubmit={event=>void submitEdit(event,item)}><div className="grid grid-cols-2 gap-2"><input className="min-w-0 border rounded-xl bg-white p-3 text-sm" name="name" defaultValue={item.name||''} placeholder="保護者名"/><input className="min-w-0 border rounded-xl bg-white p-3 text-sm" name="relationship" defaultValue={firstRelationship(item)} placeholder="続柄"/></div><input className="border rounded-xl bg-white p-3 text-sm" name="email" type="email" defaultValue={item.email} placeholder="メールアドレス" required/><fieldset className="rounded-xl border bg-white p-3"><legend className="px-1 text-sm font-bold">対象園児</legend><div className="grid grid-cols-2 gap-2">{children.map(child=><label className="flex items-center gap-2 rounded-lg bg-slate-50 p-2 text-sm" key={child.id}><input type="checkbox" checked={editingChildren.includes(child.id)} onChange={()=>toggleEditingChild(child.id)}/><span>{child.name}</span></label>)}</div></fieldset><label className="flex items-start gap-2 rounded-xl bg-white p-3 text-sm"><input className="mt-1" type="checkbox" name="email_enabled" defaultChecked={item.email_enabled}/><span>メール通知を送る</span></label><label className="flex items-start gap-2 rounded-xl bg-white p-3 text-sm"><input className="mt-1" type="checkbox" name="line_enabled" defaultChecked={item.line_enabled}/><span>LINE通知を希望する</span></label><label className="flex items-start gap-2 rounded-xl bg-white p-3 text-sm"><input className="mt-1" type="checkbox" name="notify_alighted" defaultChecked={notifyAlightedDefault(item)}/><span>降車記録を通知する</span></label><label className="flex items-start gap-2 rounded-xl bg-white p-3 text-sm"><input className="mt-1" type="checkbox" name="consent" defaultChecked={!!item.consented_at}/><span>通知先登録と通知履歴保存の同意を確認済み</span></label><div className="grid grid-cols-2 gap-2"><button className="rounded-lg bg-teal px-3 py-2 text-sm font-bold text-white">保存</button><button className="rounded-lg border bg-white px-3 py-2 text-sm font-bold" type="button" onClick={cancelEdit}>キャンセル</button></div></form>:<div className="mt-3 flex flex-wrap gap-2"><button className="rounded-lg border bg-white px-3 py-2 text-xs font-bold" onClick={()=>startEdit(item)}>編集</button>{item.consented_at&&!item.line_enabled&&<button className="rounded-lg bg-teal px-3 py-2 text-xs font-bold text-white" onClick={()=>void onUpdate(item.id,{email_enabled:true,line_enabled:true})}>LINE通知を有効化</button>}{item.line_enabled&&<button className="rounded-lg bg-teal px-3 py-2 text-xs font-bold text-white" onClick={()=>void onIssue(item)}>{item.line_status==='pending'||item.line_status==='expired'?'QRを再発行':'QR案内を発行'}</button>}{item.line_enabled&&item.line_status!=='linked'&&<button className="rounded-lg border bg-white px-3 py-2 text-xs font-bold" onClick={()=>void onUpdate(item.id,{email_enabled:true,line_enabled:false})}>LINE希望を停止</button>}{item.line_status==='linked'&&<button className="rounded-lg border border-red-200 bg-white px-3 py-2 text-xs font-bold text-red-700" onClick={()=>void onUnlink(item)}>LINE連携解除</button>}{item.consented_at?<button className="rounded-lg border bg-white px-3 py-2 text-xs font-bold text-slate-600" onClick={()=>window.confirm(`${item.name||item.email} の通知同意を撤回し、LINE・メール通知を停止しますか？`)&&void onUpdate(item.id,{consent:false})}>通知停止・同意撤回</button>:<button className="rounded-lg border bg-white px-3 py-2 text-xs font-bold text-teal" onClick={()=>void onUpdate(item.id,{consent:true,email_enabled:true,line_enabled:false})}>メール通知を再開</button>}</div>}</article>)}</div>
    </section>
    {preview&&<section className="card mt-4 p-4"><div className="flex justify-between gap-3"><div><h2 className="m-0 text-lg font-black">QR連携案内</h2><p className="m-0 mt-1 text-xs text-slate-600">{preview.official_account_name}（{preview.line_basic_id}）／メール：{preview.email_delivery_status}</p></div><button className="border-0 bg-white text-sm font-bold" onClick={onClosePreview}>閉じる</button></div><div className="mt-4 grid place-items-center"><img className="w-52 max-w-full rounded-xl border bg-white p-2" src={preview.qr_png_data_url} alt={`${preview.official_account_name} LINE連携用QRコード`}/></div><a className="mt-3 block break-all rounded-xl bg-slate-50 p-3 text-sm font-bold text-teal" href={preview.line_link_url} rel="noreferrer">LINEアプリで連携を開く</a><div className="mt-3 rounded-xl bg-amber-50 p-3"><p className="m-0 text-xs text-slate-700">LINE一般サイトが開く場合は、下のメッセージをコピーし、LINEで「バナナ幼稚園」のトークへ貼り付けて送信してください。</p><code className="mt-2 block break-all rounded-lg bg-white p-2 text-xs">{preview.line_link_message}</code><button className="mt-2 w-full rounded-lg bg-slate-800 px-3 py-2 text-xs font-bold text-white" onClick={async()=>{try{await navigator.clipboard.writeText(preview.line_link_message);window.alert("連携メッセージをコピーしました")}catch{window.prompt("この連携メッセージをコピーしてください",preview.line_link_message)}}}>連携メッセージをコピー</button></div><p className="mb-0 mt-2 text-xs text-slate-600">有効期限：{formatDateTime(preview.expires_at)}。この画面を閉じると同じリンクは再表示できません。必要時は再発行してください。</p></section>}
    <section className="card mt-4 p-4"><div className="flex justify-between gap-3"><div><h2 className="m-0 text-lg font-black">通知履歴</h2><p className="m-0 mt-1 text-xs text-slate-600">LINEとメールは別々に送信結果を記録します。</p></div><span className="text-xs text-slate-500">直近 {Math.min(notifications.length,12)}件</span></div><div className="mt-3 divide-y">{notifications.slice(0,12).map(item=><article className="py-3 text-sm" key={item.id}><div className="flex justify-between gap-2"><b>{item.guardian_name||'通知先'}・{item.channel==='line'?'LINE':'メール'}</b><span className={`rounded-full px-2 py-1 text-xs font-bold ${statusClass(item.status)}`}>{item.status}</span></div><p className="m-0 mt-1 text-xs text-slate-600">{formatDateTime(item.created_at)}／試行 {item.attempt_count||0}回</p>{item.status==='failed'&&<><p className="m-0 mt-1 break-all text-xs text-red-700">{item.provider_response||'送信に失敗しました'}</p>{item.template_key==='line.link.v1'?<p className="m-0 mt-2 text-xs text-slate-600">QR案内は保護者欄から再発行してください。</p>:<button className="mt-2 rounded-lg bg-slate-800 px-3 py-2 text-xs font-bold text-white" onClick={()=>void onRetry(item)}>失敗した通知を再送</button>}</>}</article>)}{notifications.length===0&&<p className="text-sm text-slate-600">通知履歴はありません。</p>}</div></section>
  </>
}
function RouteRosterEditor({route,children,onEdit,onRemove,onSave}:{route:Route;children:RosterChild[];onEdit:()=>void;onRemove:()=>void;onSave:(ids:number[])=>void}) {
  const [selected,setSelected] = useState<number[]>(route.children.map(child=>child.id))
  useEffect(()=>setSelected(route.children.map(child=>child.id)),[route.children])
  const toggle=(id:number)=>setSelected(current=>current.includes(id)?current.filter(x=>x!==id):[...current,id])
  return <section className="border-t pt-3 mt-3 text-sm"><div className="flex justify-between gap-3"><b>{route.name}・{route.direction}</b><span className="text-slate-500">通常 {selected.length}人</span></div><div className="mt-1 flex gap-3"><button className="border-0 bg-white p-0 text-xs font-bold text-teal" onClick={onEdit}>便名を変更</button><button className="border-0 bg-white p-0 text-xs font-bold text-coral" onClick={onRemove}>削除</button></div><p className="m-0 mt-1 text-xs text-slate-600">このバスに通常乗る園児を選びます。</p><div className="mt-2 grid grid-cols-2 gap-2">{children.map(child=><label key={child.id} className="flex items-center gap-2 rounded-lg bg-slate-50 p-2"><input type="checkbox" checked={selected.includes(child.id)} onChange={()=>toggle(child.id)}/><span>{child.name}</span></label>)}</div><button className="mt-2 w-full rounded-xl bg-slate-800 p-2 font-bold text-white" onClick={()=>onSave(selected)}>通常名簿を保存</button></section>
}
function TripRosterEditor({children,selectedIds,onSave}:{children:RosterChild[];selectedIds:number[];onSave:(ids:number[])=>void}) {
  const [selected,setSelected] = useState<number[]>(selectedIds)
  const toggle=(id:number)=>setSelected(current=>current.includes(id)?current.filter(x=>x!==id):[...current,id])
  return <div className="border-t px-4 pb-4"><p className="mb-2 text-sm text-slate-600">欠席の園児を外す、臨時に乗る園児を追加できます。確認済みの園児は外せません。</p><div className="grid grid-cols-2 gap-2">{children.map(child=><label key={child.id} className="flex items-center gap-2 rounded-lg bg-slate-50 p-2 text-sm"><input type="checkbox" checked={selected.includes(child.id)} onChange={()=>toggle(child.id)}/><span>{child.name}</span></label>)}</div><button className="mt-3 w-full rounded-xl bg-teal p-3 font-bold text-white" onClick={()=>onSave(selected)}>当日の名簿を保存</button></div>
}
function ComingSoon({view}:{view:View}) { const title=view==='records'?'記録':'設定'; return <section className="card mt-4 p-5"><h1 className="m-0 text-xl font-black">{title}</h1><p className="text-sm text-slate-600">この画面は次の段階で実記録と園設定に接続します。</p></section> }
function Nav({active,onChange}:{active:View;onChange:(v:View)=>void}) { return <nav className="nav"><button className={active==='home'?'active':''} onClick={()=>onChange('home')}>⌂<span>ホーム</span></button><button className={active==='operation'?'active':''} onClick={()=>onChange('operation')}>🚌<span>運行</span></button><button className={active==='children'?'active':''} onClick={()=>onChange('children')}>👧<span>園児</span></button><button className={active==='records'?'active':''} onClick={()=>onChange('records')}>▤<span>記録</span></button><button className={active==='line'?'active':''} onClick={()=>onChange('line')}>💬<span>LINE</span></button><button className={active==='settings'?'active':''} onClick={()=>onChange('settings')}>⚙<span>設定</span></button></nav> }
type Detector={detect:(s:ImageBitmapSource)=>Promise<Array<{rawValue:string}>>}; declare global { interface Window { BarcodeDetector?:new(o:{formats:string[]})=>Detector } }
function Scanner({title,onRead,onClose}:{title:string;onRead:(v:string)=>void;onClose:()=>void}) {
  const video=useRef<HTMLVideoElement>(null),canvas=useRef<HTMLCanvasElement>(null),[manual,setManual]=useState(''),[cameraError,setCameraError]=useState(''),[scanStatus,setScanStatus]=useState('QRをカメラに近づけてください')
  useEffect(()=>{
    let stream:MediaStream|undefined,timer=0,done=false,detector:Detector|undefined
    const submit=(value:string)=>{const normalized=value.trim();if(done||!normalized)return;done=true;setScanStatus(`読み取りました：${normalized}`);onRead(normalized)}
    const scanWithCanvas=()=>{const v=video.current,c=canvas.current;if(!v||!c||v.readyState<2)return;const width=v.videoWidth,height=v.videoHeight;if(!width||!height)return;c.width=width;c.height=height;const context=c.getContext('2d',{willReadFrequently:true});if(!context)return;context.drawImage(v,0,0,width,height);const image=context.getImageData(0,0,width,height);const code=jsQR(image.data,width,height,{inversionAttempts:'attemptBoth'});if(code?.data)submit(code.data)}
    ;(async()=>{try{
      stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}}})
      if(video.current){video.current.srcObject=stream;await video.current.play().catch(()=>undefined)}
      if(window.BarcodeDetector) detector=new window.BarcodeDetector({formats:['qr_code']})
      timer=window.setInterval(async()=>{if(done)return;try{if(detector&&video.current&&video.current.readyState>=2){const found=await detector.detect(video.current);if(found[0])submit(found[0].rawValue)}}catch{detector=undefined}scanWithCanvas()},300)
    }catch{setCameraError('カメラを利用できません。権限を許可するか、QR文字列を入力してください。')}})()
    return()=>{done=true;clearInterval(timer);stream?.getTracks().forEach(track=>track.stop())}
  },[onRead])
  return <div className="modal"><div className="sheet"><h2 className="text-center text-xl font-black">{title}</h2><video ref={video} autoPlay playsInline muted className="w-full aspect-square bg-slate-900 rounded-2xl"/><canvas ref={canvas} className="hidden"/><p className="mb-0 mt-2 text-center text-xs text-slate-600">{cameraError||scanStatus}</p><div className="flex gap-2 mt-3"><input className="flex-1 border rounded-xl p-3" value={manual} onChange={e=>setManual(e.target.value)} placeholder="QR文字列"/><button className="bg-teal text-white rounded-xl px-3" onClick={()=>manual.trim()&&onRead(manual.trim())}>送信</button></div><button className="w-full p-3 border-0 bg-white" onClick={onClose}>キャンセル</button></div></div>
}


