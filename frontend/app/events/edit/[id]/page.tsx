"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

type Event={id:number;title:string;description:string;date:string;time:string;venue:string;capacity:number};

export default function EditEvent(){
  const {id}=useParams<{id:string}>(); const router=useRouter(); const eventId=Number(id);
  const [form,setForm]=useState({title:"",description:"",date:"",time:"",venue:"",capacity:""});
  useEffect(()=>{const events:Event[]=JSON.parse(localStorage.getItem("events")||"[]"); const e=events.find(x=>x.id===eventId); if(!e){alert("Event not found.");router.push("/events");return;} setForm({title:e.title,description:e.description,date:e.date,time:e.time,venue:e.venue,capacity:String(e.capacity)});},[eventId,router]);
  const update=(k:string,v:string)=>setForm(f=>({...f,[k]:v}));
  const save=(e:React.FormEvent)=>{e.preventDefault();if(Object.values(form).some(v=>!v.trim()))return alert("Please fill in all fields.");const events:Event[]=JSON.parse(localStorage.getItem("events")||"[]");localStorage.setItem("events",JSON.stringify(events.map(x=>x.id===eventId?{...x,...form,capacity:Number(form.capacity)}:x)));alert("Event updated successfully!");router.push("/events");};
  return <main className="min-h-screen bg-slate-100 px-4 py-8 md:px-6"><div className="mx-auto max-w-3xl"><button onClick={()=>router.push("/events")} className="mb-5 text-sm font-medium text-blue-600">← Back to My Events</button><h1 className="text-3xl font-bold">Edit Event</h1><form onSubmit={save} className="mt-8 space-y-5 rounded-2xl bg-white p-8 shadow-lg">{(["title","description","date","time","venue","capacity"] as const).map(k=><div key={k}><label className="mb-2 block text-sm font-medium">{k==="title"?"Event Title":k==="description"?"Description":k==="date"?"Event Date":k==="time"?"Event Time":k==="venue"?"Venue":"Capacity"}</label>{k==="description"?<textarea rows={4} value={form[k]} onChange={e=>update(k,e.target.value)} className="w-full rounded-lg border px-4 py-3"/>:<input type={k==="date"?"date":k==="time"?"time":k==="capacity"?"number":"text"} min={k==="capacity"?"1":undefined} value={form[k]} onChange={e=>update(k,e.target.value)} className="w-full rounded-lg border px-4 py-3"/></div>)}<div className="flex gap-4"><button type="button" onClick={()=>router.push("/events")} className="w-1/2 rounded-lg border py-3 font-semibold">Cancel</button><button className="w-1/2 rounded-lg bg-blue-600 py-3 font-semibold text-white">Update Event</button></div></form></div></main>;
}