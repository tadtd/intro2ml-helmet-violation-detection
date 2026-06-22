"use client";

import { FormEvent, useState } from "react";
import { createClient } from "@/utils/supabase/client";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function UploadPage() {
  const [status, setStatus] = useState("Idle");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const supabase = createClient();
    const { data: sessionData } = await supabase.auth.getSession();
    const token = sessionData.session?.access_token;

    if (!token) {
      setStatus("Sign in before uploading.");
      return;
    }

    setStatus("Uploading");
    const response = await fetch(`${apiBaseUrl}/videos/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: data,
    });
    const payload = await response.json();
    setStatus(response.ok ? `Queued task ${payload.task_id}` : payload.detail);
  }

  return (
    <section className="max-w-2xl">
      <h1 className="text-3xl font-semibold">Upload Video</h1>
      <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
        <label className="block">
          <span className="text-sm font-medium">Model</span>
          <select
            className="mt-2 w-full rounded-md border border-[#cbd8d1] bg-white px-3 py-2"
            defaultValue="yolo"
            name="model_name"
          >
            <option value="yolo">YOLO</option>
            <option value="rtdetr">RT-DETR</option>
            <option value="fasterrcnn">Faster R-CNN</option>
          </select>
        </label>
        <label className="block">
          <span className="text-sm font-medium">Video file</span>
          <input
            accept="video/*"
            className="mt-2 w-full rounded-md border border-[#cbd8d1] bg-white px-3 py-2"
            name="video"
            required
            type="file"
          />
        </label>
        <button className="rounded-md bg-[#1e5a45] px-4 py-2 text-sm font-semibold text-white">
          Queue processing
        </button>
      </form>
      <p className="mt-6 text-sm text-[#53635b]">{status}</p>
    </section>
  );
}
