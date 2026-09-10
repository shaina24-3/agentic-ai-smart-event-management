"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Event={id:number;title:string;description:string;date:string;time:string;venue:string;capacity:number};

export default function UpcomingEvents(){
 const router=useRouter();const [events,setEvents]=useState<Event[]>([]);
 useEffect(()=>{const load=()=>{const all:Event[]=JSON.parse(localStorage.getItem("events")||"[]");const today=new Date().toISOString().split("T")[0];setEvents(all.filter(e=>e.date>=today).sort((a,b)=>a.date.localeCompare(b.date)));};load();window.addEventListener("focus",load);return()=>window.removeEventListener("focus",load);},[]);
 return <main className="min-h-screen bg-slate-100 px-4 py-8 md:px-6"><div className="mx-auto max-w-6xl"><h1 className="text-3xl font-bold">Upcoming Events</h1><p className="mt-2 text-slate-600">Check the events that are coming up.</p>{events.length?<div className="mt-8 grid gap-6 md:grid-cols-2">{events.map(e=><div key={e.id} className="rounded-xl bg-white p-6 shadow"><h2 className="text-2xl font-semibold">{e.title}</h2><p className="mt-3 text-slate-600">{e.description}</p><div className="mt-5 space-y-2 text-sm"><p><strong>Date:</strong> {e.date}</p><p><strong>Time:</strong> {e.time}</p><p><strong>Venue:</strong> {e.venue}</p><p><strong>Capacity:</strong> {e.capacity}</p></div><button onClick={()=>router.push(`/events/view/${e.id}`)} className="mt-5 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white">View Event</button></div>)}</div>:<div className="mt-8 rounded-xl bg-white p-8 text-center shadow"><h2 className="text-xl font-semibold">No Upcoming Events</h2><p className="mt-2 text-slate-500">There are no upcoming events available.</p><button onClick={()=>router.push("/create")} className="mt-5 rounded-lg bg-blue-600 px-5 py-3 font-medium text-white">Create Event</button></div>}</div></main>;
}