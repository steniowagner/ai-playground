import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

const API_BASE_URL = process.env.TRIAGE_API_URL ?? "http://127.0.0.1:8000";
const COLLECTION_ROUTES_WITH_TRAILING_SLASH = new Set([
  "evaluations",
  "sample-questions",
  "threads",
]);

async function proxy(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const needsTrailingSlash =
    path.length === 1 && COLLECTION_ROUTES_WITH_TRAILING_SLASH.has(path[0]);
  const upstreamPath = `${path.join("/")}${needsTrailingSlash ? "/" : ""}`;
  const target = new URL(upstreamPath, `${API_BASE_URL.replace(/\/$/, "")}/`);
  target.search = request.nextUrl.search;
  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  const body = hasBody ? await request.arrayBuffer() : undefined;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  headers.set("accept", request.headers.get("accept") ?? "application/json");

  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: body?.byteLength ? body : undefined,
      cache: "no-store",
      redirect: "follow",
    });

    const responseHeaders = new Headers(upstream.headers);
    responseHeaders.delete("content-length");
    responseHeaders.delete("content-encoding");
    responseHeaders.set("cache-control", "no-store");

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error(`Failed to proxy ${request.method} ${target.href}`, error);
    return Response.json(
      {
        detail: "The triage API is unavailable. Start the FastAPI server and try again.",
      },
      { status: 502 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
