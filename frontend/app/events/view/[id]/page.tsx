"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

type Event={id:number;title:string;description:string;date:string;time:string;venue:string;capacity:number};

export default function ViewEvent(){
  const {id}=useParams<{id:string}>(); const router=useRouter(); const eventId=Number(id);
  const [event,setEvent]=useState<Event|null>(null);
  useEffect(()=>{const events:Event[]=JSON.parse(localStorage.getItem("events")||"[]");const found=events.find(e=>e.id===eventId);if(!found){alert("Event not found.");router.push("/events");return;}setEvent(found);},[eventId,router]);
  if(!event)return <main className="min-h-screen bg-slate-100 px-6 py-10"><p>Loading event...</p></main>;
  return <main className="min-h-screen bg-slate-100 px-4 py-8 md:px-6"><div className="mx-auto max-w-3xl"><button onClick={()=>router.push("/events")} className="mb-5 text-sm font-medium text-blue-600">← Back to My Events</button><h1 className="text-3xl font-bold">Event Details</h1><p className="mt-2 text-slate-600">Complete information about this event.</p><div className="mt-8 rounded-2xl bg-white p-8 shadow-lg"><h2 className="text-3xl font-bold">{event.title}</h2><div className="mt-6"><p className="text-sm font-semibold uppercase text-slate-500">Description</p><p className="mt-2 text-lg text-slate-700">{event.description}</p></div><div className="mt-8 grid gap-5 md:grid-cols-2">{[["Date",event.date],["Time",event.time],["Venue",event.venue],["Maximum Capacity",`${event.capacity} participants`]].map(([a,b])=><div key={a} className="rounded-xl bg-slate-50 p-5"><p className="text-sm text-slate-500">{a}</p><p className="mt-2 text-lg font-semibold">{b}</p></div>)}</div><div className="mt-8 flex gap-4"><button onClick={()=>router.push(`/events/edit/${event.id}`)} className="w-1/2 rounded-lg bg-blue-600 py-3 font-semibold text-white">Edit Event</button><button onClick={()=>router.push("/events")} className="w-1/2 rounded-lg border py-3 font-semibold">Back to Events</button></div></div></div></main>;
}