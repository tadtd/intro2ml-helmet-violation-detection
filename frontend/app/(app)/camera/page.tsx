"use client";

import { useRef, useState } from "react";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function CameraPage() {
  const socketRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState("Disconnected");

  function connect() {
    const wsUrl = apiBaseUrl.replace(/^http/, "ws");
    const socket = new WebSocket(`${wsUrl}/ws/camera`);
    socketRef.current = socket;
    socket.onopen = () => setStatus("Connected");
    socket.onmessage = (event) => setStatus(event.data);
    socket.onclose = () => setStatus("Disconnected");
  }

  function disconnect() {
    socketRef.current?.close();
  }

  return (
    <section>
      <h1 className="text-3xl font-semibold">Camera Realtime</h1>
      <div className="mt-8 aspect-video rounded-md border border-[#d8e1dc] bg-[#17211c]" />
      <div className="mt-5 flex gap-3">
        <button
          className="rounded-md bg-[#1e5a45] px-4 py-2 text-sm font-semibold text-white"
          onClick={connect}
        >
          Connect
        </button>
        <button
          className="rounded-md border border-[#1e5a45] px-4 py-2 text-sm font-semibold text-[#1e5a45]"
          onClick={disconnect}
        >
          Disconnect
        </button>
      </div>
      <p className="mt-4 text-sm text-[#53635b]">{status}</p>
    </section>
  );
}
