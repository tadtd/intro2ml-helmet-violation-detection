const stats = [
  { label: "Queued videos", value: "0" },
  { label: "Live streams", value: "0" },
  { label: "Violations today", value: "0" },
  { label: "Models ready", value: "3" },
];

const workflows = [
  {
    title: "Video upload",
    description: "Queue offline processing with YOLO, RT-DETR, or Faster R-CNN.",
    action: "Upload",
    href: "/upload",
  },
  {
    title: "Camera realtime",
    description: "Stream frames through the FastAPI WebSocket for live checks.",
    action: "Open camera",
    href: "/camera",
  },
  {
    title: "Violations",
    description: "Review captured images, timestamps, track IDs, and model source.",
    action: "View dashboard",
    href: "/dashboard",
  },
];

export default function Page() {
  return (
    <main className="min-h-screen bg-[#f7f9f8] text-[#17211c]">
      <section className="border-b border-[#d8e1dc] bg-white">
        <div className="mx-auto flex min-h-[88vh] max-w-6xl flex-col justify-between px-6 py-8">
          <nav className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-[#5f7168]">
                Helmet Violation Detection
              </p>
              <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight md:text-6xl">
                Detection operations for upload review and live camera checks.
              </h1>
            </div>
            <a
              className="hidden rounded-md bg-[#1e5a45] px-4 py-2 text-sm font-semibold text-white md:inline-flex"
              href="/login"
            >
              Sign in
            </a>
          </nav>

          <div className="grid gap-4 py-10 md:grid-cols-4">
            {stats.map((item) => (
              <div
                className="border-l border-[#cbd8d1] py-3 pl-4"
                key={item.label}
              >
                <div className="text-3xl font-semibold">{item.value}</div>
                <div className="mt-1 text-sm text-[#5f7168]">{item.label}</div>
              </div>
            ))}
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {workflows.map((item) => (
              <article
                className="rounded-md border border-[#d8e1dc] bg-[#fbfcfb] p-5"
                key={item.title}
              >
                <h2 className="text-lg font-semibold">{item.title}</h2>
                <p className="mt-3 min-h-16 text-sm leading-6 text-[#53635b]">
                  {item.description}
                </p>
                <a
                  className="mt-5 inline-flex rounded-md border border-[#1e5a45] px-3 py-2 text-sm font-semibold text-[#1e5a45]"
                  href={item.href}
                >
                  {item.action}
                </a>
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
