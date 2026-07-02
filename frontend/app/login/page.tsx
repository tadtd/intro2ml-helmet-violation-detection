"use client";

import { FormEvent, useState } from "react";
import { createClient } from "@/utils/supabase/client";

export default function LoginPage() {
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email"));
    const password = String(form.get("password"));
    const supabase = createClient();
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setMessage(error ? error.message : "Signed in.");
  }

  return (
    <main className="min-h-screen bg-[#f7f9f8] px-6 py-12 text-[#17211c]">
      <section className="mx-auto max-w-md">
        <h1 className="text-3xl font-semibold">Sign In</h1>
        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <label className="block">
            <span className="text-sm font-medium">Email</span>
            <input
              className="mt-2 w-full rounded-md border border-[#cbd8d1] bg-white px-3 py-2"
              name="email"
              required
              type="email"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium">Password</span>
            <input
              className="mt-2 w-full rounded-md border border-[#cbd8d1] bg-white px-3 py-2"
              name="password"
              required
              type="password"
            />
          </label>
          <button className="rounded-md bg-[#1e5a45] px-4 py-2 text-sm font-semibold text-white">
            Sign in
          </button>
        </form>
        <p className="mt-5 text-sm text-[#53635b]">{message}</p>
      </section>
    </main>
  );
}
