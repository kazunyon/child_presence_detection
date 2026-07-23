import { useEffect, useRef, useState } from 'react'

type View = 'home' | 'operation' | 'records' | 'settings'
type Mode = '乗車' | '降車'
type Operator = { id:number; name:string; role:string }
type Attendance = { child_id:number; name:string; boarded_at:string|null; alighted_at:string|null }
type TripStatus = { trip_id:number; status:string; boarded:number; alighted:number; unconfirmed:number; tail_confirmed:boolean; third_party_confirmed:boolean; children:Attendance[] }
type Route = { id:number; name:string; direction:string; vehicle_id:number|null }
type Vehicle = { id:number; name:string }
type Dashboard = { organization_name:string; date:string; today_trip_count:number; active_trip_count:number; completed_trip_count:number; unconfirmed_count:number }
type OfflineEvent = { client_event_id:string; trip_id:number; qr_token:string; event_type:Mode }

const API = (import.meta.env.VITE_API_BASE_URL || '').trim() || 'http://127.0.0.1:8000'
const OFFLINE_KEY = 'mamoru-bus-offline-events'
const queue = (): OfflineEvent[] => JSON.parse(localStorage.getItem(OFFLINE_KEY) || '[]')
const saveQueue = (items: OfflineEvent[]) => localStorage.setItem(OFFLINE_KEY, JSON.stringify(items))
const messageOf = async (response:Response) => { try { const body = await response.json(); return body.detail || '記録を保存できませんでした' } catch { return '記録を保存できませんでした' } }

export default function App() {
  const [view,setView] = useState<View>('home')
  const [token,setToken] = useState<string|null>(localStorage.getItem('mamoru-bus-token'))
  const [operator,setOperator] = useState<Operator|null>(null)
  const [dashboard,setDashboard] = useState<Dashboard|null>(null)
  const [routes,setRoutes] = useState<Route[]>([])
  const [vehicles,setVehicles] = useState<Vehicle[]>([])
  const [trip,setTrip] = useState<TripStatus|null>(null)
  const [mode,setMode] = useState<Mode>('乗車')
  const [scanner,setScanner] = useState<'child'|'tail'|null>(null)
  const [message,setMessage] = useState('ログインして本日の状況を確認してください')
  const [offlineCount,setOfflineCount] = useState(queue().length)
  const [locationStatus,setLocationStatus] = useState('')
  const auth = (init:RequestInit={}) => ({...init, headers:{'Content-Type':'application/json', Authorization:`Bearer ${token}`,...(init.headers||{})}})
  const logout = () => { localStorage.removeItem('mamoru-bus-token'); setToken(null); setOperator(null); setTrip(null); setDashboard(null); setRoutes([]); setView('home'); setMessage('ログアウトしました') }
  const loadDashboard = async () => { if (!token) return; const r = await fetch(`${API}/api/dashboard`,auth()); if (!r.ok) throw new Error(); setDashboard(await r.json()) }
  const loadBootstrap = async () => { const [routeResponse, vehicleResponse] = await Promise.all([fetch(`${API}/api/routes`,auth()), fetch(`${API}/api/vehicles`,auth())]); if (!routeResponse.ok || !vehicleResponse.ok) throw new Error(); setRoutes(await routeResponse.json()); setVehicles(await vehicleResponse.json()) }
  const refresh = async (tripId:number) => { const r = await fetch(`${API}/api/trips/${tripId}/status`,auth()); if (!r.ok) throw new Error(await messageOf(r)); setTrip(await r.json()); await loadDashboard() }
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
    try { const r = await fetch(`${API}/api/trips?status_filter=運行中`,auth()); if (!r.ok) throw new Error(); const active = await r.json(); setView('operation'); if (active[0]) { await refresh(active[0].trip_id); setMessage('進行中の便を表示しています') } else { setTrip(null); setMessage('便を選択して運行を開始してください') } } catch { setMessage('進行中の便を取得できません。API接続を確認してください。') }
  }
  const startTrip = async (route:Route) => {
    try { const r = await fetch(`${API}/api/trips`,auth({method:'POST',body:JSON.stringify({route_id:route.id,vehicle_id:route.vehicle_id,direction:route.direction})})); if (!r.ok) throw new Error(await messageOf(r)); const created = await r.json(); await refresh(created.id); setMessage(`${route.name} を開始しました。乗車確認を行ってください。`) } catch (error) { setMessage(error instanceof Error ? error.message : '便を開始できませんでした') }
  }
  const scanChild = async (qr:string) => {
    if (!trip) return
    try { const r = await fetch(`${API}/api/trips/${trip.trip_id}/scans`,auth({method:'POST',body:JSON.stringify({qr_token:qr,event_type:mode})})); if (!r.ok) throw new Error(await messageOf(r)); await refresh(trip.trip_id); setScanner(null); setMessage(`${mode}を記録しました`) }
    catch (error) {
      setScanner(null)
      if (!navigator.onLine) { const items=[...queue(),{client_event_id:crypto.randomUUID(),trip_id:trip.trip_id,qr_token:qr,event_type:mode}]; saveQueue(items); setOfflineCount(items.length); setMessage('オフラインのため、記録をこの端末に保留しました') }
      else setMessage(error instanceof Error ? error.message : 'QR記録を保存できませんでした')
    }
  }
  const tail = async (qr:string) => {
    if (!trip) return
    if (qr !== 'bus-tail-2') { setMessage('このQRは最後尾確認用ではありません'); return }
    setLocationStatus('位置情報を取得しています…')
    let latitude:string|undefined, longitude:string|undefined
    try {
      if (!navigator.geolocation) throw new Error('この端末は位置情報に対応していません')
      const position = await new Promise<GeolocationPosition>((resolve,reject) => navigator.geolocation.getCurrentPosition(resolve,reject,{timeout:10000,enableHighAccuracy:true}))
      latitude=String(position.coords.latitude); longitude=String(position.coords.longitude)
      const r = await fetch(`${API}/api/vehicle-checks`,auth({method:'POST',body:JSON.stringify({trip_id:trip.trip_id,check_type:'tail_qr',qr_token:qr,latitude,longitude})}))
      if (!r.ok) throw new Error(await messageOf(r))
      await refresh(trip.trip_id); setScanner(null); setLocationStatus('位置情報を付けて記録しました'); setMessage('最後尾確認を記録しました。第三者確認へ進んでください。')
    } catch (error) { setLocationStatus('位置情報または最後尾確認を保存できませんでした'); setMessage(error instanceof Error ? error.message : '最後尾確認を保存できませんでした') }
  }
  const approve = async (staffId:number,pin:string) => { if (!trip) return; try { const r=await fetch(`${API}/api/trips/${trip.trip_id}/third-party-approval`,auth({method:'POST',body:JSON.stringify({staff_id:staffId,pin})})); if(!r.ok) throw new Error(await messageOf(r)); await refresh(trip.trip_id); setMessage('第三者確認を記録しました。完了処理が可能です。') } catch(error) { setMessage(error instanceof Error ? error.message : '第三者確認を保存できませんでした') } }
  const complete = async () => { if (!trip) return; try { const r=await fetch(`${API}/api/trips/${trip.trip_id}/complete`,auth({method:'POST'})); if(!r.ok) throw new Error(await messageOf(r)); await refresh(trip.trip_id); setMessage('便の安全確認が完了しました') } catch(error) { setMessage(error instanceof Error ? error.message : '便を完了できませんでした') } }
  const content = !operator ? <Login onLogin={login}/> : view==='home' ? <Home dashboard={dashboard} onOperation={openOperation}/> : view==='operation' ? <Operation trip={trip} routes={routes} vehicles={vehicles} mode={mode} setMode={setMode} onStart={startTrip} onScan={()=>setScanner('child')} onTail={()=>setScanner('tail')} locationStatus={locationStatus} onApprove={approve} onComplete={complete}/> : <ComingSoon view={view}/>
  return <div className="app"><header className="px-5 pt-5 pb-4 bg-white flex justify-between"><div><div className="text-xs font-bold text-teal">送迎バス安全確認</div><b className="text-xl">まもるバス</b></div><button className="border-0 bg-white text-sm font-bold" onClick={operator?logout:undefined}>{operator?.name??'ログイン'}</button></header><main className="px-5 pb-24">{offlineCount>0&&<button className="w-full rounded-xl bg-amber-100 p-3 text-sm font-bold text-amber-900" onClick={sync}>未同期の記録 {offlineCount} 件 — 同期する</button>}<section className="mt-3 rounded-2xl bg-sand p-4 border border-amber-100"><p className="m-0 text-sm">{message}</p></section>{content}</main>{operator&&<Nav active={view} onChange={setView}/>} {scanner&&<Scanner title={scanner==='child'?`${mode}QRを読み取る`:'最後尾QRを読み取る'} onRead={scanner==='child'?scanChild:tail} onClose={()=>setScanner(null)}/>}</div>
}
function Home({dashboard,onOperation}:{dashboard:Dashboard|null;onOperation:()=>void}) { return <><section className="mt-4 rounded-3xl bg-teal p-5 text-white"><p className="m-0 text-sm opacity-85">{dashboard?.organization_name||'園'}</p><h1 className="mt-1 mb-2 text-2xl font-black">本日の送迎状況</h1><p className="m-0 text-sm">{dashboard?.date||'集計を読み込み中です'}</p></section><section className="grid grid-cols-3 gap-3 mt-4"><Metric label="本日の便" value={dashboard?.today_trip_count||0}/><Metric label="運行中" value={dashboard?.active_trip_count||0}/><Metric label="未確認" value={dashboard?.unconfirmed_count||0} danger={(dashboard?.unconfirmed_count||0)>0}/></section><section className="card mt-4 p-5"><h2 className="m-0 text-lg font-black">運行</h2><p className="text-sm text-slate-600">便を選択して開始、または進行中の便を再開します。</p><button className="big-action" onClick={onOperation}>運行画面を開く</button></section><section className="card mt-4 p-5"><h2 className="m-0 text-lg font-black">安全上の注意</h2><p className="mb-0 text-sm text-slate-600">未降車の園児が1人でもいる間は、最後尾確認・第三者確認・完了はできません。必ず車内を目視で確認してください。</p></section></> }
function Metric({label,value,danger}:{label:string;value:number;danger?:boolean}) { return <section className="card p-3 text-center"><b className={'text-2xl '+(danger?'text-coral':'text-teal')}>{value}</b><br/><span className="text-xs">{label}</span></section> }
function Operation({trip,routes,vehicles,mode,setMode,onStart,onScan,onTail,locationStatus,onApprove,onComplete}:{trip:TripStatus|null;routes:Route[];vehicles:Vehicle[];mode:Mode;setMode:(v:Mode)=>void;onStart:(r:Route)=>void;onScan:()=>void;onTail:()=>void;locationStatus:string;onApprove:(id:number,pin:string)=>void;onComplete:()=>void}) {
  if (!trip) return <section className="card mt-4 p-5"><h1 className="m-0 text-xl font-black">便を選択</h1><p className="text-sm text-slate-600">開始する便を選んでください。進行中の便はホームから再開できます。</p>{routes.length ? routes.map(route => <button key={route.id} className="w-full mt-3 rounded-2xl border border-slate-200 bg-white p-4 text-left" onClick={()=>onStart(route)}><b>{route.name}</b><br/><span className="text-sm text-slate-600">{route.direction}・{vehicles.find(v=>v.id===route.vehicle_id)?.name||'車両未設定'}</span></button>) : <p className="text-sm text-coral">登録済みの便がありません。設定で便を登録してください。</p>}</section>
  const allAlighted = trip.boarded > 0 && trip.unconfirmed === 0
  return <><section className="card mt-4 p-4"><h1 className="m-0 text-xl font-black">運行便 #{trip.trip_id}</h1><div className="grid grid-cols-3 text-center mt-3"><Metric label="乗車" value={trip.boarded}/><Metric label="降車" value={trip.alighted}/><Metric label="未降車" value={trip.unconfirmed} danger={trip.unconfirmed>0}/></div></section>{trip.unconfirmed>0&&<section className="mt-4 rounded-2xl border-2 border-coral bg-red-50 p-4 text-red-800"><b>未降車の園児が {trip.unconfirmed} 人います</b><p className="m-0 mt-1 text-sm">対象園児を確認し、降車QRを記録するまで安全確認・完了は行えません。</p></section>}<div className="grid grid-cols-2 gap-3 mt-4"><button className={'rounded-2xl p-4 font-bold border-2 '+(mode==='乗車'?'bg-sky-600 text-white border-sky-600':'bg-white border-slate-200')} onClick={()=>setMode('乗車')}>乗車を記録</button><button className={'rounded-2xl p-4 font-bold border-2 '+(mode==='降車'?'bg-teal text-white border-teal':'bg-white border-slate-200')} onClick={()=>setMode('降車')}>降車を記録</button></div><button className="big-action mt-4" onClick={onScan}>QRを読み取る</button><section className="card mt-4 overflow-hidden"><h2 className="p-4 m-0 text-lg font-black">この便の園児</h2>{trip.children.length===0?<p className="px-4 pb-4 text-sm text-slate-600">乗車記録はまだありません。</p>:trip.children.map(x=><div className="px-4 py-3 border-t flex justify-between" key={x.child_id}><span>{x.name}</span><span className={'badge '+(!x.boarded_at?'bg-slate-100':x.alighted_at?'bg-teal text-white':'bg-red-100 text-red-800')}>{!x.boarded_at?'未乗車':x.alighted_at?'降車済':'未降車'}</span></div>)}</section><section className="card mt-4 p-4"><h2 className="m-0 text-lg font-black">完了前の安全確認</h2><p className="text-sm text-slate-600">すべての乗車園児の降車確認後に、車内目視・最後尾QR・第三者確認を実施します。</p><button disabled={!allAlighted||trip.tail_confirmed} className="big-action mt-2 disabled:opacity-40" onClick={onTail}>{trip.tail_confirmed?'最後尾確認済み':'最後尾QRを確認する'}</button>{locationStatus&&<p className="text-xs text-slate-600">{locationStatus}</p>}{trip.tail_confirmed&&!trip.third_party_confirmed&&<ThirdApproval onApprove={onApprove}/>}<button disabled={!allAlighted||!trip.tail_confirmed||!trip.third_party_confirmed||trip.status==='完了'} className="mt-3 w-full rounded-xl bg-slate-800 p-4 font-bold text-white disabled:opacity-40" onClick={onComplete}>{trip.status==='完了'?'この便は完了しています':'便を完了する'}</button></section></>
}
function Login({onLogin}:{onLogin:(x:Operator,t:string)=>void}) { const [id,setId]=useState(''),[pin,setPin]=useState(''),[error,setError]=useState(''); const submit=async()=>{try{const r=await fetch(`${API}/api/auth/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({staff_id:Number(id),pin})});if(!r.ok)throw new Error(await messageOf(r));const data=await r.json();onLogin(data.staff,data.access_token)}catch(e){setError(e instanceof Error?e.message:'本番APIへログインできません')}};return <section className="card mt-4 p-5"><h1 className="m-0 text-xl font-black">職員ログイン</h1><p className="text-sm">本番APIの職員IDとPINを入力してください。</p><input className="w-full border rounded-xl p-3 mb-2" inputMode="numeric" value={id} onChange={e=>setId(e.target.value)} placeholder="職員ID"/><input className="w-full border rounded-xl p-3" type="password" value={pin} onChange={e=>setPin(e.target.value)} placeholder="PIN"/><button className="big-action mt-3" onClick={submit}>ログイン</button>{error&&<p className="text-sm text-red-700">{error}</p>}</section> }
function ThirdApproval({onApprove}:{onApprove:(id:number,pin:string)=>void}) { const [id,setId]=useState(''),[pin,setPin]=useState(''); return <div className="mt-3"><h3 className="text-base font-bold">第三者確認</h3><p className="text-sm text-slate-600">運転担当者以外の確認者が職員IDとPINを入力します。</p><input className="w-full border rounded-xl p-3 mb-2" value={id} onChange={e=>setId(e.target.value)} placeholder="第三者確認者の職員ID"/><input className="w-full border rounded-xl p-3" type="password" value={pin} onChange={e=>setPin(e.target.value)} placeholder="第三者確認者のPIN"/><button className="mt-2 w-full rounded-xl bg-teal p-3 font-bold text-white" onClick={()=>id&&pin&&onApprove(Number(id),pin)}>第三者承認する</button></div> }
function ComingSoon({view}:{view:View}) { const title=view==='records'?'記録':'設定'; return <section className="card mt-4 p-5"><h1 className="m-0 text-xl font-black">{title}</h1><p className="text-sm text-slate-600">この画面は次の段階で実記録と園設定に接続します。</p></section> }
function Nav({active,onChange}:{active:View;onChange:(v:View)=>void}) { return <nav className="nav"><button className={active==='home'?'active':''} onClick={()=>onChange('home')}>⌂<span>ホーム</span></button><button className={active==='operation'?'active':''} onClick={()=>onChange('operation')}>🚌<span>運行</span></button><button className={active==='records'?'active':''} onClick={()=>onChange('records')}>▤<span>記録</span></button><button className={active==='settings'?'active':''} onClick={()=>onChange('settings')}>⚙<span>設定</span></button></nav> }
type Detector={detect:(s:ImageBitmapSource)=>Promise<Array<{rawValue:string}>>}; declare global { interface Window { BarcodeDetector?:new(o:{formats:string[]})=>Detector } }
function Scanner({title,onRead,onClose}:{title:string;onRead:(v:string)=>void;onClose:()=>void}) { const video=useRef<HTMLVideoElement>(null),[manual,setManual]=useState(''),[cameraError,setCameraError]=useState(''); useEffect(()=>{let stream:MediaStream|undefined;let timer=0;(async()=>{try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}});if(video.current)video.current.srcObject=stream;if(window.BarcodeDetector){const detector=new window.BarcodeDetector({formats:['qr_code']});timer=window.setInterval(async()=>{if(video.current){const found=await detector.detect(video.current);if(found[0])onRead(found[0].rawValue)}},700)}}catch{setCameraError('カメラを利用できません。権限を許可するか、QR文字列を入力してください。')}})();return()=>{clearInterval(timer);stream?.getTracks().forEach(track=>track.stop())}},[onRead]);return <div className="modal"><div className="sheet"><h2 className="text-center text-xl font-black">{title}</h2><video ref={video} autoPlay playsInline muted className="w-full aspect-square bg-slate-900 rounded-2xl"/>{cameraError&&<p className="text-sm text-red-700">{cameraError}</p>}<div className="flex gap-2 mt-3"><input className="flex-1 border rounded-xl p-3" value={manual} onChange={e=>setManual(e.target.value)} placeholder="QR文字列"/><button className="bg-teal text-white rounded-xl px-3" onClick={()=>manual&&onRead(manual)}>送信</button></div><button className="w-full p-3 border-0 bg-white" onClick={onClose}>キャンセル</button></div></div> }