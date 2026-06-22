"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/utils/supabase/client";

type Violation = {
  id: string;
  image_url: string | null;
  timestamp: string;
  track_id: number | null;
  model_used: string | null;
};

export default function DashboardPage() {
  const [items, setItems] = useState<Violation[]>([]);

  useEffect(() => {
    const supabase = createClient();
    supabase
      .from("violations")
      .select("*")
      .order("timestamp", { ascending: false })
      .then(({ data }) => setItems((data ?? []) as Violation[]));

    const channel = supabase
      .channel("violations-dashboard")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "violations" },
        (payload) => setItems((current) => [payload.new as Violation, ...current]),
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  return (
    <section>
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">Violations</h1>
          <p className="mt-2 text-sm text-[#53635b]">
            Captured violation metadata from upload and camera workflows.
          </p>
        </div>
        <a
          className="rounded-md bg-[#1e5a45] px-4 py-2 text-sm font-semibold text-white"
          href="/upload"
        >
          Upload video
        </a>
      </div>

      <div className="mt-8 overflow-hidden rounded-md border border-[#d8e1dc] bg-white">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="bg-[#edf3f0] text-[#53635b]">
            <tr>
              <th className="px-4 py-3 font-medium">Image</th>
              <th className="px-4 py-3 font-medium">Timestamp</th>
              <th className="px-4 py-3 font-medium">Track ID</th>
              <th className="px-4 py-3 font-medium">Model</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr className="border-t border-[#edf3f0]" key={item.id}>
                <td className="px-4 py-3">
                  {item.image_url ? (
                    <a className="font-medium text-[#1e5a45]" href={item.image_url}>
                      Open image
                    </a>
                  ) : (
                    "Pending"
                  )}
                </td>
                <td className="px-4 py-3">{new Date(item.timestamp).toLocaleString()}</td>
                <td className="px-4 py-3">{item.track_id ?? "-"}</td>
                <td className="px-4 py-3">{item.model_used ?? "-"}</td>
              </tr>
            ))}
            {items.length === 0 ? (
              <tr>
                <td className="px-4 py-10 text-center text-[#53635b]" colSpan={4}>
                  No violations recorded yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
